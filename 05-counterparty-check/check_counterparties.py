"""
Check counterparties by tax ID in a public company-check service and write
the current name and the status of each into the table.

December 2024: written by ChatGPT to my specification over 8 rounds, then run
on a table of several hundred counterparties. Cleaned up for publication in
October 2026: settings at the top, English comments and statuses, a local copy
of a service page to run it on, and 3 fixes, marked "FIX" in the code and
listed in the README.

The table: column A is the counterparty's name, column B its tax ID, and
column C is filled in by the script. For every tax ID the script opens the
service, types the ID into the search box, waits for the result card and reads
2 lines from it: the current name and the status. The name is written only
when the card was read; the status only when the page states it.

Run on the fictional sample:
    pip install selenium openpyxl
    python check_counterparties.py
"""
import time
from pathlib import Path

import openpyxl
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

HERE = Path(__file__).resolve().parent

# ---- Settings -------------------------------------------------------------

TABLE = HERE / "sample" / "counterparties.xlsx"
# None writes into the table itself, as in 2024. For the sample, a new file.
OUTPUT = HERE / "sample" / "counterparties_checked.xlsx"
NAME_COL, TAX_ID_COL, STATUS_COL = 1, 2, 3  # A, B, C

# The service. In 2024 this was a real public company-check page; here it is
# a local copy with fictional data, built the same way: a search box, and a
# card which appears under it with the name on line 1 and the status on line 2.
SERVICE_URL = (HERE / "sample" / "mock_service" / "index.html").as_uri()
SEARCH_BOX = "input[data-qa-type='search.input']"
RESULT_CARD = "div[data-qa-type='result.popover']"
NOT_FOUND_TEXT = "No such counterparty"
ACTIVE_WORDS = ["operating"]       # the real service: "Ведёт деятельность"
LIQUIDATED_WORDS = ["liquidated"]  # the real service: "ликвидирован(а)"

LOAD_DELAY = 5     # seconds: lets the card fill in before it is read
RESULT_WAIT = 20   # seconds to wait for the card to appear at all
NOT_FOUND_WAIT = 5 # then seconds to look for the "no such counterparty" note

BROWSER = "firefox"   # as in 2024 (ChromeDriver was not available), or "chrome"
DRIVER_PATH = None    # None: Selenium finds the driver itself
BROWSER_BINARY = None # None: the browser installed on the computer
HEADLESS = False      # True: no browser window

# What goes into the status column.
ACTIVE = "Active"
LIQUIDATED = "Liquidated"
NOT_FOUND = "Not found"              # only when the page says so
UNCLEAR = "Status unclear"           # the card was read, the status is neither
NOT_READ = "Could not read status"   # the card did not load in time
SEARCH_ERROR = "Search error"        # the page or the search box failed

# FIX 1: the second pass goes over the rows where the page failed. In the
# 2024 version it went over the "Not found" rows instead, which are the only
# ones the page had answered for certain.
RETRY = {NOT_READ, SEARCH_ERROR}

# ---------------------------------------------------------------------------


def start_browser():
    if BROWSER == "chrome":
        options = webdriver.ChromeOptions()
        if HEADLESS:
            options.add_argument("--headless=new")
        if BROWSER_BINARY:
            options.binary_location = str(BROWSER_BINARY)
        service = webdriver.ChromeService(executable_path=DRIVER_PATH)
        return webdriver.Chrome(service=service, options=options)
    options = webdriver.FirefoxOptions()
    if HEADLESS:
        options.add_argument("-headless")
    if BROWSER_BINARY:
        options.binary_location = str(BROWSER_BINARY)
    service = webdriver.FirefoxService(executable_path=DRIVER_PATH)
    return webdriver.Firefox(service=service, options=options)


def read_status(line):
    text = line.lower()
    if any(w in text for w in ACTIVE_WORDS):
        return ACTIVE
    # "Liquidated" only when the card does not also say it is operating.
    if any(w in text for w in LIQUIDATED_WORDS):
        return LIQUIDATED
    return UNCLEAR


def check_one(driver, tax_id):
    """Return (name or None, status) for 1 tax ID."""
    driver.get(SERVICE_URL)
    try:
        box = WebDriverWait(driver, RESULT_WAIT).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, SEARCH_BOX)))
        box.send_keys(str(tax_id))
        box.send_keys(Keys.RETURN)
        time.sleep(LOAD_DELAY)

        try:
            card = WebDriverWait(driver, RESULT_WAIT).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, RESULT_CARD)))
        except TimeoutException:
            # No card: either the page says there is no such counterparty,
            # or it has not loaded. Only the first is "Not found".
            try:
                WebDriverWait(driver, NOT_FOUND_WAIT).until(
                    EC.presence_of_element_located(
                        (By.XPATH, f"//*[contains(text(), '{NOT_FOUND_TEXT}')]")))
                return None, NOT_FOUND
            except TimeoutException:
                return None, NOT_READ

        lines = [s.strip() for s in card.text.strip().split("\n") if s.strip()]
        if len(lines) < 2:
            return None, NOT_READ  # the card is there, its contents are not yet
        return lines[0], read_status(lines[1])

    except WebDriverException as e:
        print(f"Search failed for {tax_id}: {e.msg if hasattr(e, 'msg') else e}")
        return None, SEARCH_ERROR


def check_table(sheet, driver, retry=False):
    done = 0
    for row in range(2, sheet.max_row + 1):
        tax_id = sheet.cell(row=row, column=TAX_ID_COL).value
        status_cell = sheet.cell(row=row, column=STATUS_COL)
        if not tax_id or (retry and status_cell.value not in RETRY):
            continue
        name, status = check_one(driver, tax_id)
        status_cell.value = status
        # FIX 2: the name is written on the second pass too. In 2024 it was
        # written on the first pass only, so a counterparty read on the
        # second pass got its status but kept the old name.
        if name:
            sheet.cell(row=row, column=NAME_COL, value=name)
        done += 1
        print(f"{'retry ' if retry else ''}{tax_id}: {status}"
              + (f", {name}" if name else ""))
    return done


def main():
    workbook = openpyxl.load_workbook(TABLE)
    sheet = workbook.active
    # FIX 3: the browser starts before the try block. In 2024, if it failed
    # to start, the cleanup step itself crashed and hid the real error.
    driver = start_browser()
    try:
        checked = check_table(sheet, driver)
        retried = check_table(sheet, driver, retry=True)
        print(f"Checked {checked}, checked again {retried}.")
    finally:
        # Saved even if the run stops half-way, so nothing done is lost.
        workbook.save(OUTPUT or TABLE)
        driver.quit()
    counts = {}
    for row in range(2, sheet.max_row + 1):
        s = sheet.cell(row=row, column=STATUS_COL).value
        if s:
            counts[s] = counts.get(s, 0) + 1
    print(", ".join(f"{k}: {v}" for k, v in counts.items()))
    print(f"Written: {OUTPUT or TABLE}")


if __name__ == "__main__":
    main()

# Code by Zapier step (Run Python) of the weekly digest Zap.
#
# In Zapier, the previous step (Notion: Query Data Source) returns every open
# line of the tracker. Each line arrives already joined into 1 string by a
# Notion formula property (see notion_formula.txt):
#   number|company|status|submitted
# and Zapier passes all the lines to this step as 1 field, `rows`, separated
# by commas. The formula replaces any comma inside a company name with ";",
# so a comma here always separates 2 lines.
# Zapier defines `input_data` and reads the dict `output` back; nothing else.
#
# Run outside Zapier (`python weekly_digest.py`), the script loads
# sample/zapier_input.json instead, which also fixes "today" so that the
# result is the same on every run.

from datetime import date, datetime, timedelta, timezone

SILENCE_AFTER_DAYS = 10   # no reply in 10 days: the line goes to "Silence"
WARN_FROM_DAYS = 3        # lines younger than this are not worth a mention

try:
    input_data  # defined by Zapier
except NameError:
    import json
    from pathlib import Path
    sample = Path(__file__).with_name('sample') / 'zapier_input.json'
    input_data = json.loads(sample.read_text(encoding='utf-8'))

if input_data.get('today'):  # only the local sample sets it
    today = date.fromisoformat(input_data['today'])
else:  # Zapier runs in UTC; the tracker lives in UTC-5
    today = (datetime.now(timezone.utc) - timedelta(hours=5)).date()

action, overdue, soon, broken = [], [], [], []
for item in (input_data.get('rows') or '').split(','):
    item = item.strip()
    if not item:
        continue
    parts = [p.strip() for p in item.split('|')]
    if len(parts) != 4:  # a line the formula did not build as expected
        broken.append(item)
        continue
    n, c, s, d = parts
    if s == 'In progress':
        action.append(f'#{n} {c}')
        continue
    if not d:
        continue
    try:
        submitted = date.fromisoformat(d[:10])
    except ValueError:  # not a date: report the line rather than guess
        broken.append(item)
        continue
    days = (today - submitted).days
    if days >= SILENCE_AFTER_DAYS:
        overdue.append(f'#{n} {c} - {days} days without a reply')
    elif days >= WARN_FROM_DAYS:
        silent_from = submitted + timedelta(days=SILENCE_AFTER_DAYS)
        soon.append(f'#{n} {c} - Silence from {silent_from:%d.%m}')


def block(title, items):
    return title + '\n' + ('\n'.join(items) if items else '(none)')


blocks = [
    block('In progress - check whether anyone is waiting for you:', action),
    block('Time for Silence (10+ days):', overdue),
    block('Will become Silence this week:', soon),
]
if broken:  # never pair a line with the wrong data in silence
    blocks.append(block('Could not read (check these lines in the tracker):', broken))

output = {'digest': '\n\n'.join(blocks)}

if __name__ == '__main__':
    print(output['digest'])

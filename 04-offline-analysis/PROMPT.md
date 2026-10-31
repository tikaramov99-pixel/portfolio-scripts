# The task, as given to the AI

This is the whole message which went to the AI together with `sample_for_ai.xlsx`, the anonymized sample. The app in step 2 fills in the description of the file by itself, so for another file the same text works after changing the list of what the script should do.

```text
I attach an anonymized sample of a monthly time report from a law firm: names, case numbers and texts are replaced, and money values are changed, so do not rely on the sample's totals. The real file has the same columns and about {ROWS} rows. I will run your script on my own computer, on the real file, and you will not see it.

{STRUCTURE}

Please write 1 Python script which reads the real file and:
1. totals hours and amounts by client and matter, and compares the hours with the monthly cap of each matter from the sheet "Matters";
2. totals hours and amounts by lawyer, with the number of days worked;
3. lists every entry which has to be checked before the report goes to the client, each with the reason: a lawyer's day over 10 hours, an entry on a weekend, an exact duplicate, an empty description, a rate which differs from the lawyer's usual rate, hours not in tenths, an amount which is not hours x rate, and a matter over its cap;
4. saves everything to 1 Excel file with the sheets Summary, To check, By matter, By lawyer.

Use only pandas and openpyxl and nothing which goes to the internet. Keep the column names exactly as they are, put the settings (like the 10 hours) at the top, and tell me in 2 lines how to run it.
```

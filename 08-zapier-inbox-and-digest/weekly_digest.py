# Code by Zapier step (Run Python) of the weekly digest Zap.
#
# In Zapier, the previous step (Notion: Query Data Source) returns every open
# line of the tracker, and each field arrives here as 1 comma-separated string:
#   nums       <- the line number
#   companies  <- the company
#   statuses   <- the status: "Applied" or "In progress"
#   dates      <- the date the application was actually submitted
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


def parts(key):
    return [x.strip() for x in (input_data.get(key) or '').split(',')]


nums, comps, stats, dates = parts('nums'), parts('companies'), parts('statuses'), parts('dates')

if input_data.get('today'):  # only the local sample sets it
    today = date.fromisoformat(input_data['today'])
else:  # Zapier runs in UTC; the tracker lives in UTC-5
    today = (datetime.now(timezone.utc) - timedelta(hours=5)).date()

action, overdue, soon = [], [], []
for n, c, s, d in zip(nums, comps, stats, dates):
    n = n.replace('.0', '')  # Notion numbers arrive as "46.0"
    if s == 'In progress':
        action.append(f'#{n} {c}')
        continue
    if not d:
        continue
    try:
        submitted = date.fromisoformat(d[:10])
    except ValueError:  # not a date: skip the line rather than guess
        continue
    days = (today - submitted).days
    if days >= SILENCE_AFTER_DAYS:
        overdue.append(f'#{n} {c} - {days} days without a reply')
    elif days >= WARN_FROM_DAYS:
        silent_from = submitted + timedelta(days=SILENCE_AFTER_DAYS)
        soon.append(f'#{n} {c} - Silence from {silent_from:%d.%m}')


def block(title, items):
    return title + '\n' + ('\n'.join(items) if items else '(none)')


output = {'digest': '\n\n'.join([
    block('In progress - check whether anyone is waiting for you:', action),
    block('Time for Silence (10+ days):', overdue),
    block('Will become Silence this week:', soon),
])}

if __name__ == '__main__':
    print(output['digest'])

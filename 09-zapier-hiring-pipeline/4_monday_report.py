# Zap 4, step 3 - Code by Zapier (Run Python)
# Input Data:
#   raw = ClickUp "API Request" step: the response body (JSON text) of
#         GET https://api.clickup.com/api/v2/list/1600740000001715/task?include_closed=true&subtasks=false
# Builds the Monday report from statuses and tags (the ClickUp Free plan
# does not let automations update custom fields, so every flag is a tag):
#   check-in-sent      - the reminder went out (3 hours after the deadline)
#   contact-confirmed  - the candidate has written back
#   question           - the candidate asked something, waiting for an answer
import json
from datetime import datetime, timezone, timedelta

try:
    input_data  # defined by Zapier
except NameError:  # run outside Zapier: read the sample instead
    import json as _json
    from pathlib import Path
    input_data = _json.loads((Path(__file__).with_name('sample') / 'zap4_clickup_tasks.json').read_text(encoding='utf-8'))

ORDER = ['applied', 'contact missing', 'test sent', 'under review', 'on hold',
         'referred', 'interview 1', 'interview 2', 'offer', 'hired', 'rejected']

data = json.loads(input_data.get('raw') or '{"tasks": []}')
tasks = [t for t in data.get('tasks', []) if not t.get('parent')]
now = datetime.now(timezone.utc)

def tags(task):
    return {g.get('name', '').lower() for g in task.get('tags', [])}

def field(task, name):
    for f in task.get('custom_fields', []):
        if f.get('name') == name:
            return f.get('value')
    return None

def days_since(ms):
    try:
        return (now - datetime.fromtimestamp(int(ms) / 1000, timezone.utc)).days
    except (TypeError, ValueError):
        return 0

counts, silent, waiting, questions, manual = {}, [], [], [], []
for t in tasks:
    status = t.get('status', {}).get('status', '')
    counts[status] = counts.get(status, 0) + 1
    name, tg = t.get('name', ''), tags(t)
    if status == 'test sent' and 'check-in-sent' in tg and 'contact-confirmed' not in tg:
        silent.append(name)
    if status == 'under review':
        d = days_since(t.get('date_updated'))
        waiting.append((d, f"{name}: {d} day{'s' if d != 1 else ''} with the recruiter"))
    if 'question' in tg:
        questions.append(name)
    if status == 'contact missing':
        manual.append(f"{name} ({field(t, 'Phone') or 'no phone'}; resume ID {field(t, 'Resume ID') or '-'})")

lines = [f"Pipeline as of {now - timedelta(hours=5):%A, %B %d}: {len(tasks)} candidates", '']
for st in ORDER + sorted(set(counts) - set(ORDER)):
    if counts.get(st):
        lines.append(f"  {st.capitalize():<18} {counts[st]}")

def block(title, items):
    return ['', title] + ([f"  - {i}" for i in items] if items else ['  (none)'])

lines += block('Waiting for a decision (oldest first):', [w for _, w in sorted(waiting, reverse=True)])
lines += block('Reminder sent after the deadline, still no answer:', silent)
lines += block('Questions waiting for an answer:', questions)
lines += block('No email on file - contact via the job board:', manual)

output = {'report': '\n'.join(lines), 'waiting': str(len(waiting))}

if __name__ == '__main__':  # outside Zapier, show what the step would return
    import json as _json
    print(_json.dumps(output, indent=2, ensure_ascii=False))

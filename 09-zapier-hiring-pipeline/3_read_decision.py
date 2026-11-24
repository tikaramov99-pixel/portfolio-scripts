# Zap 3, step 4 - Code by Zapier (Run Python)
# Input Data:
#   body    = Gmail trigger: Body Plain
#   status  = ClickUp Find Task by ID: Status
#   subject = Gmail trigger: Subject ("Re: Review: First Last [ref ...]")
# Reads the recruiter's 1-word decision from the first line of the reply,
# typos included, and works out the candidate's next status.
import re
import json
from datetime import datetime, timedelta, timezone

try:
    input_data  # defined by Zapier
except NameError:  # run outside Zapier: read the sample instead
    import json as _json
    from pathlib import Path
    input_data = _json.loads((Path(__file__).with_name('sample') / 'zap3_reply.json').read_text(encoding='utf-8'))

SIGNALS = {
    'invite':  ['invite', 'yes', 'interview', 'go', 'proceed'],
    'decline': ['decline', 'reject', 'no', 'pass'],
    'hold':    ['hold', 'waitlist', 'maybe', 'think', 'later'],
}

def distance(a, b):
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]

body = input_data.get('body') or ''
# only the new text, not the quoted letter below it
body = re.split(r'\n\s*(On .+ wrote:|From:|-----Original Message-----|_{5,})', body)[0]
first = next((l for l in body.splitlines() if l.strip()), '')
words = re.findall(r"[a-zA-Z]+", first.lower())[:3]

decision, best = 'unclear', 99
for word in words:
    for key, variants in SIGNALS.items():
        for v in variants:
            d = distance(word, v)
            allowed = 0 if len(v) <= 3 else (1 if len(v) <= 5 else 2)
            if d <= allowed and d < best:
                decision, best = key, d

status = (input_data.get('status') or '').lower()
next_status = {
    'invite': 'interview 2' if status == 'interview 1' else ('offer' if status == 'interview 2' else 'interview 1'),
    'decline': 'rejected',
    'hold': 'on hold',
    'unclear': status,
}[decision]

subject = input_data.get('subject') or ''
m = re.search(r'Review:\s*(.+?)\s*\[ref\s+([A-Za-z0-9]+)\]', subject)
full, task_id = (m.group(1).strip(), m.group(2)) if m else ('', '')
first_name = full.split()[0] if full else 'there'
ref = f'[ref {task_id}]'
sign = '\n\nBest regards,\nTimur Karamov\nHiring Coordinator, Hollis Grant LLP'

letters = {
    'invite': (f'Junior Associate: next step {ref}',
               (f'Hi {first_name},\n\nThank you for the first interview. We would like to invite you to the second one.\n\n'
                if next_status == 'interview 2' else
                f'Hi {first_name},\n\nThank you for your test assignment. We were glad to read it and would like to invite you '
                'to the first interview.\n\n') +
               'I will write to you within 1 business day with a few time options. If there are days that do not work for you, '
               'just reply and let me know.' + sign),
    'decline': (f'Junior Associate: your application {ref}',
                f'Hi {first_name},\n\nThank you for the time you put into the test assignment. After careful review, we have decided '
                'not to move forward with your application for this position.\n\nWe appreciate your interest in Hollis Grant LLP '
                'and wish you every success in your search.' + sign),
    'hold': (f'Junior Associate: your application {ref}',
             f'Hi {first_name},\n\nThank you for your test assignment. Our review of applications for this position is still '
             'in progress, and we will get back to you as soon as we have news.\n\nThank you for your patience.' + sign),
}
if next_status == 'offer':
    letters['invite'] = (f'Junior Associate: good news {ref}',
                         f'Hi {first_name},\n\nThank you for the interviews. We are happy to let you know that we would like '
                         'to make you an offer. Our recruiter will contact you shortly with the details.' + sign)
letter_subject, letter_body = letters.get(decision, ('', ''))

output = {
    'task_id': task_id,
    'full_name': full,
    'letter_subject': letter_subject,
    'letter_body': letter_body,
    'waitlist_subject': f'Junior Associate: your application {ref}',
    'waitlist_body': (f'Hi {first_name},\n\nThank you again for your interest in the Junior Associate position. '
                      'We have now completed the first round of selection. Your application stood out, and we have placed you '
                      'on our waitlist: if a position opens up, we will contact you first.' + sign),
    'decision': decision,
    'next_status': next_status,
    'stage': 'second' if next_status == 'interview 2' else 'first',
    'status_body': json.dumps({'status': next_status}),
    'waitlist_at': (datetime.now(timezone.utc) + timedelta(days=10)).isoformat(),
    'note': first.strip()[:200],
}

if __name__ == '__main__':  # outside Zapier, show what the step would return
    import json as _json
    print(_json.dumps(output, indent=2, ensure_ascii=False))

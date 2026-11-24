# Zap 2, step 6 - Code by Zapier (Run Python)
# Input Data:
#   names    = Gmail trigger: attachment file names (comma-separated)
#   deadline = the card's Test deadline (ms timestamp)
#   subject  = Gmail trigger: Subject (the candidate's name sits before [ref ...])
# The resume is already on the card (from the shortlist), so the candidate
# only sends the answer, named by the template. Everything else that is a
# document goes on to the recruiter too, except copies of the resume.
import re
from datetime import datetime, timezone

try:
    input_data  # defined by Zapier
except NameError:  # run outside Zapier: read the sample instead
    import json as _json
    from pathlib import Path
    input_data = _json.loads((Path(__file__).with_name('sample') / 'zap2b_reply.json').read_text(encoding='utf-8'))

DOCS = ('.pdf', '.doc', '.docx', '.rtf', '.odt', '.pages', '.txt', '.xlsx', '.pptx')
RESUME = re.compile(r'(resume|résumé|(?<![a-z])cv(?![a-z])|curriculum)', re.I)
ANSWER = re.compile(r'^answer[ _\-]', re.I)

names = [n.strip() for n in (input_data.get('names') or '').split(',') if n.strip()]
docs = [n for n in names if n.lower().endswith(DOCS)]       # signature images do not count
answer = [n for n in docs if ANSWER.search(n)]
resumes = [n for n in docs if RESUME.search(n) and n not in answer]
extras = [n for n in docs if n not in answer and n not in resumes]

notes = []
if answer:
    if not any(n.lower().endswith('.pdf') for n in answer):
        notes.append('the answer came as ' + answer[0].rsplit('.', 1)[-1].upper() + ', not PDF')
elif extras:
    notes.append('no file was named by the template; the answer is probably ' + extras[0])
if resumes:
    notes.append('the candidate also sent a resume (' + ', '.join(resumes) + '); the job board one is attached as well')

action = 'forward' if (answer or extras) else 'question'

timing = 'on time'
try:
    due = datetime.fromtimestamp(int(input_data.get('deadline')) / 1000, timezone.utc)
    hours = (datetime.now(timezone.utc) - due).total_seconds() / 3600
    if hours >= 1.5:
        timing = f'{round(hours)} hours after the deadline'
    elif hours > 0:
        timing = 'within 1 hour after the deadline'
except (TypeError, ValueError):
    pass

main = answer[0] if answer else (extras[0] if extras else '')
subject = input_data.get('subject') or ''
m = re.search(r' - (.+?)\s*\[ref', subject)
full = m.group(1).strip() if m else ''
r = re.search(r'\[ref\s+([A-Za-z0-9]+)\]', subject)
task_id = r.group(1) if r else ''

others = ', '.join(n for n in answer + extras if n != main) or 'none'
body = '\n'.join(line for line in [
    'Hi Anna,',
    '',
    f'{full} has sent the test assignment for the Junior Associate position ({timing}).',
    f'Attached: {main}, and the resume from the job board. Other files from the candidate: {others}.',
    ('Note: ' + '; '.join(notes) + '.') if notes else None,
    '',
    f'Candidate card: https://app.clickup.com/t/{task_id}',
    '',
    'To decide, just reply with one word: invite, decline or hold.',
    '',
    'Timur',
] if line is not None)
od = re.search(r'file ID:\s*(\S+)', input_data.get('desc') or '')
output = {
    'resume_file_id': od.group(1) if od else '',
    'full_name': full,
    'resume_file': 'Resume_' + '_'.join(full.split()) + '.pdf',
    'action': action,
    'answer_file': main,
    'other_files': others,
    'review_subject': f'Review: {full} [ref {task_id}]',
    'review_body': body,
    'timing': timing,
    'notes': ('Note: ' + '; '.join(notes) + '.') if notes else '',
}

if __name__ == '__main__':  # outside Zapier, show what the step would return
    import json as _json
    print(_json.dumps(output, indent=2, ensure_ascii=False))

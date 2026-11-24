# Zap 1, step 3 - Code by Zapier (Run Python)
# Input Data: text = Files by Zapier "Convert file to text" output
# Reads the job board's standard resume, works out the test deadline
# (96 hours, rounded up to the hour, moved into 10 AM - 7 PM ET on a weekday)
# the reminder (3 hours after the deadline) and the auto-close (2 days later).
import re
from datetime import datetime, timedelta, timezone

try:
    input_data  # defined by Zapier
except NameError:  # run outside Zapier: read the sample instead
    import json as _json
    from pathlib import Path
    input_data = _json.loads((Path(__file__).with_name('sample') / 'zap1_resume_text.json').read_text(encoding='utf-8'))

text = input_data.get('text') or ''
lines = [l.strip() for l in text.splitlines() if l.strip()]

def field(label):
    m = re.search(r'^' + label + r'\s*:\s*(.+)$', text, re.I | re.M)
    v = m.group(1).strip() if m else ''
    return '' if v.lower() in ('not provided', 'n/a', '-', 'none') else v

name = next((l for l in lines if re.fullmatch(r"[A-Z][A-Z' .\-]+", l) and len(l.split()) >= 2), '')
full_name = ' '.join(w.capitalize() if not '-' in w else '-'.join(p.capitalize() for p in w.split('-')) for w in name.split())
email = field('Email')
email = email if re.fullmatch(r'[^@\s]+@[^@\s]+\.[^@\s]+', email) else ''
phone = field('Phone')
m = re.search(r'Resume ID:\s*([A-Z0-9\-]+)', text)
resume_id = m.group(1) if m else ''

# --- US Eastern time without external libraries (DST rules since 2007) ---
def nth_sunday(year, month, n):
    d = datetime(year, month, 1)
    d += timedelta(days=(6 - d.weekday()) % 7)
    return d + timedelta(weeks=n - 1)

def et_offset(utc):
    y = utc.year
    dst_start = nth_sunday(y, 3, 2) + timedelta(hours=7)   # 2 AM EST = 7 AM UTC
    dst_end = nth_sunday(y, 11, 1) + timedelta(hours=6)    # 2 AM EDT = 6 AM UTC
    naive = utc.replace(tzinfo=None)
    return timedelta(hours=-4) if dst_start <= naive < dst_end else timedelta(hours=-5)

def to_et(utc):
    return (utc + et_offset(utc)).replace(tzinfo=None)

def from_et(local):
    guess = local - timedelta(hours=-5)            # assume EST first
    utc = guess.replace(tzinfo=timezone.utc)
    return utc - (et_offset(utc) - timedelta(hours=-5))

OPEN, CLOSE = 10, 19

def into_business_hours(t, round_up=True):
    if round_up and (t.minute or t.second or t.microsecond):
        t = t.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
    if t.hour < OPEN:
        t = t.replace(hour=OPEN, minute=0)
    elif t.hour > CLOSE or (t.hour == CLOSE and t.minute > 0):
        t = (t + timedelta(days=1)).replace(hour=OPEN, minute=0)
    while t.weekday() >= 5:                           # Saturday, Sunday -> Monday
        t = (t + timedelta(days=1)).replace(hour=OPEN, minute=0)
    return t

now_et = to_et(datetime.now(timezone.utc))
deadline_et = into_business_hours(now_et + timedelta(hours=96))
check_et = deadline_et + timedelta(hours=3)          # reminder: 3 hours after the deadline
final_et = check_et + timedelta(days=2)              # auto-close: 2 days after the reminder

def label(t):
    hour = t.strftime('%I').lstrip('0')
    return f"{t:%A, %B} {t.day}, {hour}:{t:%M} {t:%p} ET (New York time)"

missing = [x for x, v in (('email', email), ('phone', phone)) if not v]

output = {
    'full_name': full_name or 'Unknown candidate',
    'first_name': (full_name.split() or ['there'])[0],
    'email': email,
    'phone': phone or 'none',
    'resume_id': resume_id,
    'has_email': 'yes' if email else 'no',
    'status': 'test sent' if email else 'contact missing',
    'missing': ', '.join(missing),
    'deadline_iso': from_et(deadline_et).isoformat(),
    'deadline_text': label(deadline_et),
    'check_iso': from_et(check_et).isoformat(),
    'final_iso': from_et(final_et).isoformat(),
    'final_text': label(final_et),
    'dedupe_key': resume_id or ('no-id-' + now_et.strftime('%Y%m%d%H%M%S')),
    'answer_file': 'Answer_' + '_'.join(full_name.split()) + '.pdf',
}

if __name__ == '__main__':  # outside Zapier, show what the step would return
    import json as _json
    print(_json.dumps(output, indent=2, ensure_ascii=False))

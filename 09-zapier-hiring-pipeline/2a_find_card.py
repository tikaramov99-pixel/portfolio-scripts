# Zap 2, step 3: find the candidate's card from the [ref ...] tag in the subject
import re

try:
    input_data  # defined by Zapier
except NameError:  # run outside Zapier: read the sample instead
    import json as _json
    from pathlib import Path
    input_data = _json.loads((Path(__file__).with_name('sample') / 'zap2a_subject.json').read_text(encoding='utf-8'))
m = re.search(r'\[ref\s+([A-Za-z0-9]+)\]', input_data.get('subject') or '')
output = {'task_id': m.group(1) if m else ''}

if __name__ == '__main__':  # outside Zapier, show what the step would return
    import json as _json
    print(_json.dumps(output, indent=2, ensure_ascii=False))

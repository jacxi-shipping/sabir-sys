import importlib.util
import json
from pathlib import Path

spec = importlib.util.spec_from_file_location('i18n', 'egg_farm_system/utils/i18n.py')
i18n = importlib.util.module_from_spec(spec)
spec.loader.exec_module(i18n)

ps_trans = getattr(i18n, 'TRANSLATIONS', {}).get('ps', {})

tr_calls = set()

for p in Path('egg_farm_system').rglob('*.py'):
    text = p.read_text(encoding='utf-8')
    for line in text.splitlines():
        # crude scan for tr('...') or tr("...") occurrences
        start = 0
        while True:
            idx = line.find('tr(', start)
            if idx == -1:
                break
            # find opening quote
            q_idx = line.find("'", idx)
            dq_idx = line.find('"', idx)
            if q_idx == -1 or (dq_idx != -1 and dq_idx < q_idx):
                q = '"'
                start_q = dq_idx
            else:
                q = "'"
                start_q = q_idx
            if start_q == -1:
                start = idx + 3
                continue
            end_q = line.find(q, start_q+1)
            if end_q == -1:
                start = idx + 3
                continue
            inner = line[start_q+1:end_q]
            tr_calls.add(inner)
            start = end_q+1

missing = sorted([s for s in tr_calls if s not in ps_trans])

out = {k: "" for k in missing}

out_path = Path('tools/missing_translations.json')
out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding='utf-8')
print(f'Wrote {len(out)} keys to {out_path}')

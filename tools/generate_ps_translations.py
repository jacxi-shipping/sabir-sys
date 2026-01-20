import json
import re
import importlib.util
from pathlib import Path

# Load existing translations
spec = importlib.util.spec_from_file_location('i18n', 'egg_farm_system/utils/i18n.py')
i18n = importlib.util.module_from_spec(spec)
spec.loader.exec_module(i18n)
base_ps = getattr(i18n, 'TRANSLATIONS', {}).get('ps', {})

# Load missing keys
missing_path = Path('tools/missing_translations.json')
if not missing_path.exists():
    print('Missing translations file not found:', missing_path)
    raise SystemExit(1)
missing = json.loads(missing_path.read_text(encoding='utf-8'))

# tokenization
split_re = re.compile(r"(\w+|[^\w]+)")

def map_token(tok):
    if tok.strip() == '':
        return tok
    # try exact
    if tok in base_ps:
        return base_ps[tok]
    # try lower
    if tok.lower() in base_ps:
        return base_ps[tok.lower()]
    # try title
    if tok.title() in base_ps:
        return base_ps[tok.title()]
    # punctuation or numeric
    if not re.search(r'[A-Za-zА-Яа-яء-ي]', tok):
        return tok
    # fallback: return English token (keep original)
    return tok

new_trans = {}
for key in missing.keys():
    if not key:
        continue
    parts = split_re.findall(key)
    translated_parts = [map_token(p) for p in parts]
    candidate = ''.join(translated_parts)
    # if candidate is identical to key, leave empty to indicate untranslated
    if candidate == key:
        new_trans[key] = key
    else:
        new_trans[key] = candidate

# Write additional ps file
out_path = Path('egg_farm_system/utils/i18n_additional_ps.py')
content_lines = ["# Auto-generated additional Pashto translations (best-effort)", "ADDITIONAL_PS = {"]
for k,v in sorted(new_trans.items()):
    # escape backslashes and quotes
    safe_k = k.replace('\\', '\\\\').replace('"', '\\"')
    safe_v = v.replace('\\', '\\\\').replace('"', '\\"')
    content_lines.append(f'    "{safe_k}": "{safe_v}",')
content_lines.append('}')
out_path.write_text('\n'.join(content_lines), encoding='utf-8')
print(f'Wrote {len(new_trans)} entries to {out_path}')

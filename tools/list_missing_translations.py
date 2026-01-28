import re
from pathlib import Path
import importlib.util

# Load TRANSLATIONS from egg_farm_system.utils.i18n
spec = importlib.util.spec_from_file_location('i18n', 'egg_farm_system/utils/i18n.py')
i18n = importlib.util.module_from_spec(spec)
spec.loader.exec_module(i18n)

ps_trans = getattr(i18n, 'TRANSLATIONS', {}).get('ps', {})

tr_calls = set()

for p in Path('egg_farm_system').rglob('*.py'):
    text = p.read_text(encoding='utf-8')
    for m in re.finditer(r"tr\(\s*(['\"])((?:(?!\1).)*)\1\s*\)", text):
        tr_calls.add(m.group(2))

missing = sorted([s for s in tr_calls if s not in ps_trans])
print(f"Total tr() calls found: {len(tr_calls)}")
print(f"Missing translations for 'ps': {len(missing)}")
for s in missing[:200]:
    print(s)

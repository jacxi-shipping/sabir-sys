from pathlib import Path
import re

ROOT = Path('egg_farm_system')
pyfiles = list(ROOT.rglob('*.py'))
add_count = 0
for f in pyfiles:
    text = f.read_text(encoding='utf-8')
    if 'tr(' not in text:
        continue
    if 'from egg_farm_system.utils.i18n import tr' in text:
        continue
    # find module docstring end (simple heuristic)
    insert = 'from egg_farm_system.utils.i18n import tr\n'
    new_text = text
    stripped = text.lstrip()
    leading_ws = text[:len(text)-len(stripped)]
    if stripped.startswith('"""') or stripped.startswith("'''"):
        quote = '"""' if stripped.startswith('"""') else "'''"
        end_idx = stripped.find(quote, 3)
        if end_idx != -1:
            # include closing quotes
            prefix = stripped[:end_idx+3]
            rest = stripped[end_idx+3:]
            new_text = leading_ws + prefix + insert + rest
        else:
            new_text = insert + text
    else:
        new_text = insert + text
    f.write_text(new_text, encoding='utf-8')
    add_count += 1
    print('Inserted import in', f)
print('Done. Inserted in', add_count, 'files')

import re
from pathlib import Path

ROOT = Path('egg_farm_system')
files = list(ROOT.rglob('*.py'))
pattern = re.compile(r'tr\(\s*(["\'])(.*?)\1\s*\)\s*(["\'])(.*?)\3', re.S)

updated = 0
for f in files:
    text = f.read_text(encoding='utf-8')
    new_text = text
    while True:
        m = pattern.search(new_text)
        if not m:
            break
        a_quote = m.group(1)
        a_text = m.group(2)
        b_quote = m.group(3)
        b_text = m.group(4)
        # build replacement using original quotes (use double quotes for safety)
        repl = f'tr("{a_text}" + "{b_text}")'
        new_text = new_text[:m.start()] + repl + new_text[m.end():]
    if new_text != text:
        f.write_text(new_text, encoding='utf-8')
        updated += 1
        print('Fixed', f)
print('Done. Files updated:', updated)

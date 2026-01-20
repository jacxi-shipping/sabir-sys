from pathlib import Path
import re

for p in Path('egg_farm_system').rglob('*.py'):
    text = p.read_text(encoding='utf-8')
    new = text.replace('"""from egg_farm_system.utils.i18n import tr', '"""\nfrom egg_farm_system.utils.i18n import tr')
    new = new.replace("'''from egg_farm_system.utils.i18n import tr", "'''\nfrom egg_farm_system.utils.i18n import tr")
    if new != text:
        p.write_text(new, encoding='utf-8')
        print('Fixed', p)
print('Done')

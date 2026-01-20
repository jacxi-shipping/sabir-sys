import re
import sys
from pathlib import Path

TARGET_DIRS = ["egg_farm_system/ui", "egg_farm_system/ui/forms", "egg_farm_system/ui/widgets", "egg_farm_system/ui/reports"]

# Patterns to wrap: functions or constructors where first arg is a plain string
CALL_PATTERNS = [
    r"\bQPushButton\s*\(\s*(['\"])((?:(?!\1).)*)\1",
    r"\bQLabel\s*\(\s*(['\"])((?:(?!\1).)*)\1",
    r"\.setWindowTitle\s*\(\s*(['\"])((?:(?!\1).)*)\1\)",
    r"\.setToolTip\s*\(\s*(['\"])((?:(?!\1).)*)\1\)",
    r"\.setPlaceholderText\s*\(\s*(['\"])((?:(?!\1).)*)\1\)",
    r"\.setText\s*\(\s*(['\"])((?:(?!\1).)*)\1\)",
    r"QMessageBox\.warning\s*\(\s*[^,]+,\s*(['\"])((?:(?!\1).)*)\1",
    r"QMessageBox\.critical\s*\(\s*[^,]+,\s*(['\"])((?:(?!\1).)*)\1",
    r"QMessageBox\.information\s*\(\s*[^,]+,\s*(['\"])((?:(?!\1).)*)\1",
    r"setWindowTitle\s*\(\s*(['\"])((?:(?!\1).)*)\1\)",
]

# Heuristics to skip wrapping
def should_wrap(text):
    if not text.strip():
        return False
    # skip if contains format braces or percent formatting placeholders
    if '{' in text or '%' in text:
        return False
    # skip very short icons / arrows / single-char symbols
    if len(text.strip()) <= 2 and not text.isalpha():
        return False
    # skip if already contains tr(
    if 'tr(' in text:
        return False
    return True


def process_file(path: Path):
    text = path.read_text(encoding='utf-8')
    orig = text
    changed = False

    for pat in CALL_PATTERNS:
        # replace occurrences where group 2 is the literal text
        def repl(m):
            quote = m.group(1)
            inner = m.group(2)
            if not should_wrap(inner):
                return m.group(0)
            # Build replacement: inject tr("inner") in place of the string literal
            before = m.group(0)
            # find the exact quoted substring in the match to replace
            quoted = f"{quote}{inner}{quote}"
            return before.replace(quoted, f'tr({quote}{inner}{quote})')

        new_text = re.sub(pat, repl, text)
        if new_text != text:
            changed = True
            text = new_text

    if changed:
        backup = path.with_suffix(path.suffix + '.bak')
        backup.write_text(orig, encoding='utf-8')
        path.write_text(text, encoding='utf-8')
        print(f"Updated: {path}")
    return changed


def main():
    base = Path('.')
    files = []
    for d in TARGET_DIRS:
        p = base / d
        if p.exists():
            files.extend(list(p.rglob('*.py')))
    if not files:
        print('No files to process')
        return
    updated = 0
    for f in files:
        try:
            if process_file(f):
                updated += 1
        except Exception as e:
            print(f'Error processing {f}: {e}')
    print(f'Finished. Files updated: {updated}')

if __name__ == '__main__':
    main()

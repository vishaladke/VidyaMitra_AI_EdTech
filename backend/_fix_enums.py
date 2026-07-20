"""Fix all Enum columns to use values_callable."""
import re
import glob

pattern = r'Enum\((\w+),\s*name="([^"]+)"'
replacement = r'Enum(\1, name="\2", values_callable=lambda x: [e.value for e in x]'

for f in glob.glob('app/models/*.py'):
    with open(f, 'r', encoding='utf-8') as fh:
        content = fh.read()
    new_content = re.sub(pattern, replacement, content)
    # Don't double-add
    new_content = new_content.replace(
        'values_callable=lambda x: [e.value for e in x], values_callable=lambda x: [e.value for e in x]',
        'values_callable=lambda x: [e.value for e in x]'
    )
    if new_content != content:
        with open(f, 'w', encoding='utf-8') as fh:
            fh.write(new_content)
        print(f'Fixed: {f}')
    else:
        print(f'OK:    {f}')

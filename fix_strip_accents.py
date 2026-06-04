for fname in [
    r'C:\Users\Damon\Documents\python_programs\elta5.7.py',
    r'C:\Users\Damon\Documents\python_programs\elta5.6.py',
]:
    with open(fname, 'r', encoding='utf-8') as f:
        content = f.read()

    # Replace curly single quotes used as Python string delimiters with straight apostrophes
    fixed = content.replace('‘', "'").replace('’', "'")

    if fixed != content:
        with open(fname, 'w', encoding='utf-8') as f:
            f.write(fixed)
        n = content.count('‘') + content.count('’')
        print(f'{fname}: replaced {n} curly quote(s)')
    else:
        print(f'{fname}: no curly quotes found')

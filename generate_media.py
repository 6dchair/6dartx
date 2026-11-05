"""
generate_media.py

Writes generated-media.js with the ARTWORKS list for index.html.
SONGS are NOT generated: they are typed by hand in index.html.

FOLDER (next to this script and index.html):

  artworks/   -> your artwork images (.jpg, .png, .webp, .gif)

USAGE:
  python3 generate_media.py

WHAT IT DOES:
  * Reads the existing generated-media.js first and KEEPS everything you
    edited by hand (titles, mediums, years). Re-running only adds new
    images, so your edits are never wiped.
  * A new image in artworks/ becomes a new entry (title guessed from the
    file name, medium "Medium", year "20XX"). Edit those afterwards.
  * An entry whose image file was deleted is dropped.
  * Any old SONGS list left in generated-media.js is removed.

Nothing here uploads or sends your files anywhere. It only reads file names
on your own computer and writes a text file next to it.
"""

import os
import re

IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.webp', '.gif'}

ARTWORKS_DIR = 'artworks'
OUTPUT_FILE = 'generated-media.js'

FIELD = re.compile(r"(\w+):'((?:[^'\\]|\\.)*)'")


def js_escape(s):
    return s.replace('\\', '\\\\').replace("'", "\\'")


def js_unescape(s):
    return s.replace("\\'", "'").replace('\\\\', '\\')


def title_from_filename(filename):
    name = os.path.splitext(filename)[0]
    name = name.replace('-', ' ').replace('_', ' ').strip()
    return name.title() if name else 'Untitled'


def list_images(folder):
    if not os.path.isdir(folder):
        return []
    files = sorted(os.listdir(folder))
    return [f for f in files
            if os.path.splitext(f)[1].lower() in IMAGE_EXTS and not f.startswith('.')]


def read_existing_artworks():
    """Return the entries (as dicts) from the ARTWORKS list in the current output file."""
    if not os.path.isfile(OUTPUT_FILE):
        return []
    with open(OUTPUT_FILE, encoding='utf-8') as f:
        text = f.read()
    m = re.search(r'const ARTWORKS\s*=\s*\[(.*?)\n\];', text, re.S)
    if not m:
        return []
    entries = []
    for line in m.group(1).splitlines():
        line = line.strip()
        if not line.startswith('{'):          # skips blank lines and // comments
            continue
        fields = {k: js_unescape(v) for k, v in FIELD.findall(line)}
        if 'img' in fields:
            entries.append(fields)
    return entries


def fmt(fields):
    parts = [f"{k}:'{js_escape(fields[k])}'" for k in ('img', 'title', 'medium', 'year') if k in fields]
    return '  {' + ', '.join(parts) + '},'


def build_artworks(existing):
    by_path = {a['img']: a for a in existing}
    on_disk = {f'{ARTWORKS_DIR}/{f}' for f in list_images(ARTWORKS_DIR)}
    lines, added, dropped = [], [], []

    for path, entry in by_path.items():       # keep your order and your edits
        if path in on_disk:
            lines.append(fmt(entry))
        else:
            dropped.append(path)

    for img in list_images(ARTWORKS_DIR):
        path = f'{ARTWORKS_DIR}/{img}'
        if path not in by_path:
            lines.append(fmt({'img': path, 'title': title_from_filename(img),
                              'medium': 'Medium', 'year': '20XX'}))
            added.append(img)

    return lines, added, dropped


def main():
    lines, added, dropped = build_artworks(read_existing_artworks())

    out = ['const ARTWORKS = [']
    out.extend(lines if lines else ['  // no files found in artworks/'])
    out.append('];')

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write('\n'.join(out) + '\n')

    print(f'Wrote {OUTPUT_FILE}: {len(lines)} artwork(s).')
    if added:
        print('New artworks (edit the medium and year):')
        for n in added:
            print(f'  + {n}')
    if dropped:
        print('Removed (image file no longer exists):')
        for n in dropped:
            print(f'  - {n}')


if __name__ == '__main__':
    main()
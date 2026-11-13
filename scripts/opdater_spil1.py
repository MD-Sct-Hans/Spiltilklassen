#!/usr/bin/env python3
"""Genererer spiloversigt til statisk GitHub Pages-side. Kun Python standardbibliotek."""
import json
import re
from html import unescape
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
GAMES = ROOT / 'spil'
OUTPUT = GAMES / 'spiloversigt.json'

# Titler/fag kan overskrives med spilinfo.json i mappen (se README).
KNOWN = {
    'piratjagten': ('Piratjagten', 'Matematik', '⚓'),
    'galgeleg': ('Galgeleg', 'Dansk', '🔤'),
    'skojr-quiz': ('Den skøre quiz', 'Almen viden', '🧠'),
    'skoer-quiz': ('Den svære og skøre quiz', 'Almen viden', '🧠'),
    'quiz-let': ('Den helt skøre quiz', 'Almen viden', '🎪'),
    'gaet-ordet': ('Gæt ordet', 'Dansk', '🗣️'),
}

def clean_title(text):
    text = re.sub(r'<[^>]*>', '', text)
    return re.sub(r'\s+', ' ', unescape(text)).strip()

def auto_title(file):
    try:
        with file.open('r', encoding='utf-8', errors='replace') as fh:
            text = fh.read(35000)
        match = re.search(r'<title[^>]*>(.*?)</title>', text, re.I | re.S)
        if match:
            val = clean_title(match.group(1))
            # Undgå standard-website-navnet, når titel indeholder spilnavn.
            val = re.split(r'\s+[–|]\s+', val)[-1] if 'SpilTilKlassen' in val or 'KlasseSpil' in val else val
            if val and len(val) < 100:
                return val
    except OSError:
        pass
    return file.parent.name.replace('-', ' ').title() if file.stem.lower() == 'index' else file.stem.replace('-', ' ').title()

def config_for(file):
    # Spilmappe: spil/gaet-ordet/spilinfo.json; enkeltfil: spil/minquiz.json
    location = file.parent / ('spilinfo.json' if file.name.lower() == 'index.html' else file.stem + '.json')
    try:
        if location.is_file():
            return json.loads(location.read_text(encoding='utf-8'))
    except (ValueError, OSError) as exc:
        print('Kan ikke læse metadata', location, exc)
    return {}

def main():
    GAMES.mkdir(exist_ok=True)
    entries = []
    files = sorted(GAMES.rglob('*.html'), key=lambda p: p.as_posix().casefold())
    for file in files:
        rel = file.relative_to(ROOT)
        if any(part.startswith('.') for part in rel.parts) or file.name.lower() in ('demo.html','test.html'):
            continue
        # Kun index.html direkte i spilundermapper. Andre HTML-filer direkte i spil/ er også spil.
        if file.parent != GAMES and file.name.lower() != 'index.html':
            continue
        key = file.parent.name if file.name.lower() == 'index.html' else file.stem
        standard = KNOWN.get(key.lower(), (auto_title(file), 'Almen viden', '🎮'))
        info = config_for(file)
        if info.get('skjul') is True:
            continue
        title = str(info.get('titel') or standard[0]).strip()
        subject = str(info.get('fag') or standard[1]).strip()
        grades = info.get('klassetrin', [2,3,4,5,6])
        if not isinstance(grades, list) or not grades:
            grades = [2,3,4,5,6]
        grades = [str(i) for i in grades if str(i) in [str(n) for n in range(0,11)]]
        description = str(info.get('beskrivelse') or f'Spil {title} direkte på tavlen eller computeren.').strip()
        icon = str(info.get('ikon') or standard[2])
        # Path-segment for path-segment encoding (bevar /)
        link = '/'.join(quote(segment) for segment in rel.parts)
        cover = info.get('billede')
        if cover:
            # relative image paths within the game directory, no external URL
            p = (file.parent / str(cover)).resolve()
            if not p.is_relative_to(ROOT) or not p.is_file():
                print('Forsidebillede mangler, ignoreres:', cover)
                cover = None
            else:
                cover = '/'.join(quote(s) for s in p.relative_to(ROOT).parts)
        entries.append(dict(titel=title, fag=subject, klassetrin=grades,
                            beskrivelse=description, ikon=icon, url=link,
                            billede=cover))
    OUTPUT.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'Opdaterede {OUTPUT.relative_to(ROOT)} med {len(entries)} spil')

if __name__ == '__main__':
    main()

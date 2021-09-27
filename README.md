# plzcallstella
This python script scrapes the GMU [Speech Accent Archive](http://accent.gmu.edu/index.php) and dumps the files out by participant ID with an excel manifest.

e.g.
```
recordings/
    0001.mp3
transcripts
    0001.gif
json/
    0001.json
manifest.xlsx
info.json
```

## Usage
**REQ:**
- Python 3.9+
- [poetry](https://python-poetry.org/)

```
# install deps
poetry install --no-dev

# run script
poetry run python scrape.py
```

Results will be output into `output/<TIMESTAMP>/`

## Purpose
This was written to provide data for linguistics students (i.e. [phonetics](https://en.wikipedia.org/wiki/Phonetics) transcription exercises).

This repackaging is intended for educational purposes. Credit goes completely to Steven H. Weinberger, George Maison University, and [others](http://accent.gmu.edu/about.php).

P.S. The Speech Accent Archive is proof that you do not need 20MB of frontend javascript to make something truly valuble.
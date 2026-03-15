# tests/debug_markdown.py
"""
Zeigt den rohen Markdown-Output von pymupdf4llm.
Damit sehen wir ob ## Headings erkannt werden.
"""
import pymupdf4llm
 
md = pymupdf4llm.to_markdown("tests/sample.pdf")
 
# erste 3000 Zeichen — dort stehen Titel + Abstract + erste Headings
print("── MARKDOWN ANFANG (erste 3000 Zeichen) ──────────────")
print(md[:3000])
 
print("\n\n── ALLE ZEILEN DIE MIT # BEGINNEN ────────────────────")
for i, line in enumerate(md.splitlines()):
    if line.strip().startswith("#"):
        print(f"  Zeile {i:4d}: {repr(line)}")
 
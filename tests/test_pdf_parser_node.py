# tests/test_pdf_parser.py
#python -m tests.test_pdf_parser_node
import asyncio
from backend.app.agents.nodes.ingest.pdf_parser_node import PDFParserNode


async def test_pdf_parser():
    state = {
        # ── Required Input ─────────────────────────────────────
        "user_id":   "test_user",
        "file_path": "tests/sample.pdf",   # ← echte PDF hier

        # ── Felder die PDFParserNode füllt ─────────────────────
        # müssen im State existieren, auch wenn leer
        "raw_text":     "",
        "abstract":     "",
        "sections":     {},    # NEU – war in deinem State vergessen
        "title":        "",    # NEU – war in deinem State vergessen

        # ── Felder für spätere Nodes ───────────────────────────
        "entities":     {},
        "embeddings":   [],
        "entity_texts": [],
        "entity_types": [],
        "paper_id":     "",

        # ── Shared ─────────────────────────────────────────────
        "node_results": [],
        "output":       {},
    }

    result = await PDFParserNode.run(state)

    # ── Basis Checks ───────────────────────────────────────────
    print("✓ title:       ", result["title"])
    print("✓ page_count:  ", result["output"]["page_count"])
    print("✓ raw_text:    ", len(result["raw_text"]), "chars")
    print("✓ abstract:    ", len(result["abstract"]), "chars")
    print("✓ sections:    ", list(result["sections"].keys()))

    # ── Abstract Preview ───────────────────────────────────────
    print("\n── ABSTRACT ──────────────────────────────────────────")
    print(result["abstract"])

    # ── Sections ───────────────────────────────────────────────
    print("\n── SECTIONS ──────────────────────────────────────────")
    for section_type, text in result["sections"].items():
        print(f"  [{section_type}] {len(text)} chars — {text[:80].strip()!r}...")

    # ── Node Metadata ──────────────────────────────────────────
    print("\n── NODE OUTPUT ───────────────────────────────────────")
    print("  node:      ", result["output"]["node"])
    print("  timestamp: ", result["output"]["timestamp"])
    print("  metadata:  ", result["output"]["metadata"])


if __name__ == "__main__":
    asyncio.run(test_pdf_parser())
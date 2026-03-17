# tests/test_entity_extractor_node.py
import asyncio
from keybert import KeyBERT
from backend.app.agents.nodes.ingest.pdf_parser_node import PDFParserNode
from backend.app.agents.nodes.ingest.entity_extractor_node import EntityExtractorNode


# ── Mock LLM Client ────────────────────────────────────────────
# Kein echter API-Call nötig zum Testen
# Gibt fixtures zurück als wäre es ein echtes LLM
class MockLLMClient:
    async def generate(self, system: str, prompt: str, **kwargs) -> str:
        return """{"gaps": ["quadratic complexity", "sequential computation", "memory bottleneck"], "innovations": ["self-attention mechanism", "multi-head attention", "positional encoding"]}"""


async def test_entity_extractor():

    # ── Schritt 1: PDF parsen (brauchen wir als Input) ─────────
    print("── Schritt 1: PDF parsen ──────────────────────────────")
    parse_state = {
        "user_id":      "test_user",
        "file_path":    "tests/sample.pdf",
        "raw_text":     "",
        "abstract":     "",
        "sections":     {},
        "title":        "",
        "entities":     {},
        "embeddings":   [],
        "entity_texts": [],
        "entity_types": [],
        "paper_id":     "",
        "node_results": [],
        "output":       {},
    }

    state = await PDFParserNode.run(parse_state)
    print(f"✓ PDF geparst: {len(state['sections'])} Sektionen gefunden")
    print(f"  sections: {list(state['sections'].keys())}")
    print(f"  abstract: {len(state['abstract'])} chars")

    # ── Schritt 2: KeyBERT Modell laden ────────────────────────
    print("\n── Schritt 2: KeyBERT laden ───────────────────────────")
    print("  Lade all-MiniLM-L6-v2 (erster Start: ~50MB Download)...")
    kw_model = KeyBERT("all-MiniLM-L6-v2")
    print("✓ KeyBERT geladen")

    # ── Schritt 3: Entity Extraction ───────────────────────────
    print("\n── Schritt 3: Entity Extraction ───────────────────────")

    # Option A: Mit Mock LLM (kein API-Key nötig)
    llm_client = MockLLMClient()

    # Option B: Mit echtem LLM (API-Key nötig, auskommentiert)
    # from backend.app.llm.client import LLMClient
    # llm_client = LLMClient()

    result = await EntityExtractorNode.run(state, llm_client, kw_model)

    # ── Output anzeigen ────────────────────────────────────────
    entities = result["entities"]

    print(f"\n✓ Total entities: {sum(len(v) for v in entities.values())}")
    print()

    for category, items in entities.items():
        if items:
            print(f"  [{category}] ({len(items)} items)")
            for item in items:
                print(f"    · {item}")
        else:
            print(f"  [{category}] (leer)")

    print("\n── NODE METADATA ──────────────────────────────────────")
    meta = result["output"]["metadata"]
    print(f"  total_entities: {meta['total_entities']}")
    print(f"  llm_source:     {meta['llm_source']}")
    print(f"  keybert_source: {meta['keybert_source']}")
    print(f"  abstract_chars: {meta['abstract_chars']}")
    print(f"  truncated_to:   {meta['truncated_to']}")


if __name__ == "__main__":
    asyncio.run(test_entity_extractor())
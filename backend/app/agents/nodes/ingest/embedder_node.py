# agents/nodes/ingest/embedder_node.py
from typing import ClassVar
from backend.app.agents.state import BaseNodeOutput


class EmbedderNode:
    name: ClassVar[str] = "EmbedderNode"

    class Output(BaseNodeOutput):
        embeddings:   list[list[float]]
        entity_texts: list[str]   # parallel zu embeddings
        entity_types: list[str]   # parallel zu embeddings

    @staticmethod
    async def run(state: dict, embedder) -> dict:
        """
        Embeddet alle Entities als einzigen Batch-Call.

        Kontext-Enrichment:
          "sparse attention" → "method: sparse attention. {abstract[:300]}"
          → reichhaltigerer Vektor, bessere similarity scores im Graph

        normalize_embeddings=True → cosine similarity = dot product
        → schnellere pgvector Queries
        """
        entities = state.get("entities", {})
        abstract = state.get("abstract", "")

        if not entities:
            raise ValueError("entities cannot be empty")

        # ── Flach auflisten ────────────────────────────────────
        entity_texts: list[str] = []
        entity_types: list[str] = []

        for entity_type, items in entities.items():
            for item in items:
                if item.strip():
                    entity_texts.append(item.strip())
                    entity_types.append(entity_type)

        if not entity_texts:
            raise ValueError("no valid entities to embed")

        # ── Kontext-Enrichment ─────────────────────────────────
        abstract_snippet = abstract[:300].strip()
        enriched = [
            f"{etype}: {text}. Context: {abstract_snippet}"
            if abstract_snippet else f"{etype}: {text}"
            for text, etype in zip(entity_texts, entity_types)
        ]

        # ── Einziger Batch-Call ────────────────────────────────
        # ~50ms für 25 entities auf CPU
        embeddings_array = embedder.encode(
            enriched,
            batch_size=32,
            show_progress_bar=False,
            normalize_embeddings=True,
        )

        embeddings = embeddings_array.tolist()

        node_output = EmbedderNode.Output(
            node=EmbedderNode.name,
            embeddings=embeddings,
            entity_texts=entity_texts,
            entity_types=entity_types,
            metadata={
                "entity_count":  len(entity_texts),
                "embedding_dim": len(embeddings[0]) if embeddings else 0,
                "context_chars": len(abstract_snippet),
            }
        )

        output_dict = node_output.model_dump()

        return {
            **state,
            "embeddings":   embeddings,
            "entity_texts": entity_texts,
            "entity_types": entity_types,
            "node_results": state.get("node_results", []) + [output_dict],
            "output":       output_dict,
        }

# agents/nodes/ingest/storage_node.py
import uuid
import json
from typing import ClassVar
from backend.app.agents.state import BaseNodeOutput

SIMILARITY_THRESHOLD = 0.75
TOP_N_SIMILAR        = 5


class StorageNode:
    name: ClassVar[str] = "StorageNode"

    class Output(BaseNodeOutput):
        paper_id: str

    @staticmethod
    async def run(state: dict, db_session, neo4j_session) -> dict:
        """
        Schreibt alles in PostgreSQL + Neo4j.

        Reihenfolge:
        1. PostgreSQL: papers Zeile
        2. PostgreSQL: node_embeddings Zeilen (bulk)
        3. Neo4j: Paper Node + Entity Nodes + Kanten
        4. Neo4j: SIMILAR_TO Kanten zu bestehenden Knoten
        """
        paper_id     = str(uuid.uuid4())
        user_id      = state["user_id"]
        title        = state.get("title", "Unknown")
        abstract     = state.get("abstract", "")
        raw_text     = state.get("raw_text", "")
        sections     = state.get("sections", {})
        entities     = state.get("entities", {})
        embeddings   = state.get("embeddings", [])
        entity_texts = state.get("entity_texts", [])
        entity_types = state.get("entity_types", [])

        await StorageNode._store_paper(
            db_session, paper_id, user_id,
            title, abstract, raw_text, sections, entities
        )
        await StorageNode._store_embeddings(
            db_session, paper_id, user_id,
            entity_texts, entity_types, embeddings
        )
        await StorageNode._store_neo4j(
            neo4j_session, paper_id, user_id,
            title, abstract, entities
        )
        await StorageNode._create_similarity_edges(
            neo4j_session, db_session,
            paper_id, user_id,
            entity_texts, entity_types, embeddings
        )

        node_output = StorageNode.Output(
            node=StorageNode.name,
            paper_id=paper_id,
            metadata={
                "paper_id":        paper_id,
                "entities_stored": len(entity_texts),
            }
        )

        output_dict = node_output.model_dump()

        return {
            **state,
            "paper_id":     paper_id,
            "node_results": state.get("node_results", []) + [output_dict],
            "output":       output_dict,
        }

    # ── PostgreSQL: Paper ──────────────────────────────────────
    @staticmethod
    async def _store_paper(
        db_session, paper_id, user_id,
        title, abstract, raw_text, sections, entities
    ):
        await db_session.execute(
            """
            INSERT INTO papers
              (paper_id, user_id, title, abstract, raw_text, sections, entities)
            VALUES
              (:paper_id, :user_id, :title, :abstract, :raw_text, :sections, :entities)
            """,
            {
                "paper_id": paper_id,
                "user_id":  user_id,
                "title":    title,
                "abstract": abstract,
                "raw_text": raw_text,
                "sections": json.dumps(sections),
                "entities": json.dumps(entities),
            }
        )
        await db_session.commit()

    # ── PostgreSQL: Embeddings (bulk) ──────────────────────────
    @staticmethod
    async def _store_embeddings(
        db_session, paper_id, user_id,
        entity_texts, entity_types, embeddings
    ):
        rows = [
            {
                "id":        str(uuid.uuid4()),
                "paper_id":  paper_id,
                "user_id":   user_id,
                "node_type": entity_type,
                "name":      entity_text,
                "source":    "paper",
                "embedding": json.dumps(embedding),
            }
            for entity_text, entity_type, embedding
            in zip(entity_texts, entity_types, embeddings)
        ]

        await db_session.execute_many(
            """
            INSERT INTO node_embeddings
              (id, paper_id, user_id, node_type, name, source, embedding)
            VALUES
              (:id, :paper_id, :user_id, :node_type, :name, :source, :embedding::vector)
            """,
            rows
        )
        await db_session.commit()

    # ── Neo4j: Paper + Entity Nodes + Kanten ──────────────────
    @staticmethod
    async def _store_neo4j(
        neo4j_session, paper_id, user_id,
        title, abstract, entities
    ):
        # Paper Node
        await neo4j_session.run(
            """
            MERGE (p:Paper {paper_id: $paper_id, user_id: $user_id})
            SET p.title = $title, p.abstract = $abstract
            """,
            paper_id=paper_id, user_id=user_id,
            title=title, abstract=abstract,
        )

        # Entity type → Neo4j Label + Relationship
        type_config = {
            "concepts":    ("Concept",    "HAS_CONCEPT"),
            "methods":     ("Method",     "USES_METHOD"),
            "techniques":  ("Technique",  "USES_TECHNIQUE"),
            "keywords":    ("Keyword",    "HAS_KEYWORD"),
            "gaps":        ("Gap",        "HAS_GAP"),
            "innovations": ("Innovation", "HAS_INNOVATION"),
        }

        for entity_type, items in entities.items():
            config = type_config.get(entity_type)
            if not config:
                continue
            label, rel_type = config

            for item in items:
                await neo4j_session.run(
                    f"""
                    MERGE (e:{label} {{name: $name, user_id: $user_id}})
                    ON CREATE SET e.id = $node_id
                    WITH e
                    MATCH (p:Paper {{paper_id: $paper_id}})
                    MERGE (p)-[:{rel_type}]->(e)
                    """,
                    name=item,
                    user_id=user_id,
                    node_id=str(uuid.uuid4()),
                    paper_id=paper_id,
                )

    # ── Neo4j: Similarity Edges ────────────────────────────────
    @staticmethod
    async def _create_similarity_edges(
        neo4j_session, db_session,
        paper_id, user_id,
        entity_texts, entity_types, embeddings
    ):
        """
        Für jeden neuen Knoten:
        → pgvector findet Top-5 ähnlichste bestehende Knoten (score ≥ 0.75)
        → SIMILAR_TO Kanten in Neo4j

        Das sind die Kanten die den Graph zum Wissensnetz machen —
        Konzepte aus verschiedenen Papers werden automatisch verbunden.
        """
        for entity_text, entity_type, embedding in zip(
            entity_texts, entity_types, embeddings
        ):
            rows = await db_session.fetch_all(
                """
                SELECT name, node_type,
                       1 - (embedding <=> :embedding::vector) AS score
                FROM node_embeddings
                WHERE user_id  = :user_id
                  AND name    != :name
                  AND paper_id != :paper_id
                  AND 1 - (embedding <=> :embedding::vector) >= :threshold
                ORDER BY score DESC
                LIMIT :top_n
                """,
                {
                    "embedding": json.dumps(embedding),
                    "user_id":   user_id,
                    "name":      entity_text,
                    "paper_id":  paper_id,
                    "threshold": SIMILARITY_THRESHOLD,
                    "top_n":     TOP_N_SIMILAR,
                }
            )

            for row in rows:
                await neo4j_session.run(
                    """
                    MATCH (a {name: $name_a, user_id: $user_id})
                    MATCH (b {name: $name_b, user_id: $user_id})
                    MERGE (a)-[r:SIMILAR_TO]->(b)
                    SET r.score = $score, r.auto = true
                    """,
                    name_a=entity_text,
                    name_b=row["name"],
                    user_id=user_id,
                    score=row["score"],
                )

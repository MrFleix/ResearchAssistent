# agents/nodes/ingest/entity_extractor_node.py

import re
import json
from typing import ClassVar
from pydantic import BaseModel, field_validator
from backend.app.agents.state import BaseNodeOutput


# ── Konstanten ─────────────────────────────────────────────────
MAX_ABSTRACT_CHARS = 800
MAX_TEXT_CHARS     = 4000

KEYBERT_DIVERSITY_CONCEPTS   = 0.75
KEYBERT_DIVERSITY_METHODS    = 0.60
KEYBERT_DIVERSITY_TECHNIQUES = 0.85
KEYBERT_DIVERSITY_KEYWORDS   = 0.80

LLM_MAX_TOKENS  = 200
LLM_TEMPERATURE = 0.0


# ── LLM Prompts ────────────────────────────────────────────────
SYSTEM_PROMPT = "Scientific entity extractor. Return ONLY valid JSON."

USER_PROMPT = """Abstract:
{abstract}

Return JSON with exactly these keys:
{{"gaps": [], "innovations": []}}

Rules:
- gaps: open problems or limitations this paper addresses (max 3)
- innovations: novel contributions of this paper (max 3)
- 2-5 words per item
- english only
"""


# ── Output Schema ──────────────────────────────────────────────
class Entities(BaseModel):

    concepts:    list[str]
    methods:     list[str]
    techniques:  list[str]
    keywords:    list[str]
    gaps:        list[str]
    innovations: list[str]

    @field_validator(
        "concepts", "methods", "techniques",
        "keywords", "gaps", "innovations"
    )
    @classmethod
    def clean_items(cls, v: list[str]) -> list[str]:

        cleaned = []

        for item in v:

            item = item.strip().lower()

            if not item:
                continue

            if len(item) < 4:
                continue

            if any(char.isdigit() for char in item):
                continue

            cleaned.append(item)

        return cleaned[:7]


class EntityExtractorNode:

    name: ClassVar[str] = "EntityExtractorNode"

    class Output(BaseNodeOutput):
        entities: dict


    # ── Main Node ─────────────────────────────────────────────
    @staticmethod
    async def run(state: dict, llm_client, kw_model) -> dict:

        sections = state.get("sections", {})
        raw_text = state.get("raw_text", "")
        abstract = state.get("abstract", "")

        if not abstract:
            raise ValueError("abstract cannot be empty")

        # ── 1. Concepts: abstract + introduction ──────────────
        concept_text = " ".join(filter(None, [
            sections.get("abstract", ""),
            sections.get("introduction", "")
        ]))

        concept_text = concept_text[:MAX_TEXT_CHARS]

        concepts = EntityExtractorNode._keybert_extract(
            kw_model,
            concept_text or abstract,
            ngram_range=(2,3),
            top_n=8,
            diversity=KEYBERT_DIVERSITY_CONCEPTS
        )


        # ── 2. Methods + Techniques ───────────────────────────
        methods_text = " ".join(filter(None, [
            sections.get("methods", ""),
            sections.get("approach", ""),
            sections.get("model", ""),
        ]))

        methods_text = methods_text[:MAX_TEXT_CHARS]

        methods = EntityExtractorNode._keybert_extract(
            kw_model,
            methods_text or raw_text[:MAX_TEXT_CHARS],
            ngram_range=(2,3),
            top_n=6,
            diversity=KEYBERT_DIVERSITY_METHODS
        )

        techniques = EntityExtractorNode._keybert_extract(
            kw_model,
            methods_text or raw_text[:MAX_TEXT_CHARS],
            ngram_range=(1,2),
            top_n=6,
            diversity=KEYBERT_DIVERSITY_TECHNIQUES
        )


        # ── 3. Keywords (wichtige Sektionen) ──────────────────
        keyword_text = " ".join(filter(None, [
            sections.get("abstract", ""),
            sections.get("introduction", ""),
            sections.get("conclusion", "")
        ]))

        keyword_text = keyword_text[:MAX_TEXT_CHARS]

        keywords = EntityExtractorNode._keybert_extract(
            kw_model,
            keyword_text,
            ngram_range=(2,3),
            top_n=10,
            diversity=KEYBERT_DIVERSITY_KEYWORDS
        )


        # ── 4. LLM: gaps + innovations ────────────────────────
        gaps, innovations = await EntityExtractorNode._llm_extract(
            llm_client,
            abstract[:MAX_ABSTRACT_CHARS]
        )


        # ── 5. Merge ──────────────────────────────────────────
        entities = EntityExtractorNode._merge(
            concepts,
            methods,
            techniques,
            keywords,
            gaps,
            innovations
        )


        node_output = EntityExtractorNode.Output(
            node=EntityExtractorNode.name,
            entities=entities.model_dump(),
            metadata={
                "total_entities":
                    sum(len(v) for v in entities.model_dump().values()),

                "llm_source":
                    ["gaps", "innovations"],

                "keybert_source":
                    ["concepts", "methods", "techniques", "keywords"],

                "abstract_chars":
                    len(abstract),

                "truncated_to":
                    min(len(abstract), MAX_ABSTRACT_CHARS),
            }
        )

        output_dict = node_output.model_dump()

        return {
            **state,
            "entities":     entities.model_dump(),
            "node_results": state.get("node_results", []) + [output_dict],
            "output":       output_dict,
        }


    # ── Text Cleaning ─────────────────────────────────────────
    @staticmethod
    def _clean_text(text: str) -> str:

        text = re.sub(r"\[\d+\]", " ", text)
        text = re.sub(r"\d{3,}", " ", text)
        text = re.sub(r"\s+", " ", text)

        return text.strip()


    # ── KeyBERT Extraction ────────────────────────────────────
    @staticmethod
    def _keybert_extract(
        kw_model,
        text: str,
        ngram_range: tuple,
        top_n: int,
        diversity: float
    ) -> list[str]:

        if not text.strip():
            return []

        text = EntityExtractorNode._clean_text(text)

        try:

            keyphrases = kw_model.extract_keywords(
                text,
                keyphrase_ngram_range=ngram_range,
                stop_words="english",
                use_mmr=True,
                diversity=diversity,
                nr_candidates=40,
                top_n=top_n
            )

            phrases = []

            for phrase, _score in keyphrases:

                phrase = phrase.lower().strip()

                if len(phrase) < 4:
                    continue

                if any(char.isdigit() for char in phrase):
                    continue

                phrases.append(phrase)

            return phrases

        except Exception:
            return []


    # ── LLM Extraction ────────────────────────────────────────
    @staticmethod
    async def _llm_extract(llm_client, abstract: str):

        prompt = USER_PROMPT.format(abstract=abstract)

        try:

            raw = await llm_client.generate(
                system=SYSTEM_PROMPT,
                prompt=prompt,
                max_tokens=LLM_MAX_TOKENS,
                temperature=LLM_TEMPERATURE,
            )

            data = EntityExtractorNode._parse_llm_response(raw)

            return data.get("gaps", []), data.get("innovations", [])

        except Exception:
            return [], []


    @staticmethod
    def _parse_llm_response(raw: str) -> dict:

        text = raw.strip()

        text = re.sub(r"```(?:json)?", "", text).strip().rstrip("`")

        try:
            return json.loads(text)

        except json.JSONDecodeError:
            return {"gaps": [], "innovations": []}


    # ── Merge + Deduplication ─────────────────────────────────
    @staticmethod
    def _merge(
        concepts,
        methods,
        techniques,
        keywords,
        gaps,
        innovations,
    ) -> Entities:

        seen = set()

        result = {
            "concepts": [],
            "methods": [],
            "techniques": [],
            "keywords": [],
            "gaps": [],
            "innovations": [],
        }

        for category, items in [
            ("concepts", concepts),
            ("methods", methods),
            ("techniques", techniques),
            ("keywords", keywords),
            ("gaps", gaps),
            ("innovations", innovations),
        ]:

            for item in items:

                item_lower = item.lower().strip()

                if not item_lower:
                    continue

                is_duplicate = any(
                    item_lower == s or item_lower in s or s in item_lower
                    for s in seen
                )

                if not is_duplicate:

                    seen.add(item_lower)
                    result[category].append(item_lower)

        return Entities(**result)
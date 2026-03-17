# agents/nodes/ingest/pdf_parser_node.py
import re
from typing import ClassVar, Optional
from pydantic import field_validator
from backend.app.agents.state import BaseNodeOutput


SECTION_MAP = {
    "abstract":         "abstract",
    "summary":          "abstract",
    "introduction":     "introduction",
    "background":       "introduction",
    "motivation":       "introduction",
    "method":           "methods",
    "methods":          "methods",
    "methodology":      "methods",
    "approach":         "methods",
    "proposed method":  "methods",
    "model":            "methods",
    "architecture":     "methods",
    "framework":        "methods",
    "results":          "results",
    "experiments":      "results",
    "evaluation":       "results",
    "experimental":     "results",
    "performance":      "results",
    "benchmarks":       "results",
    "discussion":       "discussion",
    "analysis":         "discussion",
    "ablation":         "discussion",
    "conclusion":       "conclusion",
    "conclusions":      "conclusion",
    "future work":      "conclusion",
    "limitations":      "conclusion",
    "references":       "references",
    "bibliography":     "references",
    "related work":     "related_work",
}

SKIP_SECTIONS = {"references", "bibliography"}


class PDFParserNode:
    name: ClassVar[str] = "PDFParserNode"

    class Output(BaseNodeOutput):
        raw_text:   str
        abstract:   str
        sections:   dict
        page_count: int
        title:      str

        @field_validator("raw_text", "abstract")
        @classmethod
        def non_empty(cls, v: str, info) -> str:
            if not v.strip():
                raise ValueError(f"{info.field_name} cannot be empty")
            return v

    @staticmethod
    async def run(state: dict) -> dict:
        import pymupdf4llm
        import fitz

        file_path = state.get("file_path", "").strip()
        if not file_path:
            raise ValueError("file_path cannot be empty")

        # PDF → sauberes Markdown
        # - Headings als ## / ###
        # - keine Zeilenbrüche mitten im Wort
        # - Zwei-Spalten korrekt zusammengeführt
        md_text = pymupdf4llm.to_markdown(file_path)

        doc        = fitz.open(file_path)
        page_count = len(doc)
        doc.close()

        title    = PDFParserNode._extract_title(md_text)
        sections = PDFParserNode._parse_sections(md_text)
        abstract = (
            sections.get("abstract")
            or PDFParserNode._fallback_abstract(md_text)
        )

        # raw_text = alles außer References
        raw_text = "\n\n".join(
            text for section_type, text in sections.items()
            if section_type not in SKIP_SECTIONS
        ).strip() or md_text[:5000]

        node_output = PDFParserNode.Output(
            node=PDFParserNode.name,
            raw_text=raw_text,
            abstract=abstract,
            sections=sections,
            page_count=page_count,
            title=title,
            metadata={
                "file_path":      file_path,
                "page_count":     page_count,
                "sections_found": list(sections.keys()),
                "abstract_len":   len(abstract),
                "raw_text_len":   len(raw_text),
            }
        )

        output_dict = node_output.model_dump()

        return {
            **state,
            "raw_text":     raw_text,
            "abstract":     abstract,
            "sections":     sections,
            "title":        title,
            "node_results": state.get("node_results", []) + [output_dict],
            "output":       output_dict,
        }

    @staticmethod
    def _extract_title(md_text: str) -> str:
        for line in md_text.splitlines():
            line = line.strip()
            if line.startswith("# ") and not line.startswith("## "):
                return line.lstrip("# ").strip()
        for line in md_text.splitlines():
            if line.strip():
                return line.strip()[:200]
        return "Unknown Title"

    @staticmethod
    def _parse_sections(md_text: str) -> dict:
        sections: dict[str, list[str]] = {}
        current_type: Optional[str]    = None
        current_lines: list[str]       = []

        for line in md_text.splitlines():
            heading_match = re.match(r"^#{2,3}\s+(.+)$", line)

            if heading_match:
                if current_type and current_lines:
                    text = "\n".join(current_lines).strip()
                    if text:
                        sections.setdefault(current_type, []).append(text)

                heading_text  = heading_match.group(1).strip()
                # entferne **bold** und _italic_ Markdown aus Headings
                # "**Abstract**" → "Abstract", "**1 Introduction**" → "1 Introduction"
                heading_text  = re.sub(r"[*_`]", "", heading_text).strip()
                heading_clean = re.sub(r"^\d+[\.\s]+", "", heading_text).strip().lower()
                current_type  = PDFParserNode._map_section(heading_clean)
                current_lines = []
            else:
                if current_type:
                    current_lines.append(line)

        if current_type and current_lines:
            text = "\n".join(current_lines).strip()
            if text:
                sections.setdefault(current_type, []).append(text)

        result = {}
        for section_type, texts in sections.items():
            if section_type in SKIP_SECTIONS:
                continue
            combined = "\n\n".join(texts).strip()
            if not combined:
                continue
            # Abstract-Footnotes entfernen:
            # Blockquotes ("> ...") direkt nach dem Abstract sind
            # fast immer Author-Footnotes, kein Teil des Abstracts
            if section_type == "abstract":
                combined = re.sub(r"\n+>.*", "", combined, flags=re.DOTALL).strip()
            result[section_type] = combined
        return result

    @staticmethod
    def _map_section(heading: str) -> str:
        heading_lower = heading.lower().strip()
        if heading_lower in SECTION_MAP:
            return SECTION_MAP[heading_lower]
        for key, section_type in SECTION_MAP.items():
            if key in heading_lower:
                return section_type
        return "other"

    @staticmethod
    def _fallback_abstract(md_text: str) -> str:
        lines       = md_text.splitlines()
        after_title = False

        for i, line in enumerate(lines):
            if line.startswith("# ") and not line.startswith("## "):
                after_title = True
                continue
            if after_title and line.strip() and not line.startswith("#"):
                paragraph_lines = []
                for j in range(i, min(i + 30, len(lines))):
                    if lines[j].startswith("#"):
                        break
                    paragraph_lines.append(lines[j])
                paragraph = "\n".join(paragraph_lines).strip()
                if len(paragraph) >= 100:
                    return paragraph[:1500]

        return md_text[:1500].strip()
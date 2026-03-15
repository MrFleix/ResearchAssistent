# Research Intelligence System — Hackathon Architecture Prompt

## Produkt-Vision

Ein interaktiver Knowledge Graph für ML-Konzepte aus wissenschaftlichen Papers.
User laden PDFs hoch → Konzepte werden automatisch als Knoten extrahiert →
Graph visualisiert Verbindungen → User können eigene Knoten hinzufügen →
LLM hilft Ideen und Konzepte zu entwickeln.

---

## Core User Flows

### Flow 1: PDF hochladen
```
User lädt PDF hoch
  → docling parsed Paper
  → gpt-4o-mini extrahiert Konzepte/Methoden/Gaps
  → Embeddings berechnet
  → Knoten + Kanten in Neo4j gespeichert
  → Graph im Frontend aktualisiert sich live
```

### Flow 2: Eigenen Knoten hinzufügen
```
User gibt Namen + Beschreibung ein (z.B. "My Idea: Sparse Attention for Video")
  → Embedding berechnet
  → pgvector findet ähnlichste bestehende Knoten
  → Auto-Verbindungen zu Top-N ähnlichen Knoten erstellt
  → User kann Verbindungen manuell anpassen (hinzufügen / entfernen)
  → Knoten erscheint im Graph
```

### Flow 3: RAG-Interaktion
```
Option A — Einzelner Knoten:
  User klickt Knoten an → Chat öffnet sich
  → LLM erklärt Konzept, zeigt verwandte Papers, schlägt Erweiterungen vor

Option B — Mehrere Knoten selektiert:
  User wählt 2-5 Knoten → "Develop Idea" Button
  → LLM verbindet die Konzepte, identifiziert Gaps, schlägt Projekte vor
```

---

## Tech Stack

| Layer | Technology | Begründung |
|---|---|---|
| Frontend | React + TypeScript | Hackathon-Standard, schnell |
| Graph Visualisierung | `react-force-graph-2d` | Interaktiv, Force-Layout, performant |
| Backend | FastAPI + async | Passt zu LangGraph Pattern |
| PDF Parsing | `docling` | ML-basiert, kein Regex, strukturierter Output |
| Entity Extraction | `gpt-4o-mini` | ~500 tokens/Paper, einmalig |
| Embeddings | `sentence-transformers all-MiniLM-L6-v2` | Lokal, 384-dim, kein API-Cost |
| Vector Store | `pgvector` (PostgreSQL) | Multi-user, kein extra Service |
| Knowledge Graph | `Neo4j` | Native Graph DB, Cypher |
| Task Queue | `ARQ` + Redis | Async PDF Processing |
| Realtime Updates | WebSocket (FastAPI) | Graph aktualisiert sich live nach Upload |

---

## Datenmodell

### Neo4j — Node Types

```cypher
// Automatisch aus Paper extrahiert
(:Concept   {id, name, user_id, source: "paper", paper_id, description, created_at})
(:Method    {id, name, user_id, source: "paper", paper_id, description, created_at})
(:Technique {id, name, user_id, source: "paper", paper_id, description, created_at})
(:Gap       {id, name, user_id, source: "paper", paper_id, description, created_at})

// Vom User manuell erstellt
(:UserNode  {id, name, user_id, source: "user", description, created_at})

// Paper selbst
(:Paper     {id, paper_id, user_id, title, abstract, created_at})
```

### Neo4j — Edge Types

```cypher
// Paper → Entitäten
(:Paper)-[:HAS_CONCEPT]->(:Concept)
(:Paper)-[:USES_METHOD]->(:Method)
(:Paper)-[:INTRODUCES]->(:Technique)
(:Paper)-[:IDENTIFIES_GAP]->(:Gap)

// Semantische Ähnlichkeit (auto, via Embeddings)
(:Concept)-[:SIMILAR_TO   {score: float, auto: true}]->(:Concept)
(:Method)-[:RELATED_TO    {score: float, auto: true}]->(:Method)
(:UserNode)-[:CONNECTS_TO {score: float, auto: true}]->(:Concept)
(:UserNode)-[:CONNECTS_TO {score: float, auto: true}]->(:Method)

// Manuell vom User
(:UserNode)-[:MANUALLY_LINKED {created_by: "user"}]->(:Concept)
(:UserNode)-[:MANUALLY_LINKED {created_by: "user"}]->(:UserNode)
```

### PostgreSQL + pgvector

```sql
CREATE EXTENSION vector;

CREATE TABLE papers (
    paper_id   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id    UUID NOT NULL,
    title      TEXT,
    abstract   TEXT NOT NULL,
    raw_text   TEXT NOT NULL,
    entities   JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT now()
);

-- Ein Eintrag pro Entität (Konzept, Methode, etc.)
CREATE TABLE node_embeddings (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    node_id     TEXT NOT NULL,        -- Neo4j node ID
    user_id     UUID NOT NULL,
    node_type   TEXT NOT NULL,        -- Concept | Method | Technique | Gap | UserNode
    name        TEXT NOT NULL,
    description TEXT,
    source      TEXT NOT NULL,        -- "paper" | "user"
    embedding   vector(384),
    created_at  TIMESTAMP DEFAULT now()
);

CREATE INDEX ON node_embeddings USING hnsw (embedding vector_cosine_ops);
```

---

## Backend — Workflows

### 1. `ingest_workflow` (nach PDF-Upload)

```
PDFParserNode
  Input:  file_path
  Tool:   docling (OCR off, digital PDFs)
  Output: raw_text, abstract, page_count

EntityExtractorNode
  Input:  abstract
  Tool:   gpt-4o-mini
  Prompt: extrahiere {concepts[], methods[], techniques[], gaps[]} als JSON
  Output: entities dict
  Cost:   ~$0.002 / Paper

EmbedderNode
  Input:  alle entity strings (flattened)
  Tool:   sentence-transformers lokal
  Output: embeddings List[List[float]]

StorageNode
  Input:  full state
  Writes:
    PostgreSQL → papers + node_embeddings Zeilen
    Neo4j      → Paper Node + Entity Nodes + typed Edges
  Output: paper_id

SimilarityEdgeNode  ← NEU (wichtig für Graph-Qualität)
  Input:  neue node_embeddings
  Tool:   pgvector + Neo4j
  Logik:  für jeden neuen Knoten → finde Top-5 ähnlichste bestehende Knoten
          (score > 0.7) → erstelle SIMILAR_TO / RELATED_TO Kanten in Neo4j
  Output: neue Kanten im Graph
```

### 2. `add_user_node_workflow` (wenn User Knoten hinzufügt)

```
UserNodeEmbedderNode
  Input:  name + description vom User
  Tool:   sentence-transformers lokal
  Output: embedding

UserNodeStorageNode
  Input:  name, description, embedding, user_id
  Writes:
    PostgreSQL → node_embeddings Zeile (source="user")
    Neo4j      → UserNode
  Output: node_id

AutoConnectNode
  Input:  embedding des neuen UserNode
  Tool:   pgvector cosine similarity
  SQL:
    SELECT node_id, name, node_type,
           1 - (embedding <=> :new_vec) AS score
    FROM node_embeddings
    WHERE user_id = :user_id AND node_id != :new_node_id
    ORDER BY score DESC
    LIMIT 5
  Output: Top-5 ähnliche Knoten + Scores
  Writes: CONNECTS_TO Kanten in Neo4j (auto: true)

→ Frontend zeigt Auto-Verbindungen an
→ User kann Verbindungen bestätigen, entfernen, oder manuell neue ziehen
→ PATCH /nodes/{id}/edges für manuelle Anpassungen
```

### 3. `rag_workflow` (Chat über Knoten)

```
SubgraphRetrieverNode
  Input:  selected_node_ids[], user_id
  Tool:   Neo4j Cypher
  Cypher:
    MATCH (n)-[r]-(m)
    WHERE n.id IN $node_ids AND n.user_id = $user_id
    RETURN n, r, m
  Output: subgraph {nodes[], edges[]}

SubgraphSerializerNode
  Input:  subgraph
  Output: strukturierter Text-Kontext für LLM
  Format:
    "Selected concepts: Attention, Transformer
     Connected to: Self-Attention (SIMILAR_TO, 0.92), BERT (via Paper X)
     Related gaps: Long-context efficiency
     User notes: My Idea — Sparse Attention for Video"

InsightGeneratorNode
  Input:  serialized subgraph + user question
  Tool:   gpt-4o-mini (oder Claude claude-haiku-4-5-20251001 für längere Antworten)
  Modes:
    - single node  → erkläre Konzept, zeige verwandte Papers, schlage Erweiterungen vor
    - multi node   → verbinde Konzepte, identifiziere Gaps, schlage Forschungsprojekte vor
  Cost:   ~$0.004 / Query
```

---

## Frontend

### Graph-Komponente (`react-force-graph-2d`)

```typescript
// Knoten-Typen haben verschiedene Farben + Größen
const nodeColors = {
  Concept:   "#7F77DD",  // purple
  Method:    "#1D9E75",  // teal
  Technique: "#EF9F27",  // amber
  Gap:       "#E24B4A",  // red
  UserNode:  "#378ADD",  // blue  ← User-erstellte Knoten
  Paper:     "#888780",  // gray
}

// Kanten-Typen haben verschiedene Stärken
const edgeStyles = {
  SIMILAR_TO:     { width: score * 3, dashed: false },
  RELATED_TO:     { width: score * 3, dashed: false },
  CONNECTS_TO:    { width: score * 3, dashed: true  },  // auto-verbunden
  MANUALLY_LINKED:{ width: 2,         dashed: false },  // manuell
  HAS_CONCEPT:    { width: 1,         color: "#ccc" },
}
```

### UI-Panels

```
┌─────────────────────────────────────────────────────┐
│  [Upload PDF]    [+ Add Node]    [Search concepts]  │
├──────────────────────────────┬──────────────────────┤
│                              │                      │
│      Interactive Graph       │    Chat / RAG Panel  │
│      (react-force-graph)     │                      │
│                              │  Selected: [Attention│
│   ○ Attention ──── ○ BERT    │  + Transformer]      │
│        │                     │                      │
│   ○ Transformer              │  "How can I combine  │
│        │                     │   these for video?"  │
│   ★ My Idea (UserNode)       │                      │
│                              │  [LLM Response...]   │
│                              │                      │
└──────────────────────────────┴──────────────────────┘
```

### Key Interactions

```
Klick auf Knoten        → Knoten selektieren (highlight + Info-Panel)
Shift + Klick           → Mehrere Knoten selektieren
Rechtsklick auf Knoten  → Kontextmenü: "Chat", "Develop Idea", "Delete"
Drag zwischen Knoten    → Manuelle Kante erstellen
[+ Add Node] Button     → Modal: Name + Beschreibung eingeben
[Develop Idea] Button   → RAG mit allen selektierten Knoten
```

---

## API Endpoints

```
POST   /api/ingest                    → PDF hochladen, ARQ Job enqueuen
GET    /api/graph/{user_id}           → Kompletten Graph laden (nodes + edges)
POST   /api/nodes                     → Eigenen Knoten hinzufügen
PATCH  /api/nodes/{id}/edges          → Manuelle Kanten anpassen
POST   /api/chat                      → RAG: {node_ids[], question}
WS     /ws/ingest/{job_id}            → Live-Updates während PDF Processing
```

---

## File Structure

```
project/
├── backend/
│   ├── app/
│   │   ├── agents/
│   │   │   ├── state.py
│   │   │   ├── graphs/
│   │   │   │   ├── ingest_graph.py
│   │   │   │   ├── add_node_graph.py
│   │   │   │   └── rag_graph.py
│   │   │   └── nodes/
│   │   │       ├── ingest/
│   │   │       │   ├── pdf_parser_node.py
│   │   │       │   ├── entity_extractor_node.py
│   │   │       │   ├── embedder_node.py
│   │   │       │   ├── storage_node.py
│   │   │       │   └── similarity_edge_node.py   ← NEU
│   │   │       ├── user_node/
│   │   │       │   ├── user_node_embedder_node.py
│   │   │       │   ├── user_node_storage_node.py
│   │   │       │   └── auto_connect_node.py      ← NEU
│   │   │       └── rag/
│   │   │           ├── subgraph_retriever_node.py
│   │   │           ├── subgraph_serializer_node.py
│   │   │           └── insight_generator_node.py
│   │   ├── api/
│   │   │   ├── ingest.py
│   │   │   ├── graph.py
│   │   │   ├── nodes.py
│   │   │   └── chat.py
│   │   └── db/
│   │       ├── postgres.py
│   │       └── neo4j.py
│   └── workers/
│       └── ingest_worker.py
├── frontend/
│   └── src/
│       ├── components/
│       │   ├── Graph.tsx             ← react-force-graph-2d
│       │   ├── ChatPanel.tsx
│       │   ├── AddNodeModal.tsx
│       │   └── UploadModal.tsx
│       └── hooks/
│           ├── useGraph.ts
│           └── useChat.ts
└── docker-compose.yml
```

---

## Docker Compose

```yaml
services:
  postgres:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_DB: research_db
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres

  neo4j:
    image: neo4j:5
    environment:
      NEO4J_AUTH: neo4j/password
    ports: ["7474:7474", "7687:7687"]

  redis:
    image: redis:7-alpine

  grobid:
    image: otalvaro/grobid:0.8.0
    ports: ["8070:8070"]

  backend:
    build: ./backend
    depends_on: [postgres, neo4j, redis]
    ports: ["8000:8000"]

  worker:
    build: ./backend
    command: python -m workers.ingest_worker
    depends_on: [postgres, neo4j, redis]

  frontend:
    build: ./frontend
    ports: ["3000:3000"]
```

---

## Hackathon Prioritäten

### MVP (Tag 1-2)
- [ ] PDF Upload → Entity Extraction → Graph in Neo4j
- [ ] Graph Visualisierung mit react-force-graph-2d
- [ ] Knoten anklicken → Chat Panel mit RAG

### Nice to Have (Tag 3)
- [ ] User kann eigene Knoten hinzufügen + Auto-Connect
- [ ] Mehrere Knoten selektieren → "Develop Idea"
- [ ] Manuelle Kanten ziehen im Graph
- [ ] Live-Updates via WebSocket während Upload

### Stretch Goal
- [ ] arXiv URL als Input (kein PDF-Upload nötig)
- [ ] Graph exportieren als JSON / PNG

---

## Cost Estimate (Hackathon Demo)

| Aktion | Cost |
|---|---|
| 1 Paper ingesten | ~$0.002 |
| 1 User Query | ~$0.004 |
| 50 Papers + 200 Queries (Demo-Tag) | ~$0.90 |

**Compute:** Hetzner CX32 (4 vCPU / 8 GB) ~€15/Monat — reicht für Hackathon vollständig.

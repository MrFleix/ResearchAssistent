# Market Intelligence & Research Graph Agent

## Project Overview

This project is a **Market Intelligence & Research Graph Agent** that collects live web data, academic papers, AI models, and social media trends, then generates **actionable AI-powered insights** for research gaps, emerging trends, and project opportunities. It uses:

- **LangGraph** for workflow orchestration  
- **Apify** for web scraping of websites, social media, and datasets  
- A **RAG (retrieval-augmented generation) layer** for persistent knowledge and dynamic graph insights  
- A **Knowledge Graph** connecting Papers, Models, Datasets, Concepts, and Trends  

**Key Features:**

- Collects structured data from papers (arXiv), models (HuggingFace, GitHub), and social media (Reddit, Twitter/X, TikTok)  
- Builds a **dynamic Knowledge Graph** with nodes (Paper, Model, Dataset, Topic, Trend) and edges (cites, extends, applies_to, related_to, trending_in)  
- Generates **LLM-powered insights** for trends, research gaps, and actionable project ideas  
- Detects trending topics across domains using social media signals  
- Modular architecture: easy to extend to new data sources or industries  
- Step-by-step workflow visualization (StepViewer)  
- Trend detection, clustering, and ranking without excessive LLM calls  
- Optional persistent storage with vector database (FAISS/Chroma) and raw JSON/CSV  
- Minimal SaaS-ready design with JWT-based login, query tracking, and scalable architecture  

---

## Idea

Research Intelligence System – Architecture Prompt
Build a modular, token-efficient research assistant that transforms academic papers into an interactive, user-centric knowledge graph for ideation and insight generation.
Core Pipeline:
The system accepts papers (PDF/arXiv) as input and extracts structured information (concepts, methods, results, citations) using minimal LLM calls — preferring rule-based parsing where possible.
Extracted entities are embedded and connected via similarity scores into a dynamic Knowledge Graph with typed nodes (Paper, Concept, Method, Dataset, Technique) and typed edges (cites, extends, applies_to, similar_to, related_to).
User-Centric Graph Construction:
The graph is not built generically — it is anchored to a user query or interest (e.g. "attention mechanisms for long-context transformers"). Similarity scores between extracted concepts and the user's focus determine which nodes are included, ranked, and connected. The graph evolves interactively as the user refines their focus.
RAG over Knowledge Graph:
The Knowledge Graph serves as the retrieval backbone. When the user asks a question, relevant subgraphs are retrieved (not raw chunks) and passed as structured context to the LLM. This enables the LLM to act as a research advisor — identifying research gaps, suggesting project ideas, and connecting techniques across papers.
Workflows:

ingest_workflow — Parse paper → extract entities → embed → store
graph_build_workflow — User query → similarity ranking → build/update subgraph
rag_workflow — User question → subgraph retrieval → LLM insight generation

Constraints:

Minimize LLM calls: use embeddings + similarity for graph construction, LLM only for insight/advisory layer
Token-efficient prompts: pass subgraphs not full documents
Modular: each workflow independently invokable
Extensible: new sources (HuggingFace, Reddit) can plug into ingest_workflow

## Start
uvicorn backend.app.main:app --reload
-Frontend  cd frontend npm run dev
-Backend cd backend/app uvicorn main:app --port 8000
uvicorn backend.app.main:app --port 8000
## Tech Stack

- **Backend:** FastAPI, Python  
- **Frontend:** Next.js, React, TypeScript  
- **Workflow:** LangGraph (Planner, Scraper, Processing, Report Nodes)  
- **Vector DB / RAG:** FAISS or Chroma  
- **Web Scraping:** Apify API (Papers, Models, Social Media)  
- **LLM Integration:** Openrouter / LangChain-compatible  
- **Database:** PostgreSQL (optional)  
- **Authentication:** JWT tokens, password hashing  

---

## File and Folder Explanation

### `backend/`

- **`app/main.py`** – FastAPI backend entry point  
- **`app/config.py`** – Environment variables and configuration  

**API Routes:**

- **`routes_auth.py`** – Login, registration, token generation  
- **`routes_user.py`** – User profile and optional tenant info  
- **`routes_query.py`** – Endpoint to start workflows and retrieve insights  

**Auth Module:**

- **`jwt_handler.py`** – Encode/decode JWT  
- **`password_utils.py`** – Password hashing  

**User Module:**

- **`user_service.py`**, **`user_repo.py`** – User management and DB operations  

**Agents / LangGraph Workflow:**

- **`graph.py`** – Full LangGraph workflow  
- **`state.py`** – Workflow state tracking  
- **`nodes/`** – Individual nodes:  
  - `planner_node.py` – Decides which sources to scrape and which LLM prompts to generate  
  - `scraping_node.py` – Calls Apify for Papers, Models, Social Media, Trends  
  - `processing_node.py` – Graph building, clustering, trend detection, ranking  
  - `report_node.py` – Generates narrative insights and project ideas via LLM  

**Services:**

- **`apify_service.py`** – Web scraping logic  
- **`rag_service.py`** – Vector DB retrieval + RAG layer  
- **`trend_service.py`** – Social media / trend analysis and scoring  

**Storage:**

- **`database.py`** – PostgreSQL setup  
- **`vector_store.py`** – FAISS/Chroma integration  
- **`file_store.py`** – Raw JSON/CSV storage  

**Models:**

- **`user_model.py`**, **`tenant_model.py`**, **`query_model.py`**, **`insight_model.py`** – Track users, queries, and generated insights  

---

### `frontend/`

- **`pages/login.tsx`**, **`pages/register.tsx`**, **`pages/dashboard.tsx`**, **`pages/query.tsx`**  
- **Components:**  
  - `QueryInput.tsx` – Submit queries  
  - `StepViewer.tsx` – Live workflow steps  
  - `KnowledgeGraph.tsx` – Interactive graph of Papers, Models, Datasets, Trends  
  - `MarketMap.tsx` – Scatterplots / clustering  
  - `TrendChart.tsx` – Trend growth/mentions  
  - `ReportView.tsx` – LLM-generated narrative report  

---

### `data/`

- **`raw/`** – Raw JSON/CSV from scrapers  
- **`insights/`** – Processed insights, trends, project ideas  
- **`vector_db/`** – Embeddings for RAG  

---

### `scripts/`

- **`generate_demo_data.py`** – Fake data for testing  
- **`update_embeddings.py`** – Update vector database  

---

### LangGraph Prompts

**Workflow Prompt:**  
> "Act as an AI workflow engineer. Define LangGraph nodes for Papers, Models, Datasets, and Social Trends. Specify input/output JSON, edges, and data flow. Suggest LLM prompts for Planner & Report nodes. Make it modular and reusable."

**Apify Integration:**  
> "Act as a web scraping engineer. Integrate Apify to collect Papers, Models, and Social Trends. Show Python/FastAPI usage, error handling, retries, and output JSON structure for Processing node."

**Frontend Prompt:**  
> "Act as a frontend engineer. Plan pages and components to visualize workflow, Knowledge Graph, trends, and reports. Use React/Next.js + TypeScript with minimal setup."

**RAG & Vector DB Prompt:**  
> "Act as a data engineer. Design the persistent knowledge layer with FAISS/Chroma for embeddings. Store Papers, Models, Social Trend nodes with metadata. Include query/retrieval logic."

**Visualization Prompt:**  
> "Act as a data visualization expert. Show dynamic Market Maps, Trend Charts, and Knowledge Graph. Suggest libraries (React Flow, Cytoscape.js, Plotly). Make it interactive for Hackathon demo."

**Login & Auth Prompt:**  
> "Act as a backend engineer. Implement JWT login/registration with minimal user management. Track queries and support multi-tenancy. Keep it modular and hackathon-ready."

---

### **USP / Hackathon Highlights**

- Dynamic **Knowledge Graph** combining Papers, Models, Datasets, Concepts, and Social Trends  
- **RAG + LLM** generates actionable insights, research gaps, and project ideas  
- Trend detection from **Reddit, Twitter/X, TikTok**  
- Nodes and edges are **reusable for any domain or dataset**  
- Focused on **interactive visualization + actionable outputs** for strong Hackathon demo








ResearchMind – Interactive Knowledge Graph for Research Ideation
ResearchMind is a modular, token-efficient research intelligence system that transforms academic papers and knowledge sources into an interactive, user-centric knowledge graph for ideation, gap detection, and insight generation.
The Problem:
Researchers and builders drowning in papers struggle to connect concepts across sources, identify research gaps, and translate knowledge into actionable ideas. Existing tools like NotebookLM offer RAG over documents — but none offer structured, visual, interactive reasoning over knowledge relationships.
The Solution:
A dual-window interface combining an interactive knowledge graph with an AI chat advisor — synchronized in real time.
Left window: a living knowledge graph where nodes represent concepts, methods, techniques, and papers — connected by typed edges (cites, extends, applies_to, similar_to). The user shapes the graph interactively: setting focus, adding sources, pruning irrelevant nodes.
Right window: an LLM-powered research advisor that is always aware of the user's current graph focus — answering questions, surfacing research gaps, and proactively generating project ideas based on the visible subgraph.
What makes it different:
The graph is not built generically — it is anchored to user intent. When a user focuses on "attention mechanisms for long-context transformers", the system ranks and connects only the most relevant entities from ingested sources using embedding similarity. The graph evolves as the user refines their focus.
Agents go beyond answering questions — they actively detect structural gaps in the graph (concepts with no connections, underexplored intersections) and propose concrete research directions and project ideas.
Technical Architecture:

ingest_workflow — PDF/arXiv → section-aware parsing → LLM entity extraction (abstract only, ~300 tokens) → local embeddings (sentence-transformers) → stored as structured JSON + FAISS index
graph_build_workflow — User query → cosine similarity ranking → dynamic subgraph construction with typed nodes and edges → no LLM calls
rag_workflow — User question + focused subgraph → token-efficient LLM prompt (~200 tokens context) → insight, gap detection, idea generation

Built on LangGraph for modular, independently invokable workflows. Frontend: React + Cytoscape.js for graph visualization. Backend: FastAPI + async Python.
Token efficiency by design:
LLM is called only twice per paper (entity extraction from abstract) and once per user query (advisory response over subgraph). Graph construction and retrieval are purely embedding-based — no LLM involved.
Extensible:
New knowledge sources (HuggingFace models, Reddit discussions, arXiv feeds) plug directly into ingest_workflow without changing downstream workflows.
Target users:
Researchers, PhD students, AI engineers, and product builders who want to think faster and deeper across multiple knowledge sources.








ingest_graph.py
Der ingest_workflow verarbeitet ein PDF Paper vollständig und speichert 
es als strukturierten Paper Node für spätere Graph- und RAG-Nutzung.

ARCHITEKTUR:
Folgt exakt dem Pattern von chat_graph.py:
- build_ingest_graph(llm_client, embedder) → kompilierter StateGraph
- run_ingest_workflow(user_id, file_path, llm_client, embedder) → dict
- Nodes per closure mit dependencies reingeben
- initial_state mit allen leeren Feldern initialisieren

STATE:
Nutzt IngestState aus agents/state.py:
- file_path   → Input vom User
- raw_text    → von PDFParserNode gefüllt
- abstract    → von PDFParserNode gefüllt
- entities    → von EntityExtractorNode gefüllt
- embeddings  → von EmbedderNode gefüllt
- paper_id    → von StorageNode vergeben

NODE PIPELINE (in dieser Reihenfolge):
parse_pdf → extract_entities → embed → store

1. PDFParserNode (nodes/ingest/pdf_parser_node.py)
   - Input:  state["file_path"]
   - Nutzt:  pymupdf
   - Output: state["raw_text"] + state["abstract"]
   - Kein LLM, kein Embedder

2. EntityExtractorNode (nodes/ingest/entity_extractor_node.py)
   - Input:  state["abstract"]
   - Nutzt:  llm_client.generate(prompt)
   - Output: state["entities"] als dict:
             {concepts, methods, techniques, gaps, keywords}
   - Einziger LLM call im gesamten workflow (~500 tokens)

3. EmbedderNode (nodes/ingest/embedder_node.py)
   - Input:  state["entities"]
   - Nutzt:  embedder.encode(entity_strings)
   - Output: state["embeddings"] als List[List[float]]
   - Kein LLM, läuft lokal

4. StorageNode (nodes/ingest/storage_node.py)
   - Input:  kompletter state
   - Nutzt:  uuid, json, faiss
   - Output: state["paper_id"]
   - Speichert storage/papers/{paper_id}.json:
             {paper_id, user_id, file_path, raw_text, 
              abstract, entities, embeddings, created_at}
   - Updated FAISS index in storage/faiss/

DEPENDENCIES:
- llm_client → LLMProvider aus models/llm_provider.py
              wird in main.py als app.state.llm initialisiert
- embedder   → Embedder aus models/embedder.py
              wird in main.py als app.state.embedder initialisiert

NODE PATTERN (wie chat_node.py):
Jeder Node:
- hat ClassVar name
- hat innere Output(BaseNodeOutput) Klasse mit Pydantic validierung
- hat statische async run(state, ...) Methode
- gibt immer zurück:
  {
    **state,
    "neues_feld": wert,
    "node_results": state["node_results"] + [output_dict],
    "output": output_dict
  }

TOKEN BUDGET:
- PDFParserNode:       0 tokens
- EntityExtractorNode: ~500 tokens (einmalig pro Paper)
- EmbedderNode:        0 tokens
- StorageNode:         0 tokens
─────────────────────────────────
Total pro Paper:       ~500 tokens
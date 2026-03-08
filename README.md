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

## Start

-Frontend  cd frontend npm run dev
-Backend cd backend/app uvicorn main:app --port 8000

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
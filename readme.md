 # 🤖 SAP SuccessFactors Troubleshooting Engine

AI-powered RAG + Vision system for automating ERP troubleshooting.

---

## 📁 Core Components

### 1. Agent Orchestrator (`src/agent.py`)
**Central coordinator of the system**
- Orchestrates RAG search, vision analysis, and PDF data
- **Text mode:** returns only the top matching task
- **Vision mode:** tries up to 3 tasks, stops at first with confidence ≥ 0.7
- Falls back gracefully: vision → text → error
- Saves all results automatically to `/results`

---

### 2. PDF Processor (`src/pdf_processor.py`)
**Extracts structured knowledge from PDF guides**
- Parses PDF using `PyMuPDF`
- Splits content using `ENDOFTASK` markers
- Extracts lettered and numbered steps (`a.`, `b.`, `1.`, `2.`)
- Categorizes steps into action types:
  - Navigation
  - Click
  - Input
  - Verification
  - Save
- Saves all images to `data/screenshots/task_X/`

---

### 3. Vision Analyzer (`src/vision_analyzer.py`)
**AI-powered screenshot understanding**
- Uses Gemini 2.5 Flash
- Compares user screenshot against guide images
- Identifies where the user is in the workflow
- Returns all remaining steps from the current position
- Outputs confidence score (0.0–1.0) with each analysis

---

### 4. RAG Engine (`src/rag_engine.py`)
**Semantic document retrieval layer**
- Uses ChromaDB for local vector storage
- Indexes all PDF tasks as embeddings
- Fast semantic similarity search (default threshold: 0.7)
- Supports metadata filtering:
  - `has_steps`
  - Page numbers
  - Task IDs

---

### 5. Orchestrator (`src/orchestrator.py`)
**Production-ready engine wrapper**
- `Config` class for centralized settings
- `TroubleshootingEngine` class for programmatic use
- Handles initialization, error responses, and result saving
- Can be imported and used directly in your applications

---

### 6. Command Line Interface (`cli.py`)
**Interactive user interface**
- Runs the engine with a simple menu system
- Options:
  - Text-only troubleshooting
  - Screenshot troubleshooting
  - Test suite
  - Engine status
  - Reset engine
- Located in project root for easy access

---


### 7. Browser Automation (`login.py`)
**Automated ERP validation**

- Built using **Playwright**
- Intelligent SAP SuccessFactors login handling:
  - Detects fresh vs. existing sessions
- Captures full-page screenshots
- Includes:
  - 3-attempt retry mechanism
  - Robust error handling

---

## 🚀 Quick Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Install Playwright browser
playwright install chromium

# 3. Configure environment
cp .env.example .env
# Add ERP credentials and Gemini API key

# 4. Run the system
python src/main.py

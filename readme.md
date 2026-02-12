
---

## 📁 Core Components

### 1. Agent Orchestrator (`agent.py`)
**Central coordinator of the system**

- Orchestrates vision analysis, RAG search, and PDF parsing
- Uses `ENDOFTASK` markers to split PDF content
- Extracts lettered or numbered steps using regex (`a.`, `b.`, `1.`, `2.`)
- Categorizes steps into action types:
  - Navigation
  - Click
  - Search
  - Verification
- Outputs structured troubleshooting steps

---

### 2. PDF Processor (`pdf_processor.py`)
**Processes ERP troubleshooting guides**

- Reads and parses PDF documentation
- Splits content using `ENDOFTASK` delimiters
- Extracts:
  - Task numbers
  - Step counts
  - Page references
- Converts content into structured task objects for vector indexing

---

### 3. Vision Analyzer (`vision_analyzer.py`)
**AI-powered screenshot understanding**

- Uses **Gemini 2.5 Flash (Vision Model)**
- Identifies ERP screen context (Admin Center, Permissions, Errors)
- Detects visible UI elements and issues
- Returns structured JSON output

---

### 4. RAG Engine (`rag_engine.py`)
**Semantic document retrieval layer**

- Uses **ChromaDB** for local vector storage
- Indexes PDF tasks using embeddings
- Fast semantic similarity search
- Supports metadata filtering:
  - `has_steps`
  - Page numbers
  - Task IDs

---

### 5. Browser Automation (`login.py`)
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

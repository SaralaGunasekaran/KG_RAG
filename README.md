🌾 Agri AI Assistant — Knowledge Graph RAG Application

An end-to-end, bilingual (English / தமிழ்) AI-powered assistant designed to answer queries regarding Tamil Nadu Government agricultural, Farmers Welfare Department, and MSME schemes. Built using a Knowledge Graph Retrieval-Augmented Generation (GraphRAG) architecture, the application ensures grounded, hallucination-free responses backed by Neo4j AuraDB, LangChain, NVIDIA NeMo Guardrails, FastAPI, and Streamlit.


🏗️ System Architecture

The project is cleanly decoupled into three modular components:

Offline Ingestion & Evaluation Pipeline (RAG.py)

Scraping & Chunking: Fetches live scheme data from tn.gov.in (requests + BeautifulSoup) and splits text using RecursiveCharacterTextSplitter.

Knowledge Graph Extraction: Uses LLMGraphTransformer (gpt-4o-mini) to extract schema-constrained entities (Scheme, Department, Beneficiary, Benefit, Organization) and relationships (ADMINISTERED_BY, TARGETS, PROVIDES, IMPLEMENTED_WITH, PART_OF) into Neo4j AuraDB.

Automated Evaluation: Validates retrieval faithfulness and answer relevancy using DeepEval (FaithfulnessMetric and AnswerRelevancyMetric).

FastAPI Live Backend (backend.py)

Input Guardrails: Enforces topic and prompt-injection safety using NVIDIA NeMo Guardrails before executing any database queries.

Text-to-Cypher QA: Converts natural language questions into case-insensitive, undirected Cypher queries (GraphCypherQAChain) with strict grounding prompts.

Bilingual Support: Translates Tamil user queries into English for accurate graph traversal, then translates grounded Neo4j answers back into formal Tamil.

Streamlit Frontend UI (frontend.py)

Agricultural Theme: Features a custom green aesthetic with a fixed agricultural banner, light-green background, and styled chat cards.

Interactive Controls: Includes instant English / தமிழ் language toggles, session chat memory, chat history reset, and word-by-word response streaming.


📁 Project Structure

KG_RAG/
├── RAG.py           # Offline web scraper, Neo4j graph builder, and DeepEval test suite
├── backend.py       # FastAPI server integrating NeMo Guardrails, LangChain, and Neo4j
├── frontend.py      # Bilingual Streamlit web interface with custom green styling
├── .env             # Environment variables (API keys and database credentials)
└── README.md        # Project documentation


⚙️ Prerequisites & Installation

Clone or navigate to your project directory:

cd C:\Development\KG_RAG


Create and activate a Python virtual environment:

python -m venv venv
venv\Scripts\activate


Install required dependencies:

python -m pip install fastapi uvicorn streamlit requests beautifulsoup4 python-dotenv langchain langchain-core langchain-openai langchain-experimental langchain-neo4j langchain-text-splitters neo4j nemoguardrails deepeval


🔑 Environment Configuration (.env)

Create a .env file in the root folder (C:\Development\KG_RAG\.env) with your credentials:

OPENAI_API_KEY=your_openai_api_key_here

NEO4J_URI=neo4j+s://your-instance-id.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_neo4j_password_here

# Optional: LangSmith Tracing
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_langsmith_api_key_here
LANGCHAIN_PROJECT=TamilNadu-Agri-KG-RAG


🚀 Running the Application

Step 1: (Optional) Populate or Evaluate the Knowledge Graph

Your Neo4j AuraDB graph is already populated. If you ever need to re-scrape tn.gov.in or run DeepEval benchmarks:

Set BUILD_GRAPH = True inside RAG.py to rebuild the graph (set back to False afterward).

Run the evaluation suite:

python RAG.py


Step 2: Start the FastAPI Backend (Terminal 1)

cd C:\Development\KG_RAG
venv\Scripts\activate
python -m uvicorn backend:app --reload --port 8000


Verify the API is live at http://127.0.0.1:8000 (Interactive API docs available at http://127.0.0.1:8000/docs).

Step 3: Start the Streamlit Frontend (Terminal 2)

cd C:\Development\KG_RAG
venv\Scripts\activate
python -m streamlit run frontend.py


Your browser will open automatically at http://localhost:8501.

💬 Sample Queries to Test

English Mode

"What schemes are administered by the Farmers Welfare Department?"

"Which schemes or benefits mention subsidy or seed distribution?"

"What subsidies are available for patent registration or trademark registration?"

"Which schemes are connected to TNAU?"

Tamil Mode (Click தமிழ் in the UI)

"உழவர் நலத்துறையால் செயல்படுத்தப்படும் திட்டங்கள் என்னென்ன?"

"விதை விநியோகம் அல்லது மானியம் வழங்கும் திட்டங்கள் எவை?"

"காப்புரிமை மற்றும் வர்த்தக முத்திரை பதிவுக்கான மானியத் திட்டங்கள் பற்றி கூறுங்கள்."

Guardrail Verification (Off-Topic / Prompt Injection)

"Write a poem about cricket." → Blocked politely by NeMo Guardrails without querying Neo4j.

import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain_neo4j import Neo4jGraph, GraphCypherQAChain
from nemoguardrails import RailsConfig, LLMRails

load_dotenv(override=True)

app = FastAPI(title="Agri AI Assistant - Knowledge Graph RAG API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 1. LLM & Neo4j Graph Connection
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

uri = os.getenv("NEO4J_URI", "").replace("neo4j+s://", "neo4j+ssc://")
graph = Neo4jGraph(
    url=uri,
    username=os.getenv("NEO4J_USERNAME"),
    password=os.getenv("NEO4J_PASSWORD"),
    enhanced_schema=True,
)

# 2. Cypher & Grounded QA Prompts
CYPHER_PROMPT = PromptTemplate(
    input_variables=["schema", "question"],
    template="""Task: Generate a Cypher statement to query a Neo4j graph database.
Instructions:
- Use only the provided relationship types and properties in the schema.
- NEVER use exact string matching like `{{id: '...'}}`. ALWAYS use `WHERE toLower(n.id) CONTAINS toLower('...')`.
- Note: The agriculture department is stored in the graph as 'Farmers Welfare Department'.
- Always use undirected relationship patterns `-[r]-` when matching connected nodes so arrow direction never causes empty results.
- Do not include `:Document` nodes unless explicitly asked.

Schema:
{schema}

Examples:
Question: What schemes are administered by the Farmers Welfare Department?
Cypher: MATCH (s:Scheme)-[r]-(d:Department) WHERE toLower(d.id) CONTAINS 'farmers welfare' RETURN DISTINCT s.id AS Scheme, type(r) AS Relation, d.id AS Department

Question: Which schemes relate to subsidy or seed distribution?
Cypher: MATCH (n:__Entity__) WHERE NOT n:Document AND (toLower(n.id) CONTAINS 'subsidy' OR toLower(n.id) CONTAINS 'seed') RETURN DISTINCT n.id AS Name

Note: Return ONLY the Cypher statement with no markdown backticks or explanations.
The question is:
{question}""",
)

QA_PROMPT = PromptTemplate(
    input_variables=["context", "question"],
    template="""You are a factual assistant answering questions strictly from Neo4j Knowledge Graph query results.
Rules:
- Use ONLY the entities and values present in the Context below.
- Do NOT infer, extrapolate, or add claims not explicitly stated in the Context.
- If the Context is empty (`[]`), reply "I don't know based on the knowledge graph."

Context:
{context}

Question: {question}
Helpful Answer:""",
)

kg_chain = GraphCypherQAChain.from_llm(
    llm=llm,
    graph=graph,
    cypher_prompt=CYPHER_PROMPT,
    qa_prompt=QA_PROMPT,
    validate_cypher=False,
    return_intermediate_steps=True,
    allow_dangerous_requests=True,
)

# 3. NeMo Guardrails Setup
yaml_content = """
models:
  - type: main
    engine: openai
    model: gpt-4o-mini

rails:
  input:
    flows:
      - check allowed topic
"""

colang_content = """
define subflow check allowed topic
  $is_allowed = execute check_topic_allowed(user_message=$user_message)
  if not $is_allowed
    bot say "BLOCKED: I can only answer questions related to Tamil Nadu Government schemes, agriculture, and MSME benefits."
    stop

define flow
  user ...
  bot say "APPROVED"
"""

async def check_topic_allowed(user_message: str) -> bool:
    prompt = (
        "Is the following user message asking about Tamil Nadu government schemes, "
        "agriculture, farmers, subsidies, loans, MSMEs, or industries? "
        "Note: The message may be in English or Tamil. Reply ONLY 'YES' or 'NO'.\n\n"
        f"Message: {user_message}"
    )
    res = await llm.ainvoke(prompt)
    return "YES" in res.content.strip().upper()

rails_config = RailsConfig.from_content(
    colang_content=colang_content,
    yaml_content=yaml_content,
)
rails = LLMRails(rails_config)
rails.register_action(action=check_topic_allowed, name="check_topic_allowed")

# 4. API Request/Response Models
class ChatRequest(BaseModel):
    question: str
    language: str = "English"

class ChatResponse(BaseModel):
    answer: str
    context: list[str]
    blocked: bool = False

@app.get("/")
def health_check():
    return {"status": "Agri AI Assistant Backend is running"}

@app.post("/ask", response_model=ChatResponse)
async def ask_scheme(req: ChatRequest):
    try:
        # Step A: NeMo Input Guardrail check
        guard_res = await rails.generate_async(
            messages=[{"role": "user", "content": req.question}]
        )
        if guard_res["content"].startswith("BLOCKED:"):
            blocked_msg = guard_res["content"].replace("BLOCKED:", "").strip()
            if req.language == "Tamil":
                trans = await llm.ainvoke(
                    f"Translate this politely into natural Tamil:\n{blocked_msg}"
                )
                blocked_msg = trans.content.strip()
            return ChatResponse(answer=blocked_msg, context=[], blocked=True)

        # Step B: Translate Tamil question to English for Cypher generation if needed
        query_for_graph = req.question
        if req.language == "Tamil":
            en_q = await llm.ainvoke(
                f"Translate this Tamil question about government schemes into clear English:\n{req.question}"
            )
            query_for_graph = en_q.content.strip()

        # Step C: Query Neo4j Knowledge Graph
        kg_res = await kg_chain.ainvoke({"query": query_for_graph})
        raw_rows = kg_res["intermediate_steps"][1]["context"]
        context_list = [str(row) for row in raw_rows] if raw_rows else []
        final_answer = kg_res["result"]

        # Step D: Translate final grounded answer back to Tamil if requested
        if req.language == "Tamil":
            ta_ans = await llm.ainvoke(
                "Translate the following answer accurately into clear, formal Tamil. "
                "Keep scheme names clear and do not add extra facts:\n\n"
                f"{final_answer}"
            )
            final_answer = ta_ans.content.strip()

        return ChatResponse(answer=final_answer, context=context_list, blocked=False)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
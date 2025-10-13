import os
import streamlit as st
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.document_loaders import WikipediaLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain.tools import tool
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, START, END
from typing_extensions import TypedDict

os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

@st.cache_resource
def build_or_load_vector_store():
    """Builds the vector store if it doesn't exist, otherwise loads from disk."""
    faiss_index_path = "faiss_rag_index"
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    
    if os.path.exists(faiss_index_path):
        st.info("Loading existing vector store from disk...")
        # The 'allow_dangerous_deserialization=True' is needed for FAISS with langchain>=0.2.0
        vector_store = FAISS.load_local(faiss_index_path, embeddings, allow_dangerous_deserialization=True)
        st.info("Vector store loaded successfully!")
    else:
        st.info("No existing vector store found. Building a new one...")
        loader = WikipediaLoader(query="Retrieval-Augmented Generation", load_max_docs=5)
        docs = loader.load()
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        splits = text_splitter.split_documents(docs)
        
        st.info("Creating embeddings and building FAISS index... (This may take a minute the first time)")
        vector_store = FAISS.from_documents(splits, embeddings)
        vector_store.save_local(faiss_index_path)
        st.info("Vector store built and saved to disk!")
        
    return vector_store

vector_store = build_or_load_vector_store()
retriever = vector_store.as_retriever()

@tool
def rag_retrieve(query: str) -> dict:
    """Retrieve relevant context from Wikipedia using RAG. Returns context and sources."""
    docs = retriever.invoke(query)
    context = "\n\n".join(doc.page_content for doc in docs)
    sources = [doc.metadata.get('source', 'Unknown') for doc in docs]
    return {"context": context, "sources": sources}

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.5)

class AgentState(TypedDict):
    query: str
    context: str
    sources: list
    answer: str

def router_agent(state: AgentState):
    prompt = f"Query: {state['query']}. Does this need Wikipedia retrieval for facts? Respond with 'retrieve' or 'generate'."
    decision = llm.invoke(prompt).content.strip().lower()
    return {"context": decision}

def retriever_agent(state: AgentState):
    if "retrieve" in state["context"]:
        result = rag_retrieve.invoke(state["query"])
        return {"context": result["context"], "sources": result["sources"]}
    return state

def generator_agent(state: AgentState):
    template = """You are a helpful ML expert chatbot. Answer naturally using this context: {context}\nQuestion: {query}\nBe engaging and concise."""
    prompt = ChatPromptTemplate.from_template(template)
    chain = prompt | llm
    response = chain.invoke({"query": state["query"], "context": state["context"]})
    return {"answer": response.content}

workflow = StateGraph(AgentState)
workflow.add_node("router", router_agent)
workflow.add_node("retriever", retriever_agent)
workflow.add_node("generator", generator_agent)
workflow.add_edge(START, "router")
workflow.add_edge("router", "retriever")
workflow.add_edge("retriever", "generator")
workflow.add_edge("generator", END)
app_graph = workflow.compile()

st.title("Trending ML Q&A Chatbot (RAG + Agents)")
st.subheader("Ask about ML topics like RAG or LLMs!")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

query = st.chat_input("Your question (e.g., 'Explain RAG in LLMs')")

if query:
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)
    
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            result = app_graph.invoke({"query": query})
            st.markdown(result["answer"])
            if result.get("sources"):
                st.markdown("**Sources:** " + ", ".join(set(result["sources"])))
    
    st.session_state.messages.append({"role": "assistant", "content": result["answer"]})

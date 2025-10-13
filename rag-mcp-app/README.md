# RAG + Multi-Agent (MCP) Chatbot for ML Topics

This is a demonstration-ready Streamlit application that functions as an intelligent Q&A chatbot specializing in Machine Learning topics. It leverages a Retrieval-Augmented Generation (RAG) pipeline with a LangGraph multi-agent workflow to provide accurate, sourced answers.

**Live Demo URL:** [Link to your deployed Streamlit app will go here later]

---

## 🤖 Demo

[It's highly recommended to add a GIF of your app working here. You can use a free tool like Giphy Capture (macOS) or Kap to record your screen and convert it to a GIF.]

![Demo GIF](link_to_your_gif_here.gif)

---

## ✨ Features

* **Conversational AI:** Maintains chat history for follow-up questions.
* **Retrieval-Augmented Generation (RAG):** Answers are grounded in a knowledge base built from Wikipedia articles to reduce hallucinations.
* **Source Citation:** Displays the source documents used to generate an answer, building user trust.
* **Agentic Workflow:** Uses a LangGraph router to decide whether to fetch from the knowledge base or use the LLM's general knowledge.
* **Interactive UI:** Built with Streamlit for a clean, user-friendly chat interface.

---

## 🚀 How to Run Locally

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/](https://github.com/)[your-github-username]/rag-mcp-chatbot.git
    cd rag-mcp-chatbot
    ```
2.  **Create and activate the Conda environment:**
    ```bash
    conda create -n rag-mcp-app python=3.10 -y
    conda activate rag-mcp-app
    ```
3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    conda install -c conda-forge faiss-cpu -y
    ```
4.  **Set your OpenAI API Key:**
    ```bash
    export OPENAI_API_KEY="sk-your-key-here"
    ```
5.  **Run the Streamlit app:**
    ```bash
    streamlit run app.py
    ```

---

## 🛠️ Technologies Used

* **Framework:** Streamlit
* **LLM Orchestration:** LangChain, LangGraph
* **LLM:** OpenAI GPT-4o-mini
* **Vector Database:** FAISS (in-memory)
* **Data Source:** Wikipedia

---

Created by Tanishq Sharma.

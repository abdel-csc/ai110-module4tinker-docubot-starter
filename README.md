# DocuBot

DocuBot is a small documentation assistant that helps answer developer questions about a codebase.  
It can operate in three different modes:

1. **Naive LLM mode**  
   Sends the entire documentation corpus to a Gemini model and asks it to answer the question.

2. **Retrieval only mode**  
   Uses a simple indexing and scoring system to retrieve relevant snippets without calling an LLM.

3. **RAG mode (Retrieval Augmented Generation)**  
   Retrieves relevant snippets, then asks Gemini to answer using only those snippets.

The docs folder contains realistic developer documents (API reference, authentication notes, database notes), but these files are **just text**. They support retrieval experiments and do not require students to set up any backend systems.

---

## Setup

### 1. Install Python dependencies

    pip install -r requirements.txt

### 2. Configure environment variables

Copy the example file:

    cp .env.example .env

Then edit `.env` to include your Gemini API key:

    GEMINI_API_KEY=your_api_key_here

If you do not set a Gemini key, you can still run retrieval only mode.

---

## Running DocuBot

Start the program:

    python main.py

Choose a mode:

- **1**: Naive LLM (Gemini reads the full docs)  
- **2**: Retrieval only (no LLM)  
- **3**: RAG (retrieval + Gemini)

You can use built in sample queries or type your own.

---

## Running Retrieval Evaluation (optional)

    python evaluation.py

This prints simple retrieval hit rates for sample queries.

---

## Modifying the Project

You will primarily work in:

- `docubot.py`  
  Implement or improve the retrieval index, scoring, and snippet selection.

- `llm_client.py`  
  Adjust the prompts and behavior of LLM responses.

- `dataset.py`  
  Add or change sample queries for testing.

---

## Requirements

- Python 3.9+
- A Gemini API key for LLM features (only needed for modes 1 and 3)
- No database, no server setup, no external services besides LLM calls

## TF SUMMARY:
 The core concept students needed to understand is that a language model has no knowledge of your specific codebase unless you give it that information directly. RAG solves this by retrieving relevant documentation first and grounding the model's response in only that content, which is why Mode 3 gave short, accurate, project-specific answers while Mode 1 gave long, confident, generic ones.

 Students most commonly struggled with the retrieval methods, specifically build_index, score_document, and retrieve, because the logic feels too simple to actually work. Counting word matches does not feel like "AI," so students tend to overthink it or wait for Copilot to generate something more complex than what is needed.

 AI tools were helpful for explaining unfamiliar Python patterns and suggesting the punctuation stripping fix when scoring returned '0'. They were misleading when students used them to generate the retrieve function without understanding it, since the generated code sometimes returned whole documents instead of ranked results, which looked correct but buried the actual answers. Students should know *what* to look for, so that they do not fall in an endless spiral or loop of what they have to do or what they're going to do. 

 To guide a struggling student without giving the answer, I would ask: "If you had to search these files yourself with ctrl+f, what word would you type?". Questions like these probe the mind of an individual to really think about their next steps.

 We often hold AI as a 'being' that's smarter than most, but honestly, it's only as smart as *you* make it. This project really shows us behind-the-scenes across these powerful words of 'AI' and 'LLMs'.


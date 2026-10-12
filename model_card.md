# DocuBot Model Card

This model card is a short reflection on your DocuBot system. Fill it out after you have implemented retrieval and experimented with all three modes:

1. Naive LLM over full docs  
2. Retrieval only  
3. RAG (retrieval plus LLM)

Use clear, honest descriptions. It is fine if your system is imperfect.

---

## 1. System Overview

**What is DocuBot trying to do?**  
Describe the overall goal in 2 to 3 sentences.

> DocuBot is a documentation assistant that answers developer questions about a software project. Instead of relying on general knowledge, it reads actual project documentation files and uses them to generate accurate answers. It really shows you the different instances of knowledge a system can have.

**What inputs does DocuBot take?**  
For example: user question, docs in folder, environment variables.

> A user question typed into the terminal, markdown and text files loaded from the docs/ folder, and an optional Gemini API key for LLM-powered modes. I recommend the latter as there's more... flexibility when it comes to answers.

**What outputs does DocuBot produce?**

> Either raw document snippets (retrieval only mode) or a short generated answer grounded in those snippets (RAG mode), or a general LLM response with no grounding (naive mode).

---

## 2. Retrieval Design

**How does your retrieval system work?**  
Describe your choices for indexing and scoring.

- How do you turn documents into an index?
- How do you score relevance for a query?
- How do you choose top snippets?

> Each document in docs/ is split into sections at every markdown heading, so each chunk is one labeled section (for example, "### GET /api/users" plus its text). An inverted index maps each word to the files it appears in. For a query, DocuBot drops filler words (like "is", "the", "where"), strips punctuation, uses the index to find candidate files, and scores each section by how many meaningful query words it contains. A short prefix match lets "connect" match "connection". Sections below the minimum score are thrown out, and the top 3 remaining sections are returned.

**What tradeoffs did you make?**  
For example: speed vs precision, simplicity vs accuracy.

> The scoring is simple and fast but imprecise. Splitting by heading made snippets much more focused than returning whole files, but it can also cut related content apart (a "## Tables" heading ends up in a different chunk than the "### users" table under it). Exact word matching still misses different wording, like "stored" vs "Stores". After chunking and the guardrail, the retrieval hit rate in evaluation.py went from 0.88 to 0.75, because whole documents were easier to "hit" but harder to read. Jason mentions how its really just up to the situation and context at hand you want to work with. I want to say there is a balance necessary but even then honestly would not be the *right* answer.

---

## 3. Use of the LLM (Gemini)

**When does DocuBot call the LLM and when does it not?**  

- Naive LLM mode: calls the LLM with the entire docs corpus and no retrieval. The model answers from general knowledge and ignores the docs.
- Retrieval only mode: no LLM is called at all. Raw document text is returned directly.
- RAG mode: retrieval runs first, then the LLM is called with only the retrieved snippets and told to answer using only that content.

**What instructions do you give the LLM to keep it grounded?**  
Summarize the rules from your prompt. For example: only use snippets, say "I do not know" when needed, cite files.

> The LLM is instructed to answer only using the provided snippets, cite the source files it used, and say "I do not know based on these docs" if the snippets do not contain enough information. These checks allows one to "reassess" the given data. It really gives you an open door to how much data working models need.

---

## 4. Experiments and Comparisons

Run the **same set of queries** in all three modes. Fill in the table with short notes.

You can reuse or adapt the queries from `dataset.py`.

| Query | Naive LLM: helpful or harmful? | Retrieval only: helpful or harmful? | RAG: helpful or harmful? | Notes |
|------|---------------------------------|--------------------------------------|---------------------------|-------|
| **Where is the auth token generated?** | Harmful - gave generic JWT explanation, never mentioned auth_utils.py | Helpful - returned AUTH.md which had the answer, but buried in full doc | Helpful - directly said generate_access_token in auth_utils.py | RAG was most precise. I really think this is a necessity question for introductory students. |
| **How do I connect to the database?** | Harmful - gave PostgreSQL/MySQL/MongoDB examples with no relation to this project | Helpful - returned DATABASE.md and SETUP.md with correct info | Helpful - gave exact DATABASE_URL instructions with correct examples | RAG gave the cleanest answer. Overall, naive mode is something I would avoid, especially on a company computer. |
| **Which endpoint lists all users?** | Harmful - said GET /users generically, didn't know it was GET /api/users | Helpful - API_REFERENCE.md was retrieved, answer was in there | Helpful - said GET /api/users, admins only, cited API_REFERENCE.md | RAG got the exact endpoint right |
| **How does a client refresh an access token?** | Harmful - gave a long generic OAuth explanation about refresh token rotation and confidential clients, none of which applies to this project | Helpful - returned AUTH.md and API_REFERENCE.md which both had the answer | Helpful - said POST /api/refresh with Bearer token header, cited AUTH.md and API_REFERENCE.md | RAG handled multi-file answers well |

**What patterns did you notice?**  

- When does naive LLM look impressive but untrustworthy?  
- When is retrieval only clearly better?  
- When is RAG clearly better than both?

> Naive LLM sounds confident but answers as if this is a generic codebase, not this specific project. Retrieval only pulls the right files but returns too much text, making it hard to extract the actual answer. RAG consistently gave the shortest, most accurate, most grounded responses. It all goes back to this idea of tradeoffs and what you're trying to achieve. As mentioned in Jason's lecture.

---

## 5. Failure Cases and Guardrails

**Describe at least two concrete failure cases you observed.**  
For each one, say:

- What was the question?  
- What did the system do?  
- What should have happened instead?

> Question: "Where is the auth token generated?" asked in naive mode. The system gave a long answer about JWT signing and Node.js code examples. It never mentioned generate_access_token or auth_utils.py, which is the actual answer in the docs. It should have said it does not have access to the specific codebase.

> Question: "Where is the auth token generated?" asked in retrieval only mode before the punctuation fix. The system said "I do not know based on these docs" even though AUTH.md clearly contained the answer. The word matching failed because punctuation was attached to words like "generation," so the scoring returned 0.

> RAG failure: "Which fields are stored in the users table?" The answer is in DATABASE.md (user_id, email, password_hash, joined_at), but RAG mode answers "I do not know based on these docs." Chunking split the "## Tables" heading away from the "### users" section, so "table" and "users" land in different chunks. The other query words, "stored" and "fields", don't exactly match "Stores" and "Column". Every section scores only 1, which is below the guardrail threshold. Retrieval never passes the right snippet to the LLM, so even a strong model can't answer. RAG is only as good as its retrieval.

**When should DocuBot say "I do not know based on the docs I have"?**  

> When no section matches at least 2 meaningful (non-filler) words from the question. In practice, that covers questions outside the scope of the docs, like "Is there any mention of payment processing in these docs?" or "What is the weather today?", which now both return a refusal instead of unrelated docs.

**What guardrails did you implement?**  

> A minimum score threshold (MIN_SCORE = 2 in docubot.py): a section must match at least 2 meaningful query words to count as evidence. Filler words are removed first, because before this fix words like "is" and "these" matched every doc and the refusal never triggered. If no section passes, both answer_retrieval_only and answer_rag return "I do not know based on these docs" without calling the LLM. Punctuation stripping prevents false zero scores from attached punctuation.

---

## 6. Limitations and Future Improvements

**Current limitations**  

1. Heading-based chunks can split related content apart, and some sections (like the API endpoints) are still long, so snippets are not always as tight as a single paragraph.
2. Word matching is exact (plus a simple prefix match), so synonyms or different phrasings of the same question will fail to retrieve the right docs.
3. Every meaningful word counts the same, so a rare, important word like "refresh" has no more weight than a common one like "token".

**Future improvements**  

1. Attach parent headings to sub-sections (for example, include "Tables" in the "users" chunk) so related context isn't lost when splitting.
2. Use TF-IDF or semantic embeddings instead of raw word counts for more accurate relevance scoring.
3. Tune the confidence threshold against more test questions, since MIN_SCORE = 2 refuses some questions the docs can actually answer.

---

## 7. Responsible Use

**Where could this system cause real world harm if used carelessly?**  

> In naive mode, the LLM can generate plausible-sounding but completely wrong answers about security configurations, authentication flows, or database connection strings. A developer who trusts those answers and uses them in production could introduce security vulnerabilities or data loss. And honestly, it does not even have to be a developer. An individual, likely *older* may fall victim to a confident falsehood that may negatively influence their real-world decision(s).

**What instructions would you give real developers who want to use DocuBot safely?**  

- Always use RAG mode, not naive LLM mode, when answering questions about a specific codebase.
- Do not use DocuBot as a substitute for reading the docs when the stakes are high.
- Keep the docs folder up to date, since DocuBot can only be as accurate as the documentation it reads.

Most of all, never be afraid to ask for help or guidance for peer when attempting to use AI tools like Docubot responsibly.

---

"""
Core DocuBot class responsible for:
- Loading documents from the docs/ folder
- Building a simple retrieval index (Phase 1)
- Retrieving relevant snippets (Phase 1)
- Supporting retrieval only answers
- Supporting RAG answers when paired with Gemini (Phase 2)
"""

import os
import glob
import string

# Common filler words that match almost every doc and inflate scores.
STOPWORDS = {
    "a", "an", "and", "are", "any", "do", "does", "for", "how", "i",
    "in", "is", "it", "of", "on", "or", "the", "there", "these", "this",
    "to", "what", "where", "which", "who", "why", "with",
}

# Guardrail: a snippet must match at least this many meaningful query
# words, otherwise DocuBot refuses instead of guessing.
MIN_SCORE = 2


def tokenize(text):
    """Lowercase, turn punctuation into spaces, and split into words."""
    text = text.lower()
    for char in string.punctuation:
        text = text.replace(char, " ")
    return text.split()


class DocuBot:
    def __init__(self, docs_folder="docs", llm_client=None):
        """
        docs_folder: directory containing project documentation files
        llm_client: optional Gemini client for LLM based answers
        """
        self.docs_folder = docs_folder
        self.llm_client = llm_client

        # Load documents into memory
        self.documents = self.load_documents()  # List of (filename, text)

        # Split documents into heading-based sections (Part 3)
        self.chunks = self.chunk_documents(self.documents)  # List of (filename, section)

        # Build a retrieval index (implemented in Phase 1)
        self.index = self.build_index(self.documents)

    def load_documents(self):
        """
        Loads all .md and .txt files inside docs_folder.
        Returns a list of tuples: (filename, text)
        """
        docs = []
        pattern = os.path.join(self.docs_folder, "*.*")
        for path in glob.glob(pattern):
            if path.endswith(".md") or path.endswith(".txt"):
                with open(path, "r", encoding="utf8") as f:
                    text = f.read()
                filename = os.path.basename(path)
                docs.append((filename, text))
        return docs

    def chunk_documents(self, documents):
        """
        Split each document into sections, starting a new chunk at every
        markdown heading (a line starting with "#"). Each chunk keeps its
        heading, so retrieval returns a focused, labeled snippet instead of
        a whole file. Returns a list of (filename, section_text).
        """
        chunks = []
        for filename, text in documents:
            current = []
            for line in text.splitlines():
                if line.startswith("#") and current:
                    chunks.append((filename, "\n".join(current).strip()))
                    current = []
                current.append(line)
            if current:
                chunks.append((filename, "\n".join(current).strip()))
        return [(f, c) for f, c in chunks if c]

    def build_index(self, documents):
        """
        Build a tiny inverted index mapping lowercase words to the documents
        they appear in.
        """
        index = {}
        for filename, text in documents:
            for word in tokenize(text):
                if word not in index:
                    index[word] = []
                if filename not in index[word]:
                    index[word].append(filename)
        return index

    def score_document(self, query, text):
        """
        Return a relevance score: how many meaningful (non-filler)
        query words appear in the text.
        """
        query_words = {w for w in tokenize(query) if w not in STOPWORDS}
        text_words = set(tokenize(text))
        score = 0
        for word in query_words:
            # Exact match, or a simple prefix match so "connect" also
            # matches "connection" (only for words of 4+ letters)
            if word in text_words or (
                len(word) >= 4 and any(t.startswith(word) for t in text_words)
            ):
                score += 1
        return score

    def retrieve(self, query, top_k=3):
        """
        Use the index and scoring function to select top_k relevant sections.
        Return a list of (filename, text) sorted by score descending.
        """
        # Use the index to find which files contain any meaningful query word
        candidate_files = set()
        for word in tokenize(query):
            if word not in STOPWORDS:
                candidate_files.update(self.index.get(word, []))

        # Score each section in those files
        results = []
        for filename, chunk in self.chunks:
            if filename not in candidate_files:
                continue
            score = self.score_document(query, chunk)
            if score >= MIN_SCORE:  # guardrail: skip weak matches
                results.append((score, filename, chunk))

        # Highest score first; ties broken alphabetically by filename
        results.sort(key=lambda r: (-r[0], r[1]))
        return [(filename, chunk) for score, filename, chunk in results[:top_k]]

    def answer_retrieval_only(self, query, top_k=3):
        """
        Phase 1 retrieval only mode.
        Returns raw snippets and filenames with no LLM involved.
        """
        snippets = self.retrieve(query, top_k=top_k)

        if not snippets:
            return "I do not know based on these docs."

        formatted = []
        for filename, text in snippets:
            formatted.append(f"[{filename}]\n{text}\n")

        return "\n---\n".join(formatted)

    def answer_rag(self, query, top_k=3):
        """
        Phase 2 RAG mode.
        Uses student retrieval to select snippets, then asks Gemini
        to generate an answer using only those snippets.
        """
        if self.llm_client is None:
            raise RuntimeError(
                "RAG mode requires an LLM client. Provide a GeminiClient instance."
            )

        snippets = self.retrieve(query, top_k=top_k)

        if not snippets:
            return "I do not know based on these docs."

        return self.llm_client.answer_from_snippets(query, snippets)

    def full_corpus_text(self):
        """
        Returns all documents concatenated into a single string.
        This is used in Phase 0 for naive 'generation only' baselines.
        """
        return "\n\n".join(text for _, text in self.documents)

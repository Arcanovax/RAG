*This project has been created as part of the 42 curriculum by [mthetcha].*

# RAG

## Description
This repository implements a Retrieval-Augmented Generation (RAG) pipeline for mixed code and documentation datasets. It ingests a corpus, segments it into chunks, builds lexical and optional semantic indices, retrieves the most relevant chunks for a query, and optionally generates concise answers using a local LLM server.

## System Architecture
1. **Chunking**: Reads files from the knowledge folder, splits them into overlapping chunks, and stores chunk metadata (file path and character offsets).
2. **Indexing**: Builds a BM25 index over enriched chunk text. For documentation-only datasets, it also builds a Chroma vector collection.
3. **Retrieval**: Uses BM25 for lexical retrieval. Optional hybrid retrieval adds Chroma semantic results and/or query expansion, then fuses rankings with a weighted reciprocal-rank scheme.
4. **Answering**: Formats retrieved chunks as context and queries a local OpenAI-compatible LLM endpoint (VLLM) via DSPy.
5. **Evaluation**: Computes recall@k against labeled questions/answers.

## Chunking Strategy
- Uses LangChain `RecursiveCharacterTextSplitter` with a **20% overlap**.
- Splits are **type-aware**:
	- Python files use a Python-aware splitter.
	- Markdown files use a Markdown-aware splitter.
	- Text files use a generic splitter.
- Each chunk stores `file_path`, `first_character_index`, and `last_character_index` so retrieval can be traced back to exact regions.

## Retrieval Method
- **Primary retriever**: BM25 (`bm25s`) with $k_1=1.7$.
- **Optional hybrid** (docs-only): Chroma semantic search; top results are merged with BM25 using weighted reciprocal-rank fusion.
- **Optional query expansion**: spaCy (`en_core_web_lg`) expands the query; expanded results are fused as an additional ranked list.
- **Fusion scoring**: For each ranked list, each document gets a score of
	$$\text{score} = w \cdot \frac{1}{k + r + 1}$$
	where $w$ is the list weight and $r$ is the rank. Lists are weighted as:
	- BM25: 1.15
	- Chroma: 0.85
	- Expanded query BM25: 1.10

## Performance Analysis
The evaluator computes **recall@k** for $k \in \{1, 3, 5, 10\}$ (up to the configured max $k$). A retrieved chunk is considered correct if it overlaps at least 5% of the gold source span.

Use the evaluation command below to generate actual scores for your dataset. Results depend on dataset type (code/docs/all), $k$, and whether hybrid/expansion are enabled.

## Design Decisions
- **BM25-first** for speed and reproducibility; semantic search is optional and only for documentation datasets.
- **Type-aware splitting** to better preserve structure in code and markdown.
- **Character-offset metadata** to enable precise overlap-based scoring.
- **DSPy + VLLM** to keep the answering step modular and replaceable.
- **Incremental JSON outputs** to support long-running dataset searches.

## Challenges Faced
- **Retrieval quality tuning**: Iterated on $k$ selection and ranking fusion to improve recall.
- **Performance optimization**: Added caching and progressive file writing to reduce memory overhead.
- **LLM serving**: Encountered issues running VLLM; resolved by using an external VLLM folder and CPU-compatible fixes.

## Instructions
### Requirements
- Python >= 3.10
- A running OpenAI-compatible LLM endpoint (VLLM expected at http://localhost:8000/v1)

### Installation
```bash
pip install -e .
```

### Index the corpus
```bash
python -m student index --max_chunk_size 2000 --dataset_type all
```

### Search for relevant chunks
```bash
python -m student search --query "How does the retriever fuse rankings?" --k 10
```

### Answer a single question
```bash
python -m student answer --query "What is the chunk overlap?" --k 10
```

### Batch search (dataset)
```bash
python -m student search_dataset --dataset_path data/datasets/UnansweredQuestions/dataset_docs_public.json --k 10
```

### Batch answer (dataset)
```bash
python -m student answer_dataset --student_search_results_path data/output/search_results/dataset_docs_public.json
```

### Evaluate recall@k
```bash
python -m student evaluate --path_result data/output/search_results/dataset_docs_public.json --path_answered_questions data/datasets/AnsweredQuestions/dataset_docs_public.json
```

## Example Usage
- **Index docs-only with hybrid search**:
	```bash
	python -m student index --max_chunk_size 2000 --dataset_type docs
	python -m student search --query "Explain chunk metadata" --k 10 --hybrid true
	```
- **Expanded query retrieval**:
	```bash
	python -m student search --query "What is BM25 used for?" --k 10 --expand true
	```

## Resources
- DSPy tutorial: https://miptgirl.medium.com/programming-not-prompting-a-hands-on-guide-to-dspy-04ea2d966e6d
- LangChain Text Splitters: https://reference.langchain.com/python/langchain-text-splitters/base/TextSplitter
- Chunking strategies overview: https://www.geeksforgeeks.org/artificial-intelligence/chunking-strategies/
- Ollama OpenAI compatibility: https://docs.ollama.com/api/openai-compatibility
- Ollama releases: https://github.com/ollama/ollama/releases
- RAG architecture article: https://rajivshah.com/blog/rag-agentic-world.html

### AI Usage
AI tools were used to:
- Summarize and cross-check documentation for DSPy, LangChain splitters, and RAG best practices.
- Draft initial README wording and structure, then refined to match the implementation in this repository.
- Sanity-check CLI examples against the `student` Fire-based interface.

No AI-generated code was directly inserted into the core pipeline without manual review and alignment to project requirements.

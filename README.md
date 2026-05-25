*This project has been created as part of the 42 curriculum by [mthetcha].*

# RAG

## Description
This project implements a Retrieval-Augmented Generation (RAG) pipeline for mixed code and documentation datasets. It ingests a corpus, segments it into chunks, builds lexical and optional semantic indices, retrieves the most relevant chunks for a query, and optionally generates concise answers using a local LLM server.

## System Architecture
1. **Chunking**: Reads files from the knowledge folder, splits them into overlapping chunks, and stores chunk metadata (file path and character offsets).
2. **Indexing**: Builds a BM25 index over enriched chunk text. For documentation-only datasets, it also builds a Chroma vector collection.
3. **Retrieval**: Uses BM25 for lexical retrieval. Optional flag add hybrid retrieval with Chroma semantic results and a query expansion with spacy, then fuses rankings with a weighted reciprocal-rank scheme.
4. **Answering**: Formats retrieved chunks as context and queries a Qwen3-0.6B via DSPy.
5. **Evaluation**: Computes recall@k against labeled questions/answers.

## Chunking Strategy
- Uses LangChain `RecursiveCharacterTextSplitter` with a **20% overlap**.
- Splits are **type-aware**:
	- Python files use a Python splitter.
	- Markdown files use a Markdown splitter.
	- Text files use a generic splitter.
- Each chunk stores `file_path`, `content`, `first_character_index`, and `last_character_index` so retrieval can be traced back to exact regions.

## Retrieval Method
- **Primary retriever**: BM25 (`bm25s`) with $k_1=1.7$.
- **Optional hybrid** (docs-only): Chroma semantic search, top results are merged with BM25 using weighted reciprocal-rank fusion.
- **Optional query expansion**: spaCy (`en_core_web_lg`) expands the query, expanded results are fused as an additional ranked list.
- **Fusion scoring**: For each ranked list, each document gets a score of
	$$\text{score} = w \cdot \frac{1}{k + r + 1}$$
	where $w$ is the list weight and $r$ is the rank. Lists are weighted as:
	- BM25: 1.15
	- Chroma: 0.85
	- Expanded query BM25: 1.10

## Performance Analysis
*Chunk size: 1400*

#### Index all:

Docs: `{'recall@1': 0.64, 'recall@3': 0.78, 'recall@5': 0.8, 'recall@10': 0.84}`

Docs --expand: `{'recall@1': 0.66, 'recall@3': 0.79, 'recall@5': 0.83, 'recall@10': 0.88}`

Code: `{'recall@1': 0.48, 'recall@3': 0.61, 'recall@5': 0.67, 'recall@10': 0.79}`

Code --expand: `{'recall@1': 0.52, 'recall@3': 0.65, 'recall@5': 0.71, 'recall@10': 0.85}`


#### Index Docs:

`{'recall@1': 0.7, 'recall@3': 0.87, 'recall@5': 0.94, 'recall@10': 0.96}`

--expand: `{'recall@1': 0.72, 'recall@3': 0.89, 'recall@5': 0.94, 'recall@10': 0.96}`

--hybrid: `{'recall@1': 0.66, 'recall@3': 0.87, 'recall@5': 0.93, 'recall@10': 0.96}`

--expand --hybrid: `{'recall@1': 0.74, 'recall@3': 0.88, 'recall@5': 0.94, 'recall@10': 0.96}`


We can see that flags drastically improve the results, it is also important to note that to increase recall@k, you need to index in specific mode.

*Note: These questions are from the `public` dataset.*

## Design Decisions
- **BM25-first** for speed and reproducibility; semantic search is optional and only for documentation datasets. Expand query is also optional because it take some time.
- **Type splitting** to better preserve structure in code and markdown.
- **DSPy + VLLM** to keep the answering safe, modular and replaceable.
- **Incremental JSON outputs** to support long-running dataset searches.

## Challenges Faced
- **Retrieval quality tuning**: Combine the results of multiple retrivers
- **Performance optimization**: Added caching and progressive file writing to reduce memory overhead.
- **VLLM serve**: Encountered issues running VLLM; resolved by using an external VLLM folder and CPU-compatible fixes.
- **LLM response time**: The LMM should respond the fastest, but on a CPU it's still slow

## Instructions
### Requirements
- Python >= 3.10


### Installation
```bash
make install
```

### Index the corpus
```bash
uv run python -m src index --max_chunk_size 1400 --dataset_type all
```

### Search for relevant chunks
```bash
uv run python -m src search --query "What hardware platforms does vLLM support?" --k 10
```

### Answer a single question
```bash
uv run python -m src answer --query "What hardware platforms does vLLM support?" --k 10
```

### Batch search (dataset)
```bash
uv run python -m src search_dataset --dataset_path data/datasets/UnansweredQuestions/dataset_docs_public.json --k 10
```

### Batch answer (dataset)
```bash
uv run python -m src answer_dataset --student_search_results_path data/output/search_results/dataset_docs_public.json
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

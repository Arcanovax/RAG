"""Answer generation utilities using DSPy and VLLM."""

import dspy
from .utils.model import (
    MinimalSource)
from .chunking import get_chunks
from typing import List


class RAG_sign(dspy.Signature):
    """Answer the question using only the provided sources."""
    context: str = dspy.InputField(
        desc="Numbered source chunks, most relevant first"
    )
    question: str = dspy.InputField()
    answer: str = dspy.OutputField(
        desc="answer ONLY. one or two sentences. Mention the original source. No markdown, No symbols."
    )


class Model():
    """Configure the LLM backend and DSPy predictor."""
    def __init__(self, model: str):
        """Initialize the LLM client and predictor."""
        self.lm = dspy.LM(
                    model=model,
                    api_base="http://localhost:8000/v1",
                    api_key="EMPTY",
                    max_tokens=256,
                    temperature=0.1,
                    frequency_penalty=0.3,
                    extra_body={"chat_template_kwargs": {"enable_thinking": False}},
                )
        dspy.configure(lm=self.lm)
        self.predictor = dspy.Predict(RAG_sign)
        print("Model:", model)


class Answering():
    """Generate answers from retrieved context."""
    def __init__(self, model_name: str):
        """Initialize the answering pipeline."""
        self.model = Model(model_name)

    def answer_dataset(self, result, chunks_file):
        """Generate an answer for a dataset item."""
        chunks = get_chunks(chunks_file)
        try:
            retrieved_chunks = self.get_retrieved_chunks(
                result.retrieved_sources, chunks)
            self.query = result.question
            context = self.get_context(retrieved_chunks)
            result = self.model.predictor(context=context, question=self.query)
            response = result.answer
            response = response.replace("\n", "")
            response = response.replace("[[ ## completed ## ]]", "")
            return response
        except dspy.utils.exceptions.ContextWindowExceededError:
            raise ValueError("The k value is too high")
        except Exception:
            raise ValueError("Answering failed")

    def answer_query(self, selected_chunks, query):
        """Generate an answer for a single query."""
        try:
            context = self.get_context(selected_chunks)
            result = self.model.predictor(context=context, question=query)
            response = result.answer
            response = response.replace("\n", "")
            response = response.replace("[[ ## completed ## ]]", "")
            return response
        except dspy.utils.exceptions.ContextWindowExceededError:
            raise ValueError("The k value is too high")
        except Exception:
            raise ValueError("Answering failed")

    def get_context(self, chunks):
        """Build a context string from chunks."""
        context_parts = []
        for chunk in chunks:
            content = chunk.get("content", "").strip()
            context_parts.append(f"\n[[ ## SOURCE {chunk.get("file_path")} ## ]]\n{content}")
        return "\n".join(context_parts)

    def get_retrieved_chunks(self,
                             retrieved_sources: List[MinimalSource],
                             chunks):
        """Map retrieved sources to full chunk objects."""
        retrieved_chunks = []
        for source in retrieved_sources:
            for chunk in chunks:
                chunk_f_index = chunk.get("first_character_index")
                chunk_l_index = chunk.get("last_character_index")
                if ((chunk.get("file_path") == source.file_path) and
                    (chunk_f_index == source.first_character_index) and
                    (chunk_l_index == source.last_character_index
                     )):
                    retrieved_chunks.append(chunk)
        return retrieved_chunks

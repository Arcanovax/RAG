import dspy


class Signature(dspy.Signature):
    """Answer the question using only the provided sources.
    """

    context: str = dspy.InputField(
        desc="Numbered source chunks, most relevant first"
    )
    question: str = dspy.InputField()
    answer: str = dspy.OutputField(
        desc="answer ONLY. one or two sentences. No markdown, No symbols. No list. "
    )

class Answering():
    def __init__(self, chunks, query):
        self.chunks = chunks
        self.query = query
        self.lm = dspy.LM(
            model="openai/qwen3:0.6b",
            api_base="http://localhost:11434/v1",
            api_key="ollama_local",
            max_tokens=1024,
            temperature=0.1,
            frequency_penalty=0.3
        )
        dspy.configure(lm=self.lm)
        predictor = dspy.Predict(Signature)
        result = predictor(context=self.get_context(chunks), question=query)
        response = result.answer
        response = response.replace("```bash", "")
        response = response.replace("```", "")
        response = response.replace("\n", "")
        response = response.replace("***", "")
        dspy.inspect_history()
        self.answer = response

    def get_answer(self):
        return self.answer

    def get_context(self, chunks):
        context_parts = []
        for i, chunk in enumerate(chunks):
            content = chunk.get("content", "").strip()
            context_parts.append(f"\n[[ ## SOURCE {i+1} ## ]]\n{content}")
        return "\n".join(context_parts)

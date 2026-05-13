import dspy


class BasicQA(dspy.Signature):
    """DSPy signature for context-grounded question answering."""

    context = dspy.InputField()
    question = dspy.InputField()
    answer = dspy.OutputField(
        desc="No formatting."
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
            temperature=0.2,
            frequency_penalty=0.1
        )
        print(query)
        print()
        dspy.configure(lm=self.lm)
        predictor = dspy.Predict(BasicQA)
        result = predictor(context=str(self.chunks), question=query)
        dspy.inspect_history()
        self.answer = result.answer

    def get_answer(self):
        return self.answer

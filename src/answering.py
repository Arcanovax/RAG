import dspy


class Signature(dspy.Signature):
    """Answer the question using only the provided sources.
    """
    context: str = dspy.InputField(
        desc="Numbered source chunks, most relevant first"
    )
    question: str = dspy.InputField()
    answer: str = dspy.OutputField(
        desc="answer ONLY. one or two sentences. No markdown, No symbols."
    )


class Model():
    def __init__(self, model):
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
        self.predictor = dspy.Predict(Signature)
        print("Model:", model)


class Answering():
    def __init__(self, model: Model, chunks, query):
        try:
            self.chunks = chunks
            self.query = query
            result = model.predictor(context=self.get_context(chunks), question=query)
            response = result.answer
            response = response.replace("\n", "")
            response = response.replace("[[ ## completed ## ]]", "")
            self.answer = response
        except dspy.utils.exceptions.ContextWindowExceededError:
            raise ValueError("The k value is too high")
        except Exception:
            raise ValueError("Answering failed")

    def get_answer(self):
        return self.answer

    def get_context(self, chunks):
        context_parts = []
        for i, chunk in enumerate(chunks):
            content = chunk.get("content", "").strip()
            context_parts.append(f"\n[[ ## SOURCE {i+1} ## ]]\n{content}")
        return "\n".join(context_parts)

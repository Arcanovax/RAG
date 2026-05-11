import dspy




lm = dspy.LM(
        model="openai/qwen3:0.6b",
        api_base="http://localhost:11434/v1",
        api_key="ollama_local",
        max_tokens=1024,
        temperature=0.2,
        frequency_penalty=0.1
    )
dspy.configure(lm=lm)




chat_response = lm(messages=[{"role": "user", "content": "count from 1 to a million "}])
print(chat_response)

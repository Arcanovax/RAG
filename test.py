

with (open("result.json")) as f:
    data = f.read()
    dict = json.loads(data)

search_results = dict.get("search_results")


rag_map = {r["question_id"]: r for r in rag_questions}
valid = 0
for s in search_results:
    qid = s["question_id"]
    r = rag_map.get(qid)

    if not r:
        print(f"[ABSENT] {qid[:8]}... — absent dans rag_questions")
        continue

    s_paths = [src["file_path"] for src in s["retrieved_sources"]]
    r_paths = [src["file_path"] for src in r["sources"]]

    match = s_paths == r_paths
    status = "✅ MATCH" if match else f"❌ {s_paths} {r_paths}"
    print(f"{status}")
    if match:
        valid += 1
print(valid)

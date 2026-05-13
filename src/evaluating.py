import json
from .utils.model import StudentSearchResults, RagDataset, MinimalSource

class Evaluating:
    def __init__(self, path_result, path_answered_questions):
        self.results: StudentSearchResults = self.get_result(path_result)
        self.answered_questions: RagDataset = self.get_answered_questions(path_answered_questions)
        print(f"Total number of questions: {len(self.answered_questions.rag_questions)}")
        print(f"Total number of questions with sources: {sum(1 for question in self.answered_questions.rag_questions if len(question.sources) > 0)}")
        print(f"Total number of questions with students sources: {sum(1 for question in self.results.search_results if len(question.retrieved_sources) > 0)}")
        scores = self.evaluate()
        for recal, score in scores.items():
            print(f"{recal}: {score} ({score*100}%)")

    def get_result(self, path_result):
        try:
            with (open(path_result, "r")as file):
                data = file.read()
                return StudentSearchResults(**json.loads(data))
        except Exception:
            raise (ValueError(f"Cannot read {path_result}"))

    def get_answered_questions(self, path_answered_questions):
        try:
            with (open(path_answered_questions, "r")as file):
                data = file.read()
                return RagDataset(**json.loads(data))
        except Exception:
            raise (ValueError(f"Cannot read {path_answered_questions}"))

    def evaluate(self):
        max_k = self.results.k
        k_list = [1, 3, 5, 10]
        scores = {}
        for k in k_list:
            if k > max_k:
                continue
            score = self.get_recall_score(k)
            scores.update({
                f"recall@{k}": score,
            })
        return scores

    def get_recall_score(self, k):
        score = 0
        results = self.results.search_results
        answers = self.answered_questions.rag_questions
        for i in range(len(self.results.search_results)):
            if self.is_matching(results[i], answers[i], k):
                score += 1
        return score/len(results)

    def is_matching(self, result, answer, k):
        if (result.question_id != answer.question_id or
           result.question != answer.question):
            return False
        for j in range(k):
            result_src = result.retrieved_sources[j]
            answer_src = answer.sources[0]
            if result_src.file_path != answer_src.file_path:
                continue
            if not self.is_matching_lines(result_src, answer_src):
                continue
            return True
        return False

    def is_matching_lines(self, result: MinimalSource, answer: MinimalSource):
        result_x = result.first_character_index
        result_y = result.last_character_index
        answer_x = answer.first_character_index
        answer_y = answer.last_character_index
        match = max(0, min(result_y, answer_y) - max(result_x, answer_x))
        result_size = result_y - result_x
        if result_size <= 0:
            return False
        overlap = match / result_size
        return overlap >= 0.05

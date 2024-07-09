import random

class Qlist:
    def __init__(self):
        self.questions = [
            {"question": "What is the meaning of life?"},
            {"question": "If you could have any superpower, what would it be?"},
            {"question": "What is your favorite book and why?"},
            # Add more questions as needed
        ]
        self.asked_questions = set()

    def get_random_question(self):
        available_questions = list(set(map(lambda q: q["question"], self.questions)) - self.asked_questions)
        if not available_questions:
            self.asked_questions.clear()
            available_questions = list(map(lambda q: q["question"], self.questions))
        question = random.choice(available_questions)
        self.asked_questions.add(question)
        return {"question": question}  # Return a dictionary

    def add_user_question(self, question):
        self.questions.append(question)

    def get_user_questions(self, user_id):
        return [q for q in self.questions if q.get("user_id") == user_id]

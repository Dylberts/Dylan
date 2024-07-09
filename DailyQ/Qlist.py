import random

class Qlist:
    def __init__(self):
        self.default_questions = [
            "If you could have any superpower, what would it be?",
            "What's the most memorable vacation you've ever taken?",
            "If you could meet any historical figure, who would it be and why?",
            "What's the most important lesson you've learned in the past year?",
            "If you could instantly become an expert in something, what would it be?",
            "What's your favorite way to spend a day off?",
            "If you could travel anywhere in the world, where would you go?",
            "What's your favorite book and why?",
            "What's one skill you wish you had?",
            "Who is your biggest inspiration?",
            "If you could switch lives with someone for a day, who would it be?",
            "What's your favorite movie or TV show?",
            "If you could live in any fictional world, which one would it be?",
            "What's the best piece of advice you've ever received?",
            "What's something you're really proud of?",
            "If you could have dinner with anyone, dead or alive, who would it be?",
            "What's your favorite hobby?",
            "What's a goal you have for the next year?",
            "If you could only eat one food for the rest of your life, what would it be?",
            "What's your favorite childhood memory?",
            "If you won the lottery, what's the first thing you would do?",
            "What's your favorite way to relax?",
            "What's the most adventurous thing you've ever done?",
            "If you could have any job in the world, what would it be?",
            "What's your favorite holiday and why?",
            "If you could change one thing about the world, what would it be?",
            "What's something you've always wanted to learn?",
            "What's the best gift you've ever received?",
            "If you could live anywhere in the world, where would it be?",
            "What's your favorite season and why?"
        ]
        self.asked_questions = set()
        self.user_submitted_questions = []

    def get_random_question(self):
        all_questions = self.user_submitted_questions + self.default_questions
        available_questions = list(set(all_questions) - self.asked_questions)
        if not available_questions:
            self.asked_questions = set()
            available_questions = all_questions
        question = random.choice(available_questions)
        self.asked_questions.add(question)
        return question

    def add_user_question(self, question):
        self.user_submitted_questions.append(question)
    
    def remove_user_question(self, question):
        self.user_submitted_questions.remove(question)
    
    def get_user_questions(self, user_id):
        return [q for q in self.user_submitted_questions if q['user_id'] == user_id]

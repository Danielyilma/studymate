from ai_tools.main import AI
from .models import Question, Answer, Card

def generate_mutiple_questions(course):
    if course.file:
        ai = AI()
        questions = ai.run(course.file, "mutiple-choice")
        for question in questions:
            question2 = Question.objects.create(
                    question_text=question.get('questionText'),
                    course=course
                )
            for ans in question.get("answers"):
                Answer.objects.create(
                    text=ans.get('text'),
                    is_correct=ans.get('isCorrect'),
                    question=question2
                )


def generate_cards(course):
    if course.file:
        ai = AI()
        cards = ai.run(course.file, "study-card")
        for card in cards:
            question2 = Card.objects.create(
                    question=card.get('question'),
                    course=course,
                    answer=card.get('answer')
                )



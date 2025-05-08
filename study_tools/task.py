import cloudinary, cloudinary.uploader
from django.conf import settings
from ai_tools.main import AI
from .models import Question, Answer, Card, File, Course, Session
from celery import shared_task
import io


@shared_task
def upload_file(file_content, file_name, id):
    cloudinary.config(secure=True)
    file_data = cloudinary.uploader.upload(
        io.BytesIO(file_content), resource_type="raw", 
        access_mode="public", filename_override=file_name
    )

    url = file_data.get("secure_url")
    file_instance = File.objects.filter(id=id).first()
    file_instance.url = url
    file_instance.save()


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

def get_custom_response(data):
    questions = []
    cards = []
    temp = []
    # print(data.get('questions')[0])
    for i, question in enumerate(data.get('questions')):
        temp.append(question)
        if i and i % 15 == 0:
            questions.append(temp)
            temp = []

    if temp:
        questions.append(temp)

    temp = []
    for i, card in enumerate(data.get("cards")):
        temp.append(card)
        if i and i % 15 == 0:
            cards.append(temp)
            temp = []
    
    if temp:
        cards.append(temp)

    new_data = data
    new_data["questions"] = questions[::-1]
    new_data["cards"] = cards[::-1]

    return new_data


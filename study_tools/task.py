import cloudinary, cloudinary.uploader
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from ai_tools.main import AI
from .models import Question, Answer, Card, File, Course, Session
from celery import shared_task
import io, os, tempfile, requests
from ai_tools.faiss_loader import SessionVectorStore

sv = SessionVectorStore()

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

    print(file_instance.session , "my session")
    sv.store_embeddings(url, str(file_instance.session.id))
    generate_questions(id)

@shared_task
def generate_questions(file_id):
    try:
        # Fetch the File object
        try:
            _file = File.objects.get(id=file_id)
        except ObjectDoesNotExist:
            raise ValueError(f"No File found for session_id: {file_id}")

        # Download the PDF from Cloudinary
        res = requests.get(_file.url, stream=True)
        if res.status_code != 200:
            raise ValueError(f"Failed to download PDF from {_file.url}: Status {res.status_code}, Error: {res.headers.get('x-cld-error', 'No error details')}")

        # Create a temporary file for the PDF
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            temp_file.write(res.content)
            temp_file_path = temp_file.name

        try:
            ai = AI()

            # generate a multiple choice questions and save to database
            questions = ai.run(temp_file_path, "mutiple-choice")
            save_questions(_file.session, questions)

            # generate flash card questions and save to database
            cards = ai.run(temp_file_path, "study-card")
            save_cards(_file.session, cards)
         

        finally:
            # Clean up the temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)

    except Exception as e:
        error_result = {"status": "error", "message": str(e)}
        print("Question generation failed:", error_result)
        raise  ValueError(f"Question generation failed:  {error_result}")


def save_questions(session, questions):
    for question in questions:
        question2 = Question.objects.create(
                question_text=question.get('questionText'),
                session=session
            )
        for ans in question.get("answers"):
            Answer.objects.create(
                content=ans.get('text'),
                is_correct=ans.get('isCorrect'),
                question=question2
            )

def save_cards(session, cards):
    for card in cards:
        question2 = Card.objects.create(
            question=card.get('question'),
            session=session,
            answer=card.get('answer')
        )


# def generate_mutiple_questions(course):
#     if course.file:
#         ai = AI()
#         questions = ai.run(course.file, "mutiple-choice")
#         for question in questions:
#             question2 = Question.objects.create(
#                     question_text=question.get('questionText'),
#                     course=course
#                 )
#             for ans in question.get("answers"):
#                 Answer.objects.create(
#                     text=ans.get('text'),
#                     is_correct=ans.get('isCorrect'),
#                     question=question2
#                 )


# def generate_cards(course):
#     if course.file:
#         ai = AI()
#         cards = ai.run(course.file, "study-card")
#         for card in cards:
#             question2 = Card.objects.create(
#                     question=card.get('question'),
#                     course=course,
#                     answer=card.get('answer')
#                 )

# def get_custom_response(data):
#     questions = []
#     cards = []
#     temp = []
#     # print(data.get('questions')[0])
#     for i, question in enumerate(data.get('questions')):
#         temp.append(question)
#         if i and i % 15 == 0:
#             questions.append(temp)
#             temp = []

#     if temp:
#         questions.append(temp)

#     temp = []
#     for i, card in enumerate(data.get("cards")):
#         temp.append(card)
#         if i and i % 15 == 0:
#             cards.append(temp)
#             temp = []
    
#     if temp:
#         cards.append(temp)

#     new_data = data
#     new_data["questions"] = questions[::-1]
#     new_data["cards"] = cards[::-1]

#     return new_data


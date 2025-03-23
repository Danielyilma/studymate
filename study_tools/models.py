from django.db import models
from base_model import TimeStampMixin
from UserAccountManager.models import User


class Course(TimeStampMixin, models.Model):
    title = models.CharField(max_length=255)
    note_content = models.TextField(blank=True, null=True)
    file = models.FileField(upload_to='uploads')
    user = models.ForeignKey(User, related_name='courses', on_delete=models.CASCADE)

    def __str__(self):
        return self.title


class Question(TimeStampMixin, models.Model):
    course = models.ForeignKey(Course, related_name='questions', on_delete=models.CASCADE)
    question_text = models.TextField()

    def __str__(self):
        return self.question_text


class Answer(TimeStampMixin, models.Model):
    question = models.ForeignKey(Question, related_name='answers', on_delete=models.CASCADE)
    text = models.TextField()
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.text} ({'Correct' if self.is_correct else 'Incorrect'})"


class Card(TimeStampMixin, models.Model):
    course = models.ForeignKey(Course, related_name='cards', on_delete=models.CASCADE)
    question = models.TextField()
    answer = models.TextField()

    def __str__(self):
        return f"Q: {self.question} - A: {self.answer}"



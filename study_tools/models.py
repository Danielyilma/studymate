from datetime import timedelta
from django.utils import timezone
from django.db import models
from base_model import TimeStampMixin
from UserAccountManager.models import User



def two_weeks_from_now():
    return timezone.now() + timedelta(weeks=2)

class Session(TimeStampMixin, models.Model):
    user = models.ForeignKey(User, related_name='user', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    vector_store_id = models.IntegerField(null = True, blank = True) # for now I made null = true 
    expire_date = models.DateTimeField(default=two_weeks_from_now)

    def __str__(self):
        return self.name
    

class Question(TimeStampMixin, models.Model):
    session = models.ForeignKey(Session, related_name='q_session', on_delete=models.CASCADE, null=True, blank=True)
    question_text = models.TextField()

    def __str__(self):
        return self.question_text
    
    
class Answer(TimeStampMixin, models.Model):
    question = models.ForeignKey(Question, related_name='question', on_delete=models.CASCADE, null=True, blank=True)
    content = models.TextField()
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.text} ({'Correct' if self.is_correct else 'Incorrect'})"


class Card(TimeStampMixin, models.Model):
    session = models.ForeignKey(Session, related_name='c_session', on_delete = models.CASCADE, null=True, blank=True)
    question = models.TextField()
    answer = models.TextField()

    def __str__(self):
        return f"Q: {self.question} - A: {self.answer}"


class File(TimeStampMixin, models.Model):
    session = models.ForeignKey(Session, related_name='f_session', on_delete=models.CASCADE, null=True, blank=True)
    url = models.URLField()
    
    def __str__(self):
        return self.url



class Course(TimeStampMixin, models.Model):
    title = models.CharField(max_length=255)
    note_content = models.TextField(blank=True, null=True)
    # file = models.FileField(upload_to='uploads')
    user = models.ForeignKey(User, related_name='courses', on_delete=models.CASCADE)

    def __str__(self):
        return self.title

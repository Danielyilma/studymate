from rest_framework import serializers
from rest_framework.serializers import ValidationError
from ai_tools.main import AI
from .models import Course, Question, Card, Answer, Session, File
from .task import upload_file

class CourseSerializer(serializers.ModelSerializer):

    class Meta:
        model = Course 
        fields = ["id", "title", "created_at"]
    
    def create(self, validated_data):
        request = self.context['request']
        validated_data['user'] = self.context['request'].user
        instance = Course.objects.create(**validated_data)

        # uploaded_file = request.FILES.get('file')
        # if uploaded_file:
        #     uploaded_file.seek(0)
        #     upload_file(uploaded_file, instance.id)


        # ai = AI()
        # summery = ai.run(instance.file, "summerize")
        # if summery:
        #     instance.note_content = summery
        #     instance.save()
        
        return instance

class SessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Session
        fields = ['id', 'name', 'expire_date']
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        
        # vector store id must be set here
        
        return super().create(validated_data)


class AnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Answer
        fields = ['id', 'content', 'is_correct']

class QuestionSerializer(serializers.ModelSerializer):
    answers = AnswerSerializer(many=True)  # Nest answers

    class Meta:
        model = Question
        fields = ['id', 'question_text', 'answers']

class CardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Card
        fields = ['id', 'question', 'answer']


class CourseDetailsSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True)  # Nest questions
    cards = CardSerializer(many=True)          # Nest cards

    class Meta:
        model = Course
        fields = ['id', 'title', 'questions', 'cards', 'note_content']

class FileSerializer(serializers.ModelSerializer):

    class Meta:
        model = File
        fields = ["session"]
    

    def create(self, validated_data):
        request = self.context['request']
        _file = request.FILES.get('file')


        if not _file:
            raise ValidationError("required file field missing")
        
        instance = File.objects.create(**validated_data)
    
        _file_content = _file.read()
        upload_file.delay(_file_content, _file.name, instance.id)

        return instance

from rest_framework import serializers
from ai_tools.main import AI
from .models import Course, Question, Card, Answer, Session

class CourseSerializer(serializers.ModelSerializer):

    class Meta:
        model = Course 
        fields = ["id", "title", "created_at", "file"]
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        instance = Course.objects.create(**validated_data)
        
        ai = AI()
        summery = ai.run(instance.file, "summerize")
        if summery:
            instance.note_content = summery
            instance.save()
        
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
        fields = ['id', 'text', 'is_correct']

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

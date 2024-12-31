from rest_framework import serializers
from ai_tools.main import AI
from .models import Course
from .task import update_course

class CourseSerializer(serializers.ModelSerializer):

    class Meta:
        model = Course 
        fields = "__all__"
    
    def create(self, validated_data):
        instance = Course.objects.create(**validated_data)
        
        ai = AI()
        summery = ai.run(instance.file, "summerize")
        if summery:
            instance.note_content = summery
            instance.save()
        
        return instance
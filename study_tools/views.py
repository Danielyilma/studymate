from rest_framework import generics
from rest_framework.permissions import AllowAny
from .serializers import CourseSerializer, QuestionSerializer, CourseDetailsSerializer
from .models import Course

class CourseCreateView(generics.CreateAPIView):
    permission_classes = [AllowAny]
    serializer_class = CourseSerializer


class CourseListView(generics.ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = CourseSerializer
    queryset = Course.objects.all()

class CourseRetrieveView(generics.RetrieveAPIView):
    permission_classes = [AllowAny]
    serializer_class = CourseDetailsSerializer
    queryset = Course.objects.all()
    lookup_field = 'id'



class QuestionGenerateView(generics.CreateAPIView):
    permission_classes = [AllowAny]
    serializer_class = QuestionSerializer
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.shortcuts import get_object_or_404
from .serializers import CourseSerializer, QuestionSerializer, CourseDetailsSerializer, CardSerializer
from .models import Course
from .task import generate_mutiple_questions, generate_cards, get_custom_response

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

    def get(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)

        data = get_custom_response(serializer.data)

        return Response(data, status=status.HTTP_200_OK)


class QuestionGenerateView(APIView):
    permission_classes = [AllowAny]
    serializer_class = QuestionSerializer

    def post(self, request, *args, **kwargs):
        id = kwargs.get('id')

        course = get_object_or_404(Course, id=id)
        
        try:
            generate_mutiple_questions(course)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
        return Response({"status": "success"}, status=status.HTTP_200_OK)


class CardGenerateView(APIView):
    permission_classes = [AllowAny]
    serializer_class = CardSerializer

    def post(self, request, *args, **kwargs):
        id = kwargs.get('id')

        course = get_object_or_404(Course, id=id)
        
        try:
            generate_cards(course)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
        return Response({"status": "success"}, status=status.HTTP_200_OK)



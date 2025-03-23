from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from .serializers import CourseSerializer, QuestionSerializer, CourseDetailsSerializer, CardSerializer
from .models import Course
from .task import generate_mutiple_questions, generate_cards, get_custom_response

class CourseCreateView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CourseSerializer


class CourseUpdateView(generics.UpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CourseSerializer
    queryset = Course.objects.all()
    lookup_field = 'id'


class CourseDeleteView(generics.DestroyAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Course.objects.all()
    lookup_field = 'id'

    def delete(self, request, *args, **kwargs):
        instance = self.get_object()

        if instance.user != request.user:
            raise PermissionDenied("Unauthorized")
        
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


class CourseListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CourseSerializer

    def get_queryset(self):
        user = self.request.user 
        return Course.objects.filter(user=user).order_by('-created_at')


class CourseRetrieveView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CourseDetailsSerializer
    queryset = Course.objects.all()
    lookup_field = 'id'

    def get(self, request, *args, **kwargs):
        instance = self.get_object()

        if instance.user != request.user:
            raise PermissionDenied("Unauthorized")

        serializer = self.get_serializer(instance)
        data = get_custom_response(serializer.data)

        return Response(data, status=status.HTTP_200_OK)


class QuestionGenerateView(APIView):
    permission_classes = [IsAuthenticated]
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
    permission_classes = [IsAuthenticated]
    serializer_class = CardSerializer

    def post(self, request, *args, **kwargs):
        id = kwargs.get('id')

        course = get_object_or_404(Course, id=id)
        
        try:
            generate_cards(course)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
        return Response({"status": "success"}, status=status.HTTP_200_OK)

from rest_framework import generics
from rest_framework.permissions import AllowAny
from .serializers import CourseSerializer

class CourseCreateView(generics.CreateAPIView):
    permission_classes = [AllowAny]
    serializer_class = CourseSerializer


class CourseListView(generics.ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = CourseSerializer

class CourseRetrieveView(generics.RetrieveAPIView):
    permission_classes = [AllowAny]
    serializer_class = CourseCreateView

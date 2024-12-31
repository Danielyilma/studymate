from django.urls import path
from .views import CourseCreateView, CourseListView, CourseRetrieveView 

urlpatterns = [
    path("uploads/", CourseCreateView.as_view(), name='create-document'),
    path("", CourseListView.as_view(), name='list-courses'),
    path("<int:id>", CourseRetrieveView.as_view(), name="retrieve-course")
]
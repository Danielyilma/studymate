from django.urls import path
from .views import (
    CourseCreateView, CourseListView,
    CourseRetrieveView, QuestionGenerateView, 
    CardGenerateView, CourseUpdateView,
    CourseDeleteView
)

urlpatterns = [
    path("uploads/", CourseCreateView.as_view(), name='create-document'),
    path("", CourseListView.as_view(), name='list-courses'),
    path("<int:id>", CourseRetrieveView.as_view(), name="retrieve-course"),
    path("<int:id>/update", CourseUpdateView.as_view(), name="update-course"),
    path("<int:id>/delete", CourseDeleteView.as_view(), name="delete-course"),
    path("<int:id>/generate-q", QuestionGenerateView.as_view(), name="generate-question"),
    path("<int:id>/generate-c", CardGenerateView.as_view(), name="generate-card")
]
from django.urls import path
from .views import *

urlpatterns = [
    path("uploads/", CourseCreateView.as_view(), name='create-document'),
    path("", CourseListView.as_view(), name='list-courses'),
    path("<int:id>", CourseRetrieveView.as_view(), name="retrieve-course"),
    path("<int:id>/update", CourseUpdateView.as_view(), name="update-course"),
    path("<int:id>/delete", CourseDeleteView.as_view(), name="delete-course"),
    path("<int:id>/generate-q", QuestionGenerateView.as_view(), name="generate-question"),
    path("<int:id>/generate-c", CardGenerateView.as_view(), name="generate-card"),
    
    # session urls
    path("", SessionListView.as_view(), name='list-sessions'),
    path("<int:id>", SessionRetrieveView.as_view(), name="retrieve-session"),
    path("<int:id>/update", SessionUpdateView.as_view(), name="update-session"),
    path("<int:id>/delete", SessionDeleteView.as_view(), name="delete-session"),
]
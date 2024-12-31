from django.urls import path
from .views import CourseCreateView, CourseListView, CourseRetrieveView, QuestionGenerateView

urlpatterns = [
    path("uploads/", CourseCreateView.as_view(), name='create-document'),
    path("", CourseListView.as_view(), name='list-courses'),
    path("<int:id>", CourseRetrieveView.as_view(), name="retrieve-course"),
    path("<int:id>/generate", QuestionGenerateView.as_view(), name="generate-question"),
]
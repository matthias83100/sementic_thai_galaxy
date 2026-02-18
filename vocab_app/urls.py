from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('map-data/', views.MapDataView.as_view(), name='map-data'),
    path('add-word/', views.AddWordView.as_view(), name='add-word'),
    path('preview-word/', views.PreviewWordView.as_view(), name='preview-word'),
    path('suggest-word/', views.WordSuggestionView.as_view(), name='suggest-word'),
    path('quiz-words/', views.QuizWordsView.as_view(), name='quiz-words'),
    path('submit-quiz/', views.QuizSubmissionView.as_view(), name='submit-quiz'),
    path('delete-word/<int:uwi_id>/', views.DeleteWordView.as_view(), name='delete-word'),
    path('update-word/<int:uwi_id>/', views.UpdateWordView.as_view(), name='update-word'),
]

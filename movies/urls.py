from django.contrib import admin
from django.urls import path,include
from movies import views

urlpatterns = [
    path("", views.error.as_view()),
    path("filtered_movies", views.error.as_view()),
    path("similarity_movies", views.error.as_view()),

    path("filtered_movies/<str:genres>", views.model_filtering.as_view(), name = "filtered_movies"),
    path("similarity_movies/<int:movieCode>", views.model_similarity.as_view(), name = "similarity_movies"),

]

from django.contrib import admin
from django.urls import path,include
from movies import views

urlpatterns = [
    path("", views.home.as_view()),
    path("filter", views.filter.as_view()),
    path("similar", views.similar.as_view()),

    path("filter/<str:genres>", views.model_filtering.as_view(), name = "filtered_movies"),
    path("similar/<int:movieCode>", views.model_similarity.as_view(), name = "similarity_movies"),

]

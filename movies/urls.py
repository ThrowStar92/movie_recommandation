from django.contrib import admin
from django.urls import path,include
from movies import views

urlpatterns = [
    path("", views.model1.as_view()),
    path("filtered_movies/", views.model_filtering.as_view(), name = "filtered_movies"),
    path("similarity_movies/", views.model_similarity.as_view(), name = "similarity_movies"),
    # path("<str:name>",views.model2.as_view()),

]

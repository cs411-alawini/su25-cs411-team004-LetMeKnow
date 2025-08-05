
from django.urls import path
from . import views

urlpatterns = [
    path('api/add-sighting/', views.add_sighting, name='add_sighting'),

    path('signin/', views.signin, name='signin'),
]

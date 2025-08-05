from django.urls import path
from . import views

urlpatterns = [
    # ...existing urls...
    path('api/add-sighting/', views.add_sighting, name='add_sighting'),
]


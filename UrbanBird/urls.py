"""
URL configuration for UrbanBird project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from UrbanBird.UserRegister import views


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='index'),
    path('signin/', views.signin, name='signin'),
    path('home/', views.home_view, name='home'),
    path('api/bird-stats', views.get_bird_stats, name='get_bird_stats'),
    path('api/species-overlap', views.get_species_overlap, name='get_species_overlap'),
    path('partial/stats-explorer/', views.stats_explorer_partial, name='stats_explorer_partial'),
    path('api/localities/', views.get_localities, name='get_localities'),
    path('api/add-sighting/', views.add_sighting, name='add_sighting'),  

]

from django.db import models
from django.contrib.auth.models import User

class Location(models.Model):
    location_id = models.CharField(max_length=255, primary_key=True)
    latitude = models.FloatField()
    longitude = models.FloatField()
    locality = models.CharField(max_length=255)

class Occurrence(models.Model):
    occurrence_id = models.BigIntegerField(primary_key=True)
    species_id = models.CharField(max_length=255)
    location_id = models.CharField(max_length=255)
    user_id = models.IntegerField()
    event_date = models.DateField()
    individual_count = models.IntegerField()

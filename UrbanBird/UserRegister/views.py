from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.db import connection
from django.views.decorators.csrf import csrf_exempt
import json
import random
import requests
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from .models import Occurrence, Location  # Adjust if your models are named differently
from django.contrib.auth.models import User

GOOGLE_MAPS_API_KEY = 'AIzaSyCmlDRkxckPchGOXaYjCL6qcpcFCcle_94'  # Replace with your key

def get_bird_stats(request):
    region = request.GET.get("region", "")
    if not region:
        return HttpResponse("Region parameter is required", status=400)

    try:
        cursor = connection.cursor()
        cursor.execute(f"CALL GetBirdStatsByRegion(%s)", [region])
        unique_result = cursor.fetchone()
        unique_species = unique_result[0] if unique_result else 0
        cursor.nextset()
        freq_result = cursor.fetchone()
        most_frequent = {
            "species_id": freq_result[0],
            "sightings": freq_result[1]
        } if freq_result else {
            "species_id": None,
            "sightings": 0
        }

        return JsonResponse({
            "unique_species": unique_species,
            "most_frequent_species": most_frequent
        }, status=200)

    except Exception as e:
        return HttpResponse(f"Error retrieving bird stats: {str(e)}", status=500)

def home_view(request):
    return render(request, 'home.html')

def index(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        email = request.POST.get('email')
        if username and password and email:
            try:
                cursor = connection.cursor()
                cursor.execute("SELECT * FROM USER WHERE user_id = %s OR email = %s", (username, email))
                existing_user = cursor.fetchone()
                print("existing_user:", existing_user)

                if existing_user:
                    return HttpResponse("User already exists with this username or email", status=400)
                
                cursor.execute("INSERT INTO USER (user_id, email, password) VALUES (%s, %s, %s)", (username, email, password))
                connection.commit()
                return HttpResponse("User registered successfully!", status=200)
            except Exception as e:
                return HttpResponse(f"Error registering user: {str(e)}", status=500)
        else:
            return HttpResponse("All fields are required", status=400)
    
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM USER")
    users = cursor.fetchall()
    columns = [col[0] for col in cursor.description]
    users = [dict(zip(columns, user)) for user in users]
    return render(request, 'register.html', {'users': [user['user_id'] for user in users]})

@csrf_exempt
def signin(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            username = data.get('username')
            password = data.get('password')
            if not username or not password:
                return JsonResponse({
                    'success': False,
                    'message': 'Username and password are required'
                }, status=400)
            
            cursor = connection.cursor()
            cursor.execute("SELECT * FROM USER WHERE user_id = %s AND password LIKE %s", (username, password))
            user = cursor.fetchone()
            
            if user:
                columns = [col[0] for col in cursor.description]
                user_dict = dict(zip(columns, user))
                print(user_dict.get('user_id'))
                return JsonResponse({
                    'success': True,
                    'message': 'Sign in successful!',
                    'user': {
                        'user_id': user_dict.get('user_id'),
                        'email': user_dict.get('email'),
                        'password': user_dict.get('password')
                    }
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'Invalid username or password'
                }, status=401)
                
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'message': 'Invalid JSON data'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'An error occurred: {str(e)}'
            }, status=500)
    
    return JsonResponse({
        'success': False,
        'message': 'Only POST method is allowed'
    }, status=405)

@csrf_exempt
def add_sighting(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request method.'})

    try:
        data = json.loads(request.body)
        species = data['species'].strip()
        locality = data['locality'].strip()
        latitude = float(data['latitude'])
        longitude = float(data['longitude'])
        event_date = data['event_date']
        individual_count = int(data['individual_count'])
        user_id = data.get('user_id')  # <-- Get user_id from POST data

        if not user_id:
            return JsonResponse({'success': False, 'message': 'User not signed in.'})

        # Validate coordinates with Google Maps API
        gmaps_url = (
            f"https://maps.googleapis.com/maps/api/geocode/json?latlng={latitude},{longitude}&key={GOOGLE_MAPS_API_KEY}"
        )
        gmaps_resp = requests.get(gmaps_url).json()
        if not gmaps_resp['results']:
            return JsonResponse({'success': False, 'message': 'Invalid coordinates (not a real location).'})

        # Check if LOCATION exists
        location = Location.objects.filter(latitude=latitude, longitude=longitude, locality=locality).first()
        if not location:
            location_id = f"https://observation.org/observation/{random.randint(100000000, 999999999)}"
            location = Location.objects.create(
                location_id=location_id,
                latitude=latitude,
                longitude=longitude,
                locality=locality
            )
        else:
            location_id = location.location_id

        # Prevent duplicate for same user, species, location, date, count
        duplicate = Occurrence.objects.filter(
            user_id=user_id,
            species_id=species,
            location_id=location_id,
            event_date=event_date,
            individual_count=individual_count
        ).exists()
        if duplicate:
            return JsonResponse({'success': False, 'message': 'Duplicate sighting for this user.'})

        # Generate unique occurrence_id
        while True:
            occurrence_id = random.randint(1000000000, 9999999999)
            if not Occurrence.objects.filter(occurrence_id=occurrence_id).exists():
                break

        Occurrence.objects.create(
            occurrence_id=occurrence_id,
            species_id=species,
            location_id=location_id,
            user_id=user_id,
            event_date=event_date,
            individual_count=individual_count
        )

        return JsonResponse({'success': True})

    except Exception as e:
        print("Add Sighting Error:", e)  # Add this for debugging
        return JsonResponse({'success': False, 'message': f'Error: {str(e)}'})



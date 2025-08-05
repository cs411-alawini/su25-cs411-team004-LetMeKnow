from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.db import connection
from django.views.decorators.csrf import csrf_exempt
import json

def get_localities(request):
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT DISTINCT locality FROM LOCATION ORDER BY locality ASC")
        rows = cursor.fetchall()
        localities = [row[0] for row in rows]
        return JsonResponse({'localities': localities})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    
def stats_explorer_partial(request):
    return render(request, 'statsExplorer.html')

def get_species_overlap(request):
    locA = request.GET.get('locA')
    locB = request.GET.get('locB')

    if not locA or not locB:
        return HttpResponse("Both locations must be provided", status=400)

    try:
        cursor = connection.cursor()
        cursor.execute("CALL GetSpeciesOverlapInfo(%s, %s)", [locA, locB])
        overlap_species = cursor.fetchall()
        cursor.nextset()
        overlap_count_row = cursor.fetchone()

        species_list = [row[0] for row in overlap_species]
        overlap_count = overlap_count_row[0] if overlap_count_row else 0

        return JsonResponse({
            "species": species_list,
            "count": overlap_count
        })

    except Exception as e:
        return HttpResponse(f"Error fetching overlap data: {str(e)}", status=500)
    
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
def get_sightings(request):
    try:

        species = request.GET.get('species')
        locality = request.GET.get('locality')
        limit = request.GET.get('limit')

        print("Filters received:")
        print("  Species:", species)
        print("  Locality:", locality)
        print("  Limit:", limit)

        cursor = connection.cursor()

        base_query = """
            SELECT
            Tax.species_id,
            Tax.common_name AS bird_name,
            Loc.latitude,
            Loc.longitude,
            Loc.locality,
            Tax.category,
            Orde.order_name,
            Rar.label AS rarity_label
            FROM UrbanBird.OCCURRENCE Occ
            JOIN UrbanBird.TAXON Tax ON Occ.species_id = Tax.species_id
            JOIN UrbanBird.LOCATION Loc ON Occ.location_id = Loc.location_id
            JOIN UrbanBird.ORDER Orde ON Tax.order_id = Orde.order_id
            JOIN UrbanBird.RARITY Rar ON Tax.rarity_id = Rar.rarity_id
        """

        where_clauses = ["Loc.latitude IS NOT NULL", "Loc.longitude IS NOT NULL"]
        params = []

        if species:
            where_clauses.append("Tax.common_name LIKE %s")
            params.append(species)

        if locality:
            where_clauses.append("Loc.locality LIKE %s")
            params.append(locality)

        if where_clauses:
            base_query += " WHERE " + " AND ".join(where_clauses)

        if limit and limit.isdigit():
            base_query += " LIMIT %s"
            params.append(int(limit))

        cursor.execute(base_query, params)

        rows = cursor.fetchall()

        output = []
        for row in rows:
            output.append({
                "species_id": row[0],
                "bird_name": row[1],
                "latitude": float(row[2]),
                "longitude": float(row[3]),
                "locality": row[4],
                "category": row[5],
                "order_name": row[6],
                "rarity_label": row[7],
            })

        print(f"Returning {len(output)} full sightings")
        return JsonResponse({"sightings": output}, status=200)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({"error": str(e)}, status=500)

@csrf_exempt
def get_localities(request):
    cursor = connection.cursor()
    cursor.execute("SELECT DISTINCT locality FROM UrbanBird.LOCATION LIMIT 1000;")
    rows = cursor.fetchall()

    localities = []
    for row in rows:
        if row[0]:
            localities.append(row[0])

    return JsonResponse({"localities": localities})


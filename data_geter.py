#windbud.py

import gspread
import pandas as pd
import requests
from datetime import datetime, timedelta, timezone

df_riders = pd.DataFrame()
def obtenir_donnees():
    global df_riders  # Indique que nous utilisons la variable globale df_riders
    # Authentification et accès aux feuilles
    client = gspread.service_account(filename='clés.json')
    wb = client.open('WINDBUD')
    sheets = {sheet.title: sheet for sheet in wb.worksheets()}
    wb_spots = sheets['SPOTS']
    wb_riders = sheets['RIDERS']

    # Conversion des données en DataFrame
    df_spots = pd.DataFrame(wb_spots.get_all_records())
    df_riders = pd.DataFrame(wb_riders.get_all_records())

    # Initialisation des structures de données
    spots_info = {int(spot_id): {'SPOT': '', 'RIDERS': [], 'WEATHER_DATA': {}} for spot_id in df_spots['ID_SPOT'].unique()}

    # Dates pour la requête API
    heure_actuelle_moins_une = datetime.now(timezone.utc) - timedelta(hours=1)
    date_debut = heure_actuelle_moins_une.replace(minute=0, second=0, microsecond=0)
    date_fin = date_debut + timedelta(days=6)
    date_fin = date_fin.replace(hour=5, minute=0, second=0, microsecond=0)
    date_debut_str = date_debut.strftime('%Y-%m-%dT%H:%M:%S+00:00')
    date_fin_str = date_fin.strftime('%Y-%m-%dT%H:%M:%S+00:00')

    # Liste de tous les paramètres météorologiques demandés
    params = 'windSpeed,gust,windDirection,swellHeight,swellPeriod,waveHeight,waveDirection,wavePeriod'

    # Collecte des données météo pour chaque spot
    for _, spot_info in df_spots.iterrows():
        spot_id = int(spot_info['ID_SPOT'])  # Assurez-vous que spot_id est un entier
        lat, lng = spot_info['COORDINATE_LATITUDE'], spot_info['COORDINATE_LONGITUDE']
        spots_info[spot_id]['SPOT'] = spot_info['SPOT']

        response = requests.get(
            'https://api.stormglass.io/v2/weather/point',
            params={
                'lat': lat,
                'lng': lng,
                'params': params,
                'start': date_debut_str,
                'end': date_fin_str,
                'interval': '1h',
            },
            headers={'Authorization': 'f4eb84f2-119d-11ed-b697-0242ac130002-f4eb85c4-119d-11ed-b697-0242ac130002'}
        )

        if response.status_code == 200:
            json_data = response.json()
            for hour_data in json_data['hours']:
                time = hour_data['time']
                weather_data = {param: hour_data[param]['noaa'] for param in hour_data if 'noaa' in hour_data[param]}
                # Convertir le temps en objet datetime
                time_obj = datetime.strptime(time, '%Y-%m-%dT%H:%M:%S+00:00')
                # Vérifier si l'heure est comprise entre 6h et 22h
                if 6 <= time_obj.hour <= 22:
                    # Modifier ici pour inclure la date et l'heure dans la clé du dictionnaire
                    spots_info[spot_id]['WEATHER_DATA'][time_obj.strftime('%Y-%m-%d %H:%M:%S')] = weather_data

    # Association des riders à leurs spots favoris
    for _, rider in df_riders.iterrows():
        # Convertit la valeur de SPOTS_FAVORIS en chaîne de caractères, quel que soit son type original
        spots_favoris_str = str(rider['SPOTS_FAVORIS'])
        
        # Divise cette chaîne en utilisant ',' pour obtenir une liste d'IDs de spots
        spots_favoris_ids = [int(spot_id) for spot_id in spots_favoris_str.split(';') if spot_id.strip().isdigit()]

        for spot_id_favori in spots_favoris_ids:
            if spot_id_favori in spots_info:
                # Ajoute le rider à la liste des RIDERS pour chaque spot favori valide
                spots_info[spot_id_favori]['RIDERS'].append(rider['RIDER'])



    # Affichage des résultats
    for spot_id, info in spots_info.items():
        print(f"Spot ID: {spot_id}, Spot Name: {info['SPOT']}")
        riders_list = ', '.join(info['RIDERS']) if info['RIDERS'] else 'Aucun rider'
        print(f"Riders favorisant ce spot: {riders_list}")
        if info['WEATHER_DATA']:
            weather_df = pd.DataFrame(info['WEATHER_DATA'].items(), columns=['Date', 'Weather'])
            weather_df['Date'] = pd.to_datetime(weather_df['Date'])
            weather_df.set_index('Date', inplace=True)
            print(weather_df)
        else:
            print("Avertissement: Aucune donnée météo disponible pour ce spot.")
        print("\n" + "-"*40 + "\n")
    return spots_info  # Retourner spots_info pour utilisation externe
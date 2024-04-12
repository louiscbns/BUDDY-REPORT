import pandas as pd
from color_calculator import get_color
import re
import numpy as np

# Définition des seuils et couleurs pour la coloration conditionnelle
thresholds_wind = [1, 4, 7, 10, 11, 14, 17, 19, 20, 22, 25, 28, 34, 37, 41, 43, 47]
colors_wind = ['#ffffff', '#e7fdfc', '#64f9ed', '#4df9b7', '#28fc04', '#12f80e', '#a8f500', '#faf004', '#fed603', '#fe4534', '#ff791b', '#ff2e3b', '#fd0ed0', '#ff1f78', '#f303f3', '#ff04f3', '#70216e','#b423ff', '#8c33ff']
thresholds_wave = [0, 0.8, 1.7, 2.5, 3.1, 3.7, 4.8, 5.5, 6.2]
colors_wave = ['#ffffff', '#e4e6ff', '#bcc0ff', '#949bff', '#7c82fd', '#8a75ed', '#a85ece', '#ba59b9', '#cd55a1']
thresholds_wave_period = [0, 10, 20]
colors_wave_period = ['#ffffff', '#ffffff', '#E5625A']

def generate_arrow_html(angle, for_email=False):
    if for_email:
        directions = ["N", "N-NE", "NE", "E-NE", "E", "E-SE", "SE", "S-SE", "S", "S-SW", "SW", "W-SW", "W", "W-NW", "NW", "N-NW", "N"]
        index = round(angle / 22.5) % 16
        return directions[index]
    else:
        return f'<span style="display:inline-block; transform: rotate({angle}deg); font-size: 200%;">&#8595;</span>'

FACTOR_MPS_TO_KNOTS = 1.94384  # Conversion factor from m/s to knots

def prepare_data(spots_info, for_email=False, interval='1h'):
    dataframes_html = {}
    previous_day = None
    alternate_color = "#d5d5d5"
    
    for spot_id, info in spots_info.items():
        combined_df = None

        weather_data = info.get('WEATHER_DATA', {})
        for time, data in weather_data.items():
            if data:
                df = pd.DataFrame([data])
                df['Date'] = pd.to_datetime(time)
                df.set_index('Date', inplace=True)

                combined_df = df if combined_df is None else pd.concat([combined_df, df])

        if combined_df is not None:
            
            if for_email:
                combined_df = combined_df.resample('D').mean()  # Moyenne quotidienne pour les e-mails
            else:
                combined_df = combined_df.between_time('06:00', '22:00')
                combined_df = combined_df.resample(interval).mean()  # Resampling selon l'intervalle spécifié
            
            # Convertir et arrondir windSpeed et gust de m/s en nœuds
            combined_df['windSpeed'] = (combined_df['windSpeed'] * FACTOR_MPS_TO_KNOTS).round(0).fillna(0).astype(int)
            combined_df['gust'] = (combined_df['gust'] * FACTOR_MPS_TO_KNOTS).round(0).fillna(0).astype(int)
            
            # Convertir et arrondir waveHeight et swellHeight en mètres
            if 'waveHeight' in combined_df.columns:
                combined_df['waveHeight'] = combined_df['waveHeight'].round(1).fillna(0)

            # Convertir et arrondir wavePeriod et swellPeriod en secondes
            if 'wavePeriod' in combined_df.columns:
                combined_df['wavePeriod'] = combined_df['wavePeriod'].round(0).fillna(0).astype(int)

            # Filtre des colonnes en fonction des données disponibles
            columns_of_interest = ['windSpeed', 'gust', 'windDirection']
            wave_columns = ['waveHeight', 'wavePeriod', 'waveDirection']

            for col in wave_columns:
                if col in combined_df.columns and not combined_df[col].isnull().all():
                    columns_of_interest.append(col)

            combined_df = combined_df[columns_of_interest]

            for column in combined_df.columns:
                if 'wavePeriod' in column :
                    combined_df[column] = combined_df[column].apply(lambda x: f'<div style="background-color: {get_color(x, thresholds_wave_period, colors_wave_period)};">{x}</div>')
                elif column in ['windSpeed', 'gust']:
                    combined_df[column] = combined_df[column].apply(lambda x: f'<div style="background-color: {get_color(x, thresholds_wind, colors_wind)};">{x}</div>')
                elif 'waveHeight' in column :
                    combined_df[column] = combined_df[column].apply(lambda x: f'<div style="background-color: {get_color(x, thresholds_wave, colors_wave)};">{x}</div>')
                elif column in ['waveDirection', 'windDirection']:
                    combined_df[column] = combined_df[column].apply(lambda x: generate_arrow_html(x, for_email))

            # Générer le HTML
            if not for_email:
                transposed_df = combined_df.transpose()
                transposed_df.columns = [dt.strftime('%a %d. %Hh') for dt in transposed_df.columns]

                def add_class(m):
                    nonlocal previous_day, alternate_color
                    current_day = m.group(2)

                    if current_day != previous_day:
                        alternate_color = "#F7F7F7" if alternate_color == "#d5d5d5" else "#d5d5d5"
                        previous_day = current_day

                    return f'<th style="background-color: {alternate_color};">{m.group(1)}</br>{m.group(2)}.</br>{m.group(3)}h</th>'

                pattern = re.compile(r'<th>([A-Za-z]+)\s+(\d{1,2})\.\s+(\d{2})h<\/th>')
                html = transposed_df.to_html(escape=False, border=0)
                html = pattern.sub(add_class, html)
                dataframes_html[f"{info['SPOT']}"] = html.replace('<th>Spot</th>', f'<th class="spot-name">{info["SPOT"]}</th>')
            else:
                transposed_df = combined_df.transpose()
                transposed_df.columns = [dt.strftime('%A %d.') for dt in transposed_df.columns]

                def add_class(m):
                    nonlocal previous_day, alternate_color
                    current_day = m.group(2)

                    if current_day != previous_day:
                        alternate_color = "#F7F7F7" if alternate_color == "#d5d5d5" else "#d5d5d5"
                        previous_day = current_day

                    return f'<th style="background-color: {alternate_color};">{m.group(1)} {m.group(2)}</th>'

                pattern = re.compile(r'<th>([A-Za-z]+)\s+(\d{1,2})<\/th>')
                html = transposed_df.to_html(escape=False, border=0)
                html = pattern.sub(add_class, html)
                dataframes_html[f"{info['SPOT']}"] = html.replace('<th>Spot</th>', f'<th class="spot-name">{info["SPOT"]}</th>')

    return dataframes_html

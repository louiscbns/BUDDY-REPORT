import pandas as pd

# color_calculator.py

def get_color(value, thresholds, colors):
    if pd.isnull(value):
        return '#FFFFFF'  # Retourne blanc pour les valeurs NaN
    for i, threshold in enumerate(thresholds):
        if value <= threshold:
            if i == 0:
                return colors[i]  # Retourne la première couleur si la valeur est inférieure au premier seuil
            else:
                # Calculer le dégradé entre les deux couleurs
                low_value = thresholds[i - 1]
                high_value = threshold
                ratio = (value - low_value) / (high_value - low_value)
                return interpolate_color(colors[i - 1], colors[i], ratio)
    return colors[-1]  # Retourne la dernière couleur si la valeur dépasse tous les seuils

def interpolate_color(color1, color2, ratio):
    color1_rgb = hex_to_rgb(color1)
    color2_rgb = hex_to_rgb(color2)
    
    # Calculer les composantes RGB intermédiaires
    red = round(color1_rgb[0] + ratio * (color2_rgb[0] - color1_rgb[0]))
    green = round(color1_rgb[1] + ratio * (color2_rgb[1] - color1_rgb[1]))
    blue = round(color1_rgb[2] + ratio * (color2_rgb[2] - color1_rgb[2]))
    
    return rgb_to_hex(red, green, blue)

def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def rgb_to_hex(r, g, b):
    return f'#{r:02x}{g:02x}{b:02x}'

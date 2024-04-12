# app.py

from flask import Flask, render_template, request
from data_geter import obtenir_donnees
from data_manager import prepare_data

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def display_tables():
    spots_info = obtenir_donnees()
    dataframes_html = {}
    if request.method == 'POST':
        selected_spot = request.form.get('selected_spot')
        chosen_interval = request.form.get('interval', '1h')  # Par défaut à 1h si rien n'est choisi
        # Passez l'intervalle choisi à la fonction prepare_data
        dataframes_html = prepare_data({int(selected_spot): spots_info[int(selected_spot)]}, interval=chosen_interval)
    spots_list = [(info['SPOT'], spot_id) for spot_id, info in spots_info.items()]
    return render_template('template.html', spots_list=spots_list, dataframes_html=dataframes_html)

if __name__ == "__main__":
    app.run(debug=True)

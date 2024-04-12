import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import data_geter
import data_manager
import re
import time

# Suivi de la date du dernier envoi
last_sent_date = None

def create_email_content(rider, spots_info):
    css = """
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;700&display=swap');

    body {
        font-family: Montserrat, sans-serif;
    }

    table {
        border-collapse: collapse;
        width: 100%;
        margin: auto;
    }

    th, td {
        border: 1px solid #fff;
        padding: 3px;
        text-align: center;
        vertical-align: middle;
        font-size: 13px;
    }

    th {
        background-color: #f2f2f2;
        font-weight: normal;
        font-family: Montserrat;
    }

    tr:hover {
        background-color: #ddd;
    }

    th:first-child,
    td:first-child {
        position: sticky;
        left: 0;
        z-index: 1;
        background-color: #f2f2f2;
    }

    th:not(:first-child),
    td:not(:first-child) {
        position: sticky;
        z-index: 0;
        background-color: #f2f2f2;
    }

    th.spot-name,
    td.spot-name {
        position: sticky;
        left: 0;
        z-index: 2;
        background-color: #f2f2f2;
    }

    th.spot-name,
    td.spot-name {
        border-left: none;
    }

    th.spot-name {
        border-right: 1px solid #888;
    }
    """

    body = f"""<html>
                <head>
                    <style>{css}</style>
                </head>
                <body>
                    <img src="" style="display: block; margin-left: auto; margin-right: auto; width: 100%; height: 160px; object-fit: cover;">
                    <br>
                    <p>Hello {rider.RIDER},</p>
                    <p>Voici ton report de la semaine :</p><br>
                """

    for spot_id in [int(s) for s in str(rider.SPOTS_FAVORIS).split(';') if s.strip().isdigit()]:
        if spot_id in spots_info:
            spot_data = spots_info[spot_id]
            weather_html = data_manager.prepare_data({spot_id: spot_data}, for_email=True, interval='3h')
            body += f"<h3>🏄‍♂️ {spot_data['SPOT']}</h3>{weather_html.get(spot_data['SPOT'], 'Aucune donnée disponible')}<br>"

   
    body += f"""<img src="" style="display: block; margin-left: auto; margin-right: auto; width: 100%; height: auto; ">"""
    body += "</body></html>"
    return body

def send_email(subject, body, recipient, sender_email, sender_password):
    message = MIMEMultipart()
    message['From'] = sender_email
    message['To'] = recipient
    message['Subject'] = subject
    message.attach(MIMEText(body, 'html'))

    try:
        server = smtplib.SMTP('smtp.ionos.fr', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, recipient, message.as_string())
        server.quit()
        print(f"Email envoyé avec succès à {recipient}")
    except Exception as e:
        print(f"Erreur lors de l'envoi de l'email à {recipient}: {e}")

def is_valid_email(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+", email) is not None


import datetime
import time

def main():
    global last_sent_date
    today = datetime.date.today()  # Obtient la date d'aujourd'hui
    weekday = today.weekday()  # Lundi = 0, Mardi = 1, ..., Dimanche = 6

    # Vérifie si aujourd'hui est lundi (0) ou jeudi (3)
    if weekday == 0 or weekday == 4:
        today_date = time.strftime("%Y-%m-%d")
        spots_info = data_geter.obtenir_donnees()

        for rider in data_geter.df_riders.itertuples():
            if is_valid_email(rider.MAIL):
                email_content = create_email_content(rider, spots_info)
                if email_content:
                    send_email(f"Ton BuddyReport 🏄‍♂️ - {today_date}", email_content, rider.MAIL, 'louis.cabanis@meledan-conseil.com', 'ohQg5s@nBwRC&$')
    else:
        print("Aujourd'hui n'est ni un lundi ni un jeudi. Aucun e-mail n'a été envoyé.")

if __name__ == "__main__":
    main(debug=False, host='0.0.0.0')

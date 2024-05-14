import csv
import os
import mysql.connector
import joblib
import requests
import smtplib
import pandas as pd

from flask import Flask, render_template, jsonify, request
from backend.services.dbconnect import insert_notification_preferences
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta

# Path to the CSV file
data_file_path = os.path.join(os.getcwd(), 'backend/data/userdata.csv')

app = Flask(__name__)
model = joblib.load('backend/models/flood_prediction_model.pkl')

@app.route('/predict_realflood', methods=['GET'])
# Usage in the predict_realflood endpoint
def predict_realflood():
    try:
        api_url = 'https://data.weather.gov.hk/weatherAPI/opendata/weather.php?dataType=rhrread&lang=en'
        response = requests.get(api_url)
        if response.status_code == 200:
            real_time_data = response.json()
            feature = extract_feature(real_time_data)

            featureDf = pd.DataFrame([feature])
            prediction_proba = model.predict_proba(featureDf)[0] 
            probability = round(prediction_proba[1] * 100, 2) 
         
            return jsonify({'realPrediction': {'probability': probability}})
        else:
            return jsonify({'error': f"Error: {response.status_code}"})
    except Exception as e:
        return jsonify({'error': str(e)})



def extract_feature(real_time_data):
    max_rainfall = max([d['max'] for d in real_time_data['rainfall']['data'] if 'max' in d])
    avg_temperature = sum([t['value'] for t in real_time_data['temperature']['data']]) / len(real_time_data['temperature']['data'])
    avg_humidity = sum([h['value'] for h in real_time_data['humidity']['data']]) / len(real_time_data['humidity']['data'])

    now = datetime.now()

    feature = {
        'Rainfall': max_rainfall,
        'Humidity': avg_humidity,
        'Year': now.year,
        'Month': now.month,
        'Day': now.day,
        'Temperature': avg_temperature
    }
    return feature



# Feature for historical flood prediction
@app.route('/admin_simulation.html')
def show_predict_form():
    return render_template('admin_simulation.html')

@app.route('/predict_historical_flood', methods=['GET'])
def predict_flood_from_date():
    date = request.args.get('date')
    if not date:
        return jsonify({'error': 'No date provided'}), 400
    prediction, probability = predict_flood(date=date)
    if prediction is not None:
        return jsonify({'prediction': str(prediction), 'probability': str(probability)})
    else:
        return jsonify({'error': 'Failed to make prediction'}), 500

def predict_flood(date=None):
    try:
        if date:
            df = pd.read_csv('backend/data/training_df.csv')
            df['Date'] = pd.to_datetime(df[['Year', 'Month', 'Day']])
            date_parsed = datetime.strptime(date, "%Y-%m-%d")
            historical_data = df[df['Date'] == date_parsed]
            if historical_data.empty:
                return None, None, None
            
            rainfall = historical_data['Rainfall'].values[0]
            feature_vector = {
                'Rainfall': rainfall,
                'Humidity': historical_data['Humidity'].values[0],
                'Year': historical_data['Year'].values[0],
                'Month': historical_data['Month'].values[0],
                'Day': historical_data['Day'].values[0],
                'Temperature': historical_data['Temperature'].values[0]
            }
            feature_df = pd.DataFrame([feature_vector])

            probabilities = model.predict_proba(feature_df)[:, 1]
            prediction = int(probabilities > 0.68)
            probability = round(probabilities[0] * 100, 2)

            return prediction, probability, rainfall
        else:
            return None, None, None
    except Exception as e:
        print(f"Error in predict_flood: {str(e)}")
        return None, None, None



@app.route('/predict_flood_range', methods=['GET'])
def predict_flood_range():
    selected_date = request.args.get('date')
    if not selected_date:
        return jsonify({'error': 'No date provided'}), 400

    try:
        start_date = datetime.strptime(selected_date, "%Y-%m-%d") - timedelta(days=1)
        end_date = start_date + timedelta(days=2)
        date_range = pd.date_range(start_date, end_date)

        results = []
        for single_date in date_range:
            prediction, probability, rainfall = predict_flood(date=single_date.strftime("%Y-%m-%d"))
            if prediction is not None:
                results.append({
                    'date': single_date.strftime("%Y-%m-%d"), 
                    'probability': probability, 
                    'rainfall': rainfall
                })
            else:
                results.append({
                    'date': single_date.strftime("%Y-%m-%d"), 
                    'probability': None, 
                    'rainfall': None
                })

        return jsonify(results)
    except Exception as e:
        return jsonify({'error': str(e)}), 500



# Route for landing page
@app.route('/')
def index():
    # Path to CSV file
    csv_file_path = os.path.join(os.getcwd(), 'backend/data/9dforecast.csv')
    
    # List to hold rows of data
    forecasts = []
    
    # Read CSV data
    with open(csv_file_path, mode='r') as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            forecasts.append(row)
    
    # Pass data to the template
    return render_template('weather_forecast.html', forecasts=forecasts)

# Route for weather forecast page
@app.route('/weather_forecast.html')
def weatherforecast():
    # Path to CSV file
    csv_file_path = os.path.join(os.getcwd(), 'backend/data/9dforecast.csv')
    
    # List to hold rows of data
    forecasts = []
    
    # Read CSV data
    with open(csv_file_path, mode='r') as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            forecasts.append(row)
    
    # Pass data to the template
    return render_template('weather_forecast.html', forecasts=forecasts)

# Route for history.html
@app.route('/history.html')
def history():
    # Extract query parameters
    selected_location = request.args.get('location', 'cheung_chau')  # Default to 'cheung_chau' if not provided
    selected_year = request.args.get('year', '2022')  # Set initial value for year
    selected_month = request.args.get('month', '1')  # Set initial value for month

    # Construct CSV file path based on selected location
    csv_file_path = os.path.join(os.getcwd(), f"backend/data/Daily Rainfall/{selected_location}.csv")

    # Check if the file exists
    if not os.path.exists(csv_file_path):
        return f"CSV file not found: {csv_file_path}"

    # List to hold rows of data
    forecasts = []

    # Read CSV data
    try:
        with open(csv_file_path, mode='r', encoding='utf-8-sig') as file:
            csv_reader = csv.DictReader(file)
            for row in csv_reader:
                # Remove BOM from keys
                row = {key.strip('\ufeff'): value for key, value in row.items()}
                forecasts.append(row)
    except Exception as e:
        return f"Error reading CSV file: {str(e)}"

    # Filter data based on query parameters
    filtered_forecasts = [forecast for forecast in forecasts if forecast['Month'] == selected_month and forecast['Year'] == selected_year]

    # Pass data to the template
    return render_template('history.html', forecasts=filtered_forecasts, selected_year=selected_year, selected_month=selected_month)

@app.route('/history.html')
def historyh():
    # Extract query parameters
    selected_location = request.args.get('location', 'cheung_chau')  # Default to 'cheung_chau' if not provided
    selected_year = request.args.get('year', '2022')  # Set initial value for year
    selected_month = request.args.get('month', '1')  # Set initial value for month

    # Construct CSV file path based on selected location
    csv_file_path = os.path.join(os.getcwd(), f"backend/data/Daily Rainfall/{selected_location}.csv")

    # Check if the file exists
    if not os.path.exists(csv_file_path):
        return f"CSV file not found: {csv_file_path}"

    # List to hold rows of data
    forecasts = []

    # Read CSV data
    try:
        with open(csv_file_path, mode='r', encoding='utf-8-sig') as file:
            csv_reader = csv.DictReader(file)
            for row in csv_reader:
                # Remove BOM from keys
                row = {key.strip('\ufeff'): value for key, value in row.items()}
                forecasts.append(row)
    except Exception as e:
        return f"Error reading CSV file: {str(e)}"

    # Filter data based on query parameters
    filtered_forecasts = [forecast for forecast in forecasts if forecast['Month'] == selected_month and forecast['Year'] == selected_year]

    # Pass data to the template
    return render_template('history.html', forecasts=filtered_forecasts, selected_year=selected_year, selected_month=selected_month)

@app.route('/get_rainfall_data')
def get_rainfall_data():
    selected_location = request.args.get('location', 'cheung_chau')
    selected_year = request.args.get('year', '2023')
    selected_month = request.args.get('month', '1')

    # Construct the CSV file path based on the selected location
    csv_file_path = os.path.join(os.getcwd(), f"backend/data/Daily Rainfall/{selected_location}.csv")

    if not os.path.exists(csv_file_path):
        return jsonify({'error': f"CSV file not found: {csv_file_path}"})

    forecasts = []
    try:
        with open(csv_file_path, mode='r', encoding='utf-8-sig') as file:
            csv_reader = csv.DictReader(file)
            for row in csv_reader:
                row = {key.strip('\ufeff'): value for key, value in row.items()}
                forecasts.append(row)
    except Exception as e:
        return jsonify({'error': f"Error reading CSV file: {str(e)}"})

    # Filter data based on query parameters
    filtered_forecasts = [forecast for forecast in forecasts if forecast['Month'] == selected_month and forecast['Year'] == selected_year]

    # Prepare the chart data including Year, Month, Day, and Value
    chart_data = [{'YEAR': row['Year'], 'MONTH': row['Month'], 'DAY': row['Day'], 'VALUE': row['Value']} for row in filtered_forecasts]

    return jsonify(chart_data)

# Route for warning.html
@app.route ('/warning.html')
def warning():
    return render_template('warning.html')

# Route for faq.html
@app.route ('/faq.html')
def faq():
    return render_template('faq.html')

# Route for noti.html
@app.route ('/noti.html')
def noti():
    return render_template('noti.html')

# Route to handle form submission
@app.route('/submit_preferences', methods=['POST'])
def submit_preferences():
    location = request.form['location']
    name = request.form['name']
    email = request.form['email']
    rainfall = 'rainfall' in request.form
    flood = 'flood' in request.form

    # Create CSV file if it doesn't exist
    if not os.path.exists(data_file_path):
        with open(data_file_path, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['Location', 'Name', 'Email', 'Rainfall Alert', 'Flood Alert'])

    # Append new preferences to the CSV file
    with open(data_file_path, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([location, name, email, rainfall, flood])

    return render_template('noti.html', success=True)


# Route for contact.html
@app.route ('/contact.html')
def contact():
    return render_template('contact.html')

# Route for email.html
@app.route ('/email.html')
def email():
    return render_template('email.html')

# Route for data_management.html
@app.route ('/data_management.html')
def data_management():
    return render_template('data_management.html')


# Route for admin_page_alert.html
@app.route('/admin_page_alert.html')
def admin_page_alert():
    # Read data from the CSV file
    data = []
    if os.path.exists(data_file_path):
        with open(data_file_path, mode='r') as file:
            csv_reader = csv.DictReader(file)
            for row in csv_reader:
                data.append(row)

    return render_template('admin_page_alert.html', data=data)

@app.route('/send_notification', methods=['POST'])
def send_notification():
    # Load the recipient email addresses from the CSV file
    recipients = []
    with open('backend/data/userdata.csv', mode='r') as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            recipients.append(row['Email'])

    # Load email subject and body from the CSV file
    with open('backend/data/notification/emaildata.csv', mode='r') as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            subject = row['subject']
            body = row['body']

    # Append the forecast table to the email body
    with open('backend/data/9dforecast.csv', mode='r') as file:
        csv_reader = csv.DictReader(file)
        table = '<br><br><table border="1">'
        table += '<tr>' + ''.join(f'<th>{key}</th>' for key in csv_reader.fieldnames) + '</tr>'
        for row in csv_reader:
            table += '<tr>' + ''.join(f'<td>{value}</td>' for value in row.values()) + '</tr>'
        table += '</table>'
        body += table

    # Email sender details


    # Send email to each recipient
    for recipient in recipients:
        msg = MIMEMultipart()
        msg.attach(MIMEText(body, 'html'))
        msg['Subject'] = subject
        msg['From'] = sender
        msg['To'] = recipient
        try:
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp_server:
                smtp_server.login(sender, password)
                smtp_server.sendmail(sender, recipient, msg.as_string())
            print(f"Message sent to {recipient}")
        except Exception as e:
            print(f"Failed to send email to {recipient}: {str(e)}")

    return "Emails sent successfully!"

# Route for send_alert
@app.route('/send_alert', methods=['POST'])
def send_alert():
    # Load the recipient email addresses from the CSV file
    recipients = []
    with open('backend/data/userdata.csv', mode='r') as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            recipients.append(row['Email'])

    # Load email subject and body from the CSV file
    with open('backend/data/notification/rainfallwarning.csv', mode='r') as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            subject = row['subject']
            body = row['body']

    # Email sender details


    # Send email to each recipient
    for recipient in recipients:
        msg = MIMEMultipart()
        msg.attach(MIMEText(body, 'html'))
        msg['Subject'] = subject
        msg['From'] = sender
        msg['To'] = recipient
        try:
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp_server:
                smtp_server.login(sender, password)
                smtp_server.sendmail(sender, recipient, msg.as_string())
            print(f"Message sent to {recipient}")
        except Exception as e:
            print(f"Failed to send email to {recipient}: {str(e)}")

    return "Emails sent successfully!"


# Route for admin_access.html
@app.route ('/admin_access.html')
def admin_access():
    return render_template('admin_access.html')

if __name__ == '__main__':
    app.run(debug=True)
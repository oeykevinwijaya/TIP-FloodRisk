import csv
import os
import mysql.connector
import joblib
import requests
import smtplib
import pandas as pd
import os

from flask import Flask, render_template, jsonify, request, redirect, url_for
from backend.services.dbconnect import insert_notification_preferences
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from sentence_transformers import SentenceTransformer, util

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

@app.route('/updateResult', methods=['POST'])
def update_result():
    data = request.get_json()
    probability = data.get('probability')
    rainfall = data.get('rainfall')
    message = data.get('message')

    with open('backend/data/currentprediction.csv', mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([message])

    return 'Result updated successfully'

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
@app.route("/")
def index():
    # Path to CSV file for 9-day forecast
    csv_file_path_forecast = os.path.join(os.getcwd(), "backend/data/9dforecast.csv")

    # List to hold rows of data for 9-day forecast
    forecasts = []

    # Read CSV data for 9-day forecast
    with open(csv_file_path_forecast, mode="r") as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            forecasts.append(row)

    # Path to CSV file for current prediction
    csv_file_path_prediction = os.path.join(os.getcwd(), "backend/data/currentprediction.csv")

    # Read CSV data for current prediction
    with open(csv_file_path_prediction, mode="r") as file:
        csv_reader = csv.reader(file)
        # Assuming there is only one line in the CSV file
        message = next(csv_reader)[0]

    # Pass data to the template
    return render_template("weather_forecast.html", forecasts=forecasts, message=message)


# Route for weather forecast page
@app.route("/weather_forecast.html")
def weatherforecast():
    # Path to CSV file for 9-day forecast
    csv_file_path_forecast = os.path.join(os.getcwd(), "backend/data/9dforecast.csv")

    # List to hold rows of data for 9-day forecast
    forecasts = []

    # Read CSV data for 9-day forecast
    with open(csv_file_path_forecast, mode="r") as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            forecasts.append(row)

    # Path to CSV file for current prediction
    csv_file_path_prediction = os.path.join(os.getcwd(), "backend/data/currentprediction.csv")

    # Read CSV data for current prediction
    with open(csv_file_path_prediction, mode="r") as file:
        csv_reader = csv.reader(file)
        # Assuming there is only one line in the CSV file
        message = next(csv_reader)[0]

    # Pass data to the template
    return render_template("weather_forecast.html", forecasts=forecasts, message=message)

# Route for weather forecast page
@app.route("/admin_weather_forecast.html")
def adminweatherforecast():
    # Path to CSV file for 9-day forecast
    csv_file_path_forecast = os.path.join(os.getcwd(), "backend/data/9dforecast.csv")

    # List to hold rows of data for 9-day forecast
    forecasts = []

    # Read CSV data for 9-day forecast
    with open(csv_file_path_forecast, mode="r") as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            forecasts.append(row)

    # Path to CSV file for current prediction
    csv_file_path_prediction = os.path.join(os.getcwd(), "backend/data/currentprediction.csv")

    # Read CSV data for current prediction
    with open(csv_file_path_prediction, mode="r") as file:
        csv_reader = csv.reader(file)
        # Assuming there is only one line in the CSV file
        message = next(csv_reader)[0]

    # Pass data to the template
    return render_template("admin_weather_forecast.html", forecasts=forecasts, message=message)


# Route for history.html
@app.route("/history.html")
def history():
    # Extract query parameters
    selected_location = request.args.get(
        "location", "cheung_chau"
    )  # Default to 'cheung_chau' if not provided
    selected_year = request.args.get("year", "2022")  # Set initial value for year
    selected_month = request.args.get("month", "1")  # Set initial value for month

    # Construct CSV file path based on selected location
    csv_file_path = os.path.join(
        os.getcwd(), f"backend/data/Daily Rainfall/{selected_location}.csv"
    )

    # Check if the file exists
    if not os.path.exists(csv_file_path):
        return f"CSV file not found: {csv_file_path}"

    # List to hold rows of data
    forecasts = []

    # Read CSV data
    try:
        with open(csv_file_path, mode="r", encoding="utf-8-sig") as file:
            csv_reader = csv.DictReader(file)
            for row in csv_reader:
                # Remove BOM from keys
                row = {key.strip("\ufeff"): value for key, value in row.items()}
                forecasts.append(row)
    except Exception as e:
        return f"Error reading CSV file: {str(e)}"

    # Filter data based on query parameters
    filtered_forecasts = [
        forecast
        for forecast in forecasts
        if forecast["Month"] == selected_month and forecast["Year"] == selected_year
    ]

    # Pass data to the template
    return render_template(
        "history.html",
        forecasts=filtered_forecasts,
        selected_year=selected_year,
        selected_month=selected_month,
    )


@app.route("/history.html")
def historyh():
    # Extract query parameters
    selected_location = request.args.get(
        "location", "cheung_chau"
    )  # Default to 'cheung_chau' if not provided
    selected_year = request.args.get("year", "2022")  # Set initial value for year
    selected_month = request.args.get("month", "1")  # Set initial value for month

    # Construct CSV file path based on selected location
    csv_file_path = os.path.join(
        os.getcwd(), f"backend/data/Daily Rainfall/{selected_location}.csv"
    )

    # Check if the file exists
    if not os.path.exists(csv_file_path):
        return f"CSV file not found: {csv_file_path}"

    # List to hold rows of data
    forecasts = []

    # Read CSV data
    try:
        with open(csv_file_path, mode="r", encoding="utf-8-sig") as file:
            csv_reader = csv.DictReader(file)
            for row in csv_reader:
                # Remove BOM from keys
                row = {key.strip("\ufeff"): value for key, value in row.items()}
                forecasts.append(row)
    except Exception as e:
        return f"Error reading CSV file: {str(e)}"

    # Filter data based on query parameters
    filtered_forecasts = [
        forecast
        for forecast in forecasts
        if forecast["Month"] == selected_month and forecast["Year"] == selected_year
    ]

    # Pass data to the template
    return render_template(
        "history.html",
        forecasts=filtered_forecasts,
        selected_year=selected_year,
        selected_month=selected_month,
    )


@app.route("/get_rainfall_data")
def get_rainfall_data():
    selected_location = request.args.get("location", "cheung_chau")
    selected_year = request.args.get("year", "2023")
    selected_month = request.args.get("month", "1")

    # Construct the CSV file path based on the selected location
    csv_file_path = os.path.join(
        os.getcwd(), f"backend/data/Daily Rainfall/{selected_location}.csv"
    )

    if not os.path.exists(csv_file_path):
        return jsonify({"error": f"CSV file not found: {csv_file_path}"})

    forecasts = []
    try:
        with open(csv_file_path, mode="r", encoding="utf-8-sig") as file:
            csv_reader = csv.DictReader(file)
            for row in csv_reader:
                row = {key.strip("\ufeff"): value for key, value in row.items()}
                forecasts.append(row)
    except Exception as e:
        return jsonify({"error": f"Error reading CSV file: {str(e)}"})

    # Filter data based on query parameters
    filtered_forecasts = [
        forecast
        for forecast in forecasts
        if forecast["Month"] == selected_month and forecast["Year"] == selected_year
    ]

    # Prepare the chart data including Year, Month, Day, and Value
    chart_data = [
        {
            "YEAR": row["Year"],
            "MONTH": row["Month"],
            "DAY": row["Day"],
            "VALUE": row["Value"],
        }
        for row in filtered_forecasts
    ]

    return jsonify(chart_data)




@app.route("/search", methods=["POST"])
def search():
    # Load FAQ data
    faq_data = []
    faq_answers = []
    with open("backend/data/faq.csv", mode="r") as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            faq_data.append(row["question"])
            faq_answers.append(row["answer"])

    # Initialize the sentence transformer model
    model = SentenceTransformer("paraphrase-MiniLM-L6-v2")
    data = request.get_json()
    query = data["query"]
    query_embedding = model.encode(query)
    faq_embeddings = model.encode(faq_data)

    # Find the most similar FAQ question to the query
    similarity_scores = [
        util.pytorch_cos_sim(query_embedding, faq_embedding)
        for faq_embedding in faq_embeddings
    ]
    best_match_index = similarity_scores.index(max(similarity_scores))
    best_match_question = faq_data[best_match_index]
    best_match_answer = faq_answers[best_match_index]

    return {
        "query": query,
        "best_match_question": {
            "question": best_match_question,
            "answer": best_match_answer,
        },
    }


# Route for warning.html
@app.route('/warning.html')
def warning():
    # Read the rainplace.csv file
    rainplace_df = pd.read_csv('backend/data/rainplace.csv')
    
    # Extract coordinates and rainfall values
    coordinates = rainplace_df['coordinate'].tolist()
    rainfall_values = rainplace_df['Rainfall (mm)'].tolist()
    
    # Pass data to the template
    return render_template('warning.html', coordinates=coordinates, rainfall_values=rainfall_values)
    
# Route for faq.html
@app.route("/faq.html")
def faq():
    faq_data = []
    with open("backend/data/faq.csv", mode="r") as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            faq_data.append({"question": row["question"], "answer": row["answer"]})

    return render_template("faq.html", faq_data=faq_data)


# Route for noti.html
@app.route("/noti.html")
def noti():
    return render_template("noti.html")


# Route to handle form submission
@app.route("/submit_preferences", methods=["POST"])
def submit_preferences():
    location = request.form["location"]
    name = request.form["name"]
    email = request.form["email"]
    rainfall = "rainfall" in request.form
    flood = "flood" in request.form

    # Create CSV file if it doesn't exist
    if not os.path.exists(data_file_path):
        with open(data_file_path, mode="w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(
                ["Location", "Name", "Email", "Rainfall Alert", "Flood Alert"]
            )

    # Append new preferences to the CSV file
    with open(data_file_path, mode="a", newline="") as file:
        writer = csv.writer(file)
        writer.writerow([location, name, email, rainfall, flood])

    return render_template("noti.html", success=True)


# Route for contact.html
@app.route("/contact.html")
def contact():
    return render_template("contact.html")


# Route for email.html
@app.route("/email.html")
def email():
    return render_template("email.html")


# Route for data_management.html
@app.route("/data_management.html")
def data_management():
    return render_template("data_management.html")


# Route for admin_page_alert.html
@app.route("/admin_page_alert.html")
def admin_page_alert():
    # Read data from the CSV file
    data = []
    if os.path.exists(data_file_path):
        with open(data_file_path, mode="r") as file:
            csv_reader = csv.DictReader(file)
            for row in csv_reader:
                data.append(row)

    return render_template("admin_page_alert.html", data=data)


@app.route("/send_notification", methods=["POST"])
def send_notification():
    # Load the recipient email addresses from the CSV file
    recipients = []
    with open("backend/data/userdata.csv", mode="r") as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            recipients.append(row["Email"])

    # Load email subject and body from the CSV file
    with open("backend/data/notification/emaildata.csv", mode="r") as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            subject = row["subject"]
            body = row["body"]

    # Append the forecast table to the email body
    with open("backend/data/9dforecast.csv", mode="r") as file:
        csv_reader = csv.DictReader(file)
        table = '<br><br><table border="1">'
        table += (
            "<tr>"
            + "".join(f"<th>{key}</th>" for key in csv_reader.fieldnames)
            + "</tr>"
        )
        for row in csv_reader:
            table += (
                "<tr>"
                + "".join(f"<td>{value}</td>" for value in row.values())
                + "</tr>"
            )
        table += "</table>"
        body += table

    # Email sender details
    sender = "@gmail.com"
    password = "insert key here"

    # Send email to each recipient
    for recipient in recipients:
        msg = MIMEMultipart()
        msg.attach(MIMEText(body, "html"))
        msg["Subject"] = subject
        msg["From"] = sender
        msg["To"] = recipient
        try:
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp_server:
                smtp_server.login(sender, password)
                smtp_server.sendmail(sender, recipient, msg.as_string())
            print(f"Message sent to {recipient}")
        except Exception as e:
            print(f"Failed to send email to {recipient}: {str(e)}")

    return "Emails sent successfully!"


# Route for send_alert
@app.route("/send_alert_amber", methods=["POST"])
def send_alert_amber():
    # Load the recipient email addresses from the CSV file
    recipients = []
    with open("backend/data/userdata.csv", mode="r") as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            recipients.append(row["Email"])

    # Load email subject and body from the CSV file
    with open("backend/data/notification/amberwarning.csv", mode="r") as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            subject = row["subject"]
            body = row["body"]

    # Email sender details
    sender = "@gmail.com"
    password = "insert key here"

    # Send email to each recipient
    for recipient in recipients:
        msg = MIMEMultipart()
        msg.attach(MIMEText(body, "html"))
        msg["Subject"] = subject
        msg["From"] = sender
        msg["To"] = recipient
        try:
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp_server:
                smtp_server.login(sender, password)
                smtp_server.sendmail(sender, recipient, msg.as_string())
            print(f"Message sent to {recipient}")
        except Exception as e:
            print(f"Failed to send email to {recipient}: {str(e)}")

    return "Emails sent successfully!"

# Route for send_alert
@app.route("/send_alert_red", methods=["POST"])
def send_alert_red():
    # Load the recipient email addresses from the CSV file
    recipients = []
    with open("backend/data/userdata.csv", mode="r") as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            recipients.append(row["Email"])

    # Load email subject and body from the CSV file
    with open("backend/data/notification/redwarning.csv", mode="r") as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            subject = row["subject"]
            body = row["body"]

    # Email sender details
    sender = "@gmail.com"
    password = "insert key here"

    # Send email to each recipient
    for recipient in recipients:
        msg = MIMEMultipart()
        msg.attach(MIMEText(body, "html"))
        msg["Subject"] = subject
        msg["From"] = sender
        msg["To"] = recipient
        try:
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp_server:
                smtp_server.login(sender, password)
                smtp_server.sendmail(sender, recipient, msg.as_string())
            print(f"Message sent to {recipient}")
        except Exception as e:
            print(f"Failed to send email to {recipient}: {str(e)}")

    return "Emails sent successfully!"

# Route for send_alert
@app.route("/send_alert_black", methods=["POST"])
def send_alert_black():
    # Load the recipient email addresses from the CSV file
    recipients = []
    with open("backend/data/userdata.csv", mode="r") as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            recipients.append(row["Email"])

    # Load email subject and body from the CSV file
    with open("backend/data/notification/blackwarning.csv", mode="r") as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            subject = row["subject"]
            body = row["body"]

    # Email sender details
    sender = "@gmail.com"
    password = "insert key here"

    # Send email to each recipient
    for recipient in recipients:
        msg = MIMEMultipart()
        msg.attach(MIMEText(body, "html"))
        msg["Subject"] = subject
        msg["From"] = sender
        msg["To"] = recipient
        try:
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp_server:
                smtp_server.login(sender, password)
                smtp_server.sendmail(sender, recipient, msg.as_string())
            print(f"Message sent to {recipient}")
        except Exception as e:
            print(f"Failed to send email to {recipient}: {str(e)}")

    return "Emails sent successfully!"


# Route for admin_access.html
@app.route("/admin_access.html", methods=["GET", "POST"])
def admin_access():
    if request.method == "POST":
        # Extract username and password from form
        username = request.form.get("username")
        password = request.form.get("password")

        # Simple validation for demonstration purposes
        if username == "admin" and password == "password":
            return admin_page_alert()
        else:
            return render_template(
                "loginadmin.html", error="Invalid username or password"
            )

    return admin_page_alert()


@app.route("/loginadmin.html")
def admin_login():
    return render_template("loginadmin.html")


# Route for admin_file.html
@app.route("/admin_file", methods=["GET", "POST"])
def file_manager():
    if request.method == "POST" and "file" in request.files:
        file = request.files["file"]
        if file.filename != "":
            filepath = os.path.join("backend/data", file.filename)
            file.save(filepath)
            return redirect(url_for("file_manager"))
    files = os.listdir("backend/data")
    return render_template("admin_file.html", files=files)


# Route for admin_file.html/ delete_file
@app.route("/delete_file", methods=["POST"])
def delete_file():
    filename = request.form["filename"]
    file_path = os.path.join("backend/data", filename)
    if os.path.exists(file_path):
        os.remove(file_path)
    return redirect(url_for("file_manager"))


def load_data():
    if os.path.exists("backend/data/faq.csv"):
        return pd.read_csv("backend/data/faq.csv")
    else:
        return pd.DataFrame(columns=["question", "answer"])


def save_data(df):
    df.to_csv("backend/data/faq.csv", index=False)


# Route for admin_faq.html
@app.route("/admin_faq", methods=["GET"])
def admin():
    df = load_data()
    return render_template("admin_faq.html", faqs=df.to_dict(orient="records"))


# Route for admin_faq.html / search_faq
@app.route("/search_faq", methods=["GET"])
def search_faq():
    query = request.args.get("query", "")
    df = load_data()
    if query:
        df = df[
            df["question"].str.contains(query, case=False)
            | df["answer"].str.contains(query, case=False)
        ]
    return render_template("admin_faq.html", faqs=df.to_dict(orient="records"))


# Route for admin_faq.html / add_faq
@app.route("/add_faq", methods=["POST"])
def add_faq():
    df = load_data()
    new_faq = pd.DataFrame(
        {"question": [request.form["question"]], "answer": [request.form["answer"]]}
    )
    df = pd.concat([df, new_faq], ignore_index=True)
    save_data(df)
    return redirect(url_for("admin"))


# Route for admin_faq.html / update_faq
@app.route("/update_faq", methods=["POST"])
def update_faq():
    df = load_data()
    row_id = int(request.form["id"])
    if row_id < len(df):
        df.at[row_id, "question"] = request.form["question"]
        df.at[row_id, "answer"] = request.form["answer"]
        save_data(df)
    return redirect(url_for("admin"))


# Route for admin_faq.html / delete_faq
@app.route("/delete_faq", methods=["POST"])
def delete_faq():
    df = load_data()
    row_id = int(request.form["id"])
    if row_id < len(df):
        df = df.drop(row_id).reset_index(drop=True)
        save_data(df)
    return redirect(url_for("admin"))


if __name__ == "__main__":
    app.run(debug=True)


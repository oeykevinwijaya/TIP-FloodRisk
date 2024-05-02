import requests
import json
import csv

# Fetch JSON data from the API
url = "https://data.weather.gov.hk/weatherAPI/opendata/weather.php?dataType=fnd&lang=en"
response = requests.get(url)
data = response.json()

# Extract weather forecast data
forecast_data = data["weatherForecast"]

# Define CSV file path
csv_file_path = "backend/data/9dforecast.csv"

# Write data to CSV
with open(csv_file_path, mode='w', newline='') as file:
    writer = csv.writer(file)
    
    # Write header
    writer.writerow(["Date", "Day", "Max Temp (°C)", "Min Temp (°C)", "Max RH (%)", "Min RH (%)", "Weather"])
    
    # Write forecast data
    for forecast in forecast_data:
        date = forecast["forecastDate"]
        day = forecast["week"]
        max_temp = forecast["forecastMaxtemp"]["value"]
        min_temp = forecast["forecastMintemp"]["value"]
        max_rh = forecast["forecastMaxrh"]["value"]
        min_rh = forecast["forecastMinrh"]["value"]
        weather = forecast["forecastWeather"]
        
        writer.writerow([date, day, max_temp, min_temp, max_rh, min_rh, weather])

print("CSV file saved successfully at:", csv_file_path)

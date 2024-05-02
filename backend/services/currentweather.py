import requests
import json
import csv

# Fetch JSON data from the API
url = "https://data.weather.gov.hk/weatherAPI/opendata/weather.php?dataType=rhrread&lang=en"
response = requests.get(url)
data = response.json()

# Extract rainfall data
rainfall_data = data["rainfall"]["data"]

# Extract temperature data
temperature_data = data["temperature"]["data"]

# Define CSV file paths
rainfall_csv_file = "backend/data/currentrain.csv"
temperature_csv_file = "backend/data/currenttemp.csv"

# Write rainfall data to CSV
with open(rainfall_csv_file, mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(["Place", "Rainfall (mm)", "Main"])
    for entry in rainfall_data:
        place = entry["place"]
        rainfall = entry["max"]
        main = entry["main"]
        writer.writerow([place, rainfall, main])

# Write temperature data to CSV
with open(temperature_csv_file, mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(["Place", "Temperature (°C)"])
    for entry in temperature_data:
        place = entry["place"]
        temperature = entry["value"]
        writer.writerow([place, temperature])

print("Rainfall data saved successfully at:", rainfall_csv_file)
print("Temperature data saved successfully at:", temperature_csv_file)

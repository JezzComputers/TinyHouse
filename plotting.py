import requests
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime, timedelta

# Constants
API_KEY = 'your_api_key'  # Replace with your OpenWeatherMap API Key
CITY = 'your_city'  # Replace with your city
BASE_URL = 'http://api.openweathermap.org/data/2.5/weather'
INSULATION_FACTOR = 0.1  # Adjust based on insulation properties

def get_weather_data():
    params = {
        'q': CITY,
        'appid': API_KEY,
        'units': 'metric'
    }
    response = requests.get(BASE_URL, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        print("Error fetching weather data")
        return None

def predict_internal_temperature(outside_temp):
    return outside_temp - INSULATION_FACTOR * (outside_temp - 20)  # Example formula

def main():
    weather_data = get_weather_data()
    if weather_data is None:
        return

    # Extract outside temperature
    outside_temp = weather_data['main']['temp']
    print(f"Current Outside Temperature: {outside_temp}°C")

    # Get the current time
    current_time = datetime.now()
    time_points = []
    outside_temps = []
    internal_temps = []

    # Simulate for the rest of the day
    for hour in range(1, 25):  # Simulate for the next 24 hours
        future_time = current_time + timedelta(hours=hour)
        time_points.append(future_time.strftime("%H:%M"))
        outside_temps.append(outside_temp)  # Placeholder, replace with actual forecast data
        internal_temp = predict_internal_temperature(outside_temp)
        internal_temps.append(internal_temp)

    # Plotting
    plt.figure(figsize=(10, 5))
    plt.plot(time_points, outside_temps, label='Outside Temperature (°C)', marker='o')
    plt.plot(time_points, internal_temps, label='Predicted Internal Temperature (°C)', marker='x')
    
    # Simulated actual recorded temperatures (replace with real data if available)
    actual_recorded_temps = [outside_temp + np.random.uniform(-1, 1) for _ in range(24)]
    plt.plot(time_points, actual_recorded_temps, label='Actual Recorded Temperature (°C)', marker='s', linestyle='--')

    plt.title('Temperature Prediction and Recorded Data')
    plt.xlabel('Time')
    plt.ylabel('Temperature (°C)')
    plt.xticks(rotation=45)
    plt.legend()
    plt.grid()
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    main()
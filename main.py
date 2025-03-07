import json, onewire, ds18x20
from os import stat
from utime import sleep
from machine import Pin, reset
from urequests import get, post
from network import WLAN, STA_IF
from PiicoDev_TMP117 import PiicoDev_TMP117

# Initialize pins for controlling power and the on-board LED
DONE = Pin(22, Pin.OUT)
LED = Pin("LED", Pin.OUT); LED.off()

# Initialize temperature sensors
tempSensor = PiicoDev_TMP117(asw=[1, 0, 0, 0])
onewire_sensor = ds18x20.DS18X20(onewire.OneWire(Pin(28)))
onewire_sensor2 = ds18x20.DS18X20(onewire.OneWire(Pin(12)))
onewire_scan = [onewire_sensor.scan(), onewire_sensor2.scan()]

# Setup WLAN
wlan = WLAN(STA_IF)
wlan.active(True)

# Initialize the time dictionary
time = {}

# Function to set the current time
def setTime():
    try:
        print("Fetching time from API...")
        response = get("https://dweet.io/get/latest/dweet/for/TinyHouseTime")
        if response.status_code == 200:
            data = response.json()["with"][0]["content"]
            print(data)
            time.update({
                "Date": f"{data['date']}/{data['month']}/{data['year']}",
                "Hour": (data['hour'] if data['hour'] <= 12 else data['hour'] - 12),
                "AM/PM": "PM" if data['hour'] > 12 else "AM",
                "Minute": data['minute'],
                "Second": data['second']
            })
            response.close()
            print("Time successfully set.")
            return time
        else:
            log_error("Time Fetching Error", f"Status code: {response.status_code}")
            print(f"Failed to fetch time.")
    except Exception as e:
        log_error("Time Fetching Error", str(e))
        print(f"Failed to fetch time.")

# Function to read the file content, optionally returning the last line
def getFileContent(filename, last_line=False):
    try:
        file_size = stat(filename)[6]
        if file_size == 0:
            return None
        with open(filename) as f:
            return f.readlines()[-1].strip() if last_line else f.read()
    except OSError:
        return False

# Function to connect to WiFi network
def connect_to_wifi():
    wlan.connect("TechGuest", "techschool")
    for _ in range(21):
        if wlan.isconnected():
            print('Network config:', wlan.ifconfig())
            return
        print('Waiting for connection...')
        sleep(1)
    log_error("WiFi Connection Error", "Timeout")
    DONE.on()

# Function to log errors with a timestamp
def log_error(context, exception):
    error_message = f'({context} at time: {time}) Containing: {exception}'
    print("ERROR:", error_message)
    with open("time.txt", "w") as t, open("errors.txt", "a") as f:
        t.write(f'Error time: {time}')
        f.write(error_message + '\n')

# Function to get temperature data based on sensor index
def getData(whichOne):
    if whichOne == 0:
        onewire_sensor.convert_temp()
        sleep(1)
        return onewire_sensor.read_temp(onewire_scan[0][0])
    elif whichOne == 1:
        return tempSensor.readTempC()
    elif whichOne == 2:
        onewire_sensor2.convert_temp()
        sleep(1)
        return onewire_sensor2.read_temp(onewire_scan[1][0])
    else:
        log_error("getData Error", f"incorrect input: {whichOne}")
        return None

# Function to post data to a remote server
def postData():
    data = {
        'outdoor_temp': getData(0),
        'in_house_temp': getData(2),
        'cont_box_temp': tempSensor.readTempC(),
        'timestamp': str(time),
        'last_error_time': getFileContent("time.txt"),
        'last_error': getFileContent("errors.txt", True)
    }
    headers = {'Content-Type': 'application/json'}
    try:
        response = post('https://dweet.io/dweet/for/TinyHouse', data=json.dumps(data), headers=headers)
        out = response.text
        response.close()
        return out
    except Exception as e:
        log_error("Posting Error", str(e))
        return None

# Function to post status updates
def postStatus(status):
    try:
        response = post(f'https://dweet.io/dweet/for/TinyHouseStatus?status={status}')
        response.close()
    except Exception as e:
        log_error("Status Posting Error", str(e))

# Function to wait for status change
def waitForStatusChange(target_status, timeout=60):
    for _ in range(timeout):
        try:
            response = get("https://dweet.io/get/latest/dweet/for/TinyHouseStatus")
            if response.status_code == 200:
                current_status = response.json()["with"][0]["content"]["status"]
                response.close()
                if current_status == target_status:
                    return True
            sleep(1)
        except Exception as e:
            log_error("Status Fetching Error", str(e))
    return False

# Main execution block
try:
    connect_to_wifi()  # Connect to WiFi
    LED.on()  # Turn on the LED to indicate activity
    postStatus("afterTime")  # Post status update
    print('Waiting for status change to timeReady...')
    if waitForStatusChange("timeReady"):
        print('Getting time...')
        setTime()  # Sync time dict with online time
    else:
        print('Timeout waiting for status change, getting time anyway...')
        setTime()  # Sync time dict with online time
    print('Starting data posting...')
    print(postData())  # Post temperature data
    LED.off()  # Turn off the LED after completing data posting
    DONE.on()  # Set DONE pin high to remove power
except Exception as e:
    log_error("Main Execution Error", str(e))
    LED.off()
    DONE.on()  # Set DONE pin high to remove power
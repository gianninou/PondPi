
import Adafruit_DHT
import logging
import RPi.GPIO as GPIO

logger = logging.getLogger('PondPiLog')

WIRE_DIR = "/sys/bus/w1/devices/{}/w1_slave"


# Return the temperature
def get_temp_1w(sensor_id):
    logger.debug("Get temp from 1WIRE {}".format(sensor_id))
    sensor_path = WIRE_DIR.format(sensor_id)
    try:
        with open(sensor_path) as sensor_file:
            sensor_data = sensor_file.read()
            sensor_temp_raw = sensor_data.split("\n")[1].split(" ")[9]
            return float(sensor_temp_raw[2:]) / 1000
    except:
        logger.error("1WIRE {} sensor not found".format(sensor_id))
        return None


# Return the temperature and the humidity
def get_DHT22_values(pin):
    logger.debug("Get temp from PIN {}".format(pin))
    try:
        humidity, temperature = Adafruit_DHT.read_retry(Adafruit_DHT.DHT22, pin)
        return int(temperature), int(humidity)
    except RuntimeError:
        logger.error("Get DHT22 error")
        return None
    except Exception:
        logger.error("Get DHT22 exception")
        return None


# Return True if the level is good. False if there is no more water
def get_water_level_status(pin):
    logger.debug("Get water level from PIN {}".format(pin))
    if GPIO.input(pin) == GPIO.HIGH:
        return True
    else:
        return False

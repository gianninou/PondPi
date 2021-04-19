
import RPi.GPIO as GPIO
import logging

logger = logging.getLogger('PondPiLog')

def setup_pin(pin, mode):
    GPIO.setup(pin, mode)

def set_value(pin, status):
    logger.debug("GPIO SET {} for PIN {}".format(status, pin))
    GPIO.output(pin, status)

def get_value(pin):
    value = GPIO.input(pin)
    logger.debug("Get value PIN {} : {}".format(pin, value))
    return value

import argparse
import sys
import time
import random
import logging
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from waveshare_epd import epd2in13_V2
from PIL import Image,ImageDraw,ImageFont
import RPi.GPIO as GPIO
from utils.mails import send_mail

logger = logging.getLogger('PondPiLog')
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s :: %(levelname)s :: %(message)s')
file_handler = RotatingFileHandler('activity.log', 'a', 10000000, 10)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


grapher = logging.getLogger('PondPiGraph')
grapher.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s:%(message)s')
graph_handler = TimedRotatingFileHandler('graph.log', "d", 1, 365)
graph_handler.setLevel(logging.INFO)
graph_handler.setFormatter(formatter)
grapher.addHandler(graph_handler)


font20 = ImageFont.truetype('Font.ttc', 20)

BLACK=0
WHITE=255

PIN_PUMP1 = 27
PIN_PUMP2 = 23
PIN_UV = 25

epd = epd2in13_V2.EPD()

EMAIL_RECIPIENT = "valentin.giannini@gmail.com"

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(PIN_PUMP1, GPIO.OUT)
GPIO.setup(PIN_PUMP2, GPIO.OUT)
GPIO.setup(PIN_UV, GPIO.OUT)

class PondPi:

    temp1 = temp2 = temp_air = moisture = pump1 = pump2 = UV = water_level = 0

    def update_screen(self):
        epd.init(epd.FULL_UPDATE)
        time_image = Image.new('1', (epd.height, epd.width), 255)
        time_draw = ImageDraw.Draw(time_image)
        epd.displayPartBaseImage(epd.getbuffer(time_image))
        epd.init(epd.PART_UPDATE)

        time_draw.rectangle((0, 0, 240, 120), fill=WHITE)
        time_draw.text((0, 10), "Temp1: {}°".format(self.temp1), font=font20, fill=BLACK)
        time_draw.text((125, 10), "Air: {}°".format(self.temp_air), font=font20, fill=BLACK)

        time_draw.text((0, 35), "Temp2: {}°".format(self.temp2), font=font20, fill=BLACK)
        time_draw.text((125, 35), "Hum: {}%".format(self.moisture), font=font20, fill=BLACK)

        time_draw.line([(0,62),(240,62)], fill = 0,width = 1)

        time_draw.text((0, 65), "Pump 1: {}  ".format(("ON" if self.pump1 else "OFF")), font=font20, fill=BLACK)
        time_draw.text((125, 65), "UV: {}  ".format(("ON" if self.UV else "OFF")), font=font20, fill=BLACK)

        time_draw.text((0, 90), "Pump 2: {}  ".format(("ON" if self.pump2 else "OFF")), font=font20, fill=BLACK)
        time_draw.text((125, 90), "Water: {}".format(("HIGH" if self.water_level else "LOW")), font=font20, fill=BLACK)
        if not self.water_level:
            time_draw.rectangle([(185, 88), (240, 115)], width=3)
        epd.displayPartial(epd.getbuffer(time_image))

    def get_values(self):
        # Get from captors
        self.temp1 = random.randint(10, 14)
        self.temp2 = random.randint(10, 14)
        self.temp_air = random.randint(20, 25)
        self.moisture = random.randint(20, 90)
        # Get from GPIO
        self.pump1 = get_GPIO(PIN_PUMP1)
        self.pump2 = get_GPIO(PIN_PUMP2)
        self.UV = get_GPIO(PIN_UV)
        # Get from captor
        self.water_level = False if random.randint(0, 1)==0 else True
        grapher.info("{},{},{},{},{},{},{},{}".format(self.temp1, self.temp2, self.temp_air, self.moisture, self.pump1, self.pump2, self.UV, self.water_level))

    def cut_pumps(self):
        logger.info('WATER LOW -> Cut pumps')
        self.pump1 = False
        self.pump2 = False
        self.UV = False
        send_mail(EMAIL_RECIPIENT)


    def process_values(self):
        if not self.water_level:
            self.cut_pumps()

    def set_values(self, pump1, pump2, UV):
        if pump1:
            logger.info("SET : pump1 -> {}".format(pump1))
            self.pump1 = True if pump1=="ON" else False
            set_GPIO(PIN_PUMP1, self.pump1)
        if pump2:
            logger.info("SET : pump2 -> {}".format(pump2))
            self.pump2 = True if pump2=="ON" else False
            set_GPIO(PIN_PUMP2, self.pump2)
        if UV:
            logger.info("SET : UV -> {}".format(UV))
            self.UV = True if UV=="ON" else Fals
            set_GPIO(PIN_UV, self.UV)


def set_GPIO(pin, status):
    print("Set {} for PIN {}".format(status, pin))
    logger.debug("GPIO SET {} for PIN {}".format(status, pin))
    GPIO.output(pin, status)

def get_GPIO(pin):
    value = GPIO.input(pin)
    logger.debug("Get value PIN {} : {}".format(pin, value))
    return value

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    #group_action = parser.add_mutually_exclusive_group()

    subs = parser.add_subparsers()
    subs.required = True
    subs.dest = 'action'
    cron_parser = subs.add_parser('cron', help='Run the cron process')
    clear_parser = subs.add_parser('clear', help='Clear screen')
    manage_parser = subs.add_parser('manage', help='Manage Pumps and UV')
    manage_parser.add_argument('--pump1', help='Manage pump1',required=False, choices=["ON", "OFF"])
    manage_parser.add_argument('--pump2', help='Manage pump2',required=False, choices=["ON", "OFF"])
    manage_parser.add_argument('--UV', help='Manage UV',required=False, choices=["ON", "OFF"])

    args = parser.parse_args()

    pp = PondPi()

    if args.action == "cron":
        # cron: each 30s
        pp.get_values()
        pp.process_values()
        pp.update_screen()

    if args.action == "clear":
        # cron each 1h
        epd.init(epd.FULL_UPDATE)
        epd.Clear(0xFF)

    if args.action == "manage":
        # Manual
        ## Change pump/UV state
        print(args.pump1, args.pump2, args.UV)
        pp.set_values(args.pump1, args.pump2, args.UV)

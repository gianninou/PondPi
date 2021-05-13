
import RPi.GPIO as GPIO

import argparse
import logging
import os
import sys
import yaml


from datetime import datetime, timedelta
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from functools import reduce

import utils.mails
import utils.sensors
import utils.relays
import utils.camera
import utils.ftp


GPIO.setwarnings(False)  # Ignore warning for now
GPIO.setmode(GPIO.BCM)

#######################################
# YAML CONFIG FILE LOADING
#######################################

yaml_file = open("conf/conf.yml", 'r')
yaml_content = yaml.safe_load(yaml_file)

#######################################
# LOGGER DEFINITION
#######################################

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

#######################################
# GET MAIL CONTANTS
#######################################

MAIL_HOST = yaml_content.get("mail").get("host")
MAIL_PORT = yaml_content.get("mail").get("port")
MAIL_USER = yaml_content.get("mail").get("user")
MAIL_PASSWORD = yaml_content.get("mail").get("password")
MAIL_RECIPIENTS = yaml_content.get("mail").get("recipients")

BACKUP_FILE = yaml_content.get("global").get("BACKUP_FILE")
ALERT_FILE = yaml_content.get("global").get("ALERT_FILE")
ALERT_FILE_HISTORY = yaml_content.get("global").get("ALERT_FILE_HISTORY")

#######################################
# PondPi class
#######################################


class PondPi:

    relays = None
    sensors = None

    def __init__(self, sensors, relays):
        """Initialize the object with a list of sensors and a list of relays"""
        self.sensors = sensors
        self.relays = relays

    @staticmethod
    def load_from_yaml(yaml_content):
        """ Create a PondPi object from the conf YAML file """
        relays = []
        sensors = []
        for relay in yaml_content.get('relays'):
            if "name" in relay and "pin" in relay and "type" in relay:
                relays.append(relay)
            else:
                logger.error("Wrong relay declaration : '{}'".format(relays))
                sys.exit(0)

        for sensor in yaml_content.get('sensors'):
            if "type" in sensor:
                if sensor.get("type") == "dht22":
                    if "name" in sensor and "pin" in sensor:
                        sensors.append(sensor)
                elif sensor.get("type") == "temp_1W":
                    if "name" in sensor and "uid" in sensor:
                        sensors.append(sensor)
                elif sensor.get("type") == "water_level":
                    if "pin" in sensor:
                        sensors.append(sensor)
                else:
                    logger.error("Unknow sensor type")
            else:
                logger.error("Sensor type not given")
        return PondPi(sensors, relays)

    def init_pin(self):
        """ Init the GPIO PIN with the IN/OUT mode for each sensors/relays """
        for sensor in self.sensors:
            if sensor.get("type") == "dht22":
                logger.debug("Set PIN {} IN : DHT22".format(sensor.get('pin')))
                GPIO.setup(sensor.get('pin'), GPIO.IN)
            elif sensor.get("type") == "temp_1W":
                # Nothing
                pass
            elif sensor.get("type") == "water_level":
                logger.debug("Set PIN {} IN : WaterLevel".format(sensor.get('pin')))
                GPIO.setup(sensor.get('pin'), GPIO.IN)

        # Get from relays
        for relay in self.relays:
            logger.debug("Set PIN {} OUT".format(relay.get('pin')))
            GPIO.setup(relay.get('pin'), GPIO.OUT)

    def get_values(self):
        """
        Get values from sensors and relay stats
        Display the value on log file and returns
        the line in order to be display for example
        """
        # Get from sensors
        values = []
        for sensor in self.sensors:
            if sensor.get("type") == "dht22":
                value = utils.sensors.get_DHT22_values(sensor.get('pin'))
                values.append({'name': sensor.get('name')+'_T', 'value': value[0]})
                values.append({'name': sensor.get('name')+'_H', 'value': value[1]})
            elif sensor.get("type") == "temp_1W":
                value = utils.sensors.get_temp_1w(sensor.get('uid'))
                values.append({'name': sensor.get('name'), 'value': value})
            elif sensor.get("type") == "water_level":
                value = utils.sensors.get_water_level_status(sensor.get('pin'))
                values.append({'name': 'WaterLevel', 'value': value})
        # Get from relays
        for relay in self.relays:
            value = utils.relays.get_value(relay.get('pin'))
            values.append({'name': relay.get('name'), 'value': value})
        # Get from captor
        log_line = ", ".join([v['name']+":"+str(v['value']) for v in values])
        grapher.info(log_line)
        logger.debug("Values : {}".format(log_line))
        return log_line

    def cut_pumps(self):
        """ Cut off all relay managing a pump """
        logger.info('WATER LOW -> Cut pumps')
        for r in self.relays:
            if r.get("type") == "pump":
                utils.relays.set_value(r.get("pin"), 0)
        self.generate_backup_file()

    def process_led(self, status):
        """
        Set the led status
        Green : All is Ok
        Red : The water level is low, normally the pump should be cut off
        Green + Red : Should not append for the moment
        """
        if status == "OK":
            for relay in self.relays:
                if relay.get("type").lower() == "led_ok":
                    self.set_value(relay.get("name"), "ON")
                if relay.get("type").lower() == "led_ko":
                    self.set_value(relay.get("name"), "OFF")
        elif status == "KO":
            for relay in self.relays:
                if relay.get("type").lower() == "led_ok":
                    self.set_value(relay.get("name"), "OFF")
                if relay.get("type").lower() == "led_ko":
                    self.set_value(relay.get("name"), "ON")
        else:
            for relay in self.relays:
                self.set_value(relay.get("name"), "ON")

    def process_values(self):
        """ Get the water level and cut the pump + send email if needed. Then update the led status """
        # Get only water_level sensor
        water_levels = [s for s in self.sensors if s.get("type") == "water_level"]
        # Do a "and" for all value, if one is to false -> water leakage.
        values = [utils.sensors.get_water_level_status(s.get('pin')) for s in water_levels]
        water_ok = reduce(lambda i, j: int(i) and int(j), values)
        if not water_ok:
            logger.info("Water not ok")
            if self.declare_alert():
                utils.mails.send_mail()
            self.cut_pumps()
            self.process_led("KO")
        else:
            self.process_led("OK")

    def declare_alert(self):
        """
        When it's called, that function create a ALERT_FILE with
        the time of the alert for the first time.
        If the file doeas not exists the function will return True
        in order to the caller to send the email for example.
        The date of the alert is also added into
        the ALERT_FILE_HISTORY in order to keep a trace.
        """
        res = False
        now = datetime.now()
        dt_string = now.strftime("%Y/%m/%d %H:%M:%S")
        if not os.path.isfile(ALERT_FILE):
            logger.info("Create alert file : {}".format(ALERT_FILE))
            res = True
            with open(ALERT_FILE, 'a') as f:
                f.write(dt_string+"\n")
        with open(ALERT_FILE_HISTORY, 'a+') as f:
            f.write(dt_string+"\n")
        return res

    def reset_alert(self, restart_all_pump=False):
        """
        Remove the ALERT_FILE file.
        If the restart_all_pump parameter is set to true, all the pump will be started.
        At the end, the process_value function is called.
        """
        logger.info("reset alert")
        if os.path.isfile(ALERT_FILE):
            os.remove(ALERT_FILE)
        if restart_all_pump:
            logger.info("Restart all pumps")
            for relay in self.relays:
                if relay.get("type") == "pump":
                    self.set_value(relay.get("name"), "ON")
        self.process_values()

    def set_value(self, name, status):
        """ Set a value to a relay, the status should be "ON" or "OFF". """
        status_bool = GPIO.HIGH if status == "ON" else GPIO.LOW
        for relay in self.relays:
            if relay.get("name") == name:
                utils.relays.set_value(relay.get("pin"), status_bool)
                self.generate_backup_file()
                return True
        logger.info("Name {} not found".format(name))
        return False

    def generate_backup_file(self, path=None):
        """
        Generate a backup file, in case of failure,
        that file could be used to restore the state of the PIN.
        """
        logger.info("Generate Backup file")
        if not path:
            path = BACKUP_FILE
        print(path)
        with open(path, "w+") as f:
            for r in self.relays:
                line = "{}:{}\n".format(r.get("name"),
                                        utils.relays.get_value(r.get("pin")))
                f.write(line)

    def restore_backup_file(self, path=None):
        """ Restore the state of PINs with the content of the backup file """
        logger.info("Restore from Backup file")
        if not path:
            path = BACKUP_FILE
        try:
            with open(path) as f:
                for line in f.readlines():
                    linestriped = line.strip()
                    name = linestriped.split(':')[0]
                    value = linestriped.split(':')[1]
                    for r in self.relays:
                        if r.get("name") == name:
                            print("{} : {} : {} : {}".format(name, r.get("pin"), value, GPIO.HIGH if value == "1" else GPIO.LOW))
                            utils.relays.set_value(r.get("pin"), GPIO.HIGH if value == "1" else GPIO.LOW)
        except IOError:
            logger.error("No Backup File found")


if __name__ == "__main__":

    # TODO check if reboot

    parser = argparse.ArgumentParser()
    subs = parser.add_subparsers()
    subs.required = True
    subs.dest = 'action'
    init_parser = subs.add_parser('init', help='Run the cron process')
    backup_parser = subs.add_parser('backup', help='Create the backup file')
    backup_parser.add_argument('--path', help='''Set the filepath name to use,
                               by default it will use the BACKUP_FILE
                               param in the conf file''',
                               required=False)
    restore_parser = subs.add_parser('restore', help='Restore from backup file')
    restore_parser.add_argument('--path', help='''Set the filepath name to use,
                                by default it will use the BACKUP_FILE
                                param in the conf file''',
                                required=False)
    cron_parser = subs.add_parser('cron', help='Clear screen')
    reset_parser = subs.add_parser('reset', help='Reset pump and alerts')
    print_parser = subs.add_parser('print', help='Clear screen')
    camera_parser = subs.add_parser('camera', help='Take pictures')
    camera_parser.add_argument('--capture', help='''Capture photo''',
                               required=False, action='store_true')
    camera_parser.add_argument('--ftp', help='''Enable send the picture to FTP''',
                               required=False, action='store_true')
    camera_parser.add_argument('--gif-yesterday', help='''Generate gif for yesterday''',
                               required=False, action='store_true')
    manage_parser = subs.add_parser('manage', help='Manage Pumps and UV')
    manage_parser.add_argument('--name', help='Select device by name',
                               required=True)
    manage_parser.add_argument('--status', help='set status to device',
                               required=True, choices=["ON", "OFF"])
    args = parser.parse_args()

    # Load the conf (list of relays and sensors) from the YAML file
    pp = PondPi.load_from_yaml(yaml_content)

    # Init the board (IN/OUT) for each pin
    pp.init_pin()

    # Create a backup file
    if args.action == "backup":
        # TODO: if a file is provided, take it as source.
        path = args.path
        pp.generate_backup_file(path)
        sys.exit(0)

    # Check if a backup file is present and restore pin relays status
    if args.action == "restore":
        # TODO: if a file is provided, take it as source.
        path = args.path
        pp.restore_backup_file(path)
        sys.exit(0)

    # Check water level, get values
    if args.action == "cron":
        pp.process_values()
        sys.exit(0)

    # Get values and print it
    if args.action == "print":
        values = pp.get_values()
        print(values)
        sys.exit(0)

    # Get values and print it
    if args.action == "camera":
        # Take picture
        if args.capture:
            filename = utils.camera.Camera.capture()
            if args.ftp:  # Store in FTP if needed
                if filename:
                    utils.ftp.FTP.send_file(filename)
                else:
                    print("FILENAME_NULL")
        # Generate yesterday gif
        if args.gif_yesterday:
            now = datetime.now() - timedelta(1)
            yesterday = now.strftime("%Y-%m-%d")
            gif_name = utils.camera.Camera.generate_gif(yesterday)
            if args.ftp:  # Store in FTP if needed
                if gif_name:
                    utils.ftp.FTP.send_file(gif_name)
                else:
                    print("GIFNAME_NULL")

        sys.exit(0)

    # enable pumps and remove alert file
    if args.action == "reset":
        pp.reset_alert(restart_all_pump=False)
        sys.exit(0)

    # Change status of relais
    if args.action == "manage":
        pp.set_value(args.name, args.status)
        sys.exit(0)

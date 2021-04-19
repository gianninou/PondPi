import logging
import os
import smtplib
import yaml

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from string import Template

logger = logging.getLogger('PondPiLog')

yaml_file = open("conf/conf.yml", 'r')
yaml_content = yaml.safe_load(yaml_file)

MAIL_HOST = yaml_content.get("mail").get("host")
MAIL_PORT = yaml_content.get("mail").get("port")
MAIL_USER = yaml_content.get("mail").get("user")
MAIL_PASSWORD = yaml_content.get("mail").get("password")
MAIL_RECIPIENTS = yaml_content.get("mail").get("recipients")


def read_template(filename):
    with open(filename, 'r', encoding='utf-8') as template_file:
        template_file_content = template_file.read()
    return Template(template_file_content)

def send_mail():
    try:
        s = smtplib.SMTP(host=MAIL_HOST, port=MAIL_PORT)
        s.starttls()
        s.login(MAIL_USER, MAIL_PASSWORD)
    except:
        logger.erro("Error sending email")
        return None

    msg = MIMEMultipart()
    mail_message_path = os.path.dirname(os.path.realpath(__file__))+"/../template/message.txt"
    message_template = read_template(mail_message_path)
    message = message_template.substitute()
    msg['From']=MAIL_USER
    msg['To']=", ".join(MAIL_RECIPIENTS)
    msg['Subject']="PondPi alert"
    # add in the message body
    msg.attach(MIMEText(message, 'plain'))
    # send the message via the server set up earlier.
    s.send_message(msg)
    logger.info("EMAIL send to {}".format(MAIL_RECIPIENTS))

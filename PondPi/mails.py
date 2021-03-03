import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from string import Template

s = smtplib.SMTP(host='SSL0.OVH.NET', port=587)
s.starttls()
s.login("valentin@gianninou.fr", "password")

def read_template(filename):
    """
    Returns a Template object comprising the contents of the
    file specified by filename.
    """

    with open(filename, 'r', encoding='utf-8') as template_file:
        template_file_content = template_file.read()
    return Template(template_file_content)

def send_mail(email):

    msg = MIMEMultipart()
    mail_message_path = os.path.dirname(os.path.realpath(__file__))+"/template/message.txt"
    message_template = read_template(mail_message_path)
    message = message_template.substitute()

    msg['From']="valentin@gianninou.fr"
    msg['To']=email
    msg['Subject']="PondPi alerte"

    # add in the message body
    msg.attach(MIMEText(message, 'plain'))

    # send the message via the server set up earlier.
    s.send_message(msg)

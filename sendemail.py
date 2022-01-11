import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
import sys
import pprint
import logging
pp = pprint.PrettyPrinter(indent=4)


def sendEmail(receivers, senderdata, data, port=465, smtpserver='smtp.gmail.com'):
    sender_email = senderdata['email']
    password = senderdata['password']
    SUBJECT = f"Error on {data['name']} Log"
    msg = MIMEMultipart('alternative')
    msg['From'] = sender_email
    msg['Subject'] = SUBJECT
    TEXT = f"Error on log: {data['bodydata']['name']}\nLog Value: {data['bodydata']['value']}\nHost: {data['bodydata']['host']}"
    context = ssl.create_default_context()
    try:
        with smtplib.SMTP_SSL(smtpserver, port, context=context) as server:
            server.login(sender_email, password)
            for receiver in receivers:
                msg['To'] = ''.join(receiver)
                message = 'To: {}\nSubject: {}\n\n{}'.format(
                    receiver, SUBJECT, TEXT)
                server.sendmail(sender_email, receiver, message.encode('utf-8'))
                logging.info(
                    f"sent email for the logid: {data['bodydata']['logid']} to {receiver}")
        return "Success"
    except Exception as e:
        logging.error("ErrorType : {}, Error : {}".format(type(e).__name__, e))

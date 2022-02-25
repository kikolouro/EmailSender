from mailsenderpy.models import EmailContent, Attachment
from mailsenderpy import MailSenderWAPIClient
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
import sys
import pprint
import logging
pp = pprint.PrettyPrinter(indent=4)


def sendEmail(receivers, senderdata, data):
    try:
        msenderclient = MailSenderWAPIClient(
            uri="https://msenderapi_qual.docdigitizer.com",
            appKey=senderdata['SENDER_APPKEY'],
            privateKey=senderdata['SENDER_KEYPATH'])

        msenderclient.postMessage(EmailContent(
            toAddresses=receivers,
            subject=f"Error on {data['name']} Log",
            body=f"Error on log: {data['bodydata']['name']}\nLog Value: {data['bodydata']['value']}\nHost: {data['bodydata']['host']}"
        ), schedule=None)

    except Exception as e:
        logging.error("ErrorType : {}, Error : {}".format(type(e).__name__, e))
    logging.info(f"[{data['bodydata']['logid']}] Queried to EmailSender.")

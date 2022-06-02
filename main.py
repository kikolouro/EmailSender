import re
import mysql.connector
from decouple import UndefinedValueError, config
import time
from operator import itemgetter
import threading
import queue
from sendemail import sendEmail
import logging
from logging.handlers import RotatingFileHandler

logger = logging.getLogger('Rotation Log')
logger.setLevel(logging.INFO)


handler = RotatingFileHandler(
    "/app/logs/emailsender.log", maxBytes=100000000, backupCount=10)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
ch = logging.StreamHandler()
ch.setFormatter(formatter)
logger.addHandler(ch)
logger.addHandler(handler)


def getLargestID(result):
    print(result)
    aux = max(result, key=itemgetter(0))
    return aux[0], aux[1]


def handler(recipients, entry):
    logger.info(f"[{entry[0]}] Data Handler initialized.")
    try:
        data = {
            'name': entry[2],
            'bodydata': {
                'name': entry[2],
                'value': entry[1].decode('utf8'),
                'logid': entry[0],
                'host': entry[3]
            }
        }
        # print(data)
        sendEmail(recipients,  {'SENDER_APPKEY': config(
            'SENDER_APPKEY'), 'SENDER_KEYPATH': config('SENDER_KEYPATH'), "SENDER_URI": config('SENDER_URI')}, data)
        logger.info(f"[{entry[0]}] Data Handler successfully exited.")
    except Exception as e:
        logger.error("ErrorType : {}, Error : {}".format(type(e).__name__, e))


def queryString(logs):
    string = ''
    for log in logs:
        string += f" items.name = '{log}' or"
    return string[:-2]


def worker(recipients):
    logger.info("Email Worker initialized.")
    while True:
        try:
            item = q.get()
            t = threading.Thread(target=handler, args=(
                recipients, item), daemon=True)
            t.start()
            t.join()
            q.task_done()
        except Exception as e:
            logger.error("ErrorType : {}, Error : {}".format(
                type(e).__name__, e))


def findValues(word):
    try:
        temp = []
        for i in range(1, 50):
            if config(f'{word}{i}'):
                temp.append(config(f'{word}{i}'))
    except UndefinedValueError as e:
        pass
    return temp


try:

    mydb = mysql.connector.connect(
        host=config("DBHOST"),
        user=config("DBUSER"),
        password=config("DBPW"),
        database=config("DB"),
        autocommit=True
    )
    mycursor = mydb.cursor(buffered=True)
    # print(mycursor)
    logger.info("Initialing....")
    mycursor.execute("select logid, value, items.name, hosts.name from history_log join items on items.itemid = history_log.itemid JOIN hosts on hosts.hostid = items.hostid JOIN hosts_groups on hosts.hostid = hosts_groups.hostid where items.type = 7 and value_type = 2 and value like '%ERROR%' and groupid = 17 order by clock desc")
    myresult = mycursor.fetchall()
    logger.info("First Query done.")
    # print(myresult)
    lastid, lastvalue = getLargestID(myresult)
except Exception as e:
    logger.error("ErrorType : {}, Error : {}".format(type(e).__name__, e))
q = queue.Queue()


logs = findValues('LOG')
recipients = findValues('RECIPIENT')

emailworker = threading.Thread(
    target=worker, args=(recipients,), daemon=True).start()

logger.info("Initialized.")
while True:

    mycursor.execute(
        f"select logid, value, items.name, hosts.name from history_log join items on items.itemid = history_log.itemid JOIN hosts on hosts.hostid = items.hostid JOIN hosts_groups on hosts.hostid = hosts_groups.hostid where items.type = 7 and value_type = 2 and value like '%ERROR%' and groupid = 17 and logid > {lastid} order by clock desc")

    myresult = mycursor.fetchall()
    if myresult:
        lastid, lastvalue = getLargestID(myresult)
        orderedresult = sorted(myresult, key=lambda tup: tup[0])
        for x in orderedresult:
            q.put(x)

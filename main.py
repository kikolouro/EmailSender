import mysql.connector
from decouple import UndefinedValueError, config
import time
from operator import itemgetter
import threading
import queue
from sendemail import sendEmail
import logging
logging.basicConfig(filename="/app/logs/emailsender.log",
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    filemode='w', level=logging.INFO)
try:

    mydb = mysql.connector.connect(
        host=config("DBHOST"),
        user=config("DBUSER"),
        password=config("DBPW"),
        database=config("DB"),
        autocommit=True,
        auth_plugin='mysql_native_password'
    )
except Exception as e:
    logging.error("ErrorType : {}, Error : {}".format(type(e).__name__, e))
q = queue.Queue()


def findValues(word):
    try:
        temp = []
        for i in range(1, 50):
            if config(f'{word}{i}'):
                temp.append(config(f'{word}{i}'))
    except UndefinedValueError as e:
        pass
    return temp


logs = findValues('LOG')
recipients = findValues('RECIPIENT')


def getLargestID(result):
    aux = max(result, key=itemgetter(0))
    return aux[0], aux[1]


def handler(recipients, entry):
    logging.info("Data Handler initialized.")
    
    data = {
        'name': entry[2].decode(),
        'bodydata': {
            'name': entry[2].decode(),
            'value': entry[1].decode('utf8'),
            'logid': entry[0],
            'host': entry[3].decode()
        }
    }
    # print(data)
    sendEmail(recipients,  {'email': config(
        'SENDER_EMAIL'), 'password': config('SENDER_PASSWORD')}, data)
    logging.info("Data Handler successfully exited")


def queryString(logs):
    string = ''
    for log in logs:
        string += f" items.name = '{log}' or"
    return string[:-2]


querystring = queryString(logs)
mycursor = mydb.cursor(buffered=True)
logging.info("Initialing....")
mycursor.execute(
    f"select logid, value, items.name, hosts.name from history_log JOIN items ON items.itemid = history_log.itemid JOIN hosts ON hosts.hostid = items.hostid where ({querystring}) order by clock desc limit 10")
myresult = mycursor.fetchall()
logging.info("First Query done.")
lastid, lastvalue = getLargestID(myresult)


def worker(recipients):
    logging.info("Email Worker initialized.")
    while True:
        try:
            item = q.get()
            t = threading.Thread(target=handler, args=(
                recipients, item), daemon=True)
            t.start()
            t.join()
            q.task_done()
        except Exception as e:
            logging.error("ErrorType : {}, Error : {}".format(type(e).__name__, e))


emailworker = threading.Thread(
    target=worker, args=(recipients,), daemon=True).start()

logging.info("Initialized.")
while True:

    mycursor.execute(
        f"select logid, value, items.name, hosts.name from history_log JOIN items ON items.itemid = history_log.itemid JOIN hosts ON hosts.hostid = items.hostid where ({querystring}) and logid > {lastid} order by clock desc limit 10")

    myresult = mycursor.fetchall()
    if myresult:
        lastid, lastvalue = getLargestID(myresult)
        orderedresult = sorted(myresult, key=lambda tup: tup[0])
        for x in orderedresult:
            q.put(x)

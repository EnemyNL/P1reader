import requests
import urllib.request
import json
import socket
import datetime
import time
import configparser
import mysql.connector
from mysql.connector import Error
from math import ceil
from datetime import datetime
socket.setdefaulttimeout(30)

config=configparser.ConfigParser()
config.read('/home/pi/Enphase/config.ini')
P1_IP = config.get('P1_METER', 'IP')
user = config.get('P1_METER', 'user')
passwd = config.get('P1_METER', 'password')

currentUsageString = '/api/v2/sm/actual/'

# build the full url to get the current usage
url = 'http://' + P1_IP + currentUsageString

from requests.auth import HTTPBasicAuth

try:
        response = requests.get(url, auth=HTTPBasicAuth(user, passwd))
        data = response.json()
        meterTime = str(data['timestamp']['value'])[:-1]
        readTime = int(meterTime)
        dayImportMeter = float(data['energy_delivered_tariff1']['value'])
        nightImportMeter = float(data['energy_delivered_tariff2']['value'])
        dayExportMeter = float(data['energy_returned_tariff1']['value'])
        nightExportMeter = float(data['energy_returned_tariff2']['value'])
        wImport = float(data['power_delivered']['value'])
        wExport = float(data['power_returned']['value'])
        netConsNow = (wImport*1000) - (wExport*1000)
        timeNow = datetime(year=2000 + int(meterTime[0:2]),month=int(meterTime[2:4]),day=int(meterTime[4:6]), hour=int(meterTime[6:8]), minute=int(meterTime[8:10]),second=int(meterTime[10:12]))

except urllib.error.URLError as error:
        print('Data was not retrieved because error: {}\nURL: {}'.format(error.reason, url) )
        print(error.headers['www-authenticate'])
        quit()  # exit the script - some error happened
        
except socket.timeout:
        print('Connection to {} timed out, '.format( url))
        quit()  # exit the script - cannot connect   
        response.close

try:
    connection = mysql.connector.connect(host = config.get('SERVER', 'host'),
                                         database=config.get('SERVER', 'meterbase'),
                                         user=config.get('LOGIN', 'user'),
                                         password=config.get('LOGIN', 'password'))
    if connection.is_connected():
        db_Info = connection.get_server_info()
        print("Connected to MySQL Server version ", db_Info)
        cursor = connection.cursor()
        cursor.execute("select database();")
        record = cursor.fetchone()
        print("You're connected to datase: ", record)
        
        mSql_insert_query = """INSERT INTO meter_readings (dateTime, importDay, importNight, exportDay, exportNight, netImport) values (%s, %s, %s, %s, %s, %s)"""
        record = (timeNow, dayImportMeter, dayExportMeter, nightImportMeter, nightExportMeter, netConsNow)
        cursor.execute(mSql_insert_query, record)
        connection.commit()
        print("successfully inserted")
except Error as e:
    quit()
    print("Error while connecting to MySQL", e)
finally:
    if connection.is_connected():
        cursor.close()
        connection.close()
        print("MySQL connection is closed")


quit()

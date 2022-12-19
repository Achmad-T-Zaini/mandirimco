import time
import os
import json
import psycopg2
import psycopg2.extras
from datetime import datetime, timedelta
import os
import os.path
import numpy as np
import pandas as pd

def insert_kecamatan(data):
    myconz = psycopg2.connect(host=db_host, user=db_username, password=db_password, dbname=db_name )
    curz = myconz.cursor()
    csql = "INSERT INTO wilayah_kecamatan(name, kabkota_id, create_uid, create_date, write_uid, write_date) values('"
    csql = csql + data[1] + "'," + str(data[2]) + "," + str(data[3]) + ",'"  + data[4] + "',1,'" + data[6] +"');"
    curz.execute(csql)
    myconz.commit()
    myconz.close()

def insert_kelurahan(data):
    myconz = psycopg2.connect(host=db_host, user=db_username, password=db_password, dbname=db_name )
    curz = myconz.cursor()
    csql = "INSERT INTO wilayah_kelurahan(name, kecamatan_id, kodepos, create_uid, create_date, write_uid, write_date) values('"
    csql = csql + data[1] + "'," + str(data[2]) + ",'" + str(data[3]) + "',1,'"  + data[5] + "',1,'" + data[7] +"');"
    curz.execute(csql)
    myconz.commit()
    myconz.close()

def insert_anggota(data):
    myconz = psycopg2.connect(host=db_host, user=db_username, password=db_password, dbname=db_name )
    curz = myconz.cursor()
    csql = "INSERT INTO simpin_member(email,name, bank_norek, nomor_induk, nomor_anggota, create_uid, create_date, write_uid, write_date,company_id,currency_id) values('"
    csql = csql + str(data[0]) + "','" + data[1] + "','" + str(data[2]) + "','" + str(data[3]) + "','"  + str(data[4]) + "',1,'2021-12-01',1,'2021-12-01',1,12);"
    curz.execute(csql)
    myconz.commit()
    myconz.close()

def begin_upload(file_name):
    data = pd.read_csv(file_name,low_memory=False)
    baris = 0
    for baris in range(len(data.index)):
        isi = 0
        isi_data = []
        for kolom in range(len(data.columns)):
            isi_data += [data.iat[baris,isi]]
            isi+=1

        if file_name=='data_anggota.csv':
            insert_anggota(isi_data)
        elif file_name=='kecamatan.csv':
            insert_kecamatan(isi_data)
        elif file_name=='kelurahan.csv':
            insert_kelurahan(isi_data)
        print(isi_data)
    print("Elapsed Time ",file_name,time.time() - start_time)

##### MAIN #####
db_host = '192.168.15.150'
db_password = 't3r53r4h'
db_port = 5432
db_username = 'odoo14'
db_name = 'mco_master'

file_name = "*.csv" #file to be searched
fname = []

cur_dir = os.getcwd()
file_list = os.listdir(cur_dir)
parent_dir = os.path.dirname(cur_dir)
for root, dirs, files in os.walk(cur_dir):
    for file in files:
        if file.endswith(".csv"):
            fname.append(file)

if len(fname)>0:
    for file_name in fname:
        start_time = time.time()
        print(file_name, start_time)
        if file_name=='data_anggota.csv':
            begin_upload(file_name)

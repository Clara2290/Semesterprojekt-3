import mysql.connector

def dbaccess() :
    return mysql.connector.connect(host='localhost',
        database='sundtek014',
        user='sundtek014',
        password='62581-224239-e23')


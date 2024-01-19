from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory
from DBAccess import dbaccess
from fileinput import filename 
import secrets
import os
import mysql.connector
from werkzeug.utils import secure_filename
import xml.etree.ElementTree as ET
from flask import request, make_response



app = Flask(__name__)
app.secret_key = secrets.token_urlsafe(16)


def is_valid_login(username, password, user_type):
    accessDB = dbaccess()
    cursor = accessDB.cursor()
    query = ""

    if user_type == 'patient':
        query = "SELECT adgangskode FROM patient WHERE navn = %s"
    elif user_type == 'fagperson':
        query = "SELECT adgangskode FROM fagperson WHERE navn = %s"
    else:
        cursor.close()
        accessDB.close()
        return False

    cursor.execute(query, (username,))
    user = cursor.fetchone()

    cursor.close()
    accessDB.close()

    if user:
        hashed_password = user[0]
        return hashed_password == password

    return False

def hent_navn(cpr):
    accessDB = dbaccess()
    cursor = accessDB.cursor()

    query = "SELECT navn FROM patient WHERE cpr = %s"
    cursor.execute(query, (cpr,))
    result = cursor.fetchone()

    cursor.close()
    accessDB.close()

    return result[0] if result else None

def hent_navn1(cpr):
    accessDB = dbaccess()
    cursor = accessDB.cursor()

    query = "SELECT navn FROM patient WHERE navn = %s"
    cursor.execute(query, (cpr,))
    result = cursor.fetchone()

    cursor.close()
    accessDB.close()

    return result[0] if result else None


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/patientlogin', methods=['GET', 'POST'])
def patientlogin():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            return "Manglende brugernavn eller adgangskode i formen"

        success = is_valid_login(username, password, 'patient')

        if success:
            patient_navn = hent_navn1(username) 

            if not patient_navn:
                return "Brugernavn blev ikke fundet i systemet"

            user_folder = secure_filename(patient_navn)
            upload_folder = '/home/sundtek014/flask/apahm/upload_folder'
            user_path = os.path.join(upload_folder, user_folder)

            if not os.path.exists(user_path):
                try:
                    os.makedirs(user_path)
                    return redirect(url_for('patientside1'))
                except OSError as e:
                    print("Error creating directory:", e)
                    return "Der opstod en fejl under oprettelse af mappen"
            else:
                return redirect(url_for('patientside1'))
        else:
            return redirect(url_for('ugyldigtlogin'))

    return render_template('patientlogin.html', css_url=url_for('static', filename='css/index.css'), js_url=url_for('static', filename='js/welcome.js'))


@app.route('/nypatient', methods=['GET', 'POST'])
def nypatient():
    if request.method == 'POST':
        cpr = request.form.get('cpr')
        
        if not cpr:
            return "CPR-nummer mangler"

        navn = hent_navn(cpr)

        if navn:
            session['patient_navn'] = navn
            return redirect(url_for('sundhedspersonaleside1'))
        else:
            return redirect(url_for('forkertpatient'))

    return render_template('nypatient.html', css_url=url_for('static', filename='css/index.css'), js_url=url_for('static', filename='js/welcome.js'))

@app.route('/sundhedspersonalelogin', methods=['GET', 'POST'])
def sundhedspersonalelogin():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            return "Manglende brugernavn eller adgangskode i formen"

        success = is_valid_login(username, password, 'fagperson')

        if success:
            return redirect(url_for('nypatient'))
        else:
            return redirect(url_for('ugyldigtlogin2'))

    return render_template('sundhedspersonalelogin.html',css_url=url_for('static', filename='css/index.css'), js_url=url_for('static', filename='js/welcome.js'))

@app.route('/save', methods=['POST'])
def save():
    insert = "INSERT INTO oenskede_tider(ugedag, tid_start, tid_slut, personid, tiderid) VALUES ('{}', '{}', '{}', '{}', '{}')"
    accessDB = dbaccess()
    cursor = accessDB.cursor()
    personid = 1
    tiderid = 1

    try:
        box = 1
        OK = False
        for i in range(1,16):
            checkbox = request.form.get(str(box))

            if checkbox == "on":
                if box == 1 or box == 6 or box == 11:
                    ugedag = "Mandag"
                if box == 2 or box == 7 or box == 12:
                    ugedag = "Tirsdag"
                if box == 3 or box == 8 or box == 13:
                    ugedag = "Onsdag"
                if box == 4 or box == 9 or box == 14:
                    ugedag = "Torsdag"
                if box == 5 or box == 10 or box == 15:
                    ugedag = "Fredag"
                if 0 < box < 6:
                    tid_start = "10:00:00"
                    tid_slut = "12:00:00"
                if 5 < box < 11:
                    tid_start = "13:00:00"
                    tid_slut = "15:00:00"
                if 10 < box < 16:
                    tid_start = "16:00:00"
                    tid_slut = "18:00:00"
                
                cursor.execute(insert.format(ugedag, tid_start, tid_slut, personid, tiderid))
                accessDB.commit()
                OK = True
            box += 1

    except mysql.connector.Error as e:
        OK = False

    finally: 
        cursor.close()
        accessDB.close()
        
    if OK:
        return redirect(url_for('side2'))
    else:
        return "Gå tilbage og vælg venligst en eller flere tider, før du gemmer din forespørgsel. "

@app.route('/patientside1',methods=['GET', 'POST'])
def patientside1():
    patient_navn = session.get('patient_navn', 'Patient')
    return render_template('patientside1.html')


@app.route('/sundhedspersonaleside1')
def sundhedspersonaleside1():
    patient_navn = session.get('patient_navn', 'Patient')

    return render_template('sundhedspersonaleside1.html', patient_navn=patient_navn)

@app.route('/patientside2')
def patientside2():
    patient_navn = session.get('patient_navn', 'Patient')
    return render_template('patientside2.html', patient_navn=patient_navn)

@app.route('/patientside3')
def patientside3():
    patient_navn = session.get('patient_navn', 'Patient')
    return render_template('patientside3.html', patient_navn=patient_navn)

@app.route('/change')
def change():
    return render_template('patientside2.2.html')

@app.route('/patientside4')
def patientside4():
    patient_navn = session.get('patient_navn', 'Patient')
    return render_template('patientside4.html', patient_navn=patient_navn)

@app.route('/successpost', methods=['POST'])
def success_post():
    if request.method == 'POST':
        files = request.files.getlist('file')

        user_folder = session.get('user_folder')

        upload_folder = '/home/sundtek014/flask/apahm/upload_folder'
        user_path = os.path.join(upload_folder, user_folder)


        if not os.path.exists(user_path):
            os.makedirs(user_path)

        for file in files:
            filename = secure_filename(file.filename)
            file_path = os.path.join(user_path, filename)
            file.save(file_path)

        return render_template("modtaget.html", filenames=[f.filename for f in files])

@app.route('/logudpatient')
def logudpatient():
    session.pop('patient_navn', None)  
    return render_template('index.html')

@app.route('/logudsundhedspersonale')
def logudsundhedspersonale():
    session.pop('patient_navn', None)  
    return render_template('index.html')

@app.route('/sogandenpatient')
def sogandenpatient():
    session.pop('patient_navn', None)  
    return render_template('nypatient.html')
                           
@app.route('/sundhedspersonaleside2')
def sundhedspersonaleside2():
    return render_template('sundhedspersonaleside2.html')

@app.route('/sundhedspersonaleside3')
def sundhedspersonaleside3():
    return render_template('sundhedspersonaleside3.html')

@app.route('/back')
def back():
    return render_template('patientside2.html')

@app.route('/backtologinpatient')
def backtologinpatient():
    return render_template('index.html')

@app.route('/backtologinsundhedspersonale')
def backtologinsundhedspersonale():
    return render_template('index.html')

@app.route('/ugyldigtlogin')
def ugyldigtlogin():
    return render_template('ugyldigtlogin.html')

@app.route('/ugyldigtlogin2')
def ugyldigtlogin2():
    return render_template('ugyldigtlogin2.html')

@app.route('/forkertpatient')
def forkertpatient():
    return render_template('forkertpatient.html')

@app.route('/modtaget')
def modtaget():
    return render_template('modtaget.html')

if __name__ == '__main__':
    
   app.run(host='0.0.0.0', port=60140)
   app.run(debug=True)
from flask import Flask, redirect, request, abort, render_template, url_for
from flask_sqlalchemy import SQLAlchemy

import datetime
import config

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = config.dbLocation
db = SQLAlchemy(app)

import model

db.create_all()
db.commit()

activeStream = []

def usernameToKey(userName):
    try:
        key = next(key for key, value in config.authKey.items() if value == userName)
    except:
        return "*Unknown User*"
    return key

@app.route('/')
def main_page():
    activeStreams = model.stream.query.all()
    return render_template('index.html',streamList=activeStreams)

@app.route('/view/<user>/')
def view_page(user):

    streamURL = 'http://' + config.ipAddress + '/live/' + user + '/index.m3u8'
    return render_template('player.html', streamURL = streamURL)

@app.route('/auth-key', methods=['POST'])
def streamkey_check():

    key = request.form['name']
    ipaddress = request.form['addr']

    if config.authKey.has_key(key):
        returnMessage = {'time': str(datetime.datetime.now()), 'status': 'Successful Key Auth', 'key':str(key), 'user': str(config.authKey[key]), 'ipAddress': str(ipaddress)}
        print(returnMessage)

        newStream = model.stream(key,str(config.authKey[key]))
        db.session.add(newStream)
        db.session.commit()

        return redirect('rtmp://' + config.ipAddress + '/stream-data/' + config.authKey[key], code=302)
    else:
        returnMessage = {'time': str(datetime.datetime.now()), 'status': 'Failed Key Auth', 'key':str(key), 'ipAddress': str(ipaddress)}
        print(returnMessage)
        return abort(400)

@app.route('/auth-user', methods=['POST'])
def user_auth_check():

    key = request.form['name']
    ipaddress = request.form['addr']

    streamKey = usernameToKey(key)

    authedStream = model.stream.query.filter_by(streamKey=streamKey).first()

    if authedStream is not None:
        returnMessage = {'time': str(datetime.datetime.now()), 'status': 'Successful User Auth', 'key': str(streamKey), 'user': str(key), 'ipAddress': str(ipaddress)}
        print(returnMessage)
        return 'OK'
    else:
        returnMessage = {'time': str(datetime.datetime.now()), 'status': 'Failed User Auth. No Authorized Stream Key', 'user': str(key), 'ipAddress': str(ipaddress)}
        print(returnMessage)
        return abort(400)

@app.route('/deauth-user', methods=['POST'])
def user_deauth_check():

    key = request.form['name']
    ipaddress = request.form['addr']

    authedStream = model.stream.query.filter_by(streamKey=key).first()

    if authedStream is not None:
        db.session.delete(authedStream)
        db.session.commit()

        returnMessage = {'time': str(datetime.datetime.now()), 'status': 'Stream Closed', 'key': str(key), 'user': str(config.authKey[key]), 'ipAddress': str(ipaddress)}
        print(returnMessage)
        return 'OK'
    else:
        returnMessage = {'time': str(datetime.datetime.now()), 'status': 'Stream Closure Failure - No Such Stream', 'key': str(key), 'ipAddress': str(ipaddress)}
        print(returnMessage)
        return abort(400)

if __name__ == '__main__':
    app.jinja_env.auto_reload = True
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.run(debug=False, port=5000)


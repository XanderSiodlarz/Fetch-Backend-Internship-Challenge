#Import statements
from flask import Flask, request, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
import os


    
#Initialize Flask app
app = Flask(__name__)

#Specify port 8000 / For running in terminal use : flask run --port 8000
if __name__ == '__main__':
    app.run(port=8000, debug=True)
    
#Base directory
basedir = os.path.abspath(os.path.dirname(__file__))

#Setup/configure database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'db.sqlite') 
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False 

#Initialize database; used flask shell in terminal to create database
db = SQLAlchemy(app)

#Initialize Marshmallow for serialization
ma = Marshmallow(app)

#Account Class
class Account(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    payer = db.Column(db.String(50), unique=False) 
    points = db.Column(db.Integer)
    timestamp = db.Column(db.String(50))
    
    def __init__(self, payer, points, timestamp):
        self.payer = payer
        self.points = points
        self.timestamp = timestamp

#creates the database file (db.sqlite)
with app.app_context():
    db.create_all()
           
#Account Schema to help with serialization
class AccountSchema(ma.Schema):
    class Meta:
        fields = ('payer', 'points', 'timestamp')      

#Initialize Schema
account_schema = AccountSchema()
accounts_schema = AccountSchema(many=True)

#/add endpoint: POST request
@app.route('/add', methods=['POST'])
def add_points():
    payer = request.json['payer']
    points = request.json['points']
    timestamp = request.json['timestamp']
    
    new_account = Account(payer, points, timestamp)
    db.session.add(new_account)
    db.session.commit()
    
    return '', 200

#/spend endpoint: POST request
@app.route('/spend', methods=['POST'])
def spend_points():
    points = request.json['points']
    spent_points = dict()
    db.session.query(Account).order_by(Account.timestamp).all()
    all_accounts = Account.query.all()
    for account in all_accounts:
        if account.points < 0:
            points = points - account.points
            if account.payer in spent_points:
                spent_points[account.payer] = spent_points[account.payer] - account.points
            else:
                abort(400, 'Not enough points to spend')
            account.points = 0
        elif points >= account.points:
            points = points - account.points
            if account.payer in spent_points:
                spent_points[account.payer] = spent_points[account.payer] - account.points
            else:
                spent_points[account.payer] =  0 - account.points
            account.points = 0
        else:
            account.points = account.points - points
            if account.payer in spent_points:
                spent_points[account.payer] = spent_points[account.payer] - points
            else:
                spent_points[account.payer] =  0 - points
            db.session.commit()
            points = 0
            return jsonify(spent_points), 200
    if points > 0:
        abort(400, 'Not enough points to spend')
    return jsonify(spent_points), 200
       
       
#/balance endpoint: GET request 
@app.route('/balance', methods=['GET']) 
def get_balance():
    all_accounts = Account.query.all()
    dict = {}
    for account in all_accounts:
        if account.payer in dict:
            dict[account.payer] = dict[account.payer] + account.points
        else:
            dict[account.payer] = account.points
    return jsonify(dict), 200

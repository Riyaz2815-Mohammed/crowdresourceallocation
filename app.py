from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import hashlib

app = Flask(__name__)
app.secret_key = "riyaz2815"

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///crowd.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# Models
class Resource(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    stock = db.Column(db.Integer, nullable=False)

class ResourceRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    resource = db.Column(db.String(200), nullable=False)
    reason = db.Column(db.Text, nullable=False)
    urgency = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    allocated = db.Column(db.Boolean, default=False)

    votes = db.relationship("Vote", backref="request", lazy=True)

class Vote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    request_id = db.Column(db.Integer, db.ForeignKey("resource_request.id"), nullable=False)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

with app.app_context():
    db.create_all()
    
    # Add initial resources if they don't exist
    if not Resource.query.first():
        resources = [
            Resource(name="Laptop", stock=10),
            Resource(name="Projector", stock=5),
            Resource(name="Tablet", stock=8)
        ]
        db.session.bulk_save_objects(resources)
        db.session.commit()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

@app.route("/", methods=["GET", "POST"])
def submit():
    if "user_id" not in session:
        return redirect("/login")
    
    if request.method == "POST":
        new_request = ResourceRequest(
            name=request.form["name"],
            resource=request.form["resource"],
            reason=request.form["reason"],
            urgency=int(request.form["urgency"])
        )
        db.session.add(new_request)
        db.session.commit()
        return redirect(url_for("vote"))

    resources = Resource.query.all()
    return render_template("submit.html", resources=resources)

@app.route("/vote")
def vote():
    if "user_id" not in session:
        return redirect("/login")

    requests = ResourceRequest.query.all()
    return render_template("vote.html", requests=requests)

@app.route("/vote/<int:id>")
def cast_vote(id):
    if "user_id" not in session:
        return redirect("/login")
    
    user_id = session["user_id"]
    existing_vote = Vote.query.filter_by(user_id=user_id, request_id=id).first()
    
    if existing_vote:
        return "You have already voted for this request"
    
    vote = Vote(user_id=user_id, request_id=id)
    db.session.add(vote)
    db.session.commit()
    
    return redirect(url_for("vote"))

def calculate_score(request):
    now = datetime.now()
    votes = len(request.votes)
    vote_score = votes * 10
    urgency_score = request.urgency * 2
    waiting_hours = (now - request.created_at).total_seconds() /

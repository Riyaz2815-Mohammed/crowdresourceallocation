from flask import Flask, render_template, request, redirect, url_for,session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.secret_key ="riyaz2815"

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///crowd.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

class ResourceRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    resource = db.Column(db.String(200), nullable=False)
    reason = db.Column(db.Text, nullable=False)
    urgency = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)

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

import hashlib
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

    return render_template("submit.html")


@app.route("/vote")
def vote():
    if "user_id" not in session:
        return redirect("/login")

    requests = ResourceRequest.query.all()
    return render_template("vote.html", requests=requests)


@app.route("/vote/<int:id>")
def cast_vote(id):
    # 1️⃣ Login check
    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]

    # 2️⃣ Check duplicate vote
    existing_vote = Vote.query.filter_by(
        user_id=user_id,
        request_id=id
    ).first()

    if existing_vote:
        return "You have already voted for this request"

    # 3️⃣ Create vote
    vote = Vote(user_id=user_id, request_id=id)
    db.session.add(vote)
    db.session.commit()

    return redirect(url_for("vote"))


def calculate_score(request):
    now = datetime.now()

    votes = len(request.votes)
    vote_score = votes * 10

    urgency_score = request.urgency * 2

    waiting_hours = (now - request.created_at).total_seconds() / 3600
    waiting_score = min(waiting_hours, 10)

    final_score = vote_score + urgency_score + waiting_score
    return final_score


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = hash_password(request.form["password"])

        if User.query.filter_by(username=username).first():
            return "User already exists"

        user = User(username=username, password=password)
        db.session.add(user)
        db.session.commit()
        return redirect("/login")

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = User.query.filter_by(
            username=request.form["username"]
        ).first()

        if user and user.password == hash_password(request.form["password"]):
            session["user_id"] = user.id
            session["is_admin"] = user.is_admin
            return redirect("/")

        return "Invalid credentials"

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


@app.route("/ranking")
def ranking():
    if "user_id" not in session:
        return redirect("/login")
    requests = ResourceRequest.query.all()
    
    # Sort requests individually by vote count
    ranked = sorted(
        requests,
        key=lambda r : calculate_score(r),
        reverse=True
    )



    ranking_data = []
    for index, r in enumerate(ranked, start=1):
        waiting_time = int((datetime.now()-r.created_at).total_seconds() / 3600)
        explanation = (
            f"Ranked {index} because of {len(r.votes)} votes, "
            f"urgency {r.urgency}, and waiting time {r.created_at}"
        )
        ranking_data.append({
            "rank": index,
            "name": r.name,
            "resource": r.resource,
            "reason": r.reason,
            "votes": len(r.votes),
            "explanation": explanation
        })

    return render_template("ranking.html", ranking=ranking_data)

def admin_required():
    return session.get("is_admin")
@app.route("/allocate/<int:id>")
def allocate(id):
    if not session.get("is_admin"):
        return "Access denied"

    req = ResourceRequest.query.get_or_404(id)
    resource = Resource.query.filter_by(name=req.resource).first()

    if not resource or resource.stock <= 0:
        return "Out of stock"

    if req.allocated:
        return "Already allocated"

    resource.stock -= 1
    req.allocated = True
    db.session.commit()

    return redirect("/admin")

@app.route("/admin")
def admin():
    if not session.get("is_admin"):
        return "Access denied"

    resources = Resource.query.all()
    requests = ResourceRequest.query.all()

    ranked = sorted(
        [r for r in requests if not r.allocated],
        key=lambda r: calculate_score(r),
        reverse=True
    )

    return render_template(
        "admin.html",
        resources=resources,
        ranking=ranked
    )


if __name__ == "__main__":
    app.run()

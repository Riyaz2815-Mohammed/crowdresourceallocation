from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import hashlib

app = Flask(__name__)
app.secret_key = "riyaz2815"

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///crowd.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)


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
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    allocated = db.Column(db.Boolean, default=False)

    votes = db.relationship("Vote", backref="request", lazy=True)


class Vote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    request_id = db.Column(db.Integer, db.ForeignKey("resource_request.id"), nullable=False)



with app.app_context():
    db.create_all()

    # Initial resources
    if not Resource.query.first():
        db.session.add_all([
            Resource(name="Laptop", stock=5),
            Resource(name="Projector", stock=3),
            Resource(name="WiFi Dongle", stock=10),
            Resource(name="Tablet", stock=4),
            Resource(name="External Hard Drive", stock=6),
            Resource(name="Headphones", stock=8),
            Resource(name="Webcam", stock=7),   
            Resource(name="Microphone", stock=5),
            Resource(name="Smartphone", stock=9),
            Resource(name="Speakers", stock=2),
            Resource(name="CPU",stock=5)
        ])
        db.session.commit()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def calculate_score(req):
    votes = len(req.votes) * 10
    urgency = req.urgency * 2
    waiting_hours = min(
        (datetime.utcnow() - req.created_at).total_seconds() / 3600,
        10
    )
    return votes + urgency + waiting_hours



@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        user = User(
            username=request.form["username"],
            password=hash_password(request.form["password"])
        )
        db.session.add(user)
        db.session.commit()
        return redirect("/login")
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = User.query.filter_by(username=request.form["username"]).first()
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


@app.route("/", methods=["GET", "POST"])
def submit():
    if "user_id" not in session:
        return redirect("/login")

    if request.method == "POST":
        req = ResourceRequest(
            name=request.form["name"],
            resource=request.form["resource"],
            reason=request.form["reason"],
            urgency=int(request.form["urgency"])
        )
        db.session.add(req)
        db.session.commit()
        return redirect("/vote")

    resources = Resource.query.all()
    return render_template("submit.html", resources=resources)


@app.route("/vote")
def vote():
    if "user_id" not in session:
        return redirect("/login")
    return render_template("vote.html", requests=ResourceRequest.query.all())


@app.route("/vote/<int:id>")
def cast_vote(id):
    if "user_id" not in session:
        return redirect("/login")

    existing = Vote.query.filter_by(
        user_id=session["user_id"],
        request_id=id
    ).first()

    if existing:
        return "Already voted"

    db.session.add(Vote(user_id=session["user_id"], request_id=id))
    db.session.commit()
    return redirect("/vote")


@app.route("/ranking")
def ranking():
    if "user_id" not in session:
        return redirect("/login")

    requests = ResourceRequest.query.filter_by(allocated=False).all()

    ranked = sorted(
        requests,
        key=lambda r: calculate_score(r),
        reverse=True
    )

    ranking_data = []
    for index, r in enumerate(ranked, start=1):
        waiting_hours = int(
            (datetime.now() - r.created_at).total_seconds() / 3600
        )

        ranking_data.append({
            "rank": index,
            "name": r.name,
            "resource": r.resource,
            "urgency": r.urgency,
            "votes": len(r.votes),   
            "explanation": (
                f"Ranked #{index} because it received {len(r.votes)} vote(s), "
                f"urgency level {r.urgency}, "
                f"and has been waiting for {waiting_hours} hour(s)."
            )
        })

    return render_template("ranking.html", ranking=ranking_data)

@app.route("/admin")
def admin():
    if not session.get("is_admin"):
        return "Access denied"

    return render_template(
        "admin.html",
        resources=Resource.query.all(),
        ranking=ResourceRequest.query.filter_by(allocated=False).all()
    )


@app.route("/allocate/<int:id>")
def allocate(id):
    if not session.get("is_admin"):
        return "Access denied"

    req = ResourceRequest.query.get_or_404(id)
    res = Resource.query.filter_by(name=req.resource).first()

    if not res or res.stock <= 0:
        return "Out of stock"

    res.stock -= 1
    req.allocated = True
    db.session.commit()

    return redirect("/admin")


if __name__ == "__main__":
    app.run(debug=True)




from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///crowd.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

class ResourceRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    resource = db.Column(db.String(200), nullable=False)
    reason = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)

    votes = db.relationship("Vote", backref="request", lazy=True)


class Vote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey("resource_request.id"))
    created_at = db.Column(db.DateTime, default=datetime.now)

with app.app_context():
    db.create_all()

@app.route("/", methods=["GET", "POST"])
def submit():
    if request.method == "POST":
        new_request = ResourceRequest(
            name=request.form["name"],
            resource=request.form["resource"],
            reason=request.form["reason"]
        )
        db.session.add(new_request)
        db.session.commit()
        return redirect(url_for("vote"))

    return render_template("submit.html")


@app.route("/vote")
def vote():
    requests = ResourceRequest.query.all()
    return render_template("vote.html", requests=requests)


@app.route("/vote/<int:id>")
def cast_vote(id):
    vote = Vote(request_id=id)
    db.session.add(vote)
    db.session.commit()
    return redirect(url_for("vote"))


@app.route("/ranking")
def ranking():
    requests = ResourceRequest.query.all()

    ranked = sorted(
        requests,
        key=lambda r: len(r.votes),
        reverse=True
    )

    ranking_data = []
    for index, r in enumerate(ranked, start=1):
        explanation = f"Ranked #{index} because it received {len(r.votes)} vote(s)."
        ranking_data.append({
            "rank": index,
            "name": r.name,
            "resource": r.resource,
            "votes": len(r.votes),
            "explanation": explanation
        })

    return render_template("ranking.html", ranking=ranking_data)


if __name__ == "__main__":
    app.run()

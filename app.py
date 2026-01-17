import os, socket, requests
from flask import Flask, render_template, request, redirect, make_response
import uuid
import logging
import json

app = Flask(__name__)

INSTANCE_NAME = os.getenv("INSTANCE_NAME", socket.gethostname())
BE_BASE_URL = os.getenv("BE_BASE_URL", "http://localhost:5001")

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s"
)

logger = logging.getLogger("fe-app")

def log(event, status="success", **kwargs):
    logger.info(json.dumps({
        "app": "frontend",
        "instance": INSTANCE_NAME,
        "event": event,
        "status": status,
        **kwargs
    }))

@app.route("/", methods=["GET", "POST"])
def index():
    name = request.cookies.get("user_name")

    if request.method == "POST":
        resp = make_response(redirect("/"))
        resp.set_cookie("user_name", request.form["name"])
        log(
                event="user_session_started",
                user=name
            )
        return resp

    if not name:
        return render_template("index.html", ask_name=True)
    
    request_id = str(uuid.uuid4())

    log(
    event="calling_backend",
    request_id=request_id,
    user=name,
    fe_instance=INSTANCE_NAME
)

    hit_resp = requests.post(
    f"{BE_BASE_URL}/api/hit",
    json={
        "user_name": name,
        "fe_instance": INSTANCE_NAME,
        "request_id": request_id
    }
)

    be_instance = "UNKNOWN"
    if hit_resp.status_code == 200:
        be_instance = hit_resp.json().get("be_instance", "UNKNOWN")

        log(
    event="backend_response",
    request_id=request_id,
    user=name,
    be_instance=be_instance
)

    summary_resp = requests.get(f"{BE_BASE_URL}/api/summary")
    summary = summary_resp.json() if summary_resp.status_code == 200 else {}

    return render_template(
        "index.html",
        ask_name=False,
        user=name,
        fe_instance=INSTANCE_NAME,
        be_instance=be_instance,
        summary=summary
    )


@app.route("/entries")
def entries():
    data = requests.get(f"{BE_BASE_URL}/api/entries").json()
    return render_template("entries.html", entries=data)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

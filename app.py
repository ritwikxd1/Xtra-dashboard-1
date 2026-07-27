import os
import requests
from flask import Flask, redirect, request, session, url_for, render_template
from pymongo import MongoClient

app = Flask(__name__)
# Vercel env se secret keys nikalna
app.secret_key = os.getenv("FLASK_SECRET", "xtra_super_secret_fallback")

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI") 
DISCORD_API_BASE = "https://discord.com/api/v10"

# MongoDB Connection
MONGO_URI = os.getenv("MONGO_URI")
try:
    if MONGO_URI:
        mongo_client = MongoClient(MONGO_URI)
        db = mongo_client["xtra_bot_db"]
except Exception as e:
    print(f"MongoDB Connection Error: {e}")

@app.route("/")
def home():
    if "token" in session:
        return redirect(url_for("dashboard"))
    return render_template("index.html")

@app.route("/login")
def login():
    discord_login_url = f"https://discord.com/api/oauth2/authorize?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&response_type=code&scope=identify%20guilds"
    return redirect(discord_login_url)

@app.route("/callback")
def callback():
    code = request.args.get("code")
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    response = requests.post(f"{DISCORD_API_BASE}/oauth2/token", data=data, headers=headers)
    
    if response.status_code == 200:
        session["token"] = response.json()["access_token"]
        return redirect(url_for("dashboard"))
    else:
        return f"Login failed! Discord API Error: {response.text}"

@app.route("/dashboard")
def dashboard():
    if "token" not in session:
        return redirect(url_for("home"))
    
    headers = {"Authorization": f"Bearer {session['token']}"}
    user_response = requests.get(f"{DISCORD_API_BASE}/users/@me", headers=headers)
    
    if user_response.status_code == 200:
        user_info = user_response.json()
        return f"<h1>Welcome to Xtra Dashboard, {user_info['username']}!</h1><br><a href='/logout'>Logout</a>"
    else:
        return redirect(url_for("login"))

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

# Vercel ko app.run() ki zarurat nahi hoti, but local testing ke liye ye theek hai
if __name__ == "__main__":
    app.run(debug=True, port=5000)

from flask import Blueprint, redirect, session, url_for, request
from authlib.integrations.flask_client import OAuth
import os
from app.models import supabase

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')
oauth = OAuth()

# --- Updated Google Registration ---
google = oauth.register(
    name='google',
    client_id=os.getenv('GOOGLE_CLIENT_ID'),
    client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)
# ---------------------------------

@auth_bp.route('/login')
def login():
    redirect_uri = url_for('auth.authorize', _external=True)
    return google.authorize_redirect(redirect_uri)

@auth_bp.route('/authorize')
def authorize():
    token = google.authorize_access_token()
    # The 'userinfo' is now directly in the token's 'userinfo' claim
    user_info = token.get('userinfo')

    if not user_info:
        # Fallback or error handling if userinfo is not in the token
        return "Failed to get user information.", 400

    user = supabase.table("users").select("*").eq("email", user_info["email"]).execute()
    if not user.data:
        supabase.table("users").insert({
            "email": user_info["email"],
            "name": user_info.get("name"),
            "google_id": user_info.get("sub")
        }).execute()

    session['user'] = user_info
    return redirect(url_for('users.dashboard'))
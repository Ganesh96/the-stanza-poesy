from flask import Blueprint, render_template, session, redirect, url_for
from app.models import supabase

users_bp = Blueprint('users', __name__)

@users_bp.route('/')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('auth.login'))
    user_email = session['user']['email']
    user = supabase.table("users").select("*").eq("email", user_email).execute().data[0]
    books = supabase.table("books").select("*").eq("user_id", user['id']).execute().data
    return render_template("dashboard.html", books=books)
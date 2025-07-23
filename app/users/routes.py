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

    # 📘 Add progress summary for each book
    for book in books:
        progress = supabase.table("reading_progress").select("*") \
            .eq("book_id", book["id"]).execute().data
        book["total_pages_read"] = sum([p["pages_read"] for p in progress])
        book["last_note"] = progress[-1]["notes"] if progress else ""
        book["last_quote"] = progress[-1]["quote"] if progress else ""

    return render_template("dashboard.html", books=books)

from flask import Blueprint, request, redirect, url_for, session
from app.models import supabase
import uuid

books_bp = Blueprint('books', __name__, url_prefix='/books')

@books_bp.route('/add', methods=['POST'])
def add_book():
    data = request.form
    user = session['user']
    user_id = supabase.table("users").select("id").eq("email", user['email']).execute().data[0]['id']
    supabase.table("books").insert({
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "title": data['title'],
        "author": data.get('author'),
        "total_pages": int(data['pages']),
        "status": data.get('status', 'want_to_read')
    }).execute()
    return redirect(url_for('users.dashboard'))
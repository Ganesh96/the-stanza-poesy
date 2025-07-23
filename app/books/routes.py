from flask import Blueprint, request, redirect, url_for, session, flash, make_response, render_template, abort
from app.models import supabase
import uuid
import csv
import io
import requests
from datetime import datetime

books_bp = Blueprint('books', __name__, url_prefix='/books')

@books_bp.route('/add', methods=['POST'])
def add_book():
    # ... (this function is unchanged)
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

# --- NEW: Route for searching books ---
@books_bp.route('/search')
def search():
    if 'user' not in session:
        return redirect(url_for('auth.login'))
    
    query = request.args.get('q')
    if not query:
        return redirect(url_for('users.dashboard'))

    user_id = supabase.table("users").select("id").eq("email", session['user']['email']).execute().data[0]['id']
    
    # Search for books by title, case-insensitive
    books = supabase.table('books').select('*').eq('user_id', user_id).ilike('title', f'%{query}%').execute().data
    
    return render_template('search_results.html', books=books, query=query)

@books_bp.route('/<book_id>')
def detail(book_id):
    if 'user' not in session:
        return redirect(url_for('auth.login'))
    
    user_id = supabase.table("users").select("id").eq("email", session['user']['email']).execute().data[0]['id']
    
    book = supabase.table('books').select('*').eq('user_id', user_id).eq('id', book_id).single().execute().data
    
    if not book:
        abort(404) # Book not found or doesn't belong to user

    # Fetch all progress entries for this book
    progress = supabase.table('reading_progress').select('*').eq('book_id', book_id).order('progress_date', desc=True).execute().data
    
    return render_template('book_detail.html', book=book, progress_entries=progress)

@books_bp.route('/<book_id>/progress', methods=['POST'])
def add_progress(book_id):
    if 'user' not in session:
        return redirect(url_for('auth.login'))

    user_id = supabase.table("users").select("id").eq("email", session['user']['email']).execute().data[0]['id']
    
    # Verify the book belongs to the current user before adding progress
    book_check = supabase.table('books').select('id').eq('id', book_id).eq('user_id', user_id).execute().data
    if not book_check:
        abort(403) # Forbidden
        
    data = request.form
    
    # --- THIS IS THE FIX ---
    # Default 'pages_read' to 0 if the input is empty.
    pages_read_value = data.get('pages_read')
    pages_read_int = int(pages_read_value) if pages_read_value and pages_read_value.strip() else 0

    supabase.table('reading_progress').insert({
        'id': str(uuid.uuid4()),
        'book_id': book_id,
        'pages_read': pages_read_int,  # Use the corrected value
        'notes': data.get('notes') if data.get('notes') else None,
        'quote': data.get('quote') if data.get('quote') else None,
        'progress_date': datetime.now().isoformat()
    }).execute()
    
    return redirect(url_for('books.detail', book_id=book_id))

@books_bp.route('/import', methods=['POST'])
def import_csv():
    if 'user' not in session:
        return redirect(url_for('auth.login'))

    if 'csv_file' not in request.files:
        flash('No file part')
        return redirect(url_for('users.dashboard'))

    file = request.files['csv_file']
    if file.filename == '':
        flash('No selected file')
        return redirect(url_for('users.dashboard'))

    if file and file.filename.endswith('.csv'):
        user_email = session['user']['email']
        user_id = supabase.table("users").select("id").eq("email", user_email).execute().data[0]['id']

        stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
        csv_reader = csv.DictReader(stream)

        books_to_insert = []
        books_not_found = 0

        for row in csv_reader:
            # Prioritize ISBN13, but fall back to ISBN if needed.
            isbn = row.get('ISBN13') or row.get('ISBN')
            if not isbn:
                continue

            # --- Google Books API Lookup ---
            # Remove any non-numeric characters from ISBN
            isbn = "".join(filter(str.isdigit, isbn))
            url = f"https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}"
            response = requests.get(url)

            if response.status_code == 200 and response.json().get('totalItems', 0) > 0:
                data = response.json()
                volume_info = data['items'][0].get('volumeInfo', {})
                
                # Extract details from the API response, with fallbacks
                title = volume_info.get('title', 'Title Not Found')
                subtitle = volume_info.get('subtitle')
                full_title = f"{title}: {subtitle}" if subtitle else title
                
                authors = ", ".join(volume_info.get('authors', ['Unknown Author']))
                pages = volume_info.get('pageCount', 0)

                # Find ISBN-13 from the identifiers list
                isbn_13 = None
                for identifier in volume_info.get('industryIdentifiers', []):
                    if identifier['type'] == 'ISBN_13':
                        isbn_13 = identifier['identifier']
                        break

                book = {
                    "user_id": user_id,
                    "title": full_title,
                    "author": authors,
                    "total_pages": pages,
                    "goodreads_id": isbn_13 or isbn, # Store the ISBN
                    "status": 'want_to_read' # Default status
                }
                books_to_insert.append(book)
            else:
                books_not_found += 1
                # --- End of API Lookup ---

        if books_to_insert:
            supabase.table("books").insert(books_to_insert).execute()
            flash(f'Successfully imported {len(books_to_insert)} books.')
        if books_not_found > 0:
            flash(f'Could not find {books_not_found} books on Google Books using the provided ISBNs.')

    return redirect(url_for('users.dashboard'))

@books_bp.route('/export')
def export_csv():
    if 'user' not in session:
        return redirect(url_for('auth.login'))

    user_email = session['user']['email']
    user = supabase.table("users").select("id").eq("email", user_email).execute().data[0]
    books = supabase.table("books").select("*").eq("user_id", user['id']).execute().data

    # Use an in-memory string buffer
    si = io.StringIO()
    cw = csv.writer(si)

    # These are some of the standard Goodreads headers
    headers = ['Book Id', 'Title', 'Author', 'Number of Pages', 'Exclusive Shelf', 'Date Added']
    cw.writerow(headers)
    
    status_mapping_reverse = {
        'read': 'read',
        'currently_reading': 'currently-reading',
        'want_to_read': 'to-read'
    }

    for book in books:
        exclusive_shelf = status_mapping_reverse.get(book['status'], 'to-read')
        # Format the created_at date to YYYY-MM-DD
        date_added = book.get('created_at', '').split('T')[0] if book.get('created_at') else ''
        
        row = [
            book.get('goodreads_id', ''),
            book.get('title', ''),
            book.get('author', ''),
            book.get('total_pages', ''),
            exclusive_shelf,
            date_added
        ]
        cw.writerow(row)

    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=reading_tracker_export.csv"
    output.headers["Content-type"] = "text/csv"
    return output
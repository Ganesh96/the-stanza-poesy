# 📚 The Stanza Poesy - Reading Tracker

The Stanza Poesy is a full-stack web application that helps you track your reading progress. Built with Flask and Supabase, it provides a simple and secure way to manage your book library, log reading sessions, and sync with Goodreads.

## ✨ Key Features

* **Google Authentication**: Secure sign-in using your Google account.
* **Book Management**: Manually add books or import your library from a Goodreads CSV file.
* **Google Books API Integration**: Automatically enriches imported books with details like title, author, and page count using their ISBN.
* **Progress Tracking**: Log reading sessions with the number of pages read, personal notes, and memorable quotes.
* **Search Functionality**: Easily search through your personal library to find books.
* **Goodreads Sync**: Import from Goodreads via CSV and export your library to a CSV file.

## 🛠️ Tech Stack

* **Backend**: Flask (Python)
* **Database**: Supabase (PostgreSQL)
* **Authentication**: Google OAuth via `authlib`
* **Frontend**: Jinja2 Templates, HTML, CSS
* **API**: Google Books API

## 🚀 Getting Started

Follow these instructions to set up and run the project on your local machine.

### 1. Prerequisites

* Python 3.x
* A Supabase account (for database and API keys)
* A Google Cloud project (for OAuth credentials)

### 2. Installation

Clone the repository to your local machine:
```bash
git clone https://github.com/Ganesh96/the-stanza-poesy.git
cd the-stanza-poesy
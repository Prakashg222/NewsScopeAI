from multiprocessing.dummy import connection
import sqlite3
import os
from datetime import datetime

DATABASE_FOLDER = "database"
DATABASE_PATH = os.path.join(DATABASE_FOLDER, "newscope.db")

def get_connection():
    os.makedirs(DATABASE_FOLDER, exist_ok=True)
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection

def init_database():
    connection = get_connection()
    cursor = connection.cursor()

    # Articles table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            title TEXT,
            file_type TEXT,
            text TEXT NOT NULL,
            category TEXT,
            sentiment TEXT,
            confidence INTEGER,
            main_points TEXT,
            word_count INTEGER,
            positive_score INTEGER,
            negative_score INTEGER,
            language TEXT DEFAULT 'eng',
            created_at TEXT
        )
    """)

    # Add language column if an old database 
    cursor.execute("PRAGMA table_info(articles)")
    columns = [row["name"] for row in cursor.fetchall()]

    if "language" not in columns:
        cursor.execute(
            "ALTER TABLE articles ADD COLUMN language TEXT DEFAULT 'eng'"
        )

    # Pending uploads table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pending_uploads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            file_type TEXT,
            text TEXT NOT NULL,
            created_at TEXT
        )
    """)

    # Commit and close ONLY at the end
    connection.commit()
    connection.close()

def save_pending_upload(filename, file_type, text):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("""
        INSERT INTO pending_uploads (filename, file_type, text, created_at)
        VALUES (?, ?, ?, ?)
    """, (filename, file_type, text, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    pending_id = cursor.lastrowid
    connection.commit()
    connection.close()
    return pending_id

def get_pending_upload(pending_id):
    connection = get_connection()
    result = connection.execute(
        "SELECT * FROM pending_uploads WHERE id = ?", (pending_id,)
    ).fetchone()
    connection.close()
    return result

def delete_pending_upload(pending_id):
    connection = get_connection()
    connection.execute("DELETE FROM pending_uploads WHERE id = ?", (pending_id,))
    connection.commit()
    connection.close()

def save_article(article):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("""
        INSERT INTO articles
        (filename, title, file_type, text, category, sentiment, confidence,
         main_points, word_count, positive_score, negative_score, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        article["filename"], article["title"], article["file_type"],
        article["text"], article["category"], article["sentiment"],
        article["confidence"], article["main_points"], article["word_count"],
        article["positive_score"], article["negative_score"],
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))
    article_id = cursor.lastrowid
    connection.commit()
    connection.close()
    return article_id

def get_all_articles():
    connection = get_connection()
    results = connection.execute(
        "SELECT * FROM articles ORDER BY id DESC"
    ).fetchall()
    connection.close()
    return results

def get_article(article_id):
    connection = get_connection()
    result = connection.execute(
        "SELECT * FROM articles WHERE id = ?", (article_id,)
    ).fetchone()
    connection.close()
    return result

def delete_article(article_id):
    connection = get_connection()
    connection.execute("DELETE FROM articles WHERE id = ?", (article_id,))
    connection.commit()
    connection.close()

def search_articles(query="", category="", sentiment=""):
    connection = get_connection()
    sql = "SELECT * FROM articles WHERE 1=1"
    parameters = []

    if query:
        sql += " AND (title LIKE ? OR text LIKE ? OR category LIKE ? OR sentiment LIKE ?)"
        keyword = f"%{query}%"
        parameters.extend([keyword] * 4)

    if category:
        sql += " AND category = ?"
        parameters.append(category)

    if sentiment:
        sql += " AND sentiment = ?"
        parameters.append(sentiment)

    sql += " ORDER BY id DESC"
    results = connection.execute(sql, parameters).fetchall()
    connection.close()
    return results

def get_statistics():
    connection = get_connection()
    cursor = connection.cursor()

    total = cursor.execute(
        "SELECT COUNT(*) AS count FROM articles"
    ).fetchone()["count"]

    positive = cursor.execute(
        "SELECT COUNT(*) AS count FROM articles WHERE sentiment='Positive'"
    ).fetchone()["count"]

    negative = cursor.execute(
        "SELECT COUNT(*) AS count FROM articles WHERE sentiment='Negative'"
    ).fetchone()["count"]

    neutral = cursor.execute(
        "SELECT COUNT(*) AS count FROM articles WHERE sentiment='Neutral'"
    ).fetchone()["count"]

    categories = cursor.execute("""
        SELECT category, COUNT(*) AS count
        FROM articles GROUP BY category ORDER BY count DESC
    """).fetchall()

    connection.close()

    return {
        "total": total,
        "positive": positive,
        "negative": negative,
        "neutral": neutral,
        "categories": categories
    }

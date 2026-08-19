import os
import sqlite3
from datetime import datetime


# ============================================================
# DATABASE CONFIGURATION
# ============================================================

DATABASE_URL = os.getenv("DATABASE_URL")

DATABASE_FOLDER = "database"
DATABASE_PATH = os.path.join(DATABASE_FOLDER, "newscope.db")


# ============================================================
# DATABASE TYPE
# ============================================================

def is_postgres():
    return bool(DATABASE_URL)


# ============================================================
# GET DATABASE CONNECTION
# ============================================================

def get_connection():
    """
    Vercel:
        Neon PostgreSQL

    Local:
        SQLite
    """

    # --------------------------------------------------------
    # VERCEL / NEON POSTGRESQL
    # --------------------------------------------------------

    if is_postgres():

        import psycopg
        from psycopg.rows import dict_row

        connection = psycopg.connect(
            DATABASE_URL,
            row_factory=dict_row
        )

        return connection

    # --------------------------------------------------------
    # LOCAL DEVELOPMENT / SQLITE
    # --------------------------------------------------------

    os.makedirs(DATABASE_FOLDER, exist_ok=True)

    connection = sqlite3.connect(DATABASE_PATH)

    connection.row_factory = sqlite3.Row

    return connection


# ============================================================
# SQL PLACEHOLDER
# ============================================================

def get_placeholder():

    if is_postgres():
        return "%s"

    return "?"


# ============================================================
# INITIALIZE DATABASE
# ============================================================

def init_database():

    connection = get_connection()

    try:

        cursor = connection.cursor()

        # ====================================================
        # POSTGRESQL
        # ====================================================

        if is_postgres():

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS articles (
                    id SERIAL PRIMARY KEY,
                    filename TEXT NOT NULL,
                    title TEXT DEFAULT 'Untitled Article',
                    file_type TEXT,
                    text TEXT NOT NULL,
                    summary TEXT DEFAULT '',
                    category TEXT DEFAULT 'General',
                    sentiment TEXT DEFAULT 'Neutral',
                    confidence INTEGER DEFAULT 50,
                    main_points TEXT DEFAULT '',
                    word_count INTEGER DEFAULT 0,
                    positive_score INTEGER DEFAULT 0,
                    negative_score INTEGER DEFAULT 0,
                    language TEXT DEFAULT 'eng',
                    created_at TEXT
                )
            """)

            # Add missing columns for older Neon databases

            cursor.execute("""
                ALTER TABLE articles
                ADD COLUMN IF NOT EXISTS title TEXT
                DEFAULT 'Untitled Article'
            """)

            cursor.execute("""
                ALTER TABLE articles
                ADD COLUMN IF NOT EXISTS file_type TEXT
            """)

            cursor.execute("""
                ALTER TABLE articles
                ADD COLUMN IF NOT EXISTS summary TEXT
                DEFAULT ''
            """)

            cursor.execute("""
                ALTER TABLE articles
                ADD COLUMN IF NOT EXISTS category TEXT
                DEFAULT 'General'
            """)

            cursor.execute("""
                ALTER TABLE articles
                ADD COLUMN IF NOT EXISTS sentiment TEXT
                DEFAULT 'Neutral'
            """)

            cursor.execute("""
                ALTER TABLE articles
                ADD COLUMN IF NOT EXISTS confidence INTEGER
                DEFAULT 50
            """)

            cursor.execute("""
                ALTER TABLE articles
                ADD COLUMN IF NOT EXISTS main_points TEXT
                DEFAULT ''
            """)

            cursor.execute("""
                ALTER TABLE articles
                ADD COLUMN IF NOT EXISTS word_count INTEGER
                DEFAULT 0
            """)

            cursor.execute("""
                ALTER TABLE articles
                ADD COLUMN IF NOT EXISTS positive_score INTEGER
                DEFAULT 0
            """)

            cursor.execute("""
                ALTER TABLE articles
                ADD COLUMN IF NOT EXISTS negative_score INTEGER
                DEFAULT 0
            """)

            cursor.execute("""
                ALTER TABLE articles
                ADD COLUMN IF NOT EXISTS language TEXT
                DEFAULT 'eng'
            """)

            cursor.execute("""
                ALTER TABLE articles
                ADD COLUMN IF NOT EXISTS created_at TEXT
            """)

            # Pending uploads

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS pending_uploads (
                    id SERIAL PRIMARY KEY,
                    filename TEXT NOT NULL,
                    file_type TEXT,
                    text TEXT NOT NULL,
                    created_at TEXT
                )
            """)

        # ====================================================
        # SQLITE
        # ====================================================

        else:

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS articles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT NOT NULL,
                    title TEXT DEFAULT 'Untitled Article',
                    file_type TEXT,
                    text TEXT NOT NULL,
                    summary TEXT DEFAULT '',
                    category TEXT DEFAULT 'General',
                    sentiment TEXT DEFAULT 'Neutral',
                    confidence INTEGER DEFAULT 50,
                    main_points TEXT DEFAULT '',
                    word_count INTEGER DEFAULT 0,
                    positive_score INTEGER DEFAULT 0,
                    negative_score INTEGER DEFAULT 0,
                    language TEXT DEFAULT 'eng',
                    created_at TEXT
                )
            """)

            # Check existing SQLite columns

            cursor.execute("PRAGMA table_info(articles)")

            columns = {
                row["name"]
                for row in cursor.fetchall()
            }

            # Add missing columns

            if "title" not in columns:

                cursor.execute("""
                    ALTER TABLE articles
                    ADD COLUMN title TEXT
                    DEFAULT 'Untitled Article'
                """)

            if "file_type" not in columns:

                cursor.execute("""
                    ALTER TABLE articles
                    ADD COLUMN file_type TEXT
                """)

            if "summary" not in columns:

                cursor.execute("""
                    ALTER TABLE articles
                    ADD COLUMN summary TEXT
                    DEFAULT ''
                """)

            if "category" not in columns:

                cursor.execute("""
                    ALTER TABLE articles
                    ADD COLUMN category TEXT
                    DEFAULT 'General'
                """)

            if "sentiment" not in columns:

                cursor.execute("""
                    ALTER TABLE articles
                    ADD COLUMN sentiment TEXT
                    DEFAULT 'Neutral'
                """)

            if "confidence" not in columns:

                cursor.execute("""
                    ALTER TABLE articles
                    ADD COLUMN confidence INTEGER
                    DEFAULT 50
                """)

            if "main_points" not in columns:

                cursor.execute("""
                    ALTER TABLE articles
                    ADD COLUMN main_points TEXT
                    DEFAULT ''
                """)

            if "word_count" not in columns:

                cursor.execute("""
                    ALTER TABLE articles
                    ADD COLUMN word_count INTEGER
                    DEFAULT 0
                """)

            if "positive_score" not in columns:

                cursor.execute("""
                    ALTER TABLE articles
                    ADD COLUMN positive_score INTEGER
                    DEFAULT 0
                """)

            if "negative_score" not in columns:

                cursor.execute("""
                    ALTER TABLE articles
                    ADD COLUMN negative_score INTEGER
                    DEFAULT 0
                """)

            if "language" not in columns:

                cursor.execute("""
                    ALTER TABLE articles
                    ADD COLUMN language TEXT
                    DEFAULT 'eng'
                """)

            if "created_at" not in columns:

                cursor.execute("""
                    ALTER TABLE articles
                    ADD COLUMN created_at TEXT
                """)

            # Pending uploads

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS pending_uploads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT NOT NULL,
                    file_type TEXT,
                    text TEXT NOT NULL,
                    created_at TEXT
                )
            """)

        connection.commit()

    except Exception:

        connection.rollback()

        raise

    finally:

        connection.close()


# ============================================================
# PENDING UPLOADS
# ============================================================

def save_pending_upload(filename, file_type, text):

    connection = get_connection()
    placeholder = get_placeholder()

    try:

        cursor = connection.cursor()

        sql = f"""
            INSERT INTO pending_uploads
            (
                filename,
                file_type,
                text,
                created_at
            )
            VALUES (
                {placeholder},
                {placeholder},
                {placeholder},
                {placeholder}
            )
        """

        if is_postgres():

            sql += " RETURNING id"

        cursor.execute(
            sql,
            (
                filename,
                file_type,
                text,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
        )

        if is_postgres():

            pending_id = cursor.fetchone()["id"]

        else:

            pending_id = cursor.lastrowid

        connection.commit()

        return pending_id

    except Exception:

        connection.rollback()

        raise

    finally:

        connection.close()


# ============================================================
# GET PENDING UPLOAD
# ============================================================

def get_pending_upload(pending_id):

    connection = get_connection()
    placeholder = get_placeholder()

    try:

        result = connection.execute(
            f"""
                SELECT *
                FROM pending_uploads
                WHERE id = {placeholder}
            """,
            (pending_id,)
        ).fetchone()

        return result

    finally:

        connection.close()


# ============================================================
# DELETE PENDING UPLOAD
# ============================================================

def delete_pending_upload(pending_id):

    connection = get_connection()
    placeholder = get_placeholder()

    try:

        connection.execute(
            f"""
                DELETE FROM pending_uploads
                WHERE id = {placeholder}
            """,
            (pending_id,)
        )

        connection.commit()

    except Exception:

        connection.rollback()

        raise

    finally:

        connection.close()


# ============================================================
# SAVE ARTICLE
# ============================================================

def save_article(article):

    connection = get_connection()
    placeholder = get_placeholder()

    try:

        cursor = connection.cursor()

        sql = f"""
            INSERT INTO articles
            (
                filename,
                title,
                file_type,
                text,
                category,
                sentiment,
                confidence,
                main_points,
                word_count,
                positive_score,
                negative_score,
                created_at
            )
            VALUES (
                {placeholder},
                {placeholder},
                {placeholder},
                {placeholder},
                {placeholder},
                {placeholder},
                {placeholder},
                {placeholder},
                {placeholder},
                {placeholder},
                {placeholder},
                {placeholder}
            )
        """

        if is_postgres():

            sql += " RETURNING id"

        cursor.execute(
            sql,
            (
                article.get("filename"),
                article.get("title"),
                article.get("file_type"),
                article.get("text"),
                article.get("category"),
                article.get("sentiment"),
                article.get("confidence"),
                article.get("main_points"),
                article.get("word_count"),
                article.get("positive_score"),
                article.get("negative_score"),
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
        )

        if is_postgres():

            article_id = cursor.fetchone()["id"]

        else:

            article_id = cursor.lastrowid

        connection.commit()

        return article_id

    except Exception:

        connection.rollback()

        raise

    finally:

        connection.close()


# ============================================================
# GET ALL ARTICLES
# ============================================================

def get_all_articles():

    connection = get_connection()

    try:

        results = connection.execute("""
            SELECT *
            FROM articles
            ORDER BY id DESC
        """).fetchall()

        return results

    finally:

        connection.close()


# ============================================================
# GET SINGLE ARTICLE
# ============================================================

def get_article(article_id):

    connection = get_connection()
    placeholder = get_placeholder()

    try:

        result = connection.execute(
            f"""
                SELECT *
                FROM articles
                WHERE id = {placeholder}
            """,
            (article_id,)
        ).fetchone()

        return result

    finally:

        connection.close()


# ============================================================
# DELETE ARTICLE
# ============================================================

def delete_article(article_id):

    connection = get_connection()
    placeholder = get_placeholder()

    try:

        connection.execute(
            f"""
                DELETE FROM articles
                WHERE id = {placeholder}
            """,
            (article_id,)
        )

        connection.commit()

    except Exception:

        connection.rollback()

        raise

    finally:

        connection.close()


# ============================================================
# SEARCH ARTICLES
# ============================================================

def search_articles(
    query="",
    category="",
    sentiment=""
):

    connection = get_connection()
    placeholder = get_placeholder()

    try:

        sql = """
            SELECT *
            FROM articles
            WHERE 1=1
        """

        parameters = []

        if query:

            sql += f"""
                AND (
                    title LIKE {placeholder}
                    OR text LIKE {placeholder}
                    OR category LIKE {placeholder}
                    OR sentiment LIKE {placeholder}
                )
            """

            keyword = f"%{query}%"

            parameters.extend([
                keyword,
                keyword,
                keyword,
                keyword
            ])

        if category:

            sql += f"""
                AND category = {placeholder}
            """

            parameters.append(category)

        if sentiment:

            sql += f"""
                AND sentiment = {placeholder}
            """

            parameters.append(sentiment)

        sql += """
            ORDER BY id DESC
        """

        results = connection.execute(
            sql,
            parameters
        ).fetchall()

        return results

    finally:

        connection.close()


# ============================================================
# STATISTICS
# ============================================================

def get_statistics():

    connection = get_connection()
    placeholder = get_placeholder()

    try:

        total = connection.execute("""
            SELECT COUNT(*) AS count
            FROM articles
        """).fetchone()["count"]

        positive = connection.execute(
            f"""
                SELECT COUNT(*) AS count
                FROM articles
                WHERE sentiment = {placeholder}
            """,
            ("Positive",)
        ).fetchone()["count"]

        negative = connection.execute(
            f"""
                SELECT COUNT(*) AS count
                FROM articles
                WHERE sentiment = {placeholder}
            """,
            ("Negative",)
        ).fetchone()["count"]

        neutral = connection.execute(
            f"""
                SELECT COUNT(*) AS count
                FROM articles
                WHERE sentiment = {placeholder}
            """,
            ("Neutral",)
        ).fetchone()["count"]

        categories = connection.execute("""
            SELECT
                category,
                COUNT(*) AS count
            FROM articles
            GROUP BY category
            ORDER BY count DESC
        """).fetchall()

        return {
            "total": total,
            "positive": positive,
            "negative": negative,
            "neutral": neutral,
            "categories": categories
        }

    finally:

        connection.close()


# ============================================================
# INITIALIZE DATABASE
# ============================================================

init_database()
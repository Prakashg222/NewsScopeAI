from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash
)

import os
import sqlite3
import re
from datetime import datetime
from database import get_connection, is_postgres
from database import save_article
from werkzeug.utils import secure_filename

import pytesseract
from PIL import Image

try:
    import fitz
except ImportError:
    fitz = None

from analyzer import analyze_article


# ============================================================
# APPLICATION CONFIGURATION
# ============================================================

app = Flask(__name__)

app.secret_key = "newscope-ai-secret-key"

UPLOAD_FOLDER = "uploads"

DATABASE_FOLDER = "database"

DATABASE_PATH = os.path.join(
    DATABASE_FOLDER,
    "newscope.db"
)

os.makedirs(
    UPLOAD_FOLDER,
    exist_ok=True
)

os.makedirs(
    DATABASE_FOLDER,
    exist_ok=True
)


# ============================================================
# TESSERACT CONFIGURATION
# ============================================================

TESSERACT_PATH = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)

pytesseract.pytesseract.tesseract_cmd = (
    TESSERACT_PATH
)

OCR_LANGUAGES = "eng"


# ============================================================
# ALLOWED FILES
# ============================================================

ALLOWED_EXTENSIONS = {
    "txt",
    "pdf",
    "png",
    "jpg",
    "jpeg"
}


# ============================================================
# DATABASE CONNECTION
# ============================================================




# ============================================================
# TITLE GENERATION
# ============================================================

def generate_title(
    text,
    filename="article"
):

    if not text:
        return "Untitled Article"

    cleaned = re.sub(
        r"\s+",
        " ",
        text
    ).strip()

    sentences = re.split(
        r"(?<=[.!?])\s+",
        cleaned
    )

    for sentence in sentences:

        sentence = sentence.strip()

        if len(sentence) >= 15:

            title = re.sub(
                r"^[^A-Za-z0-9\u0900-\u0C7F]+",
                "",
                sentence
            )

            if len(title) > 120:

                title = (
                    title[:120]
                    .rsplit(" ", 1)[0]
                    + "..."
                )

            return title

    name = os.path.splitext(
        filename
    )[0]

    name = name.replace(
        "_",
        " "
    ).replace(
        "-",
        " "
    ).strip()

    if name:
        return name.title()

    return "Untitled Article"


# ============================================================
# SUMMARY GENERATION
# ============================================================

def generate_summary(
    text,
    max_sentences=4
):

    if not text:
        return "No summary available."

    cleaned = re.sub(
        r"\s+",
        " ",
        text
    ).strip()

    sentences = re.split(
        r"(?<=[.!?])\s+",
        cleaned
    )

    useful_sentences = []

    for sentence in sentences:

        sentence = sentence.strip()

        if len(sentence) >= 30:

            useful_sentences.append(
                sentence
            )

        if len(useful_sentences) >= max_sentences:
            break

    if not useful_sentences:

        return cleaned[:500]

    return " ".join(
        useful_sentences
    )


# ============================================================
# MAIN POINT GENERATION
# ============================================================

def generate_main_points(
    text,
    max_points=8
):

    if not text:
        return []

    cleaned = re.sub(
        r"\s+",
        " ",
        text
    ).strip()

    sentences = re.split(
        r"(?<=[.!?])\s+",
        cleaned
    )

    points = []

    for sentence in sentences:

        sentence = sentence.strip()

        if len(sentence) < 35:
            continue

        sentence = re.sub(
            r"\s+",
            " ",
            sentence
        ).strip(
            " -–—"
        )

        if not sentence:
            continue

        if len(sentence) > 300:

            sentence = (
                sentence[:300]
                .rsplit(" ", 1)[0]
                + "..."
            )

        points.append(
            sentence
        )

        if len(points) >= max_points:
            break

    if not points:

        words = cleaned.split()

        chunk_size = 35

        for index in range(
            0,
            len(words),
            chunk_size
        ):

            chunk = " ".join(
                words[
                    index:index + chunk_size
                ]
            )

            if len(chunk) >= 20:

                points.append(
                    chunk + "..."
                )

            if len(points) >= max_points:
                break

    return points


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

def init_database():

    connection = get_connection()
    cursor = connection.cursor()

    # Create articles table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            title TEXT DEFAULT 'Untitled Article',
            text TEXT NOT NULL,
            summary TEXT DEFAULT '',
            language TEXT DEFAULT 'Unknown',
            sentiment TEXT DEFAULT 'Neutral',
            category TEXT DEFAULT 'General',
            confidence INTEGER DEFAULT 50,
            word_count INTEGER DEFAULT 0,
            positive_score INTEGER DEFAULT 0,
            negative_score INTEGER DEFAULT 0,
            main_points TEXT DEFAULT '',
            created_at TEXT NOT NULL
        )
    """)

    connection.commit()

    # Get existing columns
    cursor.execute("PRAGMA table_info(articles)")

    existing_columns = {
        row["name"]
        for row in cursor.fetchall()
    }

    # Add missing columns to old databases
    if "title" not in existing_columns:
        cursor.execute("""
            ALTER TABLE articles
            ADD COLUMN title TEXT DEFAULT 'Untitled Article'
        """)

    if "summary" not in existing_columns:
        cursor.execute("""
            ALTER TABLE articles
            ADD COLUMN summary TEXT DEFAULT ''
        """)

    if "language" not in existing_columns:
        cursor.execute("""
            ALTER TABLE articles
            ADD COLUMN language TEXT DEFAULT 'Unknown'
        """)

    if "sentiment" not in existing_columns:
        cursor.execute("""
            ALTER TABLE articles
            ADD COLUMN sentiment TEXT DEFAULT 'Neutral'
        """)

    if "category" not in existing_columns:
        cursor.execute("""
            ALTER TABLE articles
            ADD COLUMN category TEXT DEFAULT 'General'
        """)

    if "confidence" not in existing_columns:
        cursor.execute("""
            ALTER TABLE articles
            ADD COLUMN confidence INTEGER DEFAULT 50
        """)

    if "word_count" not in existing_columns:
        cursor.execute("""
            ALTER TABLE articles
            ADD COLUMN word_count INTEGER DEFAULT 0
        """)

    if "positive_score" not in existing_columns:
        cursor.execute("""
            ALTER TABLE articles
            ADD COLUMN positive_score INTEGER DEFAULT 0
        """)

    if "negative_score" not in existing_columns:
        cursor.execute("""
            ALTER TABLE articles
            ADD COLUMN negative_score INTEGER DEFAULT 0
        """)

    if "main_points" not in existing_columns:
        cursor.execute("""
            ALTER TABLE articles
            ADD COLUMN main_points TEXT DEFAULT ''
        """)

    connection.commit()

    # Get existing articles
    cursor.execute("""
        SELECT
            id,
            filename,
            text,
            title,
            summary,
            main_points
        FROM articles
    """)

    old_articles = cursor.fetchall()

    # Update old articles
    for article in old_articles:

        title = article["title"]
        summary = article["summary"]
        main_points = article["main_points"]

        # Generate title if missing
        if not title or not title.strip():
            title = generate_title(
                article["text"],
                article["filename"]
            )

        # Generate summary if missing
        if not summary or not summary.strip():
            summary = generate_summary(
                article["text"]
            )

        # Generate main points if missing
        if not main_points or not main_points.strip():

            points = generate_main_points(
                article["text"]
            )

            main_points = "\n".join(points)

        # IMPORTANT:
        # SQLite uses ? instead of %s
        cursor.execute("""
            UPDATE articles
            SET title = ?,
                summary = ?,
                main_points = ?
            WHERE id = ?
        """, (
            title,
            summary,
            main_points,
            article["id"]
        ))

    connection.commit()
    connection.close()


# Initialize database
init_database()

# ============================================================
# FILE VALIDATION
# ============================================================

def allowed_file(filename):

    return (
        "."
        in filename
        and filename.rsplit(
            ".",
            1
        )[1].lower()
        in ALLOWED_EXTENSIONS
    )


# ============================================================
# TESSERACT CHECK
# ============================================================

def check_tesseract():

    if not os.path.exists(
        TESSERACT_PATH
    ):

        raise FileNotFoundError(
            "Tesseract was not found at: "
            + TESSERACT_PATH
        )

    try:

        version = (
            pytesseract
            .get_tesseract_version()
        )

        print(
            "Tesseract version:",
            version
        )

    except Exception as error:

        raise RuntimeError(
            "Tesseract is installed but "
            "could not be started: "
            + str(error)
        )


# ============================================================
# IMAGE OCR
# ============================================================

def extract_text_from_image(
    image
):

    if image.mode != "RGB":

        image = image.convert(
            "RGB"
        )

    return pytesseract.image_to_string(
        image,
        lang=OCR_LANGUAGES
    )


# ============================================================
# FILE TEXT EXTRACTION
# ============================================================

def extract_text_from_file(
    file,
    extension
):

    extension = extension.lower()

    # TXT

    if extension == "txt":

        data = file.read()

        try:

            return data.decode(
                "utf-8"
            )

        except UnicodeDecodeError:

            return data.decode(
                "utf-8",
                errors="ignore"
            )

    # IMAGE

    elif extension in {
        "png",
        "jpg",
        "jpeg"
    }:

        image = Image.open(
            file
        )

        return extract_text_from_image(
            image
        )

    # PDF

    elif extension == "pdf":

        if fitz is None:

            raise RuntimeError(
                "PyMuPDF is not installed. "
                "Run: pip install PyMuPDF"
            )

        pdf_data = file.read()

        document = fitz.open(
            stream=pdf_data,
            filetype="pdf"
        )

        pages_text = []

        for page in document:

            page_text = page.get_text()

            if (
                page_text
                and page_text.strip()
            ):

                pages_text.append(
                    page_text
                )

            else:

                pix = page.get_pixmap(
                    matrix=fitz.Matrix(
                        2,
                        2
                    )
                )

                image = Image.frombytes(
                    "RGB",
                    [
                        pix.width,
                        pix.height
                    ],
                    pix.samples
                )

                page_text = (
                    extract_text_from_image(
                        image
                    )
                )

                pages_text.append(
                    page_text
                )

        document.close()

        return "\n".join(
            pages_text
        )

    raise ValueError(
        "Unsupported file format."
    )


# ============================================================
# SAVE ARTICLE
# ============================================================

def save_article(filename, text, analysis):

    connection = get_connection()
    cursor = connection.cursor()

    main_points = "\n".join(
        analysis.get("main_points", [])
    )

    created_at = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    values = (
        filename,
        analysis.get("title", "Untitled Article"),
        analysis.get("summary", ""),
        text,
        analysis.get("language", "Unknown"),
        analysis.get("sentiment", "Neutral"),
        analysis.get("category", "General"),
        analysis.get("confidence", 50),
        analysis.get("word_count", 0),
        analysis.get("positive_score", 0),
        analysis.get("negative_score", 0),
        main_points,
        created_at
    )

    # ==========================================
    # POSTGRESQL - VERCEL
    # ==========================================
    if is_postgres():

        cursor.execute("""
            INSERT INTO articles (
                filename,
                title,
                summary,
                text,
                language,
                sentiment,
                category,
                confidence,
                word_count,
                positive_score,
                negative_score,
                main_points,
                created_at
            )
            VALUES (
                %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s
            )
            RETURNING id
        """, values)

        row = cursor.fetchone()
        article_id = row[0]

    # ==========================================
    # SQLITE - LOCAL
    # ==========================================
    else:

        cursor.execute("""
            INSERT INTO articles (
                filename,
                title,
                summary,
                text,
                language,
                sentiment,
                category,
                confidence,
                word_count,
                positive_score,
                negative_score,
                main_points,
                created_at
            )
            VALUES (
                ?, ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?
            )
        """, values)

        article_id = cursor.lastrowid

    connection.commit()
    connection.close()

    return article_id
# ============================================================
# GET ALL ARTICLES
# ============================================================

def get_all_articles():

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM articles
        ORDER BY id DESC
    """)

    rows = cursor.fetchall()

    connection.close()

    articles = []

    for row in rows:

        article = dict(row)

        main_points_text = article.get("main_points", "")

        if isinstance(main_points_text, str):

            article["main_points"] = [
                point.strip()
                for point in main_points_text.split("\n")
                if point.strip()
            ]

        else:

            article["main_points"] = []

        articles.append(article)

    return articles

# ============================================================
# GET ONE ARTICLE
# ============================================================

def get_article(article_id):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM articles
        WHERE id = ?
    """, (article_id,))

    article = cursor.fetchone()

    connection.close()

    if article is None:
        return None

    article = dict(article)

    # Convert stored main points back into a list
    main_points_text = article.get("main_points", "")

    if isinstance(main_points_text, str):
        article["main_points"] = [
            point.strip()
            for point in main_points_text.split("\n")
            if point.strip()
        ]

    elif not isinstance(main_points_text, list):
        article["main_points"] = []

    return article

# ============================================================
# DELETE ARTICLE
# ============================================================

def delete_article(article_id):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""
        DELETE FROM articles
        WHERE id = ?
    """, (article_id,))

    connection.commit()

    connection.close()


# ============================================================
# SEARCH ARTICLES
# ============================================================

def search_articles(query):

    connection = get_connection()

    cursor = connection.cursor()

    search_value = f"%{query}%"

    cursor.execute("""
        SELECT *
        FROM articles
        WHERE
            title LIKE ?
            OR filename LIKE ?
            OR text LIKE ?
            OR summary LIKE ?
            OR category LIKE ?
            OR sentiment LIKE ?
            OR language LIKE ?
        ORDER BY id DESC
    """, (
        search_value,
        search_value,
        search_value,
        search_value,
        search_value,
        search_value,
        search_value
    ))

    results = cursor.fetchall()

    connection.close()

    return results


# ============================================================
# STATISTICS
# ============================================================

def get_statistics():

    connection = get_connection()

    cursor = connection.cursor()


    # --------------------------------------------------------
    # TOTAL ARTICLES
    # --------------------------------------------------------

    cursor.execute("""
        SELECT COUNT(*) AS count
        FROM articles
    """)

    total_articles = cursor.fetchone()["count"]


    # --------------------------------------------------------
    # POSITIVE
    # --------------------------------------------------------

    cursor.execute("""
        SELECT COUNT(*) AS count
        FROM articles
        WHERE sentiment = 'Positive'
    """)

    positive = cursor.fetchone()["count"]


    # --------------------------------------------------------
    # NEGATIVE
    # --------------------------------------------------------

    cursor.execute("""
        SELECT COUNT(*) AS count
        FROM articles
        WHERE sentiment = 'Negative'
    """)

    negative = cursor.fetchone()["count"]


    # --------------------------------------------------------
    # NEUTRAL
    # --------------------------------------------------------

    cursor.execute("""
        SELECT COUNT(*) AS count
        FROM articles
        WHERE sentiment = 'Neutral'
    """)

    neutral = cursor.fetchone()["count"]


    # --------------------------------------------------------
    # LANGUAGES
    # --------------------------------------------------------

    cursor.execute("""
        SELECT
            language,
            COUNT(*) AS count

        FROM articles

        GROUP BY language

        ORDER BY count DESC
    """)

    language_rows = cursor.fetchall()

    languages = {
        row["language"] or "Unknown":
        row["count"]
        for row in language_rows
    }


    # --------------------------------------------------------
    # CATEGORIES
    # --------------------------------------------------------

    cursor.execute("""
        SELECT
            category,
            COUNT(*) AS count

        FROM articles

        GROUP BY category

        ORDER BY count DESC
    """)

    category_rows = cursor.fetchall()

    categories = {
        row["category"] or "General":
        row["count"]
        for row in category_rows
    }


    connection.close()


    return {
        "total": total_articles,
        "total_articles": total_articles,
        "positive": positive,
        "negative": negative,
        "neutral": neutral,
        "languages": languages,
        "categories": categories
    }


# ============================================================
# HOME
# ============================================================

@app.route("/")
def home():

    return redirect(
        url_for("dashboard")
    )


# ============================================================
# DASHBOARD
# ============================================================

@app.route("/dashboard")
def dashboard():

    statistics = get_statistics()

    recent_articles = get_all_articles()[:5]

    return render_template(
        "dashboard.html",
        statistics=statistics,
        recent_articles=recent_articles
    )


# ============================================================
# UPLOAD
# ============================================================

@app.route(
    "/upload",
    methods=["GET", "POST"]
)
def upload():

    if request.method == "POST":

        # ----------------------------------------------------
        # CHECK FILE
        # ----------------------------------------------------

        if "file" not in request.files:

            flash(
                "Please select a file.",
                "danger"
            )

            return redirect(
                url_for("upload")
            )


        file = request.files["file"]


        # ----------------------------------------------------
        # CHECK FILENAME
        # ----------------------------------------------------

        if not file.filename:

            flash(
                "Please select a file.",
                "danger"
            )

            return redirect(
                url_for("upload")
            )


        # ----------------------------------------------------
        # CHECK EXTENSION
        # ----------------------------------------------------

        if not allowed_file(
            file.filename
        ):

            flash(
                "Only TXT, PDF, PNG, JPG and JPEG files are supported.",
                "danger"
            )

            return redirect(
                url_for("upload")
            )


        try:

            # ------------------------------------------------
            # SECURE FILENAME
            # ------------------------------------------------

            filename = secure_filename(
                file.filename
            )


            extension = filename.rsplit(
                ".",
                1
            )[1].lower()


            print(
                f"Processing file: {filename}"
            )

            print(
                f"OCR languages: {OCR_LANGUAGES}"
            )


            # ------------------------------------------------
            # EXTRACT TEXT
            # ------------------------------------------------

            text = extract_text_from_file(
                file,
                extension
            )


            # ------------------------------------------------
            # CHECK TEXT
            # ------------------------------------------------

            if not text or not text.strip():

                flash(
                    "No readable text was found. "
                    "Please upload a clearer newspaper image.",
                    "danger"
                )

                return redirect(
                    url_for("upload")
                )


            print(
                "Text extracted successfully."
            )


            # ------------------------------------------------
            # ANALYZE ARTICLE
            # ------------------------------------------------

            analysis = analyze_article(
                text
            )


            # ------------------------------------------------
            # TITLE
            # ------------------------------------------------

            if not analysis.get(
                "title"
            ):

                analysis["title"] = generate_title(
                    text,
                    filename
                )


            # ------------------------------------------------
            # SUMMARY
            # ------------------------------------------------

            if not analysis.get(
                "summary"
            ):

                analysis["summary"] = generate_summary(
                    text
                )


            # ------------------------------------------------
            # MAIN POINTS
            # ------------------------------------------------

            if not analysis.get(
                "main_points"
            ):

                analysis["main_points"] = generate_main_points(
                    text
                )


            # ------------------------------------------------
            # WORD COUNT
            # ------------------------------------------------

            if not analysis.get(
                "word_count"
            ):

                analysis["word_count"] = len(
                    text.split()
                )


            print(
                "Title:",
                analysis.get("title")
            )

            print(
                "Language:",
                analysis.get("language")
            )

            print(
                "Sentiment:",
                analysis.get("sentiment")
            )

            print(
                "Category:",
                analysis.get("category")
            )

            print(
                "Main points:",
                len(
                    analysis.get(
                        "main_points",
                        []
                    )
                )
            )


            # ------------------------------------------------
            # SAVE ARTICLE
            # ------------------------------------------------

            article_id = save_article(
                filename,
                text,
                analysis
            )


            # ------------------------------------------------
            # SUCCESS
            # ------------------------------------------------

            flash(
                "Article analyzed successfully!",
                "success"
            )


            return redirect(
                url_for(
                    "article",
                    article_id=article_id
                )
            )


        except Exception as error:

            print(
                "UPLOAD ERROR:",
                repr(error)
            )


            flash(
                f"Upload failed: {error}",
                "danger"
            )


            return redirect(
                url_for("upload")
            )


    return render_template(
        "upload.html"
    )


# ============================================================
# ARTICLE
# ============================================================
@app.route("/article/<int:article_id>")
def article(article_id):

    # --------------------------------------------------------
    # GET ARTICLE
    # --------------------------------------------------------

    article_data = get_article(article_id)

    if article_data is None:

        flash(
            "Article not found.",
            "danger"
        )

        return redirect(
            url_for("dashboard")
        )


    # --------------------------------------------------------
    # CONVERT SQLITE ROW TO NORMAL DICTIONARY
    # --------------------------------------------------------

    article_data = dict(article_data)


    # --------------------------------------------------------
    # MAIN POINTS
    # --------------------------------------------------------

    main_points = article_data.get(
        "main_points",
        []
    )


    # SQLite currently stores main_points as TEXT.
    # Convert it back into a Python list.

    if isinstance(main_points, str):

        main_points = [
            point.strip()
            for point in main_points.split("\n")
            if point.strip()
        ]


    elif isinstance(main_points, list):

        main_points = [
            str(point).strip()
            for point in main_points
            if str(point).strip()
        ]


    else:

        main_points = []


    article_data["main_points"] = main_points


    # --------------------------------------------------------
    # TITLE
    # --------------------------------------------------------

    title = article_data.get(
        "title",
        ""
    )


    if not title:

        filename = article_data.get(
            "filename",
            "Article"
        )

        title = os.path.splitext(
            filename
        )[0]


    article_data["title"] = title


    # --------------------------------------------------------
    # FILE TYPE
    # --------------------------------------------------------

    filename = article_data.get(
        "filename",
        ""
    )


    if "." in filename:

        file_type = filename.rsplit(
            ".",
            1
        )[1].upper()

    else:

        file_type = "TEXT"


    article_data["file_type"] = file_type


    # --------------------------------------------------------
    # RENDER ARTICLE PAGE
    # --------------------------------------------------------

    return render_template(
        "article.html",
        article=article_data
    )
    # --------------------------------------------------------
    # SUMMARY
    # --------------------------------------------------------

    if not article_data.get(
        "summary"
    ):

        article_data["summary"] = (
            generate_summary(
                article_data.get(
                    "text",
                    ""
                )
            )
        )

# ============================================================
# HISTORY
# ============================================================

@app.route("/history")
def history():

    articles = get_all_articles()

    return render_template(
        "history.html",
        articles=articles
    )


# ============================================================
# SEARCH
# ============================================================

@app.route("/search")
def search():

    query = request.args.get(
        "q",
        ""
    ).strip()

    results = []

    if query:
        results = search_articles(query)

    return render_template(
        "search.html",
        results=results,
        query=query
    )


# ============================================================
# DELETE ARTICLE
# ============================================================

@app.route(
    "/delete/<int:article_id>",
    methods=["POST", "GET"]
)
def delete(article_id):

    delete_article(
        article_id
    )


    flash(
        "Article deleted successfully.",
        "success"
    )


    return redirect(
        url_for("history")
    )


# ============================================================
# ABOUT
# ============================================================

@app.route("/about")
def about():

    return render_template(
        "about.html"
    )


# ============================================================
# ERROR HANDLERS
# ============================================================

@app.errorhandler(404)
def page_not_found(error):

    return """
        <h1>404 - Page Not Found</h1>

        <p>
            The requested page does not exist.
        </p>
    """, 404


@app.errorhandler(500)
def internal_error(error):

    return """
        <h1>500 - Internal Server Error</h1>

        <p>
            Please check the VS Code terminal for details.
        </p>
    """, 500


# ============================================================
# RUN APPLICATION
# ============================================================

if __name__ == "__main__":

    print("=" * 60)

    print(
        "           NEWSCOPE AI"
    )

    print("=" * 60)


    print(
        "Tesseract:",
        TESSERACT_PATH
    )


    print(
        "OCR Languages:",
        OCR_LANGUAGES
    )


    try:

        check_tesseract()

    except Exception as error:

        print(
            "WARNING:",
            error
        )


    print(
        "Server starting..."
    )


    print(
        "Open: http://127.0.0.1:5000"
    )


    print("=" * 60)


    app.run(
        debug=True
    )
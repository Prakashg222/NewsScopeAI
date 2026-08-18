import re


# ============================================================
# OPTIONAL ENGLISH TRANSLATION
# ============================================================

try:
    from deep_translator import GoogleTranslator
except ImportError:
    GoogleTranslator = None


# ============================================================
# SENTIMENT WORDS
# ============================================================

POSITIVE_WORDS = [
    "good", "great", "success", "successful", "positive",
    "growth", "improve", "improved", "benefit", "benefits",
    "excellent", "happy", "progress", "achievement",
    "achieved", "development", "innovation", "innovative",
    "strong", "win", "winning", "increase", "increased",
    "better", "rise", "rising", "gain", "gains"
]


NEGATIVE_WORDS = [
    "bad", "negative", "failure", "failed", "crisis",
    "problem", "danger", "decline", "loss", "attack",
    "war", "threat", "death", "dead", "corruption",
    "scandal", "crime", "violence", "decrease",
    "decreased", "worse", "risk", "fall", "falling",
    "drop", "dropped", "injury", "killed"
]


# ============================================================
# CATEGORY KEYWORDS
# ============================================================

CATEGORY_KEYWORDS = {

    "Technology": [
        "technology",
        "software",
        "ai",
        "artificial intelligence",
        "computer",
        "internet",
        "robot",
        "digital",
        "programming",
        "cyber",
        "data",
        "machine learning",
        "python",
        "application",
        "smartphone",
        "mobile",
        "electric vehicle"
    ],

    "Education": [
        "education",
        "school",
        "college",
        "university",
        "student",
        "teacher",
        "exam",
        "learning",
        "classroom",
        "course",
        "degree",
        "campus",
        "education policy",
        "students"
    ],

    "Politics": [
        "government",
        "minister",
        "election",
        "politics",
        "political",
        "president",
        "parliament",
        "vote",
        "party",
        "policy",
        "leader",
        "chief minister",
        "prime minister"
    ],

    "Sports": [
        "cricket",
        "football",
        "sports",
        "match",
        "player",
        "team",
        "tournament",
        "championship",
        "goal",
        "coach",
        "league",
        "world cup"
    ],

    "Business": [
        "business",
        "company",
        "market",
        "stock",
        "finance",
        "investment",
        "profit",
        "sales",
        "startup",
        "economy",
        "economic",
        "revenue",
        "industry",
        "vehicle sales"
    ],

    "Health": [
        "health",
        "hospital",
        "doctor",
        "medicine",
        "medical",
        "disease",
        "patient",
        "treatment",
        "healthcare",
        "virus",
        "hospital",
        "health department"
    ],

    "Travel": [
        "travel",
        "tourism",
        "tourist",
        "holiday",
        "hotel",
        "flight",
        "airport",
        "trip",
        "destination",
        "tour",
        "journey"
    ]
}


# ============================================================
# LANGUAGE DETECTION
# ============================================================

def detect_language(text):

    if not text:
        return "Unknown"

    telugu_count = len(
        re.findall(
            r"[\u0C00-\u0C7F]",
            text
        )
    )

    hindi_count = len(
        re.findall(
            r"[\u0900-\u097F]",
            text
        )
    )

    english_count = len(
        re.findall(
            r"[A-Za-z]",
            text
        )
    )

    counts = {
        "Telugu": telugu_count,
        "Hindi": hindi_count,
        "English": english_count
    }

    detected = max(
        counts,
        key=counts.get
    )

    if counts[detected] == 0:
        return "Unknown"

    return detected


# ============================================================
# BASIC OCR CLEANING
# ============================================================

def clean_ocr_text(text):

    if not text:
        return ""

    # Normalize line endings
    text = text.replace(
        "\r\n",
        "\n"
    )

    text = text.replace(
        "\r",
        "\n"
    )

    # Remove excessive spaces
    text = re.sub(
        r"[ \t]+",
        " ",
        text
    )

    # Remove excessive blank lines
    text = re.sub(
        r"\n{3,}",
        "\n\n",
        text
    )

    # Remove obvious isolated OCR garbage
    cleaned_lines = []

    for line in text.splitlines():

        line = line.strip()

        if not line:
            continue

        # Ignore extremely short fragments
        if len(line) <= 2:
            continue

        # Keep useful lines
        cleaned_lines.append(line)

    text = "\n".join(
        cleaned_lines
    )

    return text.strip()


# ============================================================
# TRANSLATE TO ENGLISH
# ============================================================

def translate_to_english(text):

    if not text:
        return ""

    language = detect_language(text)

    # Already English
    if language == "English":
        return text

    # If no translator package is installed,
    # return original text rather than crashing.
    if GoogleTranslator is None:

        print(
            "WARNING: deep-translator is not installed."
        )

        print(
            "Run: pip install deep-translator"
        )

        return text

    try:

        # GoogleTranslator handles automatic
        # source language detection.

        translator = GoogleTranslator(
            source="auto",
            target="en"
        )

        # Translate in chunks because very large
        # newspaper articles can exceed translator limits.

        paragraphs = text

        translated_parts = []

        for paragraph in paragraphs:

            paragraph = paragraph.strip()

            if not paragraph:
                continue

            try:

                translated = translator.translate(
                    paragraph
                )

                if translated:
                    translated_parts.append(
                        translated
                    )

            except Exception as error:

                print(
                    "Translation warning:",
                    error
                )

                translated_parts.append(
                    paragraph
                )

        return "\n".join(
            translated_parts
        ).strip()

    except Exception as error:

        print(
            "Translation error:",
            error
        )

        return text


# ============================================================
# SENTENCE EXTRACTION
# ============================================================

def split_sentences(text):

    if not text:
        return []

    # Normalize newlines
    text = re.sub(
        r"\s*\n\s*",
        " ",
        text
    )

    # Split English + common Indian punctuation
    sentences = re.split(
        r"(?<=[.!?।])\s+",
        text
    )

    result = []

    for sentence in sentences:

        sentence = re.sub(
            r"\s+",
            " ",
            sentence
        ).strip()

        if not sentence:
            continue

        # Ignore tiny OCR fragments
        if len(sentence) < 35:
            continue

        # Ignore lines containing mostly garbage symbols
        letters = len(
            re.findall(
                r"[A-Za-z]",
                sentence
            )
        )

        total = len(sentence)

        if total > 0:

            letter_ratio = (
                letters / total
            )

            if letter_ratio < 0.25:
                continue

        result.append(
            sentence
        )

    return result


# ============================================================
# REMOVE DUPLICATE SENTENCES
# ============================================================

def remove_duplicate_sentences(sentences):

    result = []

    seen = set()

    for sentence in sentences:

        normalized = re.sub(
            r"[^a-z0-9]+",
            " ",
            sentence.lower()
        ).strip()

        if not normalized:
            continue

        if normalized in seen:
            continue

        seen.add(normalized)

        result.append(
            sentence
        )

    return result


# ============================================================
# SENTENCE QUALITY
# ============================================================

def sentence_quality(sentence):

    if not sentence:
        return 0

    words = sentence.split()

    if len(words) < 6:
        return 0

    score = 0

    # Complete-looking sentences are preferred
    if sentence.endswith(
        (".", "!", "?")
    ):
        score += 3

    # Prefer reasonable length
    if 10 <= len(words) <= 45:
        score += 3

    elif len(words) > 45:
        score += 1

    # Penalize suspicious OCR
    garbage_patterns = [
        r"\b[a-z]{1,2}\b",
        r"[|]{2,}",
        r"[~`^]{2,}",
        r"\b[0-9]{1,2}\b"
    ]

    for pattern in garbage_patterns:

        if re.search(
            pattern,
            sentence,
            re.IGNORECASE
        ):
            score -= 1

    return score


# ============================================================
# MAIN POINT EXTRACTION
# ============================================================

def extract_main_points(
    text,
    minimum=7,
    maximum=10
):

    sentences = split_sentences(
        text
    )

    sentences = remove_duplicate_sentences(
        sentences
    )

    if not sentences:

        return [
            "The article could not be converted into enough clear sentences for a reliable summary."
        ]

    # --------------------------------------------------------
    # Important words
    # --------------------------------------------------------

    important_words = set(
        POSITIVE_WORDS
        + NEGATIVE_WORDS
    )

    for keywords in CATEGORY_KEYWORDS.values():

        important_words.update(
            keywords
        )

    # --------------------------------------------------------
    # Score sentences
    # --------------------------------------------------------

    scored = []

    for index, sentence in enumerate(sentences):

        lower = sentence.lower()

        keyword_score = 0

        for word in important_words:

            if word.lower() in lower:

                keyword_score += 1

        quality = sentence_quality(
            sentence
        )

        # Earlier sentences often contain
        # the article's main story.

        position_bonus = max(
            0,
            5 - index
        )

        total_score = (
            keyword_score * 3
            + quality
            + position_bonus
        )

        scored.append(
            (
                total_score,
                index,
                sentence
            )
        )

    # Highest scoring first
    scored.sort(
        key=lambda item: item[0],
        reverse=True
    )

    selected = []

    for _, index, sentence in scored:

        # Don't select extremely similar sentences
        duplicate = False

        for existing in selected:

            words_a = set(
                sentence.lower().split()
            )

            words_b = set(
                existing.lower().split()
            )

            if not words_a or not words_b:
                continue

            overlap = (
                len(words_a & words_b)
                /
                max(
                    len(words_a | words_b),
                    1
                )
            )

            if overlap > 0.65:

                duplicate = True
                break

        if duplicate:
            continue

        selected.append(
            sentence
        )

        if len(selected) >= maximum:
            break

    # If fewer than 7 good points were found,
    # use additional good sentences.

    if len(selected) < minimum:

        for sentence in sentences:

            if sentence in selected:
                continue

            if sentence_quality(sentence) <= 0:
                continue

            selected.append(
                sentence
            )

            if len(selected) >= minimum:
                break

    # --------------------------------------------------------
    # Keep article order
    # --------------------------------------------------------

    order_map = {
        sentence: index
        for index, sentence
        in enumerate(sentences)
    }

    selected.sort(
        key=lambda sentence:
        order_map.get(
            sentence,
            999999
        )
    )

    # --------------------------------------------------------
    # Clean every point
    # --------------------------------------------------------

    final_points = []

    for sentence in selected:

        sentence = re.sub(
            r"\s+",
            " ",
            sentence
        ).strip()

        # Never cut the sentence with [:300]
        # or any character limit.

        if not sentence:
            continue

        # Ensure punctuation
        if not sentence.endswith(
            (".", "!", "?")
        ):

            sentence += "."

        final_points.append(
            sentence
        )

    return final_points[:maximum]


# ============================================================
# SUMMARY GENERATION
# ============================================================

def generate_summary(
    text,
    main_points
):

    if not text:
        return (
            "No readable article content was available."
        )

    sentences = split_sentences(
        text
    )

    sentences = remove_duplicate_sentences(
        sentences
    )

    if not sentences:

        return (
            "The article could not be summarized because the extracted text was not clear enough."
        )

    # Select a small number of the strongest
    # sentences for a paragraph.

    summary_sentences = []

    for sentence in sentences:

        if sentence_quality(sentence) <= 0:
            continue

        summary_sentences.append(
            sentence
        )

        if len(summary_sentences) >= 4:
            break

    if not summary_sentences:

        summary_sentences = sentences[:3]

    summary = " ".join(
        summary_sentences
    )

    # Make it a single readable paragraph
    summary = re.sub(
        r"\s+",
        " ",
        summary
    ).strip()

    return summary


# ============================================================
# TITLE GENERATION
# ============================================================

def generate_title(
    text,
    category
):

    sentences = split_sentences(
        text
    )

    if not sentences:

        return "Article Analysis"

    first_sentence = sentences[0]

    # Remove unnecessary punctuation
    first_sentence = re.sub(
        r"\s+",
        " ",
        first_sentence
    ).strip()

    # If the sentence is very long,
    # use its first meaningful portion.
    words = first_sentence.split()

    if len(words) > 14:

        title = " ".join(
            words[:14]
        )

        title = title.rstrip(
            ".,!?;:"
        )

    else:

        title = first_sentence.rstrip(
            ".,!?;:"
        )

    if not title:

        title = (
            f"{category} News Analysis"
        )

    return title


# ============================================================
# SENTIMENT
# ============================================================

def calculate_sentiment(text):

    text_lower = text.lower()

    positive_score = 0
    negative_score = 0

    for word in POSITIVE_WORDS:

        positive_score += text_lower.count(
            word.lower()
        )

    for word in NEGATIVE_WORDS:

        negative_score += text_lower.count(
            word.lower()
        )

    if positive_score > negative_score:

        sentiment = "Positive"

    elif negative_score > positive_score:

        sentiment = "Negative"

    else:

        sentiment = "Neutral"

    return (
        sentiment,
        positive_score,
        negative_score
    )


# ============================================================
# CATEGORY
# ============================================================

def calculate_category(text):

    text_lower = text.lower()

    category_scores = {}

    for category, keywords in CATEGORY_KEYWORDS.items():

        score = 0

        for keyword in keywords:

            score += text_lower.count(
                keyword.lower()
            )

        category_scores[category] = score

    category = max(
        category_scores,
        key=category_scores.get
    )

    if category_scores[category] == 0:

        category = "General"

    return (
        category,
        category_scores
    )


# ============================================================
# CONFIDENCE
# ============================================================

def calculate_confidence(
    text,
    category_scores,
    positive_score,
    negative_score
):

    word_count = len(
        re.findall(
            r"\b\w+\b",
            text,
            flags=re.UNICODE
        )
    )

    category_evidence = max(
        category_scores.values()
    ) if category_scores else 0

    sentiment_evidence = (
        positive_score
        + negative_score
    )

    confidence = 50

    confidence += min(
        20,
        category_evidence * 3
    )

    confidence += min(
        15,
        sentiment_evidence * 2
    )

    if word_count >= 100:
        confidence += 5

    if word_count >= 300:
        confidence += 5

    return max(
        50,
        min(
            95,
            round(confidence)
        )
    )


# ============================================================
# COMPLETE ARTICLE ANALYSIS
# ============================================================

def analyze_article(text):

    if not text or not text.strip():

        return {

            "title": "Article Analysis",

            "summary":
                "No readable article content was available.",

            "language": "Unknown",

            "sentiment": "Neutral",

            "category": "General",

            "confidence": 50,

            "word_count": 0,

            "positive_score": 0,

            "negative_score": 0,

            "main_points": [
                "No clear article information was available for analysis."
            ]

        }

    # --------------------------------------------------------
    # CLEAN OCR
    # --------------------------------------------------------

    cleaned_text = clean_ocr_text(
        text
    )

    # --------------------------------------------------------
    # DETECT ORIGINAL LANGUAGE
    # --------------------------------------------------------

    language = detect_language(
        cleaned_text
    )

    # --------------------------------------------------------
    # TRANSLATE TO ENGLISH
    # --------------------------------------------------------

    english_text = translate_to_english(
        cleaned_text
    )

    # Clean translated text again
    english_text = clean_ocr_text(
        english_text
    )

    # --------------------------------------------------------
    # SENTIMENT
    # --------------------------------------------------------

    (
        sentiment,
        positive_score,
        negative_score
    ) = calculate_sentiment(
        english_text
    )
    #--------------------------------------------------------
    # CATEGORY
    # --------------------------------------------------------

    (
        category,
        category_scores
    ) = calculate_category(
        english_text
    )

    # --------------------------------------------------------
    # WORD COUNT
    # --------------------------------------------------------

    word_count = len(
        re.findall(
            r"\b\w+\b",
            english_text,
            flags=re.UNICODE
        )
    )

    # --------------------------------------------------------
    # MAIN POINTS
    # --------------------------------------------------------

    main_points = extract_main_points(
        english_text,
        minimum=7,
        maximum=10
    )

    # --------------------------------------------------------
    # SUMMARY
    # --------------------------------------------------------

    summary = generate_summary(
        english_text,
        main_points
    )

    # --------------------------------------------------------
    # TITLE
    # --------------------------------------------------------

    title = generate_title(
        english_text,
        category
    )

    # --------------------------------------------------------
    # CONFIDENCE
    # --------------------------------------------------------

    confidence = calculate_confidence(
        english_text,
        category_scores,
        positive_score,
        negative_score
    )

    # --------------------------------------------------------
    # RESULT
    # --------------------------------------------------------

    return {

        "title": title,

        "summary": summary,

        "language": language,

        "sentiment": sentiment,

        "category": category,

        "confidence": confidence,

        "word_count": word_count,

        "positive_score": positive_score,

        "negative_score": negative_score,

        "main_points": main_points

    }
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def calculate_ats_score(resume_text, required_skills):

    if not resume_text or not required_skills:
        return 0, [], []

    resume_text = resume_text.lower()

    # -----------------------------
    # 1️⃣ WEIGHTED SKILL MATCHING
    # -----------------------------

    skills = re.split(r',|\n', required_skills)

    total_weight = 0
    matched_weight = 0

    matched = []
    missing = []

    for item in skills:

        item = item.strip()
        if not item:
            continue

        # Handle weighted skill (python:3)
        if ":" in item:
            parts = item.split(":")
            skill = parts[0].strip()
            try:
                weight = int(parts[1].strip())
            except ValueError:
                weight = 1
        else:
            skill = item
            weight = 1

        skill = skill.lower()
        total_weight += weight

        pattern = r'\b' + re.escape(skill) + r'\b'

        if re.search(pattern, resume_text):
            matched.append(skill)
            matched_weight += weight
        else:
            missing.append(skill)

    weighted_score = 0
    if total_weight > 0:
        weighted_score = (matched_weight / total_weight) * 100


    # -----------------------------
    # 2️⃣ NLP SIMILARITY SCORE
    # -----------------------------

    vectorizer = TfidfVectorizer(stop_words='english')

    try:
        tfidf_matrix = vectorizer.fit_transform(
            [resume_text, required_skills.lower()]
        )

        similarity = cosine_similarity(
            tfidf_matrix[0:1],
            tfidf_matrix[1:2]
        )[0][0]

        nlp_score = similarity * 100

    except:
        nlp_score = 0


    # -----------------------------
    # 3️⃣ FINAL COMBINED SCORE
    # -----------------------------
    # 60% weighted skill + 40% NLP similarity

    final_score = (weighted_score * 0.6) + (nlp_score * 0.4)

    return round(final_score, 2), matched[:10], missing[:10]
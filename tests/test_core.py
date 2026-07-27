from aidetect import analyze_text, detect_language


def test_short_text_is_insufficient():
    result = analyze_text("Too short.")
    assert result.verdict == "insufficient_text"
    assert result.confidence == "low"
    assert result.word_count < 80
    assert result.next_steps
    assert "too short" in result.conclusion.lower()


def test_long_text_returns_evidence():
    text = " ".join([
        "In conclusion, it is important to note that this comprehensive overview provides a nuanced perspective.",
        "First, the system considers multiple signals. Moreover, it avoids making absolute claims.",
        "However, the result should be treated as a risk estimate rather than proof.",
    ] * 8)
    result = analyze_text(text)
    assert 0 <= result.score <= 100
    assert result.signals
    assert result.verdict in {"low_ai_likelihood", "mixed_or_uncertain", "high_ai_likelihood"}
    assert result.strongest_signals()


def test_ai_like_sample_scores_higher_than_human_like_sample():
    ai_like = " ".join([
        "In conclusion, it is important to note that this comprehensive overview provides a nuanced perspective.",
        "First, the framework unlocks not only meaningful productivity but also sustainable long-term value.",
        "Moreover, the solution is a testament to the importance of careful planning and structured execution.",
        "Ultimately, this approach offers a robust and comprehensive path forward for modern teams.",
    ] * 16)
    human_like = " ".join([
        "I left the meeting with three messy notes and a coffee ring on the page.",
        "The first idea sounded clever in the room, but it fell apart when Mara asked who would maintain it.",
        "We argued for ten minutes, crossed out two assumptions, and kept the one boring fix that would actually ship.",
        "By Friday the patch was small, readable, and a little less glamorous than the pitch.",
    ] * 16)

    assert analyze_text(ai_like).score > analyze_text(human_like).score


def test_detect_language_identifies_arabic_english_and_mixed():
    assert detect_language("هذا نص عربي بالكامل وليس فيه أي كلمات أجنبية على الإطلاق") == "ar"
    assert detect_language("This is a fully English sentence with no other script at all.") == "en"
    assert detect_language("This sentence has بعض الكلمات العربية mixed in with English words too") == "mixed"


def test_arabic_ai_like_sample_scores_higher_than_arabic_human_like_sample():
    ai_like_ar = " ".join([
        "من الجدير بالذكر أن هذا الموضوع يحظى باهتمام كبير في الآونة الأخيرة والعصر الحالي.",
        "علاوة على ذلك فإن التحليل الشامل يوضح أهمية النهج المتكامل في معالجة القضية المطروحة.",
        "وفي الختام يمكن القول إن هذا الأمر يمثل شهادة على أهمية التخطيط الدقيق والتنفيذ المنظم.",
    ] * 12)
    human_like_ar = " ".join([
        "خرجت من الاجتماع وفي يدي ورقة فيها ثلاث ملاحظات متعثرة وأثر كوب قهوة على الحافة.",
        "الفكرة بدت ذكية داخل الغرفة لكنها انهارت لما سأل أحمد مين اللي رح يكمل عليها بعدين.",
        "تجادلنا لعشر دقايق وشطبنا افتراضين وخلينا بس الحل الممل اللي فعلا رح ينفذ.",
    ] * 12)

    ai_result = analyze_text(ai_like_ar)
    human_result = analyze_text(human_like_ar)

    assert ai_result.language == "ar"
    assert human_result.language == "ar"
    assert ai_result.score > human_result.score


def test_result_dict_contains_public_contract_fields():
    text = " ".join([
        "This paragraph has enough words to exercise the public result contract.",
        "It should include the score, confidence, conclusion, caveats, next steps, and weighted evidence signals.",
    ] * 10)

    data = analyze_text(text).to_dict()

    assert {"score", "verdict", "confidence", "word_count", "conclusion", "signals", "caveats", "next_steps"} <= set(data)

import os

import pytest

# These tests load real model weights (downloading them on first run), so they
# only run when explicitly opted into - avoids slow/flaky CI runs that don't
# have the models pre-cached. Run locally with: AIDETECT_RUN_ML_TESTS=1 pytest
pytestmark = pytest.mark.skipif(
    os.environ.get("AIDETECT_RUN_ML_TESTS") != "1",
    reason="set AIDETECT_RUN_ML_TESTS=1 to run real local-model ML layer tests",
)

pytest.importorskip("transformers")
pytest.importorskip("torch")

from aidetect import ml_layer  # noqa: E402


AI_LIKE_AR = (
    "من الجدير بالذكر أن هذا الموضوع يحظى باهتمام كبير في الآونة الأخيرة والعصر الحالي. "
    "علاوة على ذلك فإن التحليل الشامل يوضح أهمية النهج المتكامل في معالجة القضية المطروحة. "
    "وفي الختام يمكن القول إن هذا الأمر يمثل شهادة على أهمية التخطيط الدقيق والتنفيذ المنظم. "
    "ومن ناحية أخرى تجدر الإشارة إلى ضرورة مراعاة الجوانب المختلفة لهذا الموضوع الهام جدا."
)

HUMAN_LIKE_AR = (
    "خرجت من الاجتماع وفي يدي ورقة فيها ثلاث ملاحظات متعثرة وأثر كوب قهوة على الحافة. "
    "الفكرة بدت ذكية داخل الغرفة لكنها انهارت لما سأل أحمد مين اللي رح يكمل عليها بعدين. "
    "تجادلنا لعشر دقايق وشطبنا افتراضين وخلينا بس الحل الممل اللي فعلا رح ينفذ على أرض الواقع. "
    "يوم الخميس صار التعديل صغير ومفهوم واقل بريقا من العرض الاول اللي قدمناه بالبداية."
)

AI_LIKE_EN = (
    "It is important to note that this comprehensive overview provides a nuanced perspective "
    "on the subject at hand. Moreover, the framework unlocks not only meaningful productivity "
    "but also sustainable long-term value for every stakeholder involved in the process. "
    "Furthermore, it is worth highlighting that a holistic approach ensures every dimension of "
    "the problem is addressed in a structured and comprehensive manner. In conclusion, this "
    "represents a testament to the importance of careful planning, and it offers a robust path "
    "forward for teams navigating similarly complex challenges in the modern landscape overall."
)

HUMAN_LIKE_EN = (
    "I left the meeting with three messy notes and a coffee ring on the page from this morning. "
    "The first idea sounded clever in the room, but it fell apart the moment Mara asked who would "
    "actually maintain it once the initial excitement wore off. We argued for a good ten minutes, "
    "crossed out two shaky assumptions, and eventually settled on the one boring fix that would "
    "genuinely ship on time. By Friday the patch was small, a little unglamorous, and honestly a "
    "lot less impressive than the original pitch, but at least nobody had to pretend it worked."
)


def test_arabic_model_label_mapping_is_not_inverted():
    ai_result = ml_layer.classify(AI_LIKE_AR, "ar")
    human_result = ml_layer.classify(HUMAN_LIKE_AR, "ar")

    assert ai_result.available and human_result.available
    assert ai_result.label == "AI"
    assert human_result.label == "HUMAN"
    assert ai_result.ai_probability > 0.7
    assert human_result.ai_probability < 0.3


def test_english_model_label_mapping_is_not_inverted():
    ai_result = ml_layer.classify(AI_LIKE_EN, "en")
    human_result = ml_layer.classify(HUMAN_LIKE_EN, "en")

    assert ai_result.available and human_result.available
    assert "AI" in ai_result.label
    assert human_result.label == "Human"
    assert ai_result.ai_probability > 0.7
    assert human_result.ai_probability < 0.3

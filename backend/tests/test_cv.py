import io
import zipfile

import pytest

from core.cv.extract import MAX_CV_BYTES, extract_text
from core.cv.skills import LEVEL_ONCE, LEVEL_REPEATED, profile_skills_from_cv
from core.errors import ValidationFailed
from core.taxonomy import load_taxonomy

CV_TEXT = (
    "Summary: analyst who writes Python scripts for monthly reports. Python automation. "
    "Ran SQL queries on PostgreSQL. Microsoft Excel dashboards for the shop."
)


def _docx(paragraph: str) -> bytes:
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        f"<w:body><w:p><w:r><w:t>{paragraph}</w:t></w:r></w:p></w:body></w:document>"
    )
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("word/document.xml", xml)
    return buffer.getvalue()


def test_plain_text_is_read():
    text = extract_text("cv.txt", CV_TEXT.encode())
    assert "PostgreSQL" in text


def test_word_document_is_read_and_tags_removed():
    text = extract_text("cv.docx", _docx("Customer service &amp; cash handling at a bakery"))
    assert "Customer service & cash handling at a bakery" in text
    assert "<w:" not in text


def test_repeated_mentions_get_a_higher_level():
    skills = {s.slug: s for s in load_taxonomy()}
    found = profile_skills_from_cv(CV_TEXT, load_taxonomy())
    assert found[skills["python"].skill_id].level == LEVEL_REPEATED
    assert found[skills["sql"].skill_id].level == LEVEL_ONCE
    assert found[skills["postgresql"].skill_id].level == LEVEL_ONCE


def test_text_with_no_known_skills_finds_nothing():
    assert profile_skills_from_cv("I like long walks and the colour blue.", load_taxonomy()) == {}


@pytest.mark.parametrize(
    "filename, data, message",
    [
        ("cv.txt", b"", "empty"),
        ("cv.exe", CV_TEXT.encode(), "upload a PDF"),
        ("cv.txt", b"x" * (MAX_CV_BYTES + 1), "5 MB"),
        ("cv.pdf", b"not really a pdf but long enough to pass the length check", "not a valid PDF"),
        ("cv.docx", b"plain text pretending to be a zip file", "not a valid Word"),
        ("cv.txt", b"too short", "enough text"),
    ],
)
def test_unreadable_uploads_are_rejected_with_a_clear_message(filename, data, message):
    with pytest.raises(ValidationFailed, match=message):
        extract_text(filename, data)

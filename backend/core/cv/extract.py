import html
import io
import re
import zipfile
from pathlib import Path

from core.errors import ValidationFailed

MAX_CV_BYTES = 5 * 1024 * 1024
MAX_PDF_PAGES = 30
MAX_DOCX_TEXT_BYTES = 20 * 1024 * 1024
MIN_TEXT_CHARS = 40
MAX_TEXT_CHARS = 200_000

SUPPORTED_TYPES = frozenset({".pdf", ".docx", ".txt", ".md"})

_TAG = re.compile(r"<[^>]+>")
_PARAGRAPH_END = re.compile(r"</w:p>|<w:br/>|<w:tab/>")


def extract_text(filename: str, data: bytes) -> str:
    """Reads plain text from an uploaded CV. The file itself is never stored (see docs/FRONTEND.md, privacy)."""
    if not data:
        raise ValidationFailed("the file is empty")
    if len(data) > MAX_CV_BYTES:
        raise ValidationFailed("the CV must be 5 MB or smaller")

    suffix = Path(filename or "").suffix.lower()
    if suffix not in SUPPORTED_TYPES:
        raise ValidationFailed("upload a PDF, Word (.docx) or plain text file")

    if suffix == ".pdf":
        if not data.startswith(b"%PDF"):
            raise ValidationFailed("this file is not a valid PDF")
        text = _pdf_text(data)
    elif suffix == ".docx":
        if not data.startswith(b"PK"):
            raise ValidationFailed("this file is not a valid Word document")
        text = _docx_text(data)
    else:
        text = data.decode("utf-8", errors="replace")

    text = " ".join(text.split())
    if len(text) < MIN_TEXT_CHARS:
        raise ValidationFailed(
            "we could not read enough text from this file. Scanned images are not supported yet; "
            "try a text-based PDF or a Word document"
        )
    return text[:MAX_TEXT_CHARS]


def _pdf_text(data: bytes) -> str:
    from pypdf import PdfReader
    from pypdf.errors import PdfReadError

    try:
        reader = PdfReader(io.BytesIO(data))
        if reader.is_encrypted:
            reader.decrypt("")
        if len(reader.pages) > MAX_PDF_PAGES:
            raise ValidationFailed(f"the CV must be {MAX_PDF_PAGES} pages or fewer")
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    except ValidationFailed:
        raise
    except (PdfReadError, ValueError, KeyError, IndexError, TypeError) as exc:
        raise ValidationFailed("we could not open this PDF. Try saving it again, or upload a Word document") from exc


def _docx_text(data: bytes) -> str:
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            info = archive.getinfo("word/document.xml")
            if info.file_size > MAX_DOCX_TEXT_BYTES:
                raise ValidationFailed("this Word document is too large to read")
            xml = archive.read("word/document.xml").decode("utf-8", errors="replace")
    except ValidationFailed:
        raise
    except (zipfile.BadZipFile, KeyError) as exc:
        raise ValidationFailed("we could not open this Word document") from exc
    xml = _PARAGRAPH_END.sub("\n", xml)
    return html.unescape(_TAG.sub(" ", xml))

from hashlib import sha256
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, Form, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI()
app.mount("/static", StaticFiles(directory=str(BASE_DIR)), name="static")

templates = Jinja2Templates(directory=str(BASE_DIR))

################
## Load Words ##
################


def _load_words(filename: str) -> list[str]:
    with (BASE_DIR / filename).open() as word_file:
        return [line.strip() for line in word_file if line.strip()]


ADJECTIVES = _load_words("adjectives.txt")
NOUNS = _load_words("nouns.txt")

#############
## Helpers ##
#############


def _generate_codename(input_text: str) -> str:
    """Generates a codename based on the input text using a deterministic hashing approach."""
    digest = sha256(input_text.strip().lower().encode("utf-8")).digest()

    adjective_index = int.from_bytes(digest[:8], "big") % len(ADJECTIVES)
    noun_index = int.from_bytes(digest[8:16], "big") % len(NOUNS)

    adjective = ADJECTIVES[adjective_index].title()
    noun = NOUNS[noun_index].title()

    return f"{adjective} {noun}"


def _render_html_template(
    request: Request,
    input_text: str = "",
    codename: str | None = None,
    error_title: str | None = None,
    error_hint: str | None = None,
    status_code: int = status.HTTP_200_OK,
):
    """Renders the HTML template with the current form state."""
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "input_text": input_text,
            "codename": codename,
            "error_title": error_title,
            "error_hint": error_hint,
        },
        status_code=status_code,
    )


def _validation_error_hint(exc: RequestValidationError) -> str:
    for error in exc.errors():
        if error.get("type") != "missing":
            continue

        location = error.get("loc", ())
        if "input_text" in location:
            return "No identifier provided"

    return "Bad data"


##############
## Handlers ##
##############


@app.exception_handler(RequestValidationError)
async def handle_validation_error(request: Request, exc: RequestValidationError):
    """Renders form validation errors inside the main application shell."""
    return _render_html_template(
        request=request,
        error_title="Transmission rejected",
        error_hint=_validation_error_hint(exc),
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
    )


@app.get("/")
async def index(request: Request):
    """Returns the HTML file."""
    return _render_html_template(request=request)


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    """Serves the application favicon from the app directory."""
    return FileResponse(BASE_DIR / "favicon.ico")


@app.post("/")
async def process_submission(input_text: Annotated[str, Form()], request: Request):
    """Handles form submission and returns a deterministic codename."""
    normalized_input = input_text.strip().lower()

    return _render_html_template(
        request=request,
        input_text=normalized_input,
        codename=_generate_codename(normalized_input),
    )

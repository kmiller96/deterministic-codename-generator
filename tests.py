import random
import re
import string

from fastapi.exceptions import RequestValidationError
from fastapi.testclient import TestClient

from app.main import _validation_error_hint, app


client = TestClient(app)

#############
## Helpers ##
#############


def _extract_codename(html: str) -> str | None:
    """Extracts the generated codename from the #codename span in the HTML response."""
    match = re.search(r'<span\s+id="codename">([^<]+)</span>', html)

    if match is None:
        return None

    return match.group(1)


def _random_string(length: int = 24) -> str:
    """Generates a random string of the specified length, consisting of letters and digits."""
    alphabet = string.ascii_letters + string.digits
    return "".join(random.choices(alphabet, k=length))


###########
## Tests ##
###########


def test_get_root_returns_html_response():
    """Verify GET / returns an HTML response."""
    response = client.get("/")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert 'rel="icon" href="/favicon.ico"' in response.text


def test_get_favicon_returns_icon_response():
    """Verify GET /favicon.ico serves the uploaded favicon."""
    response = client.get("/favicon.ico")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("image/x-icon")
    assert len(response.content) > 0


def test_form_post_returns_generated_codename():
    """Verify POST / returns a rendered codename for valid form input."""
    response = client.post("/", data={"input_text": "Example Input"})

    assert response.status_code == 200
    assert _extract_codename(response.text) is not None


def test_generated_codename_is_the_same_regardless_of_case():
    """Verify mixed-case inputs map to the same codename."""
    uppercase_response = client.post("/", data={"input_text": "EXAMPLE INPUT"})
    lowercase_response = client.post("/", data={"input_text": "example input"})

    assert uppercase_response.status_code == 200
    assert lowercase_response.status_code == 200

    uppercase_codename = _extract_codename(uppercase_response.text)
    lowercase_codename = _extract_codename(lowercase_response.text)
    assert uppercase_codename == lowercase_codename


def test_unique_random_inputs_return_unique_codenames():
    """Verify distinct random inputs produce distinct codenames."""
    MAX_ATTEMPTS = 100

    ## Generate the inputs ##
    inputs = set()
    while len(inputs) < MAX_ATTEMPTS:
        inputs.add(_random_string())

    ## Verify the codenames ##
    codenames = set()
    for input_text in inputs:
        response = client.post("/", data={"input_text": input_text})

        assert response.status_code == 200

        codename = _extract_codename(response.text)
        assert codename not in codenames, (
            f"Duplicate codename '{codename}' generated for input '{input_text}'"
        )
        codenames.add(codename)


def test_bad_post_returns_error():
    """Missing required form input returns a themed validation error page."""
    response = client.post("/", data={})

    assert response.status_code == 422
    assert response.headers["content-type"].startswith("text/html")
    assert "Transmission rejected" in response.text
    assert "Hint: No identifier provided" in response.text
    assert _extract_codename(response.text) is None


def test_unrecognized_validation_error_returns_generic_hint():
    """Unexpected validation failures fall back to a generic hint."""
    exc = RequestValidationError(
        errors=[
            {
                "type": "string_type",
                "loc": ("body", "input_text"),
                "msg": "Input should be a valid string",
                "input": ["not", "a", "string"],
            }
        ]
    )

    assert _validation_error_hint(exc) == "Bad data"

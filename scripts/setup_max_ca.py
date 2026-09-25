"""Download official Russian CA for this project only; no OS trust changes."""

import ssl
from pathlib import Path

import httpx

SOURCE = "https://gu-st.ru/content/Other/doc/russian_trusted_root_ca.cer"
DESTINATION = (
    Path(__file__).resolve().parents[1] / "data/certs/russian-trusted-root.pem"
)


def main() -> None:
    response = httpx.get(SOURCE, timeout=30, follow_redirects=True)
    response.raise_for_status()
    content = response.content
    if b"BEGIN CERTIFICATE" not in content:
        content = ssl.DER_cert_to_PEM_cert(content).encode()
    # Parse before writing. HTTPS verification on the download stays enabled.
    ssl.create_default_context().load_verify_locations(cadata=content.decode("ascii"))
    DESTINATION.parent.mkdir(parents=True, exist_ok=True)
    DESTINATION.write_bytes(content)
    print(
        "CA сохранён. Добавьте в .env: MAX_CA_BUNDLE_FILE=data/certs/russian-trusted-root.pem"
    )


if __name__ == "__main__":
    main()

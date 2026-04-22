import base64
import logging
import os
import re
from datetime import datetime, timezone
from pathlib import Path

import pymongo
import requests
from bs4 import BeautifulSoup
from flask import Flask, render_template, request


logging.basicConfig(
    filename="scrapper.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)

app = Flask(__name__)

BASE_DIR = Path(__file__).resolve().parent
DOWNLOAD_DIR = BASE_DIR / "static" / "downloads"
BING_IMAGE_SEARCH_URL = "https://www.bing.com/images/search"
MAX_RESULTS = 10
REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}
EXTENSION_BY_MIME = {
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
}


def slugify_query(query: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", query.strip().lower())
    return slug.strip("_") or "images"


def prepare_output_directory(query: str) -> Path:
    query_dir = DOWNLOAD_DIR / slugify_query(query)
    query_dir.mkdir(parents=True, exist_ok=True)

    for existing_file in query_dir.iterdir():
        if existing_file.is_file():
            existing_file.unlink()

    return query_dir


def extract_image_candidates(html: str) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    candidates = []

    for image_tag in soup.select("img.mimg"):
        source = (
            image_tag.get("src")
            or image_tag.get("data-src")
            or image_tag.get("data-src-hq")
        )
        if not source:
            continue
        if not source.startswith(("http", "data:image")):
            continue
        if source not in candidates:
            candidates.append(source)

    return candidates


def parse_data_uri(source: str) -> tuple[bytes, str]:
    header, encoded = source.split(",", 1)
    mime_type = header.split(";")[0].replace("data:", "")
    extension = EXTENSION_BY_MIME.get(mime_type, ".jpg")
    return base64.b64decode(encoded), extension


def download_image(source: str) -> tuple[bytes, str]:
    if source.startswith("data:image"):
        return parse_data_uri(source)

    response = requests.get(source, headers=REQUEST_HEADERS, timeout=20)
    response.raise_for_status()
    mime_type = response.headers.get("Content-Type", "").split(";")[0].lower()
    extension = EXTENSION_BY_MIME.get(mime_type, ".jpg")
    return response.content, extension


def scrape_images(query: str, max_results: int = MAX_RESULTS) -> list[dict]:
    search_response = requests.get(
        BING_IMAGE_SEARCH_URL,
        params={"q": query, "form": "HDRSC2"},
        headers=REQUEST_HEADERS,
        timeout=20,
    )
    search_response.raise_for_status()

    output_dir = prepare_output_directory(query)
    scraped_images = []

    for candidate in extract_image_candidates(search_response.text):
        if len(scraped_images) >= max_results:
            break

        try:
            image_bytes, extension = download_image(candidate)
        except Exception as exc:
            logging.warning("Skipping image source %s because %s", candidate, exc)
            continue

        if not image_bytes:
            continue

        filename = f"{slugify_query(query)}_{len(scraped_images)}{extension}"
        file_path = output_dir / filename
        file_path.write_bytes(image_bytes)

        scraped_images.append(
            {
                "index": len(scraped_images),
                "query": query,
                "filename": filename,
                "relative_path": f"downloads/{slugify_query(query)}/{filename}",
                "source_url": candidate,
                "scraped_at": datetime.now(timezone.utc).isoformat(),
            }
        )

    return scraped_images


def save_metadata_to_mongodb(images: list[dict]) -> bool:
    mongo_uri = os.getenv("MONGODB_URI")
    if not mongo_uri or not images:
        return False

    try:
        client = pymongo.MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        client.admin.command("ping")
        collection = client["image_scrap"]["image_scrap_data"]
        collection.insert_many(images)
        return True
    except Exception as exc:
        logging.warning("MongoDB save skipped because %s", exc)
        return False


@app.route("/", methods=["GET"])
def homepage():
    return render_template("index.html", error=None)


@app.route("/review", methods=["GET", "POST"])
def review():
    if request.method == "GET":
        return render_template("index.html", error=None)

    query = request.form.get("content", "").strip()
    if not query:
        return render_template("index.html", error="Please enter something to search.")

    try:
        images = scrape_images(query=query)
        if not images:
            return render_template(
                "index.html",
                error="No images could be fetched for this query. Try another search term.",
            )

        saved_to_db = save_metadata_to_mongodb(images)
        return render_template(
            "result.html",
            query=query,
            images=images,
            saved_to_db=saved_to_db,
        )
    except Exception as exc:
        logging.exception("Image scraping failed for query '%s': %s", query, exc)
        return render_template(
            "index.html",
            error="Something went wrong while scraping images. Please try again.",
        )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=False)

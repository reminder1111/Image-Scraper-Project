# Image Scraper Project

This is a simple Flask-based image scraper project.
The user enters a keyword, the app searches image results, downloads a small set of images, saves them locally, and shows them back in a gallery page.

## What This Project Does

- takes a search keyword from a web form
- sends a request to an image search results page
- parses image URLs from the HTML using BeautifulSoup
- downloads the images with `requests`
- stores them inside `static/downloads/<query>/`
- optionally saves image metadata to MongoDB
- renders the downloaded images in the browser

## Tech Stack

- Python
- Flask
- Requests
- BeautifulSoup
- PyMongo
- HTML + CSS

## Project Flow

### 1. User opens the homepage

The `/` route renders `templates/index.html`.
This page contains a simple form where the user enters a search term.

### 2. User submits a keyword

The form sends a `POST` request to `/review`.

### 3. The app reads the query

Inside `app.py`, the app reads the form value using:

```python
query = request.form.get("content", "").strip()
```

If the query is empty, the app shows an error message.

### 4. The app requests image search HTML

The scraper sends an HTTP request to Bing image search with the query.

```python
requests.get(
    BING_IMAGE_SEARCH_URL,
    params={"q": query, "form": "HDRSC2"},
    headers=REQUEST_HEADERS,
    timeout=20,
)
```

### 5. HTML is parsed using BeautifulSoup

The app searches for `img.mimg` elements and extracts image sources from:

- `src`
- `data-src`
- `data-src-hq`

This gives us a list of image URLs or image data URIs.

### 6. Images are downloaded

For each image source:

- if it is a normal URL, the app downloads it with `requests`
- if it is a base64 data URI, the app decodes it directly

The app also detects the correct file extension like:

- `.jpg`
- `.png`
- `.webp`
- `.gif`

### 7. Images are saved locally

Downloaded files are saved in:

```text
static/downloads/<query_slug>/
```

Example:

```text
static/downloads/iphone/
```

### 8. Optional MongoDB storage

If `MONGODB_URI` is set in the environment, the app stores image metadata in MongoDB.

If it is not set, the scraper still works and simply skips database storage.

### 9. Result page is rendered

Finally, `templates/result.html` displays:

- the search query
- number of downloaded images
- whether MongoDB storage happened or not
- the downloaded image gallery

## Important Files

- `app.py`
  Main Flask app and scraper logic.

- `templates/index.html`
  Search form page.

- `templates/result.html`
  Result gallery page.

- `static/css/main.css`
  Main styling for the pages.

- `static/css/style.css`
  Small hover effects.

- `static/downloads/`
  Images are saved here after scraping.

- `image_scraper_hindi.ipynb`
  A small notebook version of the image scraping idea.

- `.env.example`
  Example placeholder for MongoDB connection string.

## How To Run

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Optional: add MongoDB URI

If you want metadata saved in MongoDB, set:

```bash
MONGODB_URI=your_mongodb_connection_string
```

If you do not set it, the project still runs normally.

### 3. Start the Flask app

```bash
python app.py
```

### 4. Open the app

Visit:

```text
http://127.0.0.1:8000
```

### 5. Search for a keyword

Try something like:

- `iphone`
- `nature`
- `laptop`

## What I Improved In This Version

- removed hardcoded MongoDB credentials
- made MongoDB optional using environment variables
- replaced the old plain text response with a real result gallery
- added better error handling and logging
- cleaned the HTML templates
- added a cleaner UI
- ignored generated files using `.gitignore`

## How To Explain This In Interview

You can explain the project like this:

1. This is a Flask web app that scrapes image search results.
2. The user enters a keyword in a form.
3. The backend sends a request to an image search page.
4. BeautifulSoup parses the HTML and extracts image links.
5. The app downloads a fixed number of images and stores them locally.
6. The results are shown in a gallery page.
7. Metadata can also be stored in MongoDB if a connection string is provided.

## Key Learning Points

- handling form data in Flask
- making HTTP requests in Python
- parsing HTML with BeautifulSoup
- saving files dynamically
- optional database integration
- rendering dynamic results using Jinja templates

## Local Verification

This project was run locally and tested successfully with a sample query:

- `iphone`

The app loaded, scraped images, downloaded them into the local folder, and rendered the result gallery page.

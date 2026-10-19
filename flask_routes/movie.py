import requests

from bs4 import BeautifulSoup

from urllib.parse import urlparse, urljoin

from flask import (
    jsonify,
    request
)


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/154.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,"
        "application/xml;q=0.9,"
        "image/avif,image/webp,"
        "*/*;q=0.8"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "identity",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
    "Upgrade-Insecure-Requests": "1"
}


def clean_text(element):
    if not element:
        return ""

    return element.get_text(
        " ",
        strip=True
    )


def validate_domain(domain):

    try:

        parsed = urlparse(domain)

        if parsed.scheme not in (
            "http",
            "https"
        ):
            return False

        if not parsed.netloc:
            return False

        return True

    except Exception:

        return False


def get_movie_details():

    try:

        # ==========================================
        # GET PARAMETERS
        # ==========================================

        domain = request.args.get(
            "domain",
            ""
        ).strip()

        path = request.args.get(
            "path",
            ""
        ).strip()

        if not domain:

            return jsonify({
                "success": False,
                "error": "domain parameter is required."
            }), 400

        if not path:

            return jsonify({
                "success": False,
                "error": "path parameter is required."
            }), 400

        # ==========================================
        # VALIDATE DOMAIN
        # ==========================================

        if not validate_domain(domain):

            return jsonify({
                "success": False,
                "error": "Invalid domain."
            }), 400

        # ==========================================
        # CREATE SOURCE URL
        # ==========================================

        source_url = urljoin(
            domain.rstrip("/") + "/",
            path.lstrip("/")
        )

        # ==========================================
        # REQUEST SOURCE PAGE
        # ==========================================

        response = requests.get(
            source_url,
            headers=HEADERS,
            timeout=30,
            allow_redirects=True
        )

        response.raise_for_status()

        # ==========================================
        # PARSE HTML
        # ==========================================

        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )

        # ==========================================
        # TITLE
        # ==========================================

        title = ""

        title_element = soup.find(
            "h2",
            class_=lambda value: (
                not value
                or "file-info-title" not in value
            )
        )

        if title_element:

            title = clean_text(
                title_element
            )

        # Fallback to page title

        if not title and soup.title:

            title = clean_text(
                soup.title
            )

        # ==========================================
        # POSTER
        # ==========================================

        poster = ""

        poster_element = soup.select_one(
            "img.movie-cover"
        )

        if poster_element:

            poster = (
                poster_element.get(
                    "src",
                    ""
                )
                or poster_element.get(
                    "data-src",
                    ""
                )
            ).strip()

            if poster:

                poster = urljoin(
                    response.url,
                    poster
                )

        # ==========================================
        # DOWNLOAD LINK
        # ==========================================
        
        download_url = ""
        download_button_name = ""
        
        download_element = soup.select_one(
            ".dlbtn a.bg2"
        )
        
        if download_element:
        
            download_button_name = (
                download_element.get_text(
                    " ",
                    strip=True
                )
            )
        
            download_url = (
                download_element.get(
                    "href",
                    ""
                )
                .strip()
            )
        
            if download_url:
                download_url = urljoin(
                    response.url,
                    download_url
                )

        # ==========================================
        # MOVIE INFO
        # ==========================================

        details = {}

        movie_info = soup.select_one(
            ".movie-info"
        )

        if movie_info:

            rows = movie_info.select(
                ".fname"
            )

            for row in rows:

                strong = row.find(
                    "strong"
                )

                if not strong:
                    continue

                label = clean_text(
                    strong
                )

                label = label.rstrip(
                    ":"
                ).strip()

                value = ""

                span = row.find(
                    "span"
                )

                if span:

                    value = clean_text(
                        span
                    )

                else:

                    value = clean_text(
                        row
                    )

                    value = value.replace(
                        clean_text(strong),
                        "",
                        1
                    ).strip()

                if label:

                    details[label] = value

        # ==========================================
        # DESCRIPTION
        # ==========================================

        description = details.get(
            "Description",
            ""
        )

        # ==========================================
        # SCREENSHOTS
        # ==========================================
        
        screenshot = ""
        
        screenshot_element = soup.select_one(".showimage.ss img")
        
        if screenshot_element:
            screenshot = urljoin(
                response.url,
                screenshot_element.get("src", "").strip()
            )

        # ==========================================
        # FINAL RESPONSE
        # ==========================================

        result = {
            "success": True,
            "source_url": response.url,
            "title": title,
            "poster": poster,
            "details": details,
            "description": description,
            "download_url": download_url,
            "download_button_name": download_button_name,
            "screenshot": screenshot
        }

        return jsonify(result)

    except requests.RequestException as e:

        print(
            "SOURCE REQUEST ERROR:",
            str(e)
        )

        return jsonify({
            "success": False,
            "error": "Source request failed.",
            "details": str(e)
        }), 502

    except Exception as e:

        print(
            "MOVIE PARSE ERROR:",
            str(e)
        )

        return jsonify({
            "success": False,
            "error": "Movie details parsing failed.",
            "details": str(e)
        }), 500
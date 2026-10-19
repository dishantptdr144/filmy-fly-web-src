from flask import Blueprint, request, jsonify, render_template
from urllib.parse import urlparse, urljoin
import requests
from bs4 import BeautifulSoup


download_bp = Blueprint(
    "download",
    __name__
)


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/154.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,"
        "application/xml;q=0.9,image/avif,image/webp,"
        "*/*;q=0.8"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive",
}


# Add only domains that you own or are authorized to access.
ALLOWED_DOWNLOAD_DOMAINS = {
    "linkmake.in",
    "files.example.com",
}


def is_allowed_domain(url):

    try:

        parsed = urlparse(url)

        if parsed.scheme not in (
            "http",
            "https"
        ):
            return False

        hostname = (
            parsed.hostname or ""
        ).lower().rstrip(".")

        if not hostname:
            return False

        hostname = hostname.removeprefix("www.")

        allowed_domains = {
            domain.lower().removeprefix("www.")
            for domain in ALLOWED_DOWNLOAD_DOMAINS
        }

        return hostname in allowed_domains

    except Exception:

        return False


@download_bp.route(
    "/download_size",
    methods=["GET"]
)
def download_page():

    url = request.args.get(
        "url",
        ""
    ).strip()

    if not url:

        return render_template(
            "download_size.html",
            error="Download URL is missing.",
            download_url=""
        )


    if not is_allowed_domain(url):

        return render_template(
            "download_size.html",
            error="This download provider is not supported.",
            download_url=url
        )


    return render_template(
        "download_size.html",
        error="",
        download_url=url
    )


@download_bp.route(
    "/api/resolve-download",
    methods=["GET"]
)
def resolve_download():

    url = request.args.get(
        "url",
        ""
    ).strip()


    # ==============================
    # URL CHECK
    # ==============================

    if not url:

        return jsonify({
            "success": False,
            "error": "URL is required."
        }), 400


    # ==============================
    # AUTHORIZATION CHECK
    # ==============================

    if not is_allowed_domain(url):

        return jsonify({
            "success": False,
            "error": "Download provider is not supported."
        }), 403


    try:

        # ==============================
        # REQUEST PROVIDER
        # ==============================

        response = requests.get(
            url,
            headers=HEADERS,
            timeout=30,
            allow_redirects=True
        )

        response.raise_for_status()


        # ==============================
        # PARSE HTML
        # ==============================

        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )


        # ==============================
        # MOVIE TITLE
        # ==============================

        title_element = soup.select_one(
            "title"
        )

        movie_title = ""

        if title_element:

            movie_title = title_element.get_text(
                " ",
                strip=True
            )


        # ==============================
        # DOWNLOAD LINKS
        # ==============================

        links = []


        for element in soup.select(
            ".dlink.dl a"
        ):

            href = element.get(
                "href",
                ""
            ).strip()


            if not href:
                continue


            title_element = element.select_one(
                ".dll"
            )


            if title_element:

                title = title_element.get_text(
                    " ",
                    strip=True
                )

            else:

                title = element.get_text(
                    " ",
                    strip=True
                )


            if not title:

                title = "Download"


            href = urljoin(
                response.url,
                href
            )


            links.append({
                "title": title,
                "url": href
            })


        # ==============================
        # RESPONSE
        # ==============================

        return jsonify({
            "success": True,
            "source_url": response.url,
            "movie_title": movie_title,
            "links": links
        })


    except requests.RequestException as e:

        return jsonify({
            "success": False,
            "error": "Provider request failed.",
            "details": str(e)
        }), 502


    except Exception as e:

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
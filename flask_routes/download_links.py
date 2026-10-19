# flask_routes/download_links.py

from flask import Blueprint, request, render_template
from urllib.parse import urlparse, urljoin
import requests
from bs4 import BeautifulSoup


download_links_bp = Blueprint(
    "download_links",
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


# Only use domains you own or are authorized to access.
ALLOWED_BASE_DOMAIN = "filesdl.in"


def is_authorized_domain(url):

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

        if hostname == ALLOWED_BASE_DOMAIN:
            return True

        if hostname.endswith(
            "." + ALLOWED_BASE_DOMAIN
        ):
            return True

        return False

    except Exception:

        return False


@download_links_bp.route(
    "/download_links",
    methods=["GET"]
)
def download_links():

    url = request.args.get(
        "url",
        ""
    ).strip()

    # ==============================
    # URL CHECK
    # ==============================

    if not url:

        return render_template(
            "download_links.html",
            title="",
            info="",
            links=[],
            error="URL is required."
        ), 400


    # ==============================
    # AUTHORIZED DOMAIN CHECK
    # ==============================

    if not is_authorized_domain(url):

        return render_template(
            "download_links.html",
            title="",
            info="",
            links=[],
            error="Unauthorized download provider."
        ), 403


    try:

        # ==============================
        # PROVIDER REQUEST
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
        # TITLE
        # ==============================

        title_element = soup.select_one(
            ".container .title"
        )

        if title_element:

            title = title_element.get_text(
                " ",
                strip=True
            )

        else:

            title = ""


        # ==============================
        # FILE SIZE / INFO
        # ==============================

        info_element = soup.select_one(
            ".container .info"
        )

        if info_element:

            info = info_element.get_text(
                " ",
                strip=True
            )

        else:

            info = ""


        # ==============================
        # DOWNLOAD LINKS
        # ==============================

        links = []


        for element in soup.select(
            ".container a[href]"
        ):

            href = element.get(
                "href",
                ""
            ).strip()


            if not href:
                continue


            link_title = element.get_text(
                " ",
                strip=True
            )


            if not link_title:

                link_title = "Download"


            href = urljoin(
                response.url,
                href
            )


            links.append({
                "title": link_title,
                "url": href
            })


        # ==============================
        # HTML PAGE
        # ==============================

        return render_template(
            "download_links.html",
            title=title,
            info=info,
            links=links,
            error=""
        )


    except requests.RequestException:

        return render_template(
            "download_links.html",
            title="",
            info="",
            links=[],
            error="Provider request failed."
        ), 502


    except Exception as e:

        return render_template(
            "download_links.html",
            title="",
            info="",
            links=[],
            error=str(e)
        ), 500
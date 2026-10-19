import requests
import re

from bs4 import BeautifulSoup

from urllib.parse import (
    urljoin,
    urlparse
)

from flask import (
    jsonify,
    request
)


# ============================================================
# DEFAULT DOMAIN
# ============================================================

FALLBACK_DOMAIN = "https://filmyfly.bingo"


# ============================================================
# HEADERS
# ============================================================

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

    "Accept-Language":
        "en-US,en;q=0.9",

    "Cache-Control":
        "no-cache",

    "Pragma":
        "no-cache",

    "Upgrade-Insecure-Requests":
        "1"

}


# ============================================================
# CLEAN DOMAIN
# ============================================================

def normalize_domain(url):

    if not url:
        return ""

    try:

        parsed = urlparse(url)

        if not parsed.scheme:
            return ""

        if not parsed.netloc:
            return ""

        return (
            f"{parsed.scheme}://{parsed.netloc}"
        ).rstrip("/")

    except Exception:

        return ""


# ============================================================
# VALIDATE DOMAIN
# ============================================================

def validate_domain(domain):

    try:

        parsed = urlparse(
            domain
        )

        if parsed.scheme not in (
            "http",
            "https"
        ):
            return False

        if not parsed.hostname:
            return False

        return True

    except Exception:

        return False


# ============================================================
# CLEAN TEXT
# ============================================================

def clean_text(element):

    if not element:
        return ""

    return element.get_text(
        " ",
        strip=True
    )


# ============================================================
# LOCAL MOVIE URL
# ============================================================

def create_local_url(movie_url):

    if not movie_url:
        return ""

    parsed = urlparse(
        movie_url
    )

    path = parsed.path

    if not path:
        return ""

    if not path.endswith(
        ".html"
    ):
        path += ".html"

    return path


# ============================================================
# PARSE MOVIE CARD
# ============================================================

def parse_movie_card(
    block,
    domain
):

    # --------------------------------------------------------
    # Find movie link
    # --------------------------------------------------------

    link = block.select_one(
        "a[href*='/movie/']"
    )

    if not link:
        return None


    href = link.get(
        "href",
        ""
    ).strip()


    if not href:
        return None


    # --------------------------------------------------------
    # Make absolute source URL
    # --------------------------------------------------------

    movie_url = urljoin(
        domain.rstrip("/") + "/",
        href
    )


    # --------------------------------------------------------
    # Title
    # --------------------------------------------------------

    title_element = block.select_one(
        ".row-title"
    )


    title = clean_text(
        title_element
    )


    # --------------------------------------------------------
    # Fallback title from image alt
    # --------------------------------------------------------

    if not title:

        image_element = block.select_one(
            "img"
        )

        if image_element:

            title = image_element.get(
                "alt",
                ""
            ).strip()


    # --------------------------------------------------------
    # Fallback title from link
    # --------------------------------------------------------

    if not title:

        title = clean_text(
            link
        )


    if not title:
        return None


    # --------------------------------------------------------
    # Category
    # --------------------------------------------------------

    badge = block.select_one(
        ".row-badge"
    )


    category = clean_text(
        badge
    )


    # --------------------------------------------------------
    # Image
    # --------------------------------------------------------

    image_element = block.select_one(
        "img"
    )


    image_url = ""


    if image_element:

        image_url = (
            image_element.get(
                "src",
                ""
            )
            or
            image_element.get(
                "data-src",
                ""
            )
            or
            image_element.get(
                "data-lazy-src",
                ""
            )
        ).strip()


        if image_url:

            image_url = urljoin(
                domain.rstrip("/") + "/",
                image_url
            )


    # --------------------------------------------------------
    # Local URL
    # --------------------------------------------------------

    local_url = create_local_url(
        movie_url
    )


    return {

        "title":
            title,

        "category":
            category,

        "image":
            image_url,

        "url":
            movie_url,

        "local_url":
            local_url

    }


# ============================================================
# FIND ALL MOVIE CARDS
# ============================================================

def find_all_movie_cards(
    soup,
    domain
):

    movies = []

    seen = set()


    # ========================================================
    # PRIMARY SELECTOR
    # ========================================================

    blocks = soup.select(
        "div.A10"
    )


    # ========================================================
    # FALLBACK SELECTORS
    # ========================================================

    if not blocks:

        blocks = soup.select(
            ".A10"
        )


    if not blocks:

        blocks = soup.select(
            "a[href*='/movie/']"
        )


    # ========================================================
    # PARSE
    # ========================================================

    for block in blocks:

        # ----------------------------------------------------
        # If fallback gave anchor directly
        # ----------------------------------------------------

        if block.name == "a":

            parent = block.find_parent(
                "div"
            )

            if parent:

                movie = parse_movie_card(
                    parent,
                    domain
                )

            else:

                movie = None

        else:

            movie = parse_movie_card(
                block,
                domain
            )


        if not movie:

            continue


        key = (
            movie.get("local_url")
            or
            movie.get("url")
            or
            movie.get("title")
        )


        if not key:

            continue


        if key in seen:

            continue


        seen.add(
            key
        )


        movies.append(
            movie
        )


    return movies


# ============================================================
# FIND SECTION FOR MOVIE CARD
# ============================================================

def get_section_name(
    block
):

    # --------------------------------------------------------
    # Look for closest previous H2
    # --------------------------------------------------------

    previous_h2 = block.find_previous(
        "h2"
    )


    if not previous_h2:

        return ""


    text = clean_text(
        previous_h2
    ).lower()


    return text


# ============================================================
# PARSE TRENDING + LATEST
# ============================================================

def parse_home_sections(
    soup,
    domain
):

    trending = []

    latest = []


    seen_trending = set()
    seen_latest = set()


    # ========================================================
    # ALL A10 BLOCKS
    # ========================================================

    blocks = soup.select(
        "div.A10"
    )


    # ========================================================
    # PROCESS EACH BLOCK
    # ========================================================

    for block in blocks:

        movie = parse_movie_card(
            block,
            domain
        )


        if not movie:

            continue


        section_name = get_section_name(
            block
        )


        # ----------------------------------------------------
        # TRENDING
        # ----------------------------------------------------

        if (
            "trending" in section_name
            or
            "this week" in section_name
        ):

            key = (
                movie["local_url"]
                or
                movie["url"]
            )


            if key not in seen_trending:

                seen_trending.add(
                    key
                )

                trending.append(
                    movie
                )


            continue


        # ----------------------------------------------------
        # LATEST
        # ----------------------------------------------------

        if "latest" in section_name:

            key = (
                movie["local_url"]
                or
                movie["url"]
            )


            if key not in seen_latest:

                seen_latest.add(
                    key
                )

                latest.append(
                    movie
                )


            continue


    # ========================================================
    # FALLBACK
    # ========================================================
    #
    # Some versions of the website can change the heading
    # structure. In that case we use the first few cards as
    # trending and the remaining cards as latest.
    #

    if not trending and not latest:

        all_movies = find_all_movie_cards(
            soup,
            domain
        )


        if all_movies:

            trending = all_movies[:3]

            latest = all_movies[3:]


    # ========================================================
    # SECOND FALLBACK
    # ========================================================

    elif not latest:

        all_movies = find_all_movie_cards(
            soup,
            domain
        )


        trending_urls = {
            movie["local_url"]
            for movie in trending
            if movie.get("local_url")
        }


        for movie in all_movies:

            local_url = movie.get(
                "local_url"
            )


            if (
                local_url
                and
                local_url not in trending_urls
            ):

                latest.append(
                    movie
                )


    return (
        trending,
        latest
    )


# ============================================================
# GET DOMAIN
# ============================================================

def get_domain():
    try:
        # STEP 1
        response = requests.get(
            "https://filmyfly.io/",
            headers=HEADERS,
            timeout=30,
            allow_redirects=True
        )

        response.raise_for_status()

        # STEP 2
        first_domain = response.text.split('<a href="')[1].split('" target="_blank" class="btn"')[0].split('"')[0]

        # STEP 3
        second_response = requests.get(
            first_domain + "/",
            headers=HEADERS,
            timeout=30,
            allow_redirects=True
        )

        second_response.raise_for_status()

        # ==========================================
        # STEP 4
        # DOMAIN DIRECTLY FROM response.text
        # ==========================================

        html = second_response.text

        match = re.search(
            r'<link[^>]+rel=["\']canonical["\'][^>]+href=["\']([^"\']+)["\']',
            html,
            re.IGNORECASE
        )

        if not match:
            # href pehle aur rel baad me ho sakta hai
            match = re.search(
                r'<link[^>]+href=["\']([^"\']+)["\'][^>]+rel=["\']canonical["\']',
                html,
                re.IGNORECASE
            )

        if not match:
            raise Exception(
                "Canonical domain not found in response text."
            )

        canonical_url = match.group(1).strip()

        # ==========================================
        # STEP 5
        # CANONICAL URL SE ONLY DOMAIN
        # ==========================================

        domain_match = re.match(
            r'^(https?://[^/]+)',
            canonical_url,
            re.IGNORECASE
        )

        if not domain_match:
            raise Exception(
                "Could not extract domain from canonical."
            )

        final_domain = domain_match.group(1)

        return jsonify({
            "success": True,
            "domain": final_domain
        })

    except requests.RequestException as e:

        return jsonify({
            "success": False,
            "error": "Domain request failed.",
            "details": str(e)
        }), 502

    except Exception as e:

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ============================================================
# HOME API
# ============================================================

def get_home_data():

    requested_domain = request.args.get(
        "domain",
        ""
    ).strip()


    # ========================================================
    # DEFAULT
    # ========================================================

    if not requested_domain:

        requested_domain = FALLBACK_DOMAIN


    # ========================================================
    # VALIDATE
    # ========================================================

    if not validate_domain(
        requested_domain
    ):

        return jsonify({

            "success":
                False,

            "error":
                "Invalid domain."

        }), 400


    try:

        # ====================================================
        # REAL GET
        # ====================================================

        response = requests.get(

            requested_domain.rstrip("/") + "/",

            headers=HEADERS,

            timeout=30,

            allow_redirects=True

        )

        response.raise_for_status()


        # ====================================================
        # IMPORTANT:
        # Domain after redirect
        # ====================================================

        effective_domain = normalize_domain(
            response.url
        )


        if not effective_domain:

            effective_domain = normalize_domain(
                requested_domain
            )


        # ====================================================
        # PARSE HTML
        # ====================================================

        soup = BeautifulSoup(

            response.text,

            "html.parser"

        )

        # ====================================================
        # PARSE SECTIONS
        # ====================================================

        trending, latest = parse_home_sections(

            soup,

            effective_domain

        )


        # ====================================================
        # FINAL FALLBACK
        # ====================================================

        if not trending and not latest:

            all_movies = find_all_movie_cards(

                soup,

                effective_domain

            )


            if all_movies:

                trending = all_movies[:3]

                latest = all_movies[3:]


        return jsonify({

            "success":
                True,

            "source_url":
                effective_domain + "/",

            "trending":
                trending,

            "latest":
                latest

        })


    except requests.RequestException as e:

        print(
            "REQUEST ERROR:",
            str(e)
        )


        return jsonify({

            "success":
                False,

            "error":
                "Source request failed.",

            "details":
                str(e)

        }), 502


    except Exception as e:

        print(
            "PARSER ERROR:",
            str(e)
        )


        return jsonify({

            "success":
                False,

            "error":
                "Home parsing failed.",

            "details":
                str(e)

        }), 500
from flask import Blueprint, request, jsonify, render_template
import requests
import re


search_bp = Blueprint(
    "search",
    __name__
)


SEARCH_API_URL = (
    "https://webfind.filmyflydla.space/search"
)


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/154.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json"
}


def make_slug(title):

    title = str(
        title or ""
    ).strip()


    # Remove ()
    title = re.sub(
        r"[()]",
        "",
        title
    )


    # Spaces -> -
    title = re.sub(
        r"\s+",
        "-",
        title
    )


    # Multiple - -> single -
    title = re.sub(
        r"-+",
        "-",
        title
    )


    # Remove starting/ending -
    title = title.strip("-")


    return title


@search_bp.route(
    "/search",
    methods=["GET"]
)
def search_page():

    return render_template(
        "search.html"
    )


@search_bp.route(
    "/api/search",
    methods=["GET"]
)
def api_search():

    search = request.args.get(
        "search",
        ""
    ).strip()


    page = request.args.get(
        "page",
        "1"
    )


    per_page = request.args.get(
        "per_page",
        "20"
    )


    if not search:

        return jsonify({
            "success": False,
            "error": "Search query is required."
        }), 400


    try:

        page = int(page)

    except ValueError:

        page = 1


    try:

        per_page = int(per_page)

    except ValueError:

        per_page = 20


    if page < 1:

        page = 1


    if per_page < 1:

        per_page = 20


    try:

        response = requests.get(
            SEARCH_API_URL,
            params={
                "q": search,
                "page": page,
                "per_page": per_page
            },
            headers=HEADERS,
            timeout=30
        )


        # ==========================================
        # MOVIE NOT FOUND
        # ==========================================

        if response.status_code == 404:

            return jsonify({
                "success": True,
                "query": search,
                "page": page,
                "per_page": per_page,
                "total": 0,
                "total_pages": 0,
                "status": 404,
                "results": []
            })


        # Other HTTP errors
        response.raise_for_status()


        data = response.json()


        results = []


        for movie in data.get(
            "results",
            []
        ):

            if not isinstance(
                movie,
                dict
            ):

                continue


            title = str(
                movie.get(
                    "title",
                    ""
                )
            ).strip()


            filmyfly = str(
                movie.get(
                    "filmyfly",
                    ""
                )
            ).strip()


            if not title or not filmyfly:

                continue


            results.append({
                "title": title,

                "foldern": movie.get(
                    "foldern",
                    ""
                ),

                "foid": movie.get(
                    "foid",
                    ""
                ),

                "filmyfly": filmyfly,

                "poster": movie.get(
                    "poster",
                    ""
                ),

                "slug": make_slug(
                    title
                )
            })


        return jsonify({
            "success": True,

            "query": data.get(
                "query",
                search
            ),

            "page": data.get(
                "page",
                page
            ),

            "per_page": data.get(
                "per_page",
                per_page
            ),

            "total": data.get(
                "total",
                len(results)
            ),

            "total_pages": data.get(
                "total_pages",
                1
            ),

            "status": data.get(
                "status",
                200
            ),

            "results": results
        })


    except requests.RequestException as e:

        return jsonify({
            "success": False,
            "error": "Search API request failed.",
            "details": str(e)
        }), 502


    except ValueError:

        return jsonify({
            "success": False,
            "error": "Invalid JSON response from search API."
        }), 502


    except Exception as e:

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
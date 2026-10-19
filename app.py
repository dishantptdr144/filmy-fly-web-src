from flask import Flask, render_template

from flask_routes.home import (
    get_domain,
    get_home_data
)

from flask_routes.movie import get_movie_details
from flask_routes.download import download_bp
from flask_routes.download_links import download_links_bp
from flask_routes.search import search_bp

app = Flask(
    __name__,
    template_folder="templates",
    static_folder="static"
)


app.register_blueprint(download_bp)
app.register_blueprint(download_links_bp)
app.register_blueprint(search_bp)

app.add_url_rule(
    "/api/details",
    view_func=get_movie_details,
    methods=["GET"]
)

# ============================================================
# HOME
# ============================================================

@app.route("/")
def index():
    return render_template("home.html")


@app.route("/home")
def home():
    return render_template("home.html")


# ============================================================
# MOVIE PAGE
# ============================================================

@app.route(
    "/movie/<int:movie_id>/<path:movie_slug>.html"
)
def movie_page(
    movie_id,
    movie_slug
):

    movie_path = (
        f"/movie/"
        f"{movie_id}/"
        f"{movie_slug}.html"
    )

    return render_template(
        "movie.html",
        movie_path=movie_path
    )


# ============================================================
# DOMAIN API
# ============================================================

@app.route("/get-domain")
def domain_api():

    return get_domain()


# ============================================================
# HOME API
# ============================================================

@app.route("/api/home")
def home_api():

    return get_home_data()


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )
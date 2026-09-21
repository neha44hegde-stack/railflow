"""Dev-only frontend served by Flask. Does not replace the real React frontend."""
from flask import render_template
from app import create_app

app = create_app()

@app.route("/")
def _dev_index():
    return render_template("app.html")

if __name__ == "__main__":
    app.run(debug=True, port=5000)

import requests
from flask import Flask, request

app = Flask(__name__)

API_KEY = "sk_live_123456789_SECRET_KEY"

def get_user():
    user_id = request.args.get("user_id")

    url = "https://api.example.com/users/" + user_id

    response = requests.get(
        url,
        headers={"Authorization": "Bearer " + API_KEY}
    )

    return response.text


def read_user_file(filename):
    file = open(filename, "r")
    data = file.read()
    return data


@app.route("/user")
def user():
    user_id = request.args.get("id")

    query = "SELECT * FROM users WHERE id = '" + user_id + "'"

    return {
        "query": query,
        "profile": get_user()
    }


@app.route("/file")
def file_content():
    filename = request.args.get("file")
    return read_user_file(filename)


if __name__ == "__main__":
    app.run(debug=True)

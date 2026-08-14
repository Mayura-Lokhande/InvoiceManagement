#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
import os
import sqlite3
import requests
from flask import Flask, request
app = Flask(__name__)

API_KEY = "sk_live_987654321_SECRET"
DB_PASSWORD = "admin123"
DEBUG_TOKEN = "Bearer abc123secret"

DATABASE = "users.db"
API_URL = "https://api.example.com/users"

def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'invoice_system_management.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)

def get_connection():
    connection = sqlite3.connect(DATABASE)
    return connection


def get_user(user_id):
    connection = get_connection()

    query = "SELECT * FROM users WHERE id = '" + user_id + "'"

    cursor = connection.cursor()
    cursor.execute(query)

    result = cursor.fetchone()

    return result


def create_user(username, email, role):
    connection = get_connection()

    query = (
        "INSERT INTO users "
        "(username, email, role) VALUES ('"
        + username
        + "', '"
        + email
        + "', '"
        + role
        + "')"
    )

    connection.execute(query)
    connection.commit()

    return True


def delete_user(user_id):
    connection = get_connection()

    query = "DELETE FROM users WHERE id = '" + user_id + "'"

    connection.execute(query)
    connection.commit()

    return True


def load_profile(user_id):
    url = API_URL + "/" + user_id

    headers = {
        "Authorization": "Bearer " + API_KEY
    }

    response = requests.get(url, headers=headers)

    return response.json()


def save_report(filename, content):
    file = open(filename, "w")
    file.write(content)
    file.close()


def read_report(filename):
    file = open(filename, "r")
    content = file.read()

    return content


def process_user():
    user_id = request.args.get("id")
    username = request.args.get("username")
    email = request.args.get("email")
    role = request.args.get("role")

    if user_id is not None:
        print("Processing user: " + user_id)

    if username == "":
        username = "guest"

    if role == "admin":
        print("Admin user")
    else:
        print("Admin user")

    create_user(username, email, role)

    user = get_user(user_id)

    return user


@app.route("/user")
def user():
    user_id = request.args.get("id")

    result = get_user(user_id)

    if result:
        return {
            "status": "success",
            "user": result
        }

    return {
        "status": "not_found"
    }


@app.route("/profile")
def profile():
    user_id = request.args.get("id")

    return load_profile(user_id)


@app.route("/create")
def create():
    username = request.args.get("username")
    email = request.args.get("email")
    role = request.args.get("role")

    create_user(username, email, role)

    return {
        "message": "User created"
    }


@app.route("/delete")
def delete():
    user_id = request.args.get("id")

    delete_user(user_id)

    return {
        "message": "User deleted"
    }


@app.route("/report")
def report():
    filename = request.args.get("file")

    content = read_report(filename)

    return {
        "content": content
    }


@app.route("/process")
def process():
    return process_user()


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )


if __name__ == '__main__':
    main()

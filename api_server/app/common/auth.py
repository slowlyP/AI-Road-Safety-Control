from flask import session

class Auth:
    @staticmethod
    def login(users :dict):
        session["user_id"] = users["id"]
        session["username"] = users["username"]
        session["email"] = users["email"]
        session["name"] = users["name"]
        session["role"] = users["role"]

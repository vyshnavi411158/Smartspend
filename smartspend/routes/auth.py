from flask import Blueprint, render_template, request, redirect, url_for, session, flash
import bcrypt

auth = Blueprint("auth", __name__)


@auth.route("/")
@auth.route("/login", methods=["GET", "POST"])
def login():

    return render_template("login.html")


@auth.route("/signup", methods=["GET", "POST"])
def signup():

    return render_template("signup.html")


@auth.route("/forgot-password")
def forgot_password():

    return render_template("forgot-password.html")


@auth.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("auth.login"))
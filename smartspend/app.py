import os
import bcrypt

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash
)

from flask_mysqldb import MySQL
from werkzeug.utils import secure_filename

import config


app = Flask(__name__)


app.config["SECRET_KEY"] = config.SECRET_KEY



app.config["MYSQL_HOST"] = config.MYSQL_HOST
app.config["MYSQL_USER"] = config.MYSQL_USER
app.config["MYSQL_PASSWORD"] = config.MYSQL_PASSWORD
app.config["MYSQL_DB"] = config.MYSQL_DB



UPLOAD_FOLDER = os.path.join("static", "uploads")

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)




mysql = MySQL(app)

ALLOWED_EXTENSIONS = {
    "png",
    "jpg",
    "jpeg",
    "webp"
}


def allowed_file(filename):

    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


@app.route("/")
@app.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    if request.method == "POST":

        email = request.form["email"].strip()
        password = request.form["password"]

        cur = mysql.connection.cursor()

        cur.execute("""
            SELECT
                id,
                full_name,
                password
            FROM users
            WHERE email=%s
        """, (email,))

        user = cur.fetchone()

        cur.close()

        if user:

            if bcrypt.checkpw(
                password.encode("utf-8"),
                user[2].encode("utf-8")
            ):

                session["user_id"] = user[0]
                session["user_name"] = user[1]

                flash("Login Successful!", "success")

                return redirect(url_for("dashboard"))

            flash("Incorrect Password", "danger")

        else:

            flash("Email not found", "danger")

    return render_template("login.html")



@app.route("/signup", methods=["GET", "POST"])
def signup():

    if request.method == "POST":

        full_name = request.form["full_name"].strip()
        email = request.form["email"].strip()
        phone = request.form["phone"].strip()
        password = request.form["password"]

        cur = mysql.connection.cursor()

        cur.execute(
            "SELECT id FROM users WHERE email=%s",
            (email,)
        )

        existing = cur.fetchone()

        if existing:

            cur.close()

            flash("Email already exists.", "warning")

            return redirect(url_for("signup"))

        hashed_password = bcrypt.hashpw(
            password.encode("utf-8"),
            bcrypt.gensalt()
        ).decode("utf-8")

        cur.execute("""
            INSERT INTO users
            (
                full_name,
                email,
                password,
                phone
            )
            VALUES
            (%s,%s,%s,%s)
        """, (
            full_name,
            email,
            hashed_password,
            phone
        ))

        mysql.connection.commit()

        cur.close()

        flash("Account created successfully!", "success")

        return redirect(url_for("login"))

    return render_template("signup.html")



@app.route("/forgot-password")
def forgot_password():

    return render_template("forgot-password.html")

@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect(url_for("login"))

    cur = mysql.connection.cursor()



    cur.execute("""
        SELECT IFNULL(SUM(amount),0)
        FROM receipts
        WHERE user_id=%s
    """, (session["user_id"],))

    total_expenses = float(cur.fetchone()[0])




    cur.execute("""
        SELECT COUNT(*)
        FROM receipts
        WHERE user_id=%s
    """, (session["user_id"],))

    total_receipts = cur.fetchone()[0]



    cur.execute("""
        SELECT monthly_budget
        FROM budgets
        WHERE user_id=%s
        ORDER BY id DESC
        LIMIT 1
    """, (session["user_id"],))

    budget = cur.fetchone()

    monthly_budget = float(budget[0]) if budget else 0

    budget_left = max(monthly_budget - total_expenses, 0)

    savings = budget_left

    

    cur.execute("""
        SELECT
            receipts.merchant,
            categories.category_name,
            receipts.receipt_date,
            receipts.amount,
            receipts.payment_method
        FROM receipts
        LEFT JOIN categories
            ON receipts.category_id = categories.id
        WHERE receipts.user_id=%s
        ORDER BY receipts.receipt_date DESC,
                 receipts.id DESC
        LIMIT 5
    """, (session["user_id"],))

    recent_transactions = cur.fetchall()


    cur.execute("""
        SELECT
            categories.category_name,
            SUM(receipts.amount)
        FROM receipts
        JOIN categories
            ON receipts.category_id = categories.id
        WHERE receipts.user_id=%s
        GROUP BY categories.category_name
        ORDER BY SUM(receipts.amount) DESC
    """, (session["user_id"],))

    category_chart = cur.fetchall()



    cur.execute("""
        SELECT
            YEAR(receipt_date) AS year,
            MONTH(receipt_date) AS month_no,
            DATE_FORMAT(MIN(receipt_date), '%%b') AS month,
            SUM(amount) AS total
        FROM receipts
        WHERE user_id=%s
        GROUP BY YEAR(receipt_date), MONTH(receipt_date)
        ORDER BY YEAR(receipt_date), MONTH(receipt_date)
    """, (session["user_id"],))

    monthly_chart = cur.fetchall()

    cur.close()

    return render_template(
        "dashboard.html",
        name=session["user_name"],
        total_expenses=total_expenses,
        total_receipts=total_receipts,
        monthly_budget=monthly_budget,
        budget_left=budget_left,
        savings=savings,
        recent_transactions=recent_transactions,
        category_chart=category_chart,
        monthly_chart=monthly_chart
    )


@app.route("/logout")
def logout():

    session.clear()

    flash("Logged out successfully.", "success")

    return redirect(url_for("login"))



@app.route("/add-receipt", methods=["GET", "POST"])
def add_receipt():

    if "user_id" not in session:
        return redirect(url_for("login"))

    cur = mysql.connection.cursor()


    if request.method == "POST":

        merchant = request.form["merchant"].strip()
        amount = request.form["amount"]
        receipt_date = request.form["receipt_date"]
        category = request.form["category"]
        payment = request.form["payment"]
        notes = request.form["notes"].strip()

        filename = ""

        image = request.files.get("receipt_image")

        if image and image.filename != "":

            if allowed_file(image.filename):

                filename = secure_filename(image.filename)

                image.save(
                    os.path.join(
                        app.config["UPLOAD_FOLDER"],
                        filename
                    )
                )

            else:

                flash(
                    "Only JPG, JPEG, PNG and WEBP images are allowed.",
                    "danger"
                )

                cur.close()

                return redirect(url_for("add_receipt"))

        cur.execute("""
            INSERT INTO receipts
            (
                user_id,
                merchant,
                amount,
                receipt_date,
                category_id,
                payment_method,
                notes,
                receipt_image
            )
            VALUES
            (%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            session["user_id"],
            merchant,
            amount,
            receipt_date,
            category,
            payment,
            notes,
            filename
        ))

        mysql.connection.commit()

        flash("Receipt added successfully!", "success")

        return redirect(url_for("receipts"))



    cur.execute("""
        SELECT
            id,
            category_name
        FROM categories
        ORDER BY category_name
    """)

    categories = cur.fetchall()

    cur.close()

    return render_template(
        "add_receipt.html",
        name=session["user_name"],
        categories=categories
    )



@app.route("/receipts")
def receipts():

    if "user_id" not in session:
        return redirect(url_for("login"))

    cur = mysql.connection.cursor()

    cur.execute("""
        SELECT
            receipts.id,
            receipts.merchant,
            receipts.amount,
            receipts.receipt_date,
            categories.category_name,
            receipts.payment_method,
            receipts.receipt_image
        FROM receipts
        LEFT JOIN categories
        ON receipts.category_id = categories.id
        WHERE receipts.user_id=%s
        ORDER BY receipts.receipt_date DESC
    """, (session["user_id"],))

    receipts = cur.fetchall()

    cur.close()

    return render_template(
        "receipts.html",
        receipts=receipts,
        name=session["user_name"]
    )



@app.route("/edit-receipt/<int:receipt_id>", methods=["GET", "POST"])
def edit_receipt(receipt_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    cur = mysql.connection.cursor()


    if request.method == "POST":

        merchant = request.form["merchant"].strip()
        amount = request.form["amount"]
        receipt_date = request.form["receipt_date"]
        category = request.form["category"]
        payment = request.form["payment"]
        notes = request.form["notes"].strip()


        cur.execute("""
            SELECT receipt_image
            FROM receipts
            WHERE id=%s
            AND user_id=%s
        """, (receipt_id, session["user_id"]))

        old_image = cur.fetchone()

        filename = old_image[0] if old_image else ""



        image = request.files.get("receipt_image")

        if image and image.filename != "":

            if allowed_file(image.filename):

                filename = secure_filename(image.filename)

                image.save(
                    os.path.join(
                        app.config["UPLOAD_FOLDER"],
                        filename
                    )
                )

            else:

                flash(
                    "Only JPG, JPEG, PNG and WEBP images are allowed.",
                    "danger"
                )

                cur.close()

                return redirect(
                    url_for(
                        "edit_receipt",
                        receipt_id=receipt_id
                    )
                )



        cur.execute("""
            UPDATE receipts
            SET
                merchant=%s,
                amount=%s,
                receipt_date=%s,
                category_id=%s,
                payment_method=%s,
                notes=%s,
                receipt_image=%s
            WHERE
                id=%s
            AND
                user_id=%s
        """, (
            merchant,
            amount,
            receipt_date,
            category,
            payment,
            notes,
            filename,
            receipt_id,
            session["user_id"]
        ))

        mysql.connection.commit()

        cur.close()

        flash(
            "Receipt updated successfully.",
            "success"
        )

        return redirect(url_for("receipts"))



    cur.execute("""
        SELECT
            id,
            merchant,
            amount,
            receipt_date,
            category_id,
            payment_method,
            notes,
            receipt_image
        FROM receipts
        WHERE id=%s
        AND user_id=%s
    """, (
        receipt_id,
        session["user_id"]
    ))

    receipt = cur.fetchone()

    if receipt is None:

        cur.close()

        flash(
            "Receipt not found.",
            "danger"
        )

        return redirect(url_for("receipts"))


    cur.execute("""
        SELECT
            id,
            category_name
        FROM categories
        ORDER BY category_name
    """)

    categories = cur.fetchall()

    cur.close()

    return render_template(
        "edit_receipt.html",
        receipt=receipt,
        categories=categories,
        name=session["user_name"]
    )



    cur.execute("""
        SELECT
            id,
            merchant,
            amount,
            receipt_date,
            category_id,
            payment_method,
            notes,
            receipt_image
        FROM receipts
        WHERE id=%s
        AND user_id=%s
    """, (receipt_id, session["user_id"]))

    receipt = cur.fetchone()

    if receipt is None:

        cur.close()

        flash("Receipt not found.")

        return redirect(url_for("receipts"))



    cur.execute("""
        SELECT
            id,
            category_name
        FROM categories
        ORDER BY category_name
    """)

    categories = cur.fetchall()

    cur.close()

    return render_template(
        "edit_receipt.html",
        receipt=receipt,
        categories=categories,
        name=session["user_name"]
    )


@app.route("/delete-receipt/<int:receipt_id>")
def delete_receipt(receipt_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    cur = mysql.connection.cursor()



    cur.execute("""
        SELECT receipt_image
        FROM receipts
        WHERE id=%s
        AND user_id=%s
    """, (receipt_id, session["user_id"]))

    receipt = cur.fetchone()

    if receipt is None:

        cur.close()

        flash("Receipt not found.")

        return redirect(url_for("receipts"))

    filename = receipt[0]


    if filename:

        image_path = os.path.join(
            app.config["UPLOAD_FOLDER"],
            filename
        )

        if os.path.exists(image_path):

            os.remove(image_path)


    cur.execute("""
        DELETE FROM receipts
        WHERE id=%s
        AND user_id=%s
    """, (receipt_id, session["user_id"]))

    mysql.connection.commit()

    cur.close()

    flash("Receipt deleted successfully.")

    return redirect(url_for("receipts"))


@app.route("/categories")
def categories():

    if "user_id" not in session:
        return redirect(url_for("login"))

    cur = mysql.connection.cursor()

    cur.execute("""
        SELECT
            id,
            category_name
        FROM categories
        ORDER BY category_name
    """)

    category_list = cur.fetchall()

    cur.close()

    return render_template(
        "categories.html",
        categories=category_list,
        name=session["user_name"]
    )


@app.route("/add-category", methods=["POST"])
def add_category():

    if "user_id" not in session:
        return redirect(url_for("login"))

    category = request.form["category"].strip()

    if category == "":

        flash("Category name cannot be empty.", "danger")

        return redirect(url_for("categories"))

    cur = mysql.connection.cursor()



    cur.execute("""
        SELECT id
        FROM categories
        WHERE LOWER(category_name)=LOWER(%s)
    """, (category,))

    existing = cur.fetchone()

    if existing:

        cur.close()

        flash("Category already exists.", "warning")

        return redirect(url_for("categories"))

  
    cur.execute("""
        INSERT INTO categories
        (
            category_name
        )
        VALUES
        (%s)
    """, (category,))

    mysql.connection.commit()

    cur.close()

    flash("Category added successfully!", "success")

    return redirect(url_for("categories"))


@app.route("/edit-category/<int:id>", methods=["POST"])
def edit_category(id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    category = request.form["category"].strip()



    if category == "":

        flash("Category name cannot be empty.", "danger")

        return redirect(url_for("categories"))

    cur = mysql.connection.cursor()



    cur.execute("""
        SELECT id
        FROM categories
        WHERE LOWER(category_name)=LOWER(%s)
        AND id != %s
    """, (category, id))

    existing = cur.fetchone()

    if existing:

        cur.close()

        flash("Category already exists.", "warning")

        return redirect(url_for("categories"))



    cur.execute("""
        UPDATE categories
        SET category_name=%s
        WHERE id=%s
    """, (
        category,
        id
    ))

    mysql.connection.commit()

    cur.close()

    flash("Category updated successfully!", "success")

    return redirect(url_for("categories"))


@app.route("/delete-category/<int:id>")
def delete_category(id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    cur = mysql.connection.cursor()



    cur.execute("""
        SELECT COUNT(*)
        FROM receipts
        WHERE category_id=%s
    """, (id,))

    receipt_count = cur.fetchone()[0]

    if receipt_count > 0:

        cur.close()

        flash(
            "Cannot delete category because it is being used by receipts.",
            "danger"
        )

        return redirect(url_for("categories"))



    cur.execute("""
        DELETE FROM categories
        WHERE id=%s
    """, (id,))

    mysql.connection.commit()

    cur.close()

    flash("Category deleted successfully!", "success")

    return redirect(url_for("categories"))


@app.route("/budget", methods=["GET", "POST"])
def budget():

    if "user_id" not in session:
        return redirect(url_for("login"))

    from datetime import datetime

    month = datetime.now().strftime("%B")
    year = datetime.now().year

    cur = mysql.connection.cursor()



    if request.method == "POST":

        monthly_budget = request.form["budget"]

        cur.execute("""
            SELECT id
            FROM budgets
            WHERE
                user_id=%s
            AND
                month=%s
            AND
                year=%s
        """, (
            session["user_id"],
            month,
            year
        ))

        existing = cur.fetchone()

        if existing:

            cur.execute("""
                UPDATE budgets
                SET monthly_budget=%s
                WHERE id=%s
            """, (
                monthly_budget,
                existing[0]
            ))

        else:

            cur.execute("""
                INSERT INTO budgets
                (
                    user_id,
                    monthly_budget,
                    month,
                    year
                )
                VALUES
                (%s,%s,%s,%s)
            """, (
                session["user_id"],
                monthly_budget,
                month,
                year
            ))

        mysql.connection.commit()

        flash("Budget saved successfully!", "success")

        return redirect(url_for("budget"))


    cur.execute("""
        SELECT monthly_budget
        FROM budgets
        WHERE
            user_id=%s
        AND
            month=%s
        AND
            year=%s
    """, (
        session["user_id"],
        month,
        year
    ))

    result = cur.fetchone()

    monthly_budget = float(result[0]) if result else 0



    cur.execute("""
        SELECT IFNULL(SUM(amount),0)
        FROM receipts
        WHERE user_id=%s
    """, (session["user_id"],))

    total_expenses = float(cur.fetchone()[0])

    budget_left = max(monthly_budget - total_expenses, 0)

    if monthly_budget > 0:
        budget_percent = round((total_expenses / monthly_budget) * 100)
    else:
        budget_percent = 0

    cur.close()

    return render_template(
        "budget.html",
        name=session["user_name"],
        monthly_budget=monthly_budget,
        total_expenses=total_expenses,
        budget_left=budget_left,
        budget_percent=budget_percent,
        current_month=month,
        current_year=year
    )


@app.route("/reports")
def reports():

    if "user_id" not in session:
        return redirect(url_for("login"))

    cur = mysql.connection.cursor()


    cur.execute("""
        SELECT IFNULL(SUM(amount),0)
        FROM receipts
        WHERE user_id=%s
    """, (session["user_id"],))

    total_expenses = float(cur.fetchone()[0])



    cur.execute("""
        SELECT monthly_budget
        FROM budgets
        WHERE user_id=%s
        ORDER BY id DESC
        LIMIT 1
    """, (session["user_id"],))

    budget = cur.fetchone()

    monthly_budget = float(budget[0]) if budget else 0

    total_savings = max(monthly_budget - total_expenses, 0)



    budget_left = max(monthly_budget - total_expenses, 0)

    if monthly_budget > 0:
        budget_percent = round((total_expenses / monthly_budget) * 100)
    else:
        budget_percent = 0


    cur.execute("""
        SELECT AVG(amount)
        FROM receipts
        WHERE user_id=%s
    """, (session["user_id"],))

    avg = cur.fetchone()

    average_expense = float(avg[0]) if avg[0] else 0


    cur.execute("""
        SELECT COUNT(*)
        FROM receipts
        WHERE user_id=%s
    """, (session["user_id"],))

    receipt_count = cur.fetchone()[0]



    cur.execute("""
        SELECT
            categories.category_name,
            SUM(receipts.amount)
        FROM receipts
        JOIN categories
            ON receipts.category_id = categories.id
        WHERE receipts.user_id=%s
        GROUP BY categories.category_name
        ORDER BY SUM(receipts.amount) DESC
    """, (session["user_id"],))

    category_chart = cur.fetchall()


    cur.execute("""
        SELECT
            YEAR(receipt_date) AS year,
            MONTH(receipt_date) AS month_no,
            DATE_FORMAT(MIN(receipt_date), '%%b') AS month,
            SUM(amount) AS total
        FROM receipts
        WHERE user_id=%s
        GROUP BY YEAR(receipt_date), MONTH(receipt_date)
        ORDER BY YEAR(receipt_date), MONTH(receipt_date)
    """, (session["user_id"],))

    monthly_chart = cur.fetchall()

    cur.close()

    return render_template(
        "reports.html",
        name=session["user_name"],
        total_expenses=total_expenses,
        total_savings=total_savings,
        average_expense=average_expense,
        receipt_count=receipt_count,
        monthly_budget=monthly_budget,
        budget_left=budget_left,
        budget_percent=budget_percent,
        category_chart=category_chart,
        monthly_chart=monthly_chart
    )




@app.route("/settings")
def settings():

    if "user_id" not in session:
        return redirect(url_for("login"))

    return render_template(
        "settings.html",
        name=session["user_name"]
    )




@app.route("/testdb")
def testdb():

    try:

        cur = mysql.connection.cursor()

        cur.execute("SELECT DATABASE();")

        db = cur.fetchone()

        cur.close()

        return f"""
        <h2 style='font-family:Arial'>
        ✅ Connected Successfully
        <br><br>
        Database :
        <span style='color:green'>
        {db[0]}
        </span>
        </h2>
        """

    except Exception as e:

        return f"""
        <h2 style='color:red'>
        Database Connection Failed
        </h2>

        <p>{e}</p>
        """



@app.errorhandler(404)
def page_not_found(error):

    return "<h2>404 - Page Not Found</h2>", 404


@app.errorhandler(500)
def internal_server(error):

    return "<h2>500 - Internal Server Error</h2>", 500



if __name__ == "__main__":

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )
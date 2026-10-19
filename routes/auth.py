from core import *
# LOGIN

# =========================================================



@app.route("/")

def index():

    if login_required():

        user = current_user()



        if user:

            if user["role"] == "student":

                return redirect(

                    url_for("student_dashboard")

                )



            if user["role"] == "cashier":

                return redirect(

                    url_for("cashier_dashboard")

                )



            if user["role"] == "admin":

                return redirect(

                    url_for("admin_dashboard")

                )



    return render_template("login.html")





@app.route("/login", methods=["POST"])

def login():

    username = request.form.get(

        "username",

        ""

    ).strip()



    password = request.form.get(

        "password",

        ""

    )



    if not username or not password:

        flash(

            "Please enter your username and password.",

            "error"

        )



        return redirect(url_for("index"))



    user = get_user_by_username(username)



    if not user or user["password"] != password:

        flash(

            "Incorrect username or password.",

            "error"

        )



        return redirect(url_for("index"))



    session.clear()

    session["user_id"] = user["id"]



    if user["role"] == "student":

        return redirect(

            url_for("student_dashboard")

        )



    if user["role"] == "cashier":

        return redirect(

            url_for("cashier_dashboard")

        )



    if user["role"] == "admin":

        return redirect(

            url_for("admin_dashboard")

        )



    session.clear()



    flash(

        "Invalid account role.",

        "error"

    )



    return redirect(url_for("index"))





@app.route("/logout")

def logout():

    session.clear()



    return redirect(url_for("index"))





# =========================================================

# REGISTER

# =========================================================



@app.route("/register", methods=["GET", "POST"])

def register():

    if request.method == "POST":



        name = request.form.get(

            "name",

            ""

        ).strip()



        username = request.form.get(

            "username",

            ""

        ).strip()



        password = request.form.get(

            "password",

            ""

        ).strip()



        confirm_password = request.form.get(

            "confirm_password",

            ""

        ).strip()



        department = request.form.get(

            "department",

            ""

        ).strip()



        year = request.form.get(

            "year",

            ""

        ).strip()



        if not name or not username or not password or not confirm_password:

            flash(

                "Please fill in all required fields.",

                "error"

            )



            return redirect(

                url_for("register")

            )



        if password != confirm_password:

            flash(

                "Passwords do not match.",

                "error"

            )



            return redirect(

                url_for("register")

            )



        if get_user_by_username(username):

            flash(

                "Username already exists.",

                "error"

            )



            return redirect(

                url_for("register")

            )



        users.append({

            "id": next_user_id(),

            "username": username,

            "password": password,

            "name": name,

            "role": "student",

            "department": department,

            "year": year

        })



        flash(

            "Registration successful. You can now login.",

            "success"

        )



        return redirect(

            url_for("index")

        )



    return render_template(

        "register.html",

        departments=departments,

        years=years

    )

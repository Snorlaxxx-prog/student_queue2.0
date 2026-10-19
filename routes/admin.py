from core import *

# ADMIN
# =========================================================


@app.route("/admin")
def admin_dashboard():
    if not login_required():
        return redirect(url_for("index"))

    user = current_user()

    if not user or user["role"] != "admin":
        return redirect(url_for("index"))

    latest_queues = sorted(
        queue_records,
        key=lambda queue: queue["id"],
        reverse=True
    )[:10]

    queue_data = []

    for queue in latest_queues:
        queue_copy = queue.copy()

        queue_copy["student"] = get_user(queue["student_id"])

        queue_copy["schedule"] = get_schedule(queue["schedule_id"])

        queue_data.append(queue_copy)

    student_count = len(
        [
            user
            for user in users
            if user["role"] == "student"
        ]
    )

    cashier_count = len(
        [
            user
            for user in users
            if user["role"] == "cashier"
        ]
    )

    return render_template(
        "admin.html",
        user=user,
        latest_queues=queue_data,
        student_count=student_count,
        cashier_count=cashier_count
    )


# =========================================================
# ADMIN ACCOUNTS
# =========================================================


@app.route("/admin/accounts")
def admin_accounts():
    if not login_required():
        return redirect(url_for("index"))

    user = current_user()

    if not user or user["role"] != "admin":
        return redirect(url_for("index"))

    students = [
        user
        for user in users
        if user["role"] == "student"
    ]

    cashiers = [
        user
        for user in users
        if user["role"] == "cashier"
    ]

    return render_template(
        "admin_accounts.html",
        user=user,
        students=students,
        cashiers=cashiers,
        departments=departments,
        years=years
    )


# =========================================================
# ADMIN CASHIERS
# =========================================================


@app.route("/admin/cashiers")
def admin_cashiers():
    if not login_required():
        return redirect(url_for("index"))

    user = current_user()

    if not user or user["role"] != "admin":
        return redirect(url_for("index"))

    cashiers = [
        cashier
        for cashier in users
        if cashier["role"] == "cashier"
    ]

    return render_template(
        "admin_cashiers.html",
        user=user,
        cashiers=cashiers
    )


# =========================================================
# ADMIN ADD ACCOUNTS
# =========================================================


@app.route("/admin/add-accounts")
def admin_add_accounts():
    if not login_required():
        return redirect(url_for("index"))

    user = current_user()

    if not user or user["role"] != "admin":
        return redirect(url_for("index"))

    return render_template(
        "admin_add_accounts.html",
        user=user,
        departments=departments,
        years=years
    )


@app.route("/admin/add-student", methods=["POST"])
def admin_add_student():
    if not login_required():
        return redirect(url_for("index"))

    admin = current_user()

    if not admin or admin["role"] != "admin":
        return redirect(url_for("index"))

    name = request.form.get("name", "").strip()

    department = request.form.get("department", "").strip()

    year = request.form.get("year", "").strip()

    username = request.form.get("username", "").strip()

    password = request.form.get("password", "")

    if not all([
        name,
        department,
        year,
        username,
        password
    ]):
        flash("Please fill in all student fields.", "error")
        return redirect(url_for("admin_add_accounts"))

    if get_user_by_username(username):
        flash("Username already exists.", "error")
        return redirect(url_for("admin_add_accounts"))

    users.append({
        "id": next_user_id(),
        "username": username,
        "password": password,
        "name": name,
        "role": "student",
        "department": department,
        "year": year
    })

    flash("Student account added successfully!", "success")

    return redirect(url_for("admin_add_accounts"))


@app.route("/admin/add-cashier", methods=["POST"])
def admin_add_cashier():
    if not login_required():
        return redirect(url_for("index"))

    admin = current_user()

    if not admin or admin["role"] != "admin":
        return redirect(url_for("index"))

    name = request.form.get("name", "").strip()

    username = request.form.get("username", "").strip()

    password = request.form.get("password", "")

    if not name or not username or not password:
        flash("Please fill in all cashier fields.", "error")
        return redirect(url_for("admin_add_accounts"))

    if get_user_by_username(username):
        flash("Username already exists.", "error")
        return redirect(url_for("admin_add_accounts"))

    users.append({
        "id": next_user_id(),
        "username": username,
        "password": password,
        "name": name,
        "role": "cashier"
    })

    flash("Cashier account added successfully!", "success")

    return redirect(url_for("admin_add_accounts"))


# =========================================================
# ADMIN EDIT USER
# =========================================================


@app.route("/admin/edit-user/<int:user_id>", methods=["POST"])
def admin_edit_user(user_id):
    if not login_required():
        return redirect(url_for("index"))

    admin = current_user()

    if not admin or admin["role"] != "admin":
        return redirect(url_for("index"))

    user = get_user(user_id)

    if not user:
        flash("User not found.", "error")
        return redirect(url_for("admin_students"))

    name = request.form.get("name", user["name"]).strip()

    username = request.form.get("username", user["username"]).strip()

    if not name or not username:
        flash("Name and username are required.", "error")

        if user["role"] == "cashier":
            return redirect(url_for("admin_cashiers"))

        return redirect(url_for("admin_students"))

    duplicate = next(
        (
            other_user
            for other_user in users
            if other_user["username"].lower() == username.lower()
            and other_user["id"] != user_id
        ),
        None
    )

    if duplicate:
        flash("Username already exists.", "error")

        if user["role"] == "cashier":
            return redirect(url_for("admin_cashiers"))

        return redirect(url_for("admin_students"))

    user["name"] = name
    user["username"] = username

    if user["role"] == "student":
        department = request.form.get(
            "department",
            user.get("department", "")
        ).strip()

        year = request.form.get(
            "year",
            user.get("year", "")
        ).strip()

        user["department"] = department
        user["year"] = year

        flash("Student account updated successfully.", "success")

        return redirect(url_for("admin_students"))

    if user["role"] == "cashier":
        flash("Cashier account updated successfully.", "success")

        return redirect(url_for("admin_cashiers"))

    flash("User updated successfully.", "success")

    return redirect(url_for("admin_accounts"))


# =========================================================
# ADMIN DELETE CASHIER
# =========================================================


@app.route("/admin/delete-student/<int:user_id>", methods=["POST"])
def admin_delete_student(user_id):
    if not login_required():
        return redirect(url_for("index"))

    admin = current_user()
    if not admin or admin["role"] != "admin":
        return redirect(url_for("index"))

    student = get_user(user_id)
    if not student:
        flash("Student not found.", "error")
        return redirect(url_for("admin_students"))

    if student["role"] != "student":
        flash("This account is not a student.", "error")
        return redirect(url_for("admin_students"))

    active_queues = [
        queue for queue in queue_records
        if queue["student_id"] == student["id"]
        and queue["status"] in ["Waiting", "Serving"]
    ]

    if active_queues and request.form.get("force_delete") != "1":
        flash(str(student["id"]), "active_queue_delete")
        return redirect(url_for("admin_students"))

    users.remove(student)
    flash("Student account deleted successfully.", "success")
    return redirect(url_for("admin_students"))


@app.route("/admin/delete-cashier/<int:user_id>", methods=["POST"])
def admin_delete_cashier(user_id):
    if not login_required():
        return redirect(url_for("index"))

    admin = current_user()
    if not admin or admin["role"] != "admin":
        return redirect(url_for("index"))

    cashier = get_user(user_id)
    if not cashier:
        flash("Cashier not found.", "error")
        return redirect(url_for("admin_cashiers"))

    if cashier["role"] != "cashier":
        flash("This account is not a cashier.", "error")
        return redirect(url_for("admin_cashiers"))

    cashier_schedules = [
        schedule for schedule in schedules
        if schedule["cashier_id"] == cashier["id"]
    ]

    cashier_schedule_ids = {
        schedule["id"] for schedule in cashier_schedules
    }

    active_queues = [
        queue for queue in queue_records
        if queue["schedule_id"] in cashier_schedule_ids
        and queue["status"] in ["Waiting", "Serving"]
    ]

    if active_queues and request.form.get("force_delete") != "1":
        flash(str(cashier["id"]), "active_queue_delete")
        return redirect(url_for("admin_cashiers"))

    users.remove(cashier)
    flash("Cashier account deleted successfully.", "success")
    return redirect(url_for("admin_cashiers"))


# =========================================================
# ADMIN STUDENTS
# =========================================================


@app.route("/admin/students")
def admin_students():
    if not login_required():
        return redirect(url_for("index"))

    user = current_user()

    if not user or user["role"] != "admin":
        return redirect(url_for("index"))

    selected_department = request.args.get("department")

    selected_year = request.args.get("year")

    students = [
        student
        for student in users
        if student["role"] == "student"
    ]

    if selected_department:
        students = [
            student
            for student in students
            if student["department"] == selected_department
        ]

    if selected_year:
        students = [
            student
            for student in students
            if student["year"] == selected_year
        ]

    return render_template(
        "admin_students.html",
        user=user,
        students=students,
        departments=departments,
        years=years,
        selected_department=selected_department,
        selected_year=selected_year
    )
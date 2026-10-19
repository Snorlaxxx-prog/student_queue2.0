from core import *

# STUDENT
# =========================================================


@app.route("/student")
def student_dashboard():
    if not login_required():
        return redirect(url_for("index"))

    user = current_user()

    if not user or user["role"] != "student":
        return redirect(url_for("index"))

    my_queues = get_student_queue(user["id"])

    latest_queue = None

    if my_queues:
        latest_queue = my_queues[0]

    serving = None

    if latest_queue:
        serving = get_current_serving(latest_queue["schedule_id"])

    schedule = None

    if latest_queue:
        schedule = get_schedule(latest_queue["schedule_id"])

        if schedule:
            schedule["cashier"] = get_user(schedule["cashier_id"])

    people_ahead = 0

    if latest_queue and latest_queue["status"] == "Waiting":
        waiting = get_waiting(latest_queue["schedule_id"])

        people_ahead = sum(
            1
            for queue in waiting
            if queue["queue_number"] < latest_queue["queue_number"]
        )

    return render_template(
        "student.html",
        user=user,
        queue=latest_queue,
        serving=serving,
        schedule=schedule,
        people_ahead=people_ahead
    )


@app.route("/student/my-queue")
def student_my_queue():
    if not login_required():
        return redirect(url_for("index"))

    user = current_user()

    if not user or user["role"] != "student":
        return redirect(url_for("index"))

    queues = get_student_queue(user["id"])

    data = []

    for queue in queues:
        queue_copy = queue.copy()

        queue_copy["schedule"] = get_schedule(queue["schedule_id"])

        if queue_copy["schedule"]:
            queue_copy["schedule"]["cashier"] = get_user(
                queue_copy["schedule"]["cashier_id"]
            )

        data.append(queue_copy)

    editable_schedules = []
    today = date.today().isoformat()
    for schedule in schedules:
        if schedule["date"] >= today:
            schedule_copy = schedule.copy()
            schedule_copy["cashier"] = get_user(schedule["cashier_id"])
            schedule_copy["waiting_count"] = get_active_queue_count(schedule["id"])
            schedule_copy["capacity"] = schedule_copy.get("capacity", 0)
            schedule_copy["available_slots"] = (
                max(schedule_copy["capacity"] - schedule_copy["waiting_count"], 0)
                if schedule_copy["capacity"] > 0 else None
            )
            editable_schedules.append(schedule_copy)

    return render_template(
        "student_my_queue.html",
        user=user,
        queues=data,
        schedules=editable_schedules
    )


@app.route("/student/schedules")
def student_schedules():
    if not login_required():
        return redirect(url_for("index"))

    user = current_user()

    if not user or user["role"] != "student":
        return redirect(url_for("index"))

    today = date.today().isoformat()

    available = [
        schedule
        for schedule in schedules
        if schedule["date"] >= today
    ]

    for schedule in available:
        schedule["cashier"] = get_user(schedule["cashier_id"])

        schedule["claimed_ticket"] = next(
            (queue for queue in queue_records
             if str(queue.get("student_id")) == str(user["id"])
             and str(queue.get("schedule_id")) == str(schedule["id"])
             and str(queue.get("status", "")).strip().lower() not in ("cancelled", "canceled")),
            None
        )
        schedule["waiting_count"] = get_active_queue_count(schedule["id"])

        schedule["capacity"] = schedule.get("capacity", 0)

        if schedule["capacity"] > 0:
            schedule["available_slots"] = max(
                schedule["capacity"] - schedule["waiting_count"],
                0
            )
        else:
            schedule["available_slots"] = None

    return render_template(
        "student_schedules.html",
        user=user,
        schedules=available
    )


@app.route("/student/get-ticket/<int:schedule_id>", methods=["POST"])
def get_ticket(schedule_id):
    if not login_required():
        return redirect(url_for("index"))

    user = current_user()

    if not user or user["role"] != "student":
        return redirect(url_for("index"))

    schedule = get_schedule(schedule_id)

    if not schedule:
        flash("Schedule not found.", "error")
        return redirect(url_for("student_schedules"))

    existing = next(
        (queue for queue in queue_records
         if str(queue.get("student_id")) == str(user["id"])
         and str(queue.get("schedule_id")) == str(schedule_id)
         and str(queue.get("status", "")).strip().lower() not in ("cancelled", "canceled")),
        None
    )

    if existing:
        flash("You already have a ticket for this schedule.", "error")
        return redirect(url_for("student_ticket", queue_id=existing["id"]))

    capacity = schedule.get("capacity", 0)

    active_count = get_active_queue_count(schedule_id)

    if capacity > 0 and active_count >= capacity:
        flash("This schedule is already full.", "error")
        return redirect(url_for("student_schedules"))

    token = secrets.token_urlsafe(16)

    queue = {
        "id": next_queue_id(),
        "student_id": user["id"],
        "schedule_id": schedule_id,
        "queue_number": get_queue_number(schedule_id),
        "token": token,
        "status": "Waiting",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    queue_records.append(queue)

    return redirect(url_for("student_ticket", queue_id=queue["id"]))


@app.route("/student/ticket/<int:queue_id>")
def student_ticket(queue_id):
    if not login_required():
        return redirect(url_for("index"))

    user = current_user()

    if not user or user["role"] != "student":
        return redirect(url_for("index"))

    queue = get_queue(queue_id)

    if not queue or queue["student_id"] != user["id"]:
        return redirect(url_for("student_dashboard"))

    schedule = get_schedule(queue["schedule_id"])

    if not schedule:
        return redirect(url_for("student_dashboard"))

    cashier = get_user(schedule["cashier_id"])

    return render_template(
        "student_ticket.html",
        user=user,
        queue=queue,
        schedule=schedule,
        cashier=cashier
    )


@app.route("/student/qr/<int:queue_id>")
def student_qr(queue_id):
    if not login_required():
        return redirect(url_for("index"))

    user = current_user()

    if not user or user["role"] != "student":
        return redirect(url_for("index"))

    queue = get_queue(queue_id)

    if not queue or queue["student_id"] != user["id"]:
        return redirect(url_for("student_dashboard"))

    image = qrcode.make(queue["token"])

    output = io.BytesIO()

    image.save(output, format="PNG")

    output.seek(0)

    return send_file(output, mimetype="image/png")


@app.route("/student/change-queue/<int:queue_id>", methods=["POST"])
def change_queue(queue_id):
    if not login_required():
        return redirect(url_for("index"))

    user = current_user()

    if not user or user["role"] != "student":
        return redirect(url_for("index"))

    queue = get_queue(queue_id)

    if not queue or queue["student_id"] != user["id"]:
        return redirect(url_for("student_dashboard"))

    if queue["status"] != "Waiting":
        flash("Only waiting queues can be moved.", "error")
        return redirect(url_for("student_my_queue"))

    new_schedule_id = request.form.get("schedule_id", type=int)

    if not new_schedule_id:
        flash("Please select a schedule.", "error")
        return redirect(url_for("student_my_queue"))

    new_schedule = get_schedule(new_schedule_id)

    if not new_schedule:
        flash("Schedule not found.", "error")
        return redirect(url_for("student_my_queue"))

    if new_schedule_id == queue["schedule_id"]:
        flash("You are already in this schedule.", "error")
        return redirect(url_for("student_my_queue"))

    if new_schedule["date"] < date.today().isoformat():
        flash("You can only move to a current or future schedule.", "error")
        return redirect(url_for("student_my_queue"))

    duplicate = next(
        (item for item in queue_records
         if item["id"] != queue["id"]
         and item["student_id"] == user["id"]
         and item["schedule_id"] == new_schedule_id
         and item["status"] != "Cancelled"),
        None
    )

    if duplicate:
        flash("You already have a ticket for that schedule.", "error")
        return redirect(url_for("student_my_queue"))

    capacity = new_schedule.get("capacity", 0)

    active_count = get_active_queue_count(new_schedule_id)

    if capacity > 0 and active_count >= capacity:
        flash("The selected schedule is already full.", "error")
        return redirect(url_for("student_my_queue"))

    queue["schedule_id"] = new_schedule_id

    queue["queue_number"] = get_queue_number(new_schedule_id)

    flash("Your queue was moved successfully.", "success")

    return redirect(url_for("student_my_queue"))


@app.route("/student/delete-queue/<int:queue_id>", methods=["POST"])
def delete_student_queue(queue_id):
    if not login_required():
        return redirect(url_for("index"))

    user = current_user()

    if not user or user["role"] != "student":
        return redirect(url_for("index"))

    queue = get_queue(queue_id)

    if not queue or queue["student_id"] != user["id"]:
        return redirect(url_for("student_dashboard"))

    if queue["status"] == "Serving":
        flash("A serving queue cannot be deleted.", "error")
        return redirect(url_for("student_my_queue"))

    queue["status"] = "Cancelled"

    flash("Queue cancelled.", "success")

    return redirect(url_for("student_my_queue"))


@app.route("/student/view-queue", methods=["GET", "POST"])
def student_view_queue():
    if not login_required():
        return redirect(url_for("index"))

    user = current_user()

    if not user or user["role"] != "student":
        return redirect(url_for("index"))

    cashier_id = request.args.get("cashier_id", type=int)

    cashiers = [
        user
        for user in users
        if user["role"] == "cashier"
    ]

    selected_cashier = None
    cashier_schedules = []
    queue_data = []

    if cashier_id:
        selected_cashier = get_user(cashier_id)

        if selected_cashier and selected_cashier["role"] == "cashier":
            cashier_schedules = [
                schedule
                for schedule in schedules
                if schedule["cashier_id"] == cashier_id
            ]

            for schedule in cashier_schedules:
                schedule_queues = get_schedule_queues(schedule["id"])

                for queue in schedule_queues:
                    queue_copy = queue.copy()

                    queue_copy["schedule"] = schedule

                    queue_copy["student"] = get_user(queue["student_id"])

                    queue_data.append(queue_copy)

        else:
            selected_cashier = None

    return render_template(
        "student_view_queue.html",
        user=user,
        cashiers=cashiers,
        selected_cashier=selected_cashier,
        schedules=cashier_schedules,
        queues=queue_data
    )
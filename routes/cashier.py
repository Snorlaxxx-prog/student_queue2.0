from core import *

# CASHIER
# =========================================================


@app.route("/cashier")
def cashier_dashboard():
    if not login_required():
        return redirect(url_for("index"))

    user = current_user()

    if not user or user["role"] != "cashier":
        return redirect(url_for("index"))

    my_schedules = [
        schedule
        for schedule in schedules
        if schedule["cashier_id"] == user["id"]
    ]

    selected_schedule = None

    schedule_id = request.args.get("schedule_id", type=int)

    if schedule_id:
        selected_schedule = get_schedule(schedule_id)

        if selected_schedule and selected_schedule["cashier_id"] != user["id"]:
            selected_schedule = None

    if not selected_schedule and my_schedules:
        selected_schedule = my_schedules[0]

    latest = None
    waiting = []

    if selected_schedule:
        latest = get_current_serving(selected_schedule["id"])

        if not latest:
            waiting = get_waiting(selected_schedule["id"])

        if latest:
            latest["student"] = get_user(latest["student_id"])

    return render_template(
        "cashier.html",
        user=user,
        schedules=my_schedules,
        selected_schedule=selected_schedule,
        latest=latest,
        waiting=waiting
    )


@app.route("/cashier/next", methods=["POST"])
def cashier_next():
    if not login_required():
        return redirect(url_for("index"))

    user = current_user()

    if not user or user["role"] != "cashier":
        return redirect(url_for("index"))

    schedule_id = request.form.get("schedule_id", type=int)

    schedule = get_schedule(schedule_id)

    if not schedule or schedule["cashier_id"] != user["id"]:
        flash("Invalid schedule.", "error")
        return redirect(url_for("cashier_dashboard"))

    serving = get_current_serving(schedule_id)

    if serving:
        serving["status"] = "Completed"

    waiting = get_waiting(schedule_id)

    if waiting:
        waiting[0]["status"] = "Serving"

    return redirect(url_for("cashier_dashboard", schedule_id=schedule_id))


@app.route("/cashier/schedules")
def cashier_schedules():
    if not login_required():
        return redirect(url_for("index"))

    user = current_user()

    if not user or user["role"] != "cashier":
        return redirect(url_for("index"))

    my_schedules = [
        schedule
        for schedule in schedules
        if schedule["cashier_id"] == user["id"]
    ]

    return render_template(
        "cashier_schedules.html",
        user=user,
        schedules=my_schedules,
        current_date=date.today().isoformat()
    )


@app.route("/cashier/schedules/add", methods=["POST"])
def add_schedule():
    if not login_required():
        return redirect(url_for("index"))

    user = current_user()

    if not user or user["role"] != "cashier":
        return redirect(url_for("index"))

    schedule_date = request.form.get("date")

    start_time = request.form.get("start_time")

    end_time = request.form.get("end_time")

    capacity = request.form.get("capacity", type=int)

    if not schedule_date or not start_time or not end_time or capacity is None:
        flash("All schedule fields are required.", "error")
        return redirect(url_for("cashier_schedules"))

    if schedule_date < date.today().isoformat():
        flash("You cannot create a schedule in the past.", "error")
        return redirect(url_for("cashier_schedules"))

    if start_time >= end_time:
        flash("End time must be later than start time.", "error")
        return redirect(url_for("cashier_schedules"))

    if capacity < 1:
        flash("Students to Cater must be at least 1.", "error")
        return redirect(url_for("cashier_schedules"))

    duplicate = next(
        (
            schedule
            for schedule in schedules
            if schedule["cashier_id"] == user["id"]
            and schedule["date"] == schedule_date
            and schedule["start_time"] == start_time
            and schedule["end_time"] == end_time
        ),
        None
    )

    if duplicate:
        flash("This schedule already exists.", "error")
        return redirect(url_for("cashier_schedules"))

    schedule_day = datetime.strptime(
        schedule_date,
        "%Y-%m-%d"
    ).strftime("%A")

    schedules.append({
        "id": next_schedule_id(),
        "cashier_id": user["id"],
        "date": schedule_date,
        "day": schedule_day,
        "start_time": start_time,
        "end_time": end_time,
        "capacity": capacity
    })

    flash("Schedule created successfully.", "success")

    return redirect(url_for("cashier_schedules"))


@app.route("/cashier/schedules/edit/<int:schedule_id>", methods=["POST"])
def edit_schedule(schedule_id):
    if not login_required():
        return redirect(url_for("index"))

    user = current_user()

    if not user or user["role"] != "cashier":
        return redirect(url_for("index"))

    schedule = get_schedule(schedule_id)

    if not schedule or schedule["cashier_id"] != user["id"]:
        return redirect(url_for("cashier_schedules"))

    schedule_date = request.form.get("date")

    start_time = request.form.get("start_time")

    end_time = request.form.get("end_time")

    capacity = request.form.get("capacity", type=int)

    if not schedule_date or not start_time or not end_time or capacity is None:
        flash("All fields are required.", "error")
        return redirect(url_for("cashier_schedules"))

    if schedule_date < date.today().isoformat():
        flash("The date cannot be in the past.", "error")
        return redirect(url_for("cashier_schedules"))

    if start_time >= end_time:
        flash("End time must be later than start time.", "error")
        return redirect(url_for("cashier_schedules"))

    if capacity < 1:
        flash("Students to Cater must be at least 1.", "error")
        return redirect(url_for("cashier_schedules"))

    active_count = get_active_queue_count(schedule_id)

    if capacity < active_count:
        flash(
            f"Capacity cannot be lower than the {active_count} active student(s) already in this schedule.",
            "error"
        )
        return redirect(url_for("cashier_schedules"))

    schedule["date"] = schedule_date

    schedule["day"] = datetime.strptime(
        schedule_date,
        "%Y-%m-%d"
    ).strftime("%A")

    schedule["start_time"] = start_time
    schedule["end_time"] = end_time
    schedule["capacity"] = capacity

    flash("Schedule updated.", "success")

    return redirect(url_for("cashier_schedules"))


@app.route("/cashier/schedules/delete/<int:schedule_id>", methods=["POST"])
def delete_schedule(schedule_id):
    if not login_required():
        return redirect(url_for("index"))

    user = current_user()

    if not user or user["role"] != "cashier":
        return redirect(url_for("index"))

    schedule = get_schedule(schedule_id)

    if not schedule or schedule["cashier_id"] != user["id"]:
        return redirect(url_for("cashier_schedules"))

    schedule_queues = get_schedule_queues(schedule_id)

    active_queues = [
        queue
        for queue in schedule_queues
        if queue["status"] in ["Waiting", "Serving"]
    ]

    if active_queues:
        flash("You cannot delete a schedule with active queues.", "error")
        return redirect(url_for("cashier_schedules"))

    schedules.remove(schedule)

    flash("Schedule deleted.", "success")

    return redirect(url_for("cashier_schedules"))


@app.route("/cashier/all-queue")
def cashier_all_queue():
    if not login_required():
        return redirect(url_for("index"))

    user = current_user()

    if not user or user["role"] != "cashier":
        return redirect(url_for("index"))

    my_schedules = [
        schedule
        for schedule in schedules
        if schedule["cashier_id"] == user["id"]
    ]

    my_schedule_ids = [
        schedule["id"]
        for schedule in my_schedules
    ]

    queues = [
        queue
        for queue in queue_records
        if queue["schedule_id"] in my_schedule_ids
    ]

    data = []

    for queue in queues:
        item = queue.copy()

        item["student"] = get_user(queue["student_id"])

        item["schedule"] = get_schedule(queue["schedule_id"])

        data.append(item)

    data.sort(
        key=lambda item: (
            item["schedule"]["date"],
            item["schedule"]["start_time"],
            item["queue_number"]
        )
    )

    return render_template(
        "cashier_all_queue.html",
        user=user,
        queues=data
    )


@app.route("/cashier/scan")
def cashier_scan():
    if not login_required():
        return redirect(url_for("index"))

    user = current_user()

    if not user or user["role"] != "cashier":
        return redirect(url_for("index"))

    return render_template("cashier_scan.html", user=user)


@app.route("/cashier/scan-result", methods=["POST"])
def cashier_scan_result():
    if not login_required():
        return redirect(url_for("index"))

    user = current_user()

    if not user or user["role"] != "cashier":
        return redirect(url_for("index"))

    token = request.form.get("token", "").strip()

    queue = next(
        (
            queue
            for queue in queue_records
            if queue["token"] == token
        ),
        None
    )

    if not queue:
        flash("QR code is invalid.", "error")
        return redirect(url_for("cashier_scan"))

    schedule = get_schedule(queue["schedule_id"])

    if not schedule:
        flash("Schedule not found.", "error")
        return redirect(url_for("cashier_scan"))

    if schedule["cashier_id"] != user["id"]:
        flash("This ticket does not belong to your schedule.", "error")
        return redirect(url_for("cashier_scan"))

    student = get_user(queue["student_id"])

    return render_template(
        "cashier_scan.html",
        user=user,
        scanned_queue=queue,
        student=student,
        schedule=schedule
    )
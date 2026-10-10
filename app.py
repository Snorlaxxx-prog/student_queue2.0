from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file
from datetime import datetime, date
import qrcode
import io
import secrets

app = Flask(__name__)
app.secret_key = "student_queue_system_secret"

users = [
    {
        "id": 1,
        "username": "student",
        "password": "1234",
        "name": "Rimuru Tempest",
        "role": "student",
        "department": "Computer Science",
        "year": "2nd Year"
    },
    {
        "id": 2,
        "username": "cashier",
        "password": "1234",
        "name": "Finance Cashier",
        "role": "cashier"
    },
    {
        "id": 3,
        "username": "admin",
        "password": "1234",
        "name": "System Administrator",
        "role": "admin"
    }
]

schedules = []
queue_records = []

departments = [
    "Department of Computer Science",
    "Department of Education",
    "Department of Criminology",
    "Department of Business Administration",
    "Department of Arts of English Literature"
]

years = [
    "1st Year",
    "2nd Year",
    "3rd Year",
    "4th Year",
    "5th Year"
]


class User:
    def __init__(self, user_id, username, password, name):
        self._user_id = user_id
        self._username = username
        self._password = password
        self._name = name

    def get_role(self):
        return "user"

    def dashboard(self):
        return "login.html"

    def check_password(self, password):
        return self._password == password

    def get_name(self):
        return self._name


class Student(User):
    def __init__(
        self,
        user_id,
        username,
        password,
        name,
        department,
        year
    ):
        super().__init__(
            user_id,
            username,
            password,
            name
        )

        self._department = department
        self._year = year

    def get_role(self):
        return "student"

    def dashboard(self):
        return "student.html"


class Cashier(User):
    def get_role(self):
        return "cashier"

    def dashboard(self):
        return "cashier.html"


class Admin(User):
    def get_role(self):
        return "admin"

    def dashboard(self):
        return "admin.html"


def get_user(user_id):
    return next(
        (
            user for user in users
            if user["id"] == user_id
        ),
        None
    )


def get_user_by_username(username):
    return next(
        (
            user for user in users
            if user["username"].lower() == username.lower()
        ),
        None
    )


def get_schedule(schedule_id):
    return next(
        (
            schedule for schedule in schedules
            if schedule["id"] == schedule_id
        ),
        None
    )


def get_queue(queue_id):
    return next(
        (
            queue for queue in queue_records
            if queue["id"] == queue_id
        ),
        None
    )


def current_user():
    if "user_id" not in session:
        return None

    return get_user(session["user_id"])


def next_user_id():
    if not users:
        return 1

    return max(
        user["id"] for user in users
    ) + 1


def next_schedule_id():
    if not schedules:
        return 1

    return max(
        schedule["id"] for schedule in schedules
    ) + 1


def next_queue_id():
    if not queue_records:
        return 1

    return max(
        queue["id"] for queue in queue_records
    ) + 1


def get_queue_number(schedule_id):
    existing_numbers = [
        queue["queue_number"]
        for queue in queue_records
        if queue["schedule_id"] == schedule_id
    ]

    if not existing_numbers:
        return 1

    return max(existing_numbers) + 1


def get_active_queue_count(schedule_id):
    return sum(
        1
        for queue in queue_records
        if queue["schedule_id"] == schedule_id
        and queue["status"] in ["Waiting", "Serving"]
    )


def get_schedule_queues(schedule_id):
    return [
        queue
        for queue in queue_records
        if queue["schedule_id"] == schedule_id
    ]


def get_current_serving(schedule_id):
    serving = [
        queue
        for queue in queue_records
        if queue["schedule_id"] == schedule_id
        and queue["status"] == "Serving"
    ]

    if not serving:
        return None

    return serving[0]


def get_waiting(schedule_id):
    return sorted(
        [
            queue
            for queue in queue_records
            if queue["schedule_id"] == schedule_id
            and queue["status"] == "Waiting"
        ],
        key=lambda queue: queue["queue_number"]
    )


def get_student_queue(student_id):
    return [
        queue
        for queue in queue_records
        if queue["student_id"] == student_id
        and queue["status"] in ["Waiting", "Serving"]
    ]


def login_required():
    return "user_id" in session


# =========================================================
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


# =========================================================
# STUDENT
# =========================================================

@app.route("/student")
def student_dashboard():
    if not login_required():
        return redirect(url_for("index"))

    user = current_user()

    if not user or user["role"] != "student":
        return redirect(url_for("index"))

    my_queues = get_student_queue(
        user["id"]
    )

    latest_queue = None

    if my_queues:
        latest_queue = my_queues[0]

    serving = None

    if latest_queue:
        serving = get_current_serving(
            latest_queue["schedule_id"]
        )

    schedule = None

    if latest_queue:
        schedule = get_schedule(
            latest_queue["schedule_id"]
        )

        if schedule:
            schedule["cashier"] = get_user(
                schedule["cashier_id"]
            )

    people_ahead = 0

    if latest_queue and latest_queue["status"] == "Waiting":

        waiting = get_waiting(
            latest_queue["schedule_id"]
        )

        people_ahead = sum(
            1
            for queue in waiting
            if queue["queue_number"]
            < latest_queue["queue_number"]
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

    queues = get_student_queue(
        user["id"]
    )

    data = []

    for queue in queues:

        queue_copy = queue.copy()

        queue_copy["schedule"] = get_schedule(
            queue["schedule_id"]
        )

        if queue_copy["schedule"]:
            queue_copy["schedule"]["cashier"] = get_user(
                queue_copy["schedule"]["cashier_id"]
            )

        data.append(queue_copy)

    return render_template(
        "student_my_queue.html",
        user=user,
        queues=data
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

        schedule["cashier"] = get_user(
            schedule["cashier_id"]
        )

        schedule["waiting_count"] = get_active_queue_count(
            schedule["id"]
        )

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


@app.route(
    "/student/get-ticket/<int:schedule_id>",
    methods=["POST"]
)
def get_ticket(schedule_id):

    if not login_required():
        return redirect(url_for("index"))

    user = current_user()

    if not user or user["role"] != "student":
        return redirect(url_for("index"))

    schedule = get_schedule(
        schedule_id
    )

    if not schedule:
        flash(
            "Schedule not found.",
            "error"
        )

        return redirect(
            url_for("student_schedules")
        )

    existing = [
        queue
        for queue in queue_records
        if queue["student_id"] == user["id"]
        and queue["schedule_id"] == schedule_id
        and queue["status"] in ["Waiting", "Serving"]
    ]

    if existing:
        return redirect(
            url_for(
                "student_ticket",
                queue_id=existing[0]["id"]
            )
        )

    capacity = schedule.get("capacity", 0)
    active_count = get_active_queue_count(schedule_id)

    if capacity > 0 and active_count >= capacity:
        flash(
            "This schedule is already full.",
            "error"
        )
        return redirect(
            url_for("student_schedules")
        )

    token = secrets.token_urlsafe(
        16
    )

    queue = {
        "id": next_queue_id(),
        "student_id": user["id"],
        "schedule_id": schedule_id,
        "queue_number": get_queue_number(
            schedule_id
        ),
        "token": token,
        "status": "Waiting",
        "created_at": datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    }

    queue_records.append(queue)

    return redirect(
        url_for(
            "student_ticket",
            queue_id=queue["id"]
        )
    )


@app.route(
    "/student/ticket/<int:queue_id>"
)
def student_ticket(queue_id):

    if not login_required():
        return redirect(url_for("index"))

    user = current_user()

    if not user or user["role"] != "student":
        return redirect(url_for("index"))

    queue = get_queue(queue_id)

    if not queue or queue["student_id"] != user["id"]:
        return redirect(
            url_for("student_dashboard")
        )

    schedule = get_schedule(
        queue["schedule_id"]
    )

    if not schedule:
        return redirect(
            url_for("student_dashboard")
        )

    cashier = get_user(
        schedule["cashier_id"]
    )

    return render_template(
        "student_ticket.html",
        user=user,
        queue=queue,
        schedule=schedule,
        cashier=cashier
    )


@app.route(
    "/student/qr/<int:queue_id>"
)
def student_qr(queue_id):

    if not login_required():
        return redirect(url_for("index"))

    user = current_user()

    if not user or user["role"] != "student":
        return redirect(url_for("index"))

    queue = get_queue(queue_id)

    if not queue or queue["student_id"] != user["id"]:
        return redirect(
            url_for("student_dashboard")
        )

    image = qrcode.make(
        queue["token"]
    )

    output = io.BytesIO()

    image.save(
        output,
        format="PNG"
    )

    output.seek(0)

    return send_file(
        output,
        mimetype="image/png"
    )


@app.route(
    "/student/change-queue/<int:queue_id>",
    methods=["POST"]
)
def change_queue(queue_id):

    if not login_required():
        return redirect(url_for("index"))

    user = current_user()

    if not user or user["role"] != "student":
        return redirect(url_for("index"))

    queue = get_queue(queue_id)

    if not queue or queue["student_id"] != user["id"]:
        return redirect(
            url_for("student_dashboard")
        )

    if queue["status"] != "Waiting":
        flash(
            "Only waiting queues can be moved.",
            "error"
        )

        return redirect(
            url_for("student_my_queue")
        )

    new_schedule_id = request.form.get(
        "schedule_id",
        type=int
    )

    if not new_schedule_id:
        flash(
            "Please select a schedule.",
            "error"
        )

        return redirect(
            url_for("student_my_queue")
        )

    new_schedule = get_schedule(
        new_schedule_id
    )

    if not new_schedule:
        flash(
            "Schedule not found.",
            "error"
        )

        return redirect(
            url_for("student_my_queue")
        )

    if new_schedule_id == queue["schedule_id"]:
        flash(
            "You are already in this schedule.",
            "error"
        )
        return redirect(url_for("student_my_queue"))

    capacity = new_schedule.get("capacity", 0)
    active_count = get_active_queue_count(new_schedule_id)

    if capacity > 0 and active_count >= capacity:
        flash(
            "The selected schedule is already full.",
            "error"
        )
        return redirect(url_for("student_my_queue"))

    queue["schedule_id"] = new_schedule_id

    queue["queue_number"] = get_queue_number(
        new_schedule_id
    )

    flash(
        "Your queue was moved successfully.",
        "success"
    )

    return redirect(
        url_for("student_my_queue")
    )


@app.route(
    "/student/delete-queue/<int:queue_id>",
    methods=["POST"]
)
def delete_student_queue(queue_id):

    if not login_required():
        return redirect(url_for("index"))

    user = current_user()

    if not user or user["role"] != "student":
        return redirect(url_for("index"))

    queue = get_queue(queue_id)

    if not queue or queue["student_id"] != user["id"]:
        return redirect(
            url_for("student_dashboard")
        )

    if queue["status"] == "Serving":
        flash(
            "A serving queue cannot be deleted.",
            "error"
        )

        return redirect(
            url_for("student_my_queue")
        )

    queue["status"] = "Cancelled"

    flash(
        "Queue cancelled.",
        "success"
    )

    return redirect(
        url_for("student_my_queue")
    )


@app.route(
    "/student/view-queue",
    methods=["GET", "POST"]
)
def student_view_queue():

    if not login_required():
        return redirect(url_for("index"))

    user = current_user()

    if not user or user["role"] != "student":
        return redirect(url_for("index"))

    cashier_id = request.args.get(
        "cashier_id",
        type=int
    )

    cashiers = [
        user
        for user in users
        if user["role"] == "cashier"
    ]

    selected_cashier = None
    cashier_schedules = []
    queue_data = []

    if cashier_id:

        selected_cashier = get_user(
            cashier_id
        )

        if (
            selected_cashier
            and selected_cashier["role"] == "cashier"
        ):

            cashier_schedules = [
                schedule
                for schedule in schedules
                if schedule["cashier_id"] == cashier_id
            ]

            for schedule in cashier_schedules:

                schedule_queues = get_schedule_queues(
                    schedule["id"]
                )

                for queue in schedule_queues:

                    queue_copy = queue.copy()

                    queue_copy["schedule"] = schedule

                    queue_copy["student"] = get_user(
                        queue["student_id"]
                    )

                    queue_data.append(
                        queue_copy
                    )

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


# =========================================================
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

    schedule_id = request.args.get(
        "schedule_id",
        type=int
    )

    if schedule_id:

        selected_schedule = get_schedule(
            schedule_id
        )

        if (
            selected_schedule
            and selected_schedule["cashier_id"] != user["id"]
        ):
            selected_schedule = None

    if not selected_schedule and my_schedules:
        selected_schedule = my_schedules[0]

    latest = None
    waiting = []

    if selected_schedule:

        latest = get_current_serving(
            selected_schedule["id"]
        )

        if not latest:
            waiting = get_waiting(
                selected_schedule["id"]
            )

        if latest:
            latest["student"] = get_user(
                latest["student_id"]
            )

    return render_template(
        "cashier.html",
        user=user,
        schedules=my_schedules,
        selected_schedule=selected_schedule,
        latest=latest,
        waiting=waiting
    )


@app.route(
    "/cashier/next",
    methods=["POST"]
)
def cashier_next():

    if not login_required():
        return redirect(url_for("index"))

    user = current_user()

    if not user or user["role"] != "cashier":
        return redirect(url_for("index"))

    schedule_id = request.form.get(
        "schedule_id",
        type=int
    )

    schedule = get_schedule(
        schedule_id
    )

    if (
        not schedule
        or schedule["cashier_id"] != user["id"]
    ):
        flash(
            "Invalid schedule.",
            "error"
        )

        return redirect(
            url_for("cashier_dashboard")
        )

    serving = get_current_serving(
        schedule_id
    )

    if serving:
        serving["status"] = "Completed"

    waiting = get_waiting(
        schedule_id
    )

    if waiting:
        waiting[0]["status"] = "Serving"

    return redirect(
        url_for(
            "cashier_dashboard",
            schedule_id=schedule_id
        )
    )


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


@app.route(
    "/cashier/schedules/add",
    methods=["POST"]
)
def add_schedule():

    if not login_required():
        return redirect(url_for("index"))

    user = current_user()

    if not user or user["role"] != "cashier":
        return redirect(url_for("index"))

    schedule_date = request.form.get(
        "date"
    )

    start_time = request.form.get(
        "start_time"
    )

    end_time = request.form.get(
        "end_time"
    )

    capacity = request.form.get("capacity", type=int)

    if not schedule_date or not start_time or not end_time or capacity is None:
        flash(
            "All schedule fields are required.",
            "error"
        )

        return redirect(
            url_for("cashier_schedules")
        )

    if schedule_date < date.today().isoformat():
        flash(
            "You cannot create a schedule in the past.",
            "error"
        )

        return redirect(
            url_for("cashier_schedules")
        )

    if start_time >= end_time:
        flash(
            "End time must be later than start time.",
            "error"
        )

        return redirect(
            url_for("cashier_schedules")
        )

    if capacity < 1:
        flash(
            "Students to Cater must be at least 1.",
            "error"
        )
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
        flash(
            "This schedule already exists.",
            "error"
        )

        return redirect(
            url_for("cashier_schedules")
        )

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

    flash(
        "Schedule created successfully.",
        "success"
    )

    return redirect(
        url_for("cashier_schedules")
    )


@app.route(
    "/cashier/schedules/edit/<int:schedule_id>",
    methods=["POST"]
)
def edit_schedule(schedule_id):

    if not login_required():
        return redirect(url_for("index"))

    user = current_user()

    if not user or user["role"] != "cashier":
        return redirect(url_for("index"))

    schedule = get_schedule(
        schedule_id
    )

    if (
        not schedule
        or schedule["cashier_id"] != user["id"]
    ):
        return redirect(
            url_for("cashier_schedules")
        )

    schedule_date = request.form.get(
        "date"
    )

    start_time = request.form.get(
        "start_time"
    )

    end_time = request.form.get(
        "end_time"
    )

    capacity = request.form.get("capacity", type=int)

    if not schedule_date or not start_time or not end_time or capacity is None:
        flash(
            "All fields are required.",
            "error"
        )

        return redirect(
            url_for("cashier_schedules")
        )

    if schedule_date < date.today().isoformat():
        flash(
            "The date cannot be in the past.",
            "error"
        )

        return redirect(
            url_for("cashier_schedules")
        )

    if start_time >= end_time:
        flash(
            "End time must be later than start time.",
            "error"
        )

        return redirect(
            url_for("cashier_schedules")
        )

    if capacity < 1:
        flash(
            "Students to Cater must be at least 1.",
            "error"
        )
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

    flash(
        "Schedule updated.",
        "success"
    )

    return redirect(
        url_for("cashier_schedules")
    )


@app.route(
    "/cashier/schedules/delete/<int:schedule_id>",
    methods=["POST"]
)
def delete_schedule(schedule_id):

    if not login_required():
        return redirect(url_for("index"))

    user = current_user()

    if not user or user["role"] != "cashier":
        return redirect(url_for("index"))

    schedule = get_schedule(
        schedule_id
    )

    if (
        not schedule
        or schedule["cashier_id"] != user["id"]
    ):
        return redirect(
            url_for("cashier_schedules")
        )

    schedule_queues = get_schedule_queues(
        schedule_id
    )

    active_queues = [
        queue
        for queue in schedule_queues
        if queue["status"] in ["Waiting", "Serving"]
    ]

    if active_queues:
        flash(
            "You cannot delete a schedule with active queues.",
            "error"
        )

        return redirect(
            url_for("cashier_schedules")
        )

    schedules.remove(schedule)

    flash(
        "Schedule deleted.",
        "success"
    )

    return redirect(
        url_for("cashier_schedules")
    )


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

        item["student"] = get_user(
            queue["student_id"]
        )

        item["schedule"] = get_schedule(
            queue["schedule_id"]
        )

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

    return render_template(
        "cashier_scan.html",
        user=user
    )


@app.route(
    "/cashier/scan-result",
    methods=["POST"]
)
def cashier_scan_result():

    if not login_required():
        return redirect(url_for("index"))

    user = current_user()

    if not user or user["role"] != "cashier":
        return redirect(url_for("index"))

    token = request.form.get(
        "token",
        ""
    ).strip()

    queue = next(
        (
            queue
            for queue in queue_records
            if queue["token"] == token
        ),
        None
    )

    if not queue:
        flash(
            "QR code is invalid.",
            "error"
        )

        return redirect(
            url_for("cashier_scan")
        )

    schedule = get_schedule(
        queue["schedule_id"]
    )

    if not schedule:
        flash(
            "Schedule not found.",
            "error"
        )

        return redirect(
            url_for("cashier_scan")
        )

    if schedule["cashier_id"] != user["id"]:
        flash(
            "This ticket does not belong to your schedule.",
            "error"
        )

        return redirect(
            url_for("cashier_scan")
        )

    student = get_user(
        queue["student_id"]
    )

    return render_template(
        "cashier_scan.html",
        user=user,
        scanned_queue=queue,
        student=student,
        schedule=schedule
    )


# =========================================================
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

        queue_copy["student"] = get_user(
            queue["student_id"]
        )

        queue_copy["schedule"] = get_schedule(
            queue["schedule_id"]
        )

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


@app.route(
    "/admin/add-student",
    methods=["POST"]
)
def admin_add_student():

    if not login_required():
        return redirect(url_for("index"))

    admin = current_user()

    if not admin or admin["role"] != "admin":
        return redirect(url_for("index"))

    name = request.form.get(
        "name",
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

    username = request.form.get(
        "username",
        ""
    ).strip()

    password = request.form.get(
        "password",
        ""
    )

    if not all([
        name,
        department,
        year,
        username,
        password
    ]):
        flash(
            "Please fill in all student fields.",
            "error"
        )

        return redirect(
            url_for("admin_add_accounts")
        )

    if get_user_by_username(username):
        flash(
            "Username already exists.",
            "error"
        )

        return redirect(
            url_for("admin_add_accounts")
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
        "Student account added successfully!",
        "success"
    )

    return redirect(
        url_for("admin_add_accounts")
    )


@app.route(
    "/admin/add-cashier",
    methods=["POST"]
)
def admin_add_cashier():

    if not login_required():
        return redirect(url_for("index"))

    admin = current_user()

    if not admin or admin["role"] != "admin":
        return redirect(url_for("index"))

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
    )

    if not name or not username or not password:
        flash(
            "Please fill in all cashier fields.",
            "error"
        )

        return redirect(
            url_for("admin_add_accounts")
        )

    if get_user_by_username(username):
        flash(
            "Username already exists.",
            "error"
        )

        return redirect(
            url_for("admin_add_accounts")
        )

    users.append({
        "id": next_user_id(),
        "username": username,
        "password": password,
        "name": name,
        "role": "cashier"
    })

    flash(
        "Cashier account added successfully!",
        "success"
    )

    return redirect(
        url_for("admin_add_accounts")
    )


# =========================================================
# ADMIN EDIT USER
# =========================================================

@app.route(
    "/admin/edit-user/<int:user_id>",
    methods=["POST"]
)
def admin_edit_user(user_id):

    if not login_required():
        return redirect(url_for("index"))

    admin = current_user()

    if not admin or admin["role"] != "admin":
        return redirect(url_for("index"))

    user = get_user(user_id)

    if not user:
        flash(
            "User not found.",
            "error"
        )

        return redirect(
            url_for("admin_students")
        )

    name = request.form.get(
        "name",
        user["name"]
    ).strip()

    username = request.form.get(
        "username",
        user["username"]
    ).strip()

    if not name or not username:
        flash(
            "Name and username are required.",
            "error"
        )

        if user["role"] == "cashier":
            return redirect(
                url_for("admin_cashiers")
            )

        return redirect(
            url_for("admin_students")
        )

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
        flash(
            "Username already exists.",
            "error"
        )

        if user["role"] == "cashier":
            return redirect(
                url_for("admin_cashiers")
            )

        return redirect(
            url_for("admin_students")
        )

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

        flash(
            "Student account updated successfully.",
            "success"
        )

        return redirect(
            url_for("admin_students")
        )

    if user["role"] == "cashier":

        flash(
            "Cashier account updated successfully.",
            "success"
        )

        return redirect(
            url_for("admin_cashiers")
        )

    flash(
        "User updated successfully.",
        "success"
    )

    return redirect(
        url_for("admin_accounts")
    )


# =========================================================
# ADMIN DELETE CASHIER
# =========================================================
@app.route(
    "/admin/delete-student/<int:user_id>",
    methods=["POST"]
)
def admin_delete_student(user_id):

    if not login_required():
        return redirect(url_for("index"))

    admin = current_user()

    if not admin or admin["role"] != "admin":
        return redirect(url_for("index"))

    student = get_user(user_id)

    if not student:
        flash(
            "Student not found.",
            "error"
        )

        return redirect(
            url_for("admin_students")
        )

    if student["role"] != "student":
        flash(
            "This account is not a student.",
            "error"
        )

        return redirect(
            url_for("admin_students")
        )

    active_queues = [
        queue
        for queue in queue_records
        if queue["student_id"] == student["id"]
        and queue["status"] in [
            "Waiting",
            "Serving"
        ]
    ]

    if active_queues:
        flash(
            "This student cannot be deleted because they have an active queue.",
            "error"
        )

        return redirect(
            url_for("admin_students")
        )

    users.remove(student)

    flash(
        "Student account deleted successfully.",
        "success"
    )

    return redirect(
        url_for("admin_students")
    )

@app.route(
    "/admin/delete-cashier/<int:user_id>",
    methods=["POST"]
)
def admin_delete_cashier(user_id):

    if not login_required():
        return redirect(url_for("index"))

    admin = current_user()

    if not admin or admin["role"] != "admin":
        return redirect(url_for("index"))

    cashier = get_user(user_id)

    if not cashier:
        flash(
            "Cashier not found.",
            "error"
        )

        return redirect(
            url_for("admin_cashiers")
        )

    if cashier["role"] != "cashier":
        flash(
            "This account is not a cashier.",
            "error"
        )

        return redirect(
            url_for("admin_cashiers")
        )

    cashier_schedules = [
        schedule
        for schedule in schedules
        if schedule["cashier_id"] == cashier["id"]
    ]

    active_queues = []

    for schedule in cashier_schedules:

        active_queues.extend(
            [
                queue
                for queue in queue_records
                if queue["schedule_id"] == schedule["id"]
                and queue["status"] in [
                    "Waiting",
                    "Serving"
                ]
            ]
        )

    if active_queues:
        flash(
            "This cashier cannot be deleted because there are active queues.",
            "error"
        )

        return redirect(
            url_for("admin_cashiers")
        )

    users.remove(cashier)

    flash(
        "Cashier account deleted successfully.",
        "success"
    )

    return redirect(
        url_for("admin_cashiers")
    )


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

    selected_department = request.args.get(
        "department"
    )

    selected_year = request.args.get(
        "year"
    )

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


# =========================================================
# RUN APPLICATION
# =========================================================

if __name__ == "__main__":
    app.run(
        debug=True
    )
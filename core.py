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

    "4th Year"

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

from core import *

# ACCOUNT SETTINGS
# =========================================================

@app.route("/account/settings", methods=["GET", "POST"])
def account_settings():
    if not login_required():
        return redirect(url_for("index"))

    user = current_user()

    if not user:
        session.clear()
        return redirect(url_for("index"))

    if request.method == "POST":
        action = request.form.get("action", "")

        if action == "username":
            new_username = request.form.get(
                "username", ""
            ).strip()

            if not new_username:
                flash("Username cannot be empty.", "error")

            else:
                duplicate = next(
                    (
                        other for other in users
                        if other["username"].lower()
                        == new_username.lower()
                        and other["id"] != user["id"]
                    ),
                    None
                )

                if duplicate:
                    flash("Username already exists.", "error")
                elif new_username == user["username"]:
                    flash("Your username is unchanged.", "error")
                else:
                    user["username"] = new_username
                    flash("Username updated successfully.", "success")

        elif action == "password":
            current_password = request.form.get(
                "current_password", ""
            )

            new_password = request.form.get(
                "new_password", ""
            )

            confirm_password = request.form.get(
                "confirm_password", ""
            )

            if current_password != user["password"]:
                flash("Current password is incorrect.", "error")

            elif len(new_password) < 2:
                flash(
                    "New password must be at least 2 characters.",
                    "error"
                )

            elif new_password != confirm_password:
                flash("New passwords do not match.", "error")

            elif new_password == current_password:
                flash(
                    "Your new password must be different.",
                    "error"
                )

            else:
                user["password"] = new_password
                flash("Password changed successfully.", "success")

        else:
            flash("Invalid account settings action.", "error")

        return redirect(url_for("account_settings"))

    return render_template(
        "account_settings.html",
        user=user
    )
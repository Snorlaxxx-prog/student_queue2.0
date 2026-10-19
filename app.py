from core import app

import routes.auth
import routes.student
import routes.cashier
import routes.admin
import routes.account


if __name__ == "__main__":
    app.run(debug=True)

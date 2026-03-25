# Original import
from flask import Flask, render_template, redirect, abort, request, url_for
from werkzeug.exceptions import HTTPException
from datetime import datetime

# Branch imports
import os
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import ForeignKey, func, or_
from sqlalchemy.orm import Mapped, mapped_column, relationship
from wtforms import Form, BooleanField, StringField, validators, PasswordField
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    logout_user,
    login_required,
    current_user,
)
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash

# Enables/disables debug messages in console and web server
enable_debug = True

# This variable is required to verify admin for password reset
global pass_reset
pass_reset = None

# Console output colour formating
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[36m"  # Not blue IK, but actual blue is hard to read and doesn't match Flask's blue
RESET = "\033[0m"  # Resets all formatting to default


# Gets the time
def time():
    time = datetime.now().strftime("%H:%M:%S")
    return time


# Key checker
while True:
    print(f"[{time()}]{GREEN}[INFO]{RESET}: Checking for key..")

    # WARNING: DO NOT USE THIS METHOD OF STORING KEYS IN PRODUCTION ENVIRONMENT
    if os.path.isfile(".env"):
        load_dotenv()
        print(f"[{time()}]{GREEN}[INFO]{RESET}: Key found!")
        break

    else:
        import secrets

        print(f"[{time()}]{RED}[ERROR]{RESET}: No key found. Generating new one? [y/N]")
        if input().lower() == "y":

            # CHANGE THIS METHOD OF STORING KEYS WHEN IN PRODUCTION
            with open(".env", "w") as f:
                f.write(f"login_key='{secrets.token_hex()}'")
            print(
                f"[{time()}]{GREEN}[INFO]{RESET}: New key generated, saved to '{BLUE}.env{RESET}'"
            )
            print(
                f"[{time()}]{RED}[WARN]{RESET}:{RED} If you are in a production environment, delete the '.env' and change the method of storing keys in code{RESET}"
            )

app = Flask(__name__)
# Database URI in "instance" folder
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///sites.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)


# Configure login
app.config["SECRET_KEY"] = os.getenv("login_key")
login_manager = LoginManager(app)
login_manager.login_view = "login"


# Forms
class LoginForm(Form):
    username = StringField("Username", [validators.DataRequired()])
    password = PasswordField("Password", [validators.DataRequired()])


# Database models
class Sites(db.Model):
    ID: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    owner: Mapped[int] = mapped_column(
        ForeignKey(
            "Accounts.ID",
        )
    )
    name: Mapped[str] = mapped_column(nullable=False)
    URL: Mapped[str] = mapped_column(primary_key=True, nullable=False)
    folder: Mapped[int] = mapped_column(ForeignKey("Folders.ID"), nullable=False)
    description: Mapped[str] = mapped_column(nullable=True)
    admin: Mapped[int] = mapped_column(default=False)
    logged_in: Mapped[int] = mapped_column(default=False)


class Folders(db.Model):
    ID: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    owner: Mapped[int] = mapped_column(ForeignKey("Accounts.ID"))
    name: Mapped[str] = mapped_column(nullable=False)
    URL: Mapped[str] = mapped_column(nullable=False)
    folder: Mapped[int] = mapped_column(nullable=False)
    admin: Mapped[int] = mapped_column(default=False)
    logged_in: Mapped[int] = mapped_column(default=False)


class Accounts(UserMixin, db.Model):
    ID: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(nullable=False, unique=True)
    password: Mapped[str] = mapped_column(nullable=False)
    admin: Mapped[int] = mapped_column(default=False)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def get_id(self):
        return str(self.ID)

    def is_admin(self):
        return bool(self.admin)

    # Is the account not terminated/banned
    @property
    def is_active(self):
        return True


with app.app_context():
    db.create_all()


# site settings
vars = {
    "site_title": "Portal",
    "anim_speed": "200ms",  # You must add unit (ms, s)'
    "slogan": "Generic slogan goes here",
    "greeting": "Sample text",
    "heading_brand": "Generic",  # This part of the heading would be highlighted
    "heading": "Portal",
    "contact_info": "Smth smth contact info | Copyright 2026 - Chris Fung",
}


# this is here cause I'm too lazy to make a dedicated home page so I just made the homepage a folder called 'home'
@app.route("/")
def root():
    return redirect("/1")


# Logout
@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("root"))


# Login manager
@login_manager.user_loader
def load_user(user_id):
    return Accounts.query.get(int(user_id))


# Login
@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm(request.form)
    if request.method == "POST" and form.validate():
        # Query database for usernames matching entered name
        account = (
            db.session.execute(
                db.select(Accounts).filter(
                    func.lower(Accounts.username) == form.username.data.lower()
                )
            )
            .scalars()
            .first()
        )
        # If the query returns nothing, account doesn't exist thus username is invalid
        if account == None:
            print(
                f"[{time()}]{YELLOW}[WARN]{RESET}: Login attempt failed; Username '{BLUE}{form.username.data}{RESET}' not found in database"
            )
            return render_template(
                "login.html",
                form=form,
                vars=vars,
                title="Login",
                Home=False,
                success=False,
                reason="Invalid username",
            )

        else:
            # Correct password
            if check_password_hash(account.password, str(form.password.data)):
                print(
                    f"[{time()}]{GREEN}[INFO]{RESET}: '{BLUE}{form.username.data}{RESET}' Logged in successfully"
                )
                login_user(account, remember=False)
                return redirect(url_for("root"))

            # Wrong password
            else:
                # This variable is for reseting admin password
                global pass_reset

                # If account is Admin
                if account.ID == 0:
                    if pass_reset == form.password.data:
                        print("resetinng")

                        pass_reset = None
                        print(
                            f"[{time()}]{YELLOW}[WARN]{RESET}: Please enter new Admin password"
                        )

                        account.password = generate_password_hash(
                            input(), method="pbkdf2:sha256"
                        )

                        db.session.commit()
                        print(
                            f"[{time()}]{YELLOW}[WARN]{RESET}: Admin password has been changed"
                        )

                    else:
                        import secrets

                        pass_reset = secrets.token_hex()
                        print(
                            f"[{time()}]{YELLOW}[WARN]{RESET}: Admin login attempt failed. To reset password, enter '{pass_reset}' into password field and check console"
                        )
                        return render_template(
                            "login.html",
                            form=form,
                            vars=vars,
                            title="Login",
                            Home=False,
                            success=False,
                            reason="Incorrect password",
                        )

                else:
                    print(
                        f"[{time()}]{GREEN}[INFO]{RESET}: '{BLUE}{account.username}{RESET}' Attempted login but entered invalid password"
                    )
                    return render_template(
                        "login.html",
                        form=form,
                        vars=vars,
                        title="Login",
                        Home=False,
                        success=False,
                        reason="Incorrect password",
                    )

    return render_template(
        "login.html", form=form, title="login", Home=False, vars=vars
    )


@app.route("/account")
def account():
    return render_template(
        "register.html",
        vars=vars,
        title="Accounts",
        Home=False,
    )


# Main site
@app.route("/<int:id>")
def directory(id):
    print("\n")
    # very basic anti-table dropping (Sanitize input)
    # for more info, refer to https://cdn.prod.website-files.com/681e366f54a6e3ce87159ca4/6877c77e021072217466290e_bobby-tables.png

    # converts '%' to ' '
    # this is cause URL links do not support spaces
    if current_user.is_anonymous:
        folders = list(
            db.session.execute(
                db.select(Folders).filter(
                    (Folders.folder == id)
                    & (Folders.logged_in == 0)
                    & (Folders.admin == 0)
                )
            ).scalars()
        )
        sites = list(
            db.session.execute(
                db.select(Sites).filter(
                    (Sites.folder == id) & (Sites.logged_in == 0) & (Sites.admin == 0)
                )
            ).scalars()
        )
    else:
        folders = list(
            db.session.execute(
                db.select(Folders).filter(
                    or_(
                        Folders.owner == current_user.ID,
                        Folders.owner.is_(None),
                        Folders.logged_in == 1,
                        Folders.admin == current_user.is_admin(),
                    )
                    & (Folders.folder == id)
                )
            ).scalars()
        )
        sites = list(
            db.session.execute(
                db.select(Sites).filter(
                    or_(
                        Sites.owner == current_user.ID,
                        Sites.owner.is_(None),
                        Sites.logged_in == 1,
                        Sites.admin == current_user.is_admin(),
                    )
                    & (Sites.folder == id)
                )
            ).scalars()
        )
    pre_folder = (
        db.session.execute(db.select(Folders.folder).filter(Folders.ID == id))
        .scalars()
        .first()
    )
    cur_folder = db.session.execute(
        db.select(Folders.name).filter(Folders.ID == id)
    ).first()

    if enable_debug == True:
        print(
            f'[{time()}]{YELLOW}[DEBUG]{RESET}: Found {BLUE}{len(folders)} folders{RESET} and {BLUE}{len(sites)} links{RESET} in requested folder "{BLUE}{id}{RESET}"'
        )  # debug

    # if var "back" is empty, return 404
    # "back" being empty means that the current folder has no upper directory meaning it's either un-accessible or doesn't exist
    if not pre_folder and id != 1:
        # the easter eggs are located here as to prevent them from conflicting with folders
        # a.k.a. it wont show the easter eggs if there is a folder with the same name
        if enable_debug == True:
            print(
                f"[{time()}]{RED}[ERROR]: Requested folder has no upper directory. Either invalid or inaccessible.{RESET}"
            )
            abort(404)
    if current_user.is_authenticated:
        # Access the username attribute of the current_user object
        username = current_user.username
    else:
        username = None
    # render(compile) the templates into one html file that the end user would see
    if id == 1:
        Home = True
    else:
        Home = False

    # Convert iterators to lists (this consumes them, but we need the data for the template)
    # Check if both lists are empty
    if not sites and not folders:
        empty = True
    else:
        empty = False

    return render_template(
        "directory.html",
        vars=vars,
        title=cur_folder,
        Home=Home,
        sites=sites,
        folders=folders,
        back=pre_folder,
        username=username,
        empty=empty,
    )


# stupid little route that forces error codes
# does nothing useful, can be removed
@app.route("/force-error/<int:code>")
def force_error(code):
    if enable_debug == True:
        print(
            f'[{time()}]{YELLOW}[DEBUG]{RESET}: Returning forced error code: "{BLUE}{code}{RESET}"'
        )  # This formats the error in a way that is more easily readable
    abort(code)


# this is the actuall error handler. The above one doesn't handle any actual errors
# returns the error code and infomation about error
@app.errorhandler(HTTPException)
def page_not_found(e):
    return render_template("error.html", vars=vars, error=e)


if __name__ == "__main__":
    # Enable/disable debug messages
    app.run(debug=enable_debug)

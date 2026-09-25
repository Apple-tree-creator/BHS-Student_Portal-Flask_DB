# Original import
import os
import secrets
import subprocess
import sys
from datetime import datetime

from dotenv import load_dotenv
from flask import (Flask, abort, redirect, render_template, request,
                   send_from_directory, url_for)
from flask_login import (LoginManager, UserMixin, current_user, login_required,
                         login_user, logout_user)
from flask_sqlalchemy import SQLAlchemy
# Branch imports
from flask_wtf import FlaskForm
from flask_wtf.csrf import CSRFError, CSRFProtect
from sqlalchemy import ForeignKey, func, or_
from sqlalchemy.orm import Mapped, mapped_column
from werkzeug.exceptions import HTTPException
from werkzeug.security import check_password_hash, generate_password_hash
from wtforms import BooleanField, PasswordField, StringField, validators

# Enables/disables debug messages in console and web server
ENABLE_DEBUG = True

# Temporary password used by the administrator reset flow.
PASS_RESET = None


# Console output colour formatting
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[36m"  # Not blue IK, but actual blue is hard to read and doesn't match Flask's blue
RESET = "\033[0m"  # Resets all formatting to default

def clear_console():
    if sys.platform == "win32":
        subprocess.run(["cmd", "/c", "cls"])  # cls is internal to cmd.exe
    else:
        subprocess.run(["clear"])

class Site:
    """Store site-wide configuration and provide time formatting utilities."""

    config = {
            "site_title": "BHS Student Portal",
            "anim_speed": "200ms",  # You must add unit (ms, s)'
            "slogan": "Te Kura O Waimairi-iri",
            "greeting": "Welcome",
            "heading_brand": "BHS",  # This part of the heading would be a different colour
            "heading": "Student Portal",
            "contact_info": "Smth smth contact info | Copyright 2026 - Chris Fung",
        }

    @staticmethod
    def time():
        """Return the current system time as HH:MM:SS."""
        current_time = datetime.now().strftime("%H:%M:%S")
        return current_time

    @classmethod
    def get_config(cls):
        """Return the site-wide configuration."""
        return cls.config


# Session cookie key checker (Note: Change the method of storing the key please)
while True:
    print(f"[{Site.time()}]{GREEN}[INFO]{RESET}: Checking for key..")

    # WARNING: DO NOT USE THIS METHOD OF STORING KEYS IN PRODUCTION ENVIRONMENT
    if os.path.isfile(".env"):
        load_dotenv()
        print(f"[{Site.time()}]{GREEN}[INFO]{RESET}: Key found!")
        break


    print(f"[{Site.time()}]{RED}[ERRR]{RESET}: No key found. Generating new one? [y/N]")
    if input().lower() == "y":

        # CHANGE THIS METHOD OF STORING KEYS WHEN IN PRODUCTION
        with open(".env", "w", encoding="utf-8") as f:
            f.write(f"login_key='{secrets.token_hex()}'")
        print(
            f"[{Site.time()}]{GREEN}[INFO]{RESET}: New key generated. Saved to '{BLUE}.env{RESET}'"
        )
        print(
            f"[{Site.time()}]{RED}[WARN]{RESET}:{RED} If you are in a production environment, delete the '.env' and change the method of storing keys in code{RESET}"
        )
        print('Press Enter to acknowledge')
        input()

app = Flask(__name__)
app.config["PASS_RESET"] = None
# Database URI in "instance" folder
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///sites.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)


# Configure login
app.config["SECRET_KEY"] = os.getenv("login_key")
login_manager = LoginManager(app)
login_manager.login_view = "login"
csrf = CSRFProtect(app)


# Forms
class LoginForm(FlaskForm):
    username = StringField("Username", [validators.DataRequired(), validators.length(min=3, max=24)])
    password = PasswordField("Password", [validators.DataRequired(), validators.length(min=8, max=32)])
    remember = BooleanField("Remember me", [])

class SignUp(FlaskForm):
    username = StringField('Username', [validators.DataRequired(), validators.Length(min=3, max=24)])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords do not match'),
        validators.length(min=8, max=32),
    ])
    confirm = PasswordField('Repeat Password', [validators.DataRequired(), validators.Length(min=8, max=32)])
    userIsAdmin = BooleanField('Admin')

class AccountsSettings(FlaskForm):
    username = StringField('Username', [validators.DataRequired(), validators.Length(min=3, max=24)])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords do not match'),
        validators.length(min=8, max=32),
    ])
    confirm = PasswordField('Repeat Password', [validators.DataRequired(), validators.Length(min=8, max=32)])

# Database models
class Groups(db.Model):
    ID: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(nullable=False)
    is_admin: Mapped[int] = mapped_column()
    can_edit: Mapped[int] = mapped_column()

class Folders(db.Model):
    ID: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    owner: Mapped[int] = mapped_column(ForeignKey("Accounts.ID"))
    name: Mapped[str] = mapped_column(nullable=False)
    URL: Mapped[str] = mapped_column(nullable=False)
    folder: Mapped[int] = mapped_column(nullable=False)
    admin: Mapped[int] = mapped_column(default=False)
    logged_in: Mapped[int] = mapped_column(default=False)
    private: Mapped[int] = mapped_column()
    group: Mapped[int] = mapped_column(ForeignKey("Groups.ID"))

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
    group: Mapped[int] = mapped_column(ForeignKey("Groups.ID"))


class Accounts(UserMixin, db.Model):
    ID: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(nullable=False, unique=True)
    password: Mapped[str] = mapped_column(nullable=False)
    group: Mapped[int] = mapped_column(ForeignKey("groups.ID"))
    
    def hash(self, password):
        return generate_password_hash(password)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def get_id(self):
        return str(self.ID)

# Tell crawlers not on this list to fuck off
@app.route('/robots.txt')
def robots():
    return send_from_directory(app.static_folder, 'robots.txt')

# Create the SQLAlchemy DB for this session
with app.app_context():
    db.create_all()

# redirects user to home folder when no url is entered
@app.route("/")
def root():
    return redirect("/1")

@app.errorhandler(CSRFError)
def handle_csrf_error(error):
    return render_template(
        "error.html",
        vars=Site.config,
        error=error,
        username=current_user.username if current_user.is_authenticated else None,
    ), 400

# Logout
@app.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    return redirect(url_for("root"))


# Login manager
@login_manager.user_loader
def load_user(user_id):
    return Accounts.query.get(int(user_id))

# @app.route("/manage-accounts")
# def manage():
#     title = 'Accounts'
#     if current_user.is_authenticated:
#         account_group = db.session.execute(db.select(Groups).filter(Groups.ID == current_user.group)).scalars().first()
#         # if admin
#         if account_group == 1:
#             pass
#         else:
#             pass
    
#         return render_template(
#             "manage-accounts.html",
#             vars=vars,
#             title=title,
#             username=current_user.username,
#             Home=False
#         )
#     else:
#         return (redirect('/login'))


# Login
@app.route("/login", methods=["GET", "POST"])
def login():
    title = 'Login'
    form = LoginForm(request.form)
    if current_user.is_authenticated:
        return redirect(url_for('root'))
    else:
        if request.method == "POST" and form.validate():
            # Query database for accounts that have entered username
            login_account = db.session.execute(db.select(Accounts).filter(func.lower(Accounts.username) == form.username.data.lower())).scalars().first()

            # If the query returns nothing, account doesn't exist thus the username is invalid
            if login_account is None:
                print(
                    f"[{Site.time()}]{YELLOW}[WARN]{RESET}: Login attempt failed; Username '{BLUE}{form.username.data}{RESET}' not found in database"
                )
                return render_template(
                    "login.html",
                    form=form,
                    vars=Site.config,
                    title=title,
                    Home=False,
                    success=False,
                    reason="Invalid username"
                )

            else:
                # Correct password
                if check_password_hash(login_account.password, str(form.password.data)):
                    print(f"[{Site.time()}]{GREEN}[INFO]{RESET}: '{BLUE}{form.username.data}{RESET}' Logged in successfully")
                    login_user(login_account, remember=form.remember.data)
                    return redirect(url_for("root"))

                # Wrong password
                else:
                    # This variable is to store the temporary admin password if they need to reset it
                    # Not the most secure way but it works
                    # If account is main Admin
                    if (login_account.ID == 1 and str(form.password.data) == "ResetAdmin") or str(form.password.data) == app.config["PASS_RESET"]:
                        # If the entered password matches the reset password
                        if app.config["PASS_RESET"] == form.password.data:

                            app.config["PASS_RESET"] = None
                            print(
                                f"[{Site.time()}]{YELLOW}[WARN]{RESET}: Please enter new Admin password"
                            )

                            login_account.password = generate_password_hash(
                                input(), method="pbkdf2:sha256"
                            )

                            db.session.commit()
                            clear_console()
                            print(
                                f"[{Site.time()}]{YELLOW}[WARN]{RESET}: Admin password has been changed"
                            )

                        # If not, create a new one and print it in console
                        else:

                            # Generate new temporary password for admin
                            app.config["PASS_RESET"] = secrets.token_hex(16)
                            print(
                                f"[{Site.time()}]{YELLOW}[WARN]{RESET}: To reset Admin password, enter '{app.config['PASS_RESET']}' into password field and check console"
                            )
                            return render_template(
                                "login.html",
                                form=form,
                                vars=Site.config,
                                title="Login",
                                Home=False,
                                success=False,
                                reason="Check server console",
                            )

                    # If account isn't the main Admin and password is wrong
                    else:
                        print(
                            f"[{Site.time()}]{GREEN}[INFO]{RESET}: '{BLUE}{login_account.username}{RESET}' Attempted login but entered invalid password"
                        )
                        return render_template(
                            "login.html",
                            form=form,
                            vars=Site.config,
                            title="Login",
                            Home=False,
                            success=False,
                            reason="Incorrect password",
                        )

        return render_template(
            "login.html", form=form, title="login", Home=False, vars=Site.config
        )

@app.route("/signup", methods=["GET", "POST"])
def signup():
    """Handle account signup requests and render the signup page."""
    form = SignUp(request.form)
    if current_user.is_authenticated:
        # Access the username attribute of the current_user object
        username = current_user.username
    else:
        username = None

    # If request includes forum response
    if request.method == "POST" and form.validate():
        # Query database for accounts that have entered username
        existing_account = (
            db.session.execute(
                db.select(Accounts).filter(
                    func.lower(Accounts.username) == form.username.data.lower() # type: ignore
                )
            )
            .scalars()
            .first()
        )
        # If the query returns nothing, account doesn't exist thus the username is invalid

        if existing_account is None:
            db.session.add(Accounts(username=str(form.username.data), password=Accounts.hash(str(form.password.data)), group=2))
            db.session.commit()
            print(
                f"[{Site.time()}]{GREEN}[INFO]{RESET}: New account created: '{BLUE}{form.username.data}{RESET}'"
            )
            return render_template(
                "signup.html",
                form=form,
                vars=Site.config,
                title="Sign Up",
                username=username,
                Home=False,
                success=True,
                reason="Account created successfully",
            )

        else:
            return render_template(
                "signup.html",
                form=form,
                vars=Site.config,
                title="Sign Up",
                username=username,
                Home=False,
                success=False,
                reason="User already exists",
            )

    else:
        return render_template(
                "signup.html", form=form, title="Sign Up", Home=False, vars=Site.config, username=username
            )

# Temp comment
@app.route("/account")
def account():
    """Render the account registration page."""
    return render_template(
        "register.html",
        vars=Site.config,
        title="Accounts",
        Home=False,
    )


# Main site
@app.route("/<int:id>")
def directory(id):
    """Display the contents of the requested directory."""
    print("\n")
    pre_folder = (
        db.session.execute(db.select(Folders.folder).filter(Folders.ID == id))
        .scalars()
        .first()
    )
    # Check if the current folder is in any existing folder
    # If the folder isn't in another folder, it most likely doesn't exist or is inaccessible
    if not pre_folder and id != 1:
        if ENABLE_DEBUG is True:
            print(
                f"[{Site.time()}]{RED}[ERRR]: Requested folder has no upper directory. Either invalid or inaccessible.{RESET}"
            )
            abort(404, "Folder doesn't exist.")
    cur_folder = db.session.execute(
        db.select(Folders.name, Folders.logged_in, Folders.admin, Folders.owner, Folders.private).filter(Folders.ID == id)
    ).first()

    # If the user isn't logged in, use a query that doesn't check the user's ID
    # and only search for folders that don't need login
    if current_user.is_anonymous:
        # cur_folder structure
        # Name=0, Login=1, Admin=2, Owner=3
        if (cur_folder[1] == 1) or (cur_folder[2] == 1) or (cur_folder[1] == 1):
            abort(403, "You don't have permission to view this folder")
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
        # Check if admin
        account_group = db.session.execute(db.select(Groups).filter(Groups.ID == current_user.group)).scalars().first()

        # cur_folder structure
        # Name=0, Login=1, Admin=2, Owner=3, Private=4
        # If not admin or is not owner and folder requires login or is not public
        if (account_group.is_admin is False and cur_folder[2] == 1) or (current_user.ID != cur_folder[3] and cur_folder[4]== 1):
            abort(403, "You do not have permission to access this folder.")

        folders = list(
            db.session.execute(
                db.select(Folders).filter(
                    or_(
                        Folders.owner == current_user.ID and Folders.private == 1,
                        Folders.owner.is_(None),
                        Folders.private == 0,
                        Folders.admin == account_group.is_admin,
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
                        Sites.admin == account_group.is_admin,
                    )
                    & (Sites.folder == id)
                )
            ).scalars()
        )
    if ENABLE_DEBUG:
        print(
            f'[{Site.time()}]{YELLOW}[DEBUG]{RESET}: Found {BLUE}{len(folders)} folders{RESET} and {BLUE}{len(sites)} links{RESET} in requested folder "{BLUE}{id}{RESET}"'
        )  # debug

    # Get the username of the current user
    if current_user.is_authenticated:
        # Access the username attribute of the current_user object
        username = current_user.username
        is_admin = account_group.is_admin
    else:
        is_admin = False
        username = None

    # Check if the current folder is the home folder
    home = id == 1

    # Checks if the current folder is empty
    if not sites and not folders:
        empty = True
    else:
        empty = False

    return render_template(
        "directory.html",
        vars=Site.config,
        title=cur_folder[0],  # Ignore this error, it works fine
        Home=home,
        sites=sites,
        folders=folders,
        back=pre_folder,
        username=username,
        empty=empty,
        admin=is_admin
    )


# Stupid little route that forces error codes
# Does nothing useful, can be removed
@app.route("/force-error/<int:code>")
def force_error(code):
    """Abort the request with the specified HTTP error code."""
    if ENABLE_DEBUG is True:
        print(
            f'[{Site.time()}]{YELLOW}[DEBUG]{RESET}: Returning forced error code: "{BLUE}{code}{RESET}"'
        )  # This formats the error in a way that is more easily readable
    abort(code)


# This is the actual error handler
# Returns the error code and information about error
@app.errorhandler(HTTPException)
def page_not_found(e):
    """Render an error page for HTTP exceptions."""
    # Get the username of the current user
    if current_user.is_authenticated:
        # Access the username attribute of the current_user object
        username = current_user.username
    else:
        username = None
    return render_template("error.html", vars=Site.config, error=e, username=username)


if __name__ == "__main__":
    # Enable/disable Flask's debug messages
    # app.run(host='10.42.0.1', port=5000)
    app.run(debug=ENABLE_DEBUG)

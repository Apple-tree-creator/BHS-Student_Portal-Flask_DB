from flask import Flask, render_template, redirect, abort
from werkzeug.exceptions import HTTPException
import sqlite3
from datetime import datetime

from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
# Configure your database URI
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sites.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

with app.app_context():
    db.reflect()

class Sites(db.Model):
    __table__ = db.metadata.tables['sites']

class Folders(db.Model):
    __table__ = db.metadata.tables['folders']


# Debug output colour formating
RED = '\033[31m'
GREEN = '\033[32m'
YELLOW = '\033[33m'
BLUE = '\033[34m'
RESET = '\033[0m' # Resets all formatting to default

# site settings
vars = {
       'site_title': "BHS Portal",
       'anim_speed': '200ms',  # You must add unit (ms, s)'
       'slogan': 'Te Kura o Waimairi-iri',
       'greeting': 'Kia ora',
       'heading_brand': 'BHS', # This part of the heading would be highlighted
       'heading': 'Student Portal',
       'contact_info': 'Site is not affiliated with Burnside High School | Copyright 2025 - Chris From 12DTP',
       }

# this is here cause I'm too lazy to make a dedicated home page so I just made the homepage a folder called 'home'
@app.route('/')
def root():
       return redirect('/home')

# this checks the database to see if the <string:name> (folder) exists and what links are in it.
@app.route('/<string:name>')
def directory(name):
      time = datetime.now().strftime("%H:%M:%S")
      print('\n')
      # very basic anti-table dropping (Sanitize input)
      # for more info, refer to https://cdn.prod.website-files.com/681e366f54a6e3ce87159ca4/6877c77e021072217466290e_bobby-tables.png
      if ';' in name or '"' in name or "'" in name:
            print(f'[{time}]{RED}[ERROR]: Dangerous characters found in request; cancelling request{RESET}')
            abort(403)

      # converts '%' to ' '
      # this is cause URL links do not support spaces
      name = name.replace('%20', ' ')

      # sets up database query by connecting to databse
      conn = sqlite3.connect('sites.db')
      cur = conn.cursor()

      # this gets all the sites in the current folder if there are any
      sites = list(db.session.execute(db.select(Sites.name, Sites.URL, Sites.description).filter(Sites.folder == name.title())))

      # this gets all the folders in the current folder if there are any
      folders = list(db.session.execute(db.select(Folders.name, Folders.URL, Folders.folder).filter(Folders.folder ==  name.title())))

      # checks for the folder/directory the current folder is in
      # e.g. 'Tools' folder is in the 'Home' folder so return 'Home'
      # this makes the 'back' button work
      back =  list(db.session.execute(db.select(Folders.folder).filter(Folders.name == name.title())))
      for back in back:
            back = back[0].replace(' ','%20' )

      print(f'[{time}]{YELLOW}[DEBUG]{RESET}: Found {BLUE}{len(folders)} folders{RESET} and {BLUE}{len(sites)} links{RESET} in requested folder "{BLUE}{name}{RESET}"') # debug

      # if var "back" is empty, return 404
      # "back" being empty means that the current folder has no upper directory meaning it's either un-accessible or doesn't exist
      if not back:
            # the easter eggs are located here as to prevent them from conflicting with folders
            # a.k.a. it wont show the easter eggs if there is a folder with the same name
            if name == 'dad':
                  print(f'[{time}]{YELLOW}[DEBUG]{RESET}: Easter egg triggered')
                  abort(410, description='')

            elif name == 'mom':
                  print(f'[{time}]{YELLOW}[DEBUG]{RESET}: Easter egg triggered')
                  abort(413, description='')

            elif name == 'sister' or name == 'brother':
                  print(f'[{time}]{YELLOW}[DEBUG]{RESET}: Easter egg triggered')
                  abort(451, description='')
            
            elif name == 'grandma' or name == 'grandpa':
                  print(f'[{time}]{YELLOW}[DEBUG]{RESET}: Easter egg triggered')
                  abort(424, description='')
                  
            else:
                  print(f'[{time}]{RED}[ERROR]: Requested folder has no upper directory. Either invalid or inaccessible.{RESET}')
                  abort(404)

      # closes connection to databse
      conn.close()

      # render(compile) the templates into one html file that the end user would see
      return render_template('directory.html', vars=vars, title=name, sites=sites, folders=folders, back=back)

# stupid little route that forces error codes
# does nothing useful, can be removed
@app.route('/force-error/<int:code>')
def force_error(code):
       time = datetime.now().strftime("%H:%M:%S")
       print(f'[{time}]{YELLOW}[DEBUG]{RESET}:{RED} Returning forced error code: "{BLUE}{code}{RESET}"') # This formats the error in a way that is more easily readable 
       abort(code)

# this is the actuall error handler. The above one does nothing
# returns the error code and infomation about error
@app.errorhandler(HTTPException)
def page_not_found(e):
      return render_template('error.html', vars=vars, error=e)

if __name__ == "__main__":
    app.run(debug=True)
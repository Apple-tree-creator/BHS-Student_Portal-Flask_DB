from flask import Flask, render_template, redirect, abort
from werkzeug.exceptions import HTTPException
import sqlite3

app = Flask(__name__)

# site settings
vars = {
       'site_title': "BHS Portal",
       'anim_speed': '200ms', # You must add unit'
       }

# this is here cause I'm too lazy to make a dedicated home page so I just made the homepage a folder called 'home'
@app.route('/')
def root():
       return redirect('/home')

# this checks the database to see if the <string:name> (folder) exists and what links are in it.
@app.route('/<string:name>')
def directory(name):
       # converts '%' to ' ' aswell as remove potentialy dangerous characters
       # this is cause URL links do not support spaces
       name = name.replace('%', ' ').replace('"', '').replace("'", '')

       # sets up database query by connecting to databse
       conn = sqlite3.connect('sites.db')
       cur = conn.cursor()

       # requests 'name' and 'URL' from the table 'sites' in database where 'folder' matches search
       # this checks if there are any links/sites in the current folder/directory
       cur.execute(f'SELECT name, URL FROM sites WHERE folder="{name}" COLLATE NOCASE ORDER BY name ASC;')
       print(name) # debug
       sites = cur.fetchall()
       print(sites) # debug

       # requests for 'name' and 'URL' of folders
       # this checks if there are any folders in the current folder/directory
       cur.execute(f'SELECT name, URL, folder, icon FROM folders WHERE folder="{name}" COLLATE NOCASE ORDER BY name ASC;')
       folders = cur.fetchall()
       print(folders) # debug

       # checks for the folder/directory the current folder is in
       # e.g. 'Tools' folder is in the 'Home' folder so return 'Home'
       # this makes the 'back' button work
       cur.execute(f'SELECT folder FROM folders WHERE name="{name}" COLLATE NOCASE ORDER BY name ASC;')
       back = cur.fetchall()
       for back in back:
             back = back[0].replace(' ','%' )

       # if var "back" is empty, return 404
       # "back" being empty means that the current folder has no upper directory meaning it's either un-accessible or doesn't exist
       if not back:
             abort(404)

       # closes connection to databse
       conn.close()

       # render(compile) the templates into one html file that the end user would see
       return render_template('directory.html', vars=vars, title=name, sites=sites, folders=folders, back=back)

# stupid little route that forces error codes
# does nothing useful, can be removed
@app.route('/force-error/<int:code>')
def force_error(code):
       abort(code)

# this is the actuall error handler. The above one does nothing
# returns the error code and infomation
@app.errorhandler(HTTPException)
def page_not_found(e):
      return render_template('error.html', vars=vars, error=e)

if __name__ == "__main__":
    app.run(debug=True)
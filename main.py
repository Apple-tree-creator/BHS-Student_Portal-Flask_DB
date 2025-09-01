from flask import Flask, render_template, redirect, abort
from werkzeug.exceptions import HTTPException
import sqlite3

app = Flask(__name__)

# site settings
vars = {
       'site_title': "BHS Portal",
       'anim_speed': '200ms', # You must add unit'
       }

# root route is estentially the same as the Directory route but the name is defined here
@app.route('/')
def root():
       return redirect('/home')

@app.route('/<string:name>')
def directory(name):
       # converts '%' to ' ' and capitalises first letter of each word
       # aswell as remove potentialy dangerous characters
       # this is cause URL links are not case sensitive and do not support spaces
       name = name.title().replace('%', ' ').replace('"', '').replace("'", '')

       # sets up database query by connecting to databse
       conn = sqlite3.connect('sites.db')
       cur = conn.cursor()

       # requests 'name' and 'URL' from the table 'sites' in database where 'folder' matches search
       cur.execute(f'SELECT name, URL FROM sites WHERE folder="{name}" ORDER BY name ASC;')
       print(name) # debug
       sites = cur.fetchall()
       print(sites) # debug

       # requests for 'name' and 'URL' of folders
       cur.execute(f'SELECT name, URL, folder, icon FROM folders WHERE folder="{name}" ORDER BY name ASC;')
       folders = cur.fetchall()
       print(folders) # debug

       cur.execute(f'SELECT folder FROM folders WHERE name="{name}";')
       back = cur.fetchall()
       for back in back:
             back = back[0].replace(' ','%' )

       # closes connection to databse
       conn.close()
       if not sites:
             abort(404)
       return render_template('directory.html', vars=vars, title=name, sites=sites, folders=folders, back=back)

@app.route('/force-error/<int:code>')
def force_error(code):
       abort(code)

@app.errorhandler(HTTPException)
def page_not_found(e):
      return render_template('error.html', vars=vars, error=e)

if __name__ == "__main__":
    app.run(debug=True)
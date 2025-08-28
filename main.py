from flask import Flask, render_template
import sqlite3

app = Flask(__name__)


vars = {
       'site_title': "BHS Portal",
       'anim_speed': '300ms', # You must add unit
       }

# basic route
@app.route('/')
def root():
       name='Home'
       # converts '%' to ' '
       name = name.replace('%', ' ')

       # sets up database query by connecting to databse
       conn = sqlite3.connect('sites.db')
       cur = conn.cursor()

       # requests 'name' and 'URL' from the table 'sites' in database where 'folder' matches search
       cur.execute(f'SELECT name, URL FROM sites WHERE is_folder=0 and folder="Home" ORDER BY name ASC;')
       sites = cur.fetchall()
       print(sites) # debug

       # requests for 'name' and 'URL' of folders
       cur.execute('SELECT name, URL FROM sites WHERE is_folder=1 and folder="Home" ORDER BY name ASC;')
       folders = cur.fetchall()
       print(folders) # debug

       # closes connection to databse
       conn.close()
       return render_template('directory.html', vars=vars, title=name, sites=sites, folders=folders)

@app.route('/<string:name>')
def directory(name):
       # converts '%' to ' '
       name = name.title().replace('%', ' ')

       # sets up database query by connecting to databse
       conn = sqlite3.connect('sites.db')
       cur = conn.cursor()

       # requests 'name' and 'URL' from the table 'sites' in database where 'folder' matches search
       cur.execute(f'SELECT name, URL FROM sites WHERE is_folder=0 and folder="{name}" ORDER BY name ASC;')
       print(name)
       sites = cur.fetchall()
       print(sites) # debug

       # requests for 'name' and 'URL' of folders
       cur.execute(f'SELECT name, URL FROM sites WHERE is_folder=1 and folder="{name}" ORDER BY name ASC;')
       folders = cur.fetchall()
       print(folders) # debug

       # closes connection to databse
       conn.close()
       return render_template('directory.html', vars=vars, title=name, sites=sites, folders=folders)


if __name__ == "__main__":
    app.run(debug=True)
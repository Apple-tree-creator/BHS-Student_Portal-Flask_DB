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
         conn = sqlite3.connect('sites.db')
         cur = conn.cursor()
         cur.execute('SELECT Name, URL FROM Pinned ORDER BY Name ASC;')

         sites = cur.fetchall()
         print(sites)
         conn.close()
         return render_template('directories/home.html', vars=vars, title='Home', sites=sites)

@app.route('/school-sites')
def sites():
         conn = sqlite3.connect('sites.db')
         cur = conn.cursor()
         cur.execute('SELECT Name, URL FROM School_sites ORDER BY Name ASC;')

         sites = cur.fetchall()
         print(sites)
         conn.close()
         return render_template('directories/school-sites.html', vars=vars, title='School Sites', sites=sites)

@app.route('/forums')
def forums():  
         conn = sqlite3.connect('sites.db')
         cur = conn.cursor()
         cur.execute('SELECT Name, URL FROM Forums ORDER BY Name ASC;')

         sites = cur.fetchall()
         print(sites)
         conn.close() 
         return render_template('directories/forums.html', vars=vars, title='Forums', sites=sites)

@app.route('/tools')
def tools(): 
         conn = sqlite3.connect('sites.db')
         cur = conn.cursor()
         cur.execute('SELECT Name, URL FROM Tools ORDER BY Name ASC;')

         sites = cur.fetchall()
         print(sites)
         conn.close()  
         return render_template('directories/tools.html', vars=vars, title='Tools', sites=sites)

if __name__ == "__main__":
    app.run(debug=True)
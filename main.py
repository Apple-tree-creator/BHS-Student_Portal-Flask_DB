from flask import Flask, render_template

app = Flask(__name__)


vars = {
       'site_title': "Untitled Site",
       'anim_speed': '300ms', # You must add unit
       }

# basic route
@app.route('/')
def root():
         title = 'Home'
         return render_template('home.html', vars=vars, title=title)

if __name__ == "__main__":
    app.run(debug=True)
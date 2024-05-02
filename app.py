from flask import Flask, render_template, jsonify
import os

app = Flask(__name__)

# Set the template folder path to the frontend directory
app.template_folder = os.path.abspath('frontend/pages')

@app.route('/')
def index():
    return render_template('index.html')  # Now Flask knows to look in the frontend/pages directory

if __name__ == '__main__':
    app.run(debug=True)

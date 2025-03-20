from flask import Flask, request, jsonify, render_template
from pymongo import MongoClient
import pdfplumber
app = Flask(__name__)

# Connect to MongoDB (local instance)
client = MongoClient('mongodb://localhost:27017/')
db = client.flask_db
todos = db.todos

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/todos', methods=['GET'])
def get_todos():
    items = list(todos.find({}, {'_id': False}))
    return jsonify(items)

@app.route('/todos', methods=['POST'])
def add_todo():
    todo = request.json
    todos.insert_one(todo)
    return jsonify({"status": "success"})

@app.route('/pdfextract/', methods=['POST'])
def pdfextract():
    if 'Files' not in request.files:
        return jsonify({"status": "error", "message": "No file uploaded"})

    file = request.files['Files']
    with pdfplumber.open(file.stream) as pdf:
        # Extract the text
        text = pdf.pages[3].extract_text()
        print(text)

        # Extract the data
        # print(pdf.pages,"====")
        # for pdf.pages
        tables = pdf.pages[8].extract_tables()
        for table in tables:
            print(table,"=============tables")

        # Extract the images
        images = pdf.pages[7].images
        # print(images,"=============images")
        for image in images:
            print(image["page_number"],"=====000")
            try:
                with open(f"image_{image['page_number']}.jpg", "wb") as f:
                    f.write(image["stream"].get_data())
            except Exception as e:
                print(f"{image['page_number']} image has error")
    return jsonify({"status": "success"})

if __name__ == '__main__':
    app.run(debug=True)

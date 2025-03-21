from flask import Flask, request, jsonify, render_template
from pymongo import MongoClient
# import pdfplumber
# import pymupdf4llm
# import pymupdf
import os
from utils.pdf_processing import pdf_to_images
from utils.text_extraction import extract_data_from_image
from utils.vector_storage import store_in_chromadb

app = Flask(__name__)
UPLOAD_FOLDER = "data"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

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

# @app.route('/pdfextract/', methods=['POST'])
# def pdfextract():
#     if 'Files' not in request.files:
#         return jsonify({"status": "error", "message": "No file uploaded"})

#     file = request.files['Files']
#     with pdfplumber.open(file.stream) as pdf:
#         # Extract the text
#         text = pdf.pages[35].extract_text()
#         print(text)

#         # Extract the data
#         # print(pdf.pages,"====")
#         # for pdf.pages
#         tables = pdf.pages[35].extract_tables()
#         print(tables ,"=====taBLE")

#         print(pdf.pages[35].extract_tables())
#         for table in tables:
#             print(table,"=============tables")

#         # Extract the images
#         images = pdf.pages[35].images
#         # print(images,"=============images")
#         for image in images:
#             print(image["page_number"],"=====000")
#             try:
#                 with open(f"image_{image['page_number']}.jpg", "wb") as f:
#                     f.write(image["stream"].get_data())
#             except Exception as e:
#                 print(f"{image['page_number']} image has error")
#     return jsonify({"status": "success"})

# @app.route('/pdfextractllm/', methods=['POST'])
# def pdfextractllm():
#     if 'Files' not in request.files:
#         return jsonify({"status": "error", "message": "No file uploaded"})
#     file = request.files['Files']
#     print(file)
#     try:
#         with pymupdf.open("/home/soham/Documents/YAAA/OverfittingExperts/backend/TIMPL-Annual-Report-2023-24.pdf") as doc:
#             # for page in doc: print("page %i" % page.number)
#             print(doc[8].find_tables())
#             tabs = doc[8].find_tables()
#             print(f"{len(tabs.tables)} found on {8}") # display number of found tables

#             if tabs.tables:  # at least one table found?
#                 print(tabs[0].extract())  # print content of first table
#         # pdf = pymupdf4llm.to_markdown("/home/soham/Documents/YAAA/OverfittingExperts/backend/TIMPL-Annual-Report-2023-24.pdf")
#         # print(pdf)
#         return jsonify({"status": "succes"})
#     except Exception as e:
#         return jsonify({"status": "error", "message": str(e)})


from transformers import T5Tokenizer, T5ForConditionalGeneration
import torch
from huggingface_hub import login

# Define the upload folder
UPLOAD_FOLDER = "uploads"
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


# Log in using the token (ONLY for private models)
access_token = "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"
login(token=access_token)

# Load the model from Hugging Face
# Load model directly
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

tokenizer = AutoTokenizer.from_pretrained("SOham01/results")
model = AutoModelForSeq2SeqLM.from_pretrained("SOham01/results")

# Set model to evaluation mode
model.eval()

# Function to generate predictions using the fine-tuned model
def generate_prediction(text):
    # Tokenize the input text
    inputs = tokenizer(f"summarize: {text}", return_tensors="pt", max_length=512, truncation=True)
    
    # Generate output
    with torch.no_grad():
        outputs = model.generate(**inputs)
    
    # Decode the output
    prediction = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return prediction


# API endpoint to upload and process PDF
@app.route("/upload/", methods=["POST"])
def upload_pdf():
    print(request.files)
    if "Files" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    try:
        file = request.files["Files"]
        file_path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(file_path)
        print(file_path)

        # Convert PDF to images
        image_paths = pdf_to_images(file_path)

        extracted_text = []
        for i, img_path in enumerate(image_paths):
            try:
                # Extract text from the image
                text = extract_data_from_image(img_path)
                extracted_text.append(text)

                # Store the extracted text in ChromaDB
                try:
                    store_in_chromadb(text, f"{file.filename}_page_{i}")
                except Exception as e:
                    print(f"Error storing in ChromaDB: {str(e)}")

                # Generate predictions using the fine-tuned model
                prediction = generate_prediction(text)
                extracted_text.append(f"Prediction for page {i}: {prediction}")

            except Exception as e:
                print(f"Error extracting text from page {i}: {str(e)}")
                extracted_text.append(f"Error extracting text from page {i}")

        if not extracted_text:
            return jsonify({"error": "Failed to extract any text"}), 500

        # Join all extracted text and predictions into a single string
        result_text = "\n\n\n".join(extracted_text).replace("Ġ", "")

        return jsonify({"message": "Extraction and prediction successful", "data": result_text})

    except Exception as e:
        return jsonify({"error": f"Extraction failed: {str(e)}"}), 500

# Run the Flask app
if __name__ == "__main__":
    app.run(debug=True)
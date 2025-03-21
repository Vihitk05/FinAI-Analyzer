from flask import Flask, request, jsonify, render_template
from pymongo import MongoClient
import os
from utils.pdf_processing import pdf_to_images
from utils.text_extraction import extract_data_from_image
from utils.vector_storage import store_in_chromadb
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch
from huggingface_hub import login

# Initialize Flask app
app = Flask(__name__)

# Define upload folder
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Connect to MongoDB (local instance)
client = MongoClient('mongodb://localhost:27017/')
db = client.flask_db
todos = db.todos

# Hugging Face Hub login (if using a private model)
access_token = "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"  # Replace with your actual token
login(token=access_token)

# Load the tokenizer and model
try:
    print("Loading tokenizer and model...")
    tokenizer = AutoTokenizer.from_pretrained("SOham01/results")
    model = AutoModelForSeq2SeqLM.from_pretrained("SOham01/results")
    model.eval()  # Set model to evaluation mode
    print("Tokenizer and model loaded successfully!")
except Exception as e:
    print(f"Error loading tokenizer or model: {e}")
    raise e  # Stop execution if model/tokenizer fails to load

# Function to generate predictions using the fine-tuned model
def generate_prediction(text):
    try:
        # Tokenize the input text
        inputs = tokenizer(f"Act as a financial expert. This is the financial statement report data extracted from a pdf. I want you understand this text data and give me the below points: 1. BUSINESS OVERVIEW 2. KEY FINDINGS, FINANCIAL DUE DILIGENCE 3. INCOME STATEMENT OVERVIEW 4. BALANCE SHEET OVERVIEW 5. ADJ EBITDA (IF DETAILED INFORMATION IS PROVIDED IN THE INPUT DOCUMENT ABOUT THIS THEN ANALYSE IT) 6. ADJ WORKING CAPITAL (IF DETAILED INFORMATION IS PROVIDED IN THE INPUT DOCUMENT ABOUT THIS THEN ANALYSE IT) I want the result in json format. : {text}", return_tensors="pt")

        # Generate output
        with torch.no_grad():
            outputs = model.generate(**inputs)

        # Decode the output
        prediction = tokenizer.decode(outputs[0], skip_special_tokens=True)
        return prediction
    except Exception as e:
        print(f"Error generating prediction: {e}")
        return f"Prediction error: {e}"

# Flask routes
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

@app.route("/upload/", methods=["POST"])
def upload_pdf():
    if "Files" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    try:
        file = request.files["Files"]
        file_path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(file_path)
        print(f"File saved at: {file_path}")

        # Convert PDF to images
        image_paths = pdf_to_images(file_path)
        if not image_paths:
            return jsonify({"error": "Failed to convert PDF to images"}), 500

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


            except Exception as e:
                print(f"Error extracting text from page {i}: {str(e)}")
                extracted_text.append(f"Error extracting text from page {i}")

        if not extracted_text:
            return jsonify({"error": "Failed to extract any text"}), 500

        # Join all extracted text and predictions into a single string
        result_text = "\n\n\n".join(extracted_text).replace("Ġ", "")
        prediction = generate_prediction(result_text)
        # extracted_text.append(f"Prediction for page {i}: {prediction}")

        return jsonify({"message": "Extraction and prediction successful", "data": prediction})

    except Exception as e:
        return jsonify({"error": f"Extraction failed: {str(e)}"}), 500

# Run the Flask app
if __name__ == "__main__":
    app.run(debug=True)

from flask import Flask, request, jsonify, render_template
from pymongo import MongoClient
import os
import requests
from utils.pdf_processing import pdf_to_images
from utils.text_extraction import extract_data_from_image
from utils.vector_storage import store_in_chromadb, retrieve_from_chromadb
from google.generativeai import GenerativeModel, configure
from langchain.vectorstores import Chroma
from langchain.embeddings import HuggingFaceEmbeddings

# Initialize Flask app
app = Flask(__name__)

# Define upload folder
UPLOAD_FOLDER = "data"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Connect to MongoDB (local instance)
client = MongoClient('mongodb://localhost:27017/')
db = client.flask_db
todos = db.todos

# Configure Google Gemini API
GOOGLE_API_KEY = "AIzaSyAyiv0POSr2A-SzWEwPDMuRZhUzxZ70hm8"  # Replace with your actual Google API key
import google.generativeai as genai

# Initialize Hugging Face Embeddings (for ChromaDB)
embeddings = HuggingFaceEmbeddings()
genai.configure(api_key="AIzaSyAyiv0POSr2A-SzWEwPDMuRZhUzxZ70hm8")

# Initialize ChromaDB
chroma_client = Chroma(persist_directory="chroma_db", embedding_function=embeddings)

def generate_prediction(text):
    try:
        # Define the prompt for Gemini
        prompt = f"""Below is an instruction that describes a task, paired with an input that provides further context. Write a response that appropriately completes the request.

### Instruction:
I will provide financial statement report data extracted from a PDF. Analyze this data in detail and provide a structured response covering the following key areas:

1. BUSINESS OVERVIEW – Summarize the nature of the business, industry, key operations, and market positioning based on the data.
2. KEY FINDINGS & FINANCIAL DUE DILIGENCE – Identify major financial insights, risks, inconsistencies, and any red flags from the analysis.
3. INCOME STATEMENT OVERVIEW – Break down revenues, expenses, profitability, and trends over the reporting periods.
4. BALANCE SHEET OVERVIEW – Summarize assets, liabilities, and equity positions, highlighting financial health indicators.
5. ADJ EBITDA – If details on Adjusted EBITDA are available, analyze the adjustments made and their impact on profitability.
6. ADJ WORKING CAPITAL – If provided, examine the adjustments to working capital and their implications on liquidity and operational efficiency.

Format the response in JSON format with clear keys for each section. Ensure the analysis is detailed, data-driven, and actionable.

### Input:
{text}"""

        # Generate the prediction using Gemini
        response = genai.GenerativeModel('gemini-1.5-pro').generate_content(prompt)

        # Parse the response to extract recommendations
        response_text = response.text
        return response_text

    except Exception as e:
        print(f"Error generating prediction: {e}")
        return f"Prediction error: {e}"

def process_large_text(text):
    """Process large text by splitting it into chunks and generating predictions."""
    # Clean the text
    text = clean_text(text)

    # Split the text into chunks
    chunks = split_text(text)

    # Process each chunk
    results = []
    for chunk in chunks:
        prediction = generate_prediction(chunk)
        results.append(prediction)

    # Combine results
    return " ".join(results)


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

            except Exception as e:
                print(f"Error extracting text from page {i}: {str(e)}")
                extracted_text.append(f"Error extracting text from page {i}")

        if not extracted_text:
            return jsonify({"error": "Failed to extract any text"}), 500

        # Join all extracted text into a single string
        result_text = "\n\n\n".join(extracted_text).replace("Ġ", "")

        # Retrieve relevant data from ChromaDB
        retrieved_data = retrieve_from_chromadb(result_text)
        if retrieved_data:
            result_text += "\n\nRetrieved Data:\n" + retrieved_data

        # Generate prediction using Gemini
        prediction = generate_prediction(result_text)

        return jsonify({"message": "Extraction and prediction successful", "data": prediction})

    except Exception as e:
        return jsonify({"error": f"Extraction failed: {str(e)}"}), 500

# Run the Flask app
if __name__ == "__main__":
    app.run(debug=True)
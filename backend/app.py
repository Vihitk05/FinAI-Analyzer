from flask import Flask, request, jsonify, render_template
from pymongo import MongoClient
import os
from utils.pdf_processing import pdf_to_images
from utils.text_extraction import extract_data_from_image
from utils.vector_storage import store_in_chromadb
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch
import re
from huggingface_hub import login
from concurrent.futures import ThreadPoolExecutor, as_completed
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
    model = AutoModelForSeq2SeqLM.from_pretrained("SOham01/results",
                                                 device_map="auto",
                                                 max_memory={"cpu": "4GB"})
    model.eval()  # Set model to evaluation mode
    print("Tokenizer and model loaded successfully!")
except Exception as e:
    print(f"Error loading tokenizer or model: {e}")
    raise e  # Stop execution if model/tokenizer fails to load

if torch.cuda.is_available():
    model.half().to("cuda")

def clean_text(text):
    """Clean extracted text by removing extra spaces and line breaks."""
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def split_text(text, chunk_size=10000):
    """Split text into smaller chunks."""
    return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]

def generate_prediction(chunk):
    """Generate predictions for a text chunk using the fine-tuned model."""
    try:
        prompt = (
            "Act as a financial expert. This is the financial statement report data extracted from a pdf. "
            "I want you to understand this text data and provide the following points in JSON format. "
            "For each point, provide at least 1000 characters of detailed analysis:\n"
            "1. BUSINESS OVERVIEW - Provide extensive details about the company's operations, market position, key products/services, competitive advantages, and business model\n"
            "2. KEY FINDINGS, FINANCIAL DUE DILIGENCE - In-depth analysis of major financial findings, risks, opportunities, and recommendations\n"
            "3. INCOME STATEMENT OVERVIEW - Detailed analysis of revenue streams, cost structures, profitability trends, and key performance indicators\n"
            "4. BALANCE SHEET OVERVIEW - Comprehensive review of assets, liabilities, equity positions, and financial health metrics\n"
            "5. ADJ EBITDA - Full analysis of EBITDA adjustments, normalization entries, and impact on valuation\n"
            "6. ADJ WORKING CAPITAL - Complete examination of working capital components, adjustments, and operational implications\n"
            f"Text: {chunk}"
        )

        # Tokenize and generate predictions
        inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=4096)
        if torch.cuda.is_available():
            inputs = {k: v.to("cuda") for k, v in inputs.items()}

        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                num_beams=4,
                no_repeat_ngram_size=3,
                early_stopping=True,
                do_sample=True,
                top_k=50,
                top_p=0.95,
                temperature=0.7,
                max_length=4096,
                min_length=1000
            )

        return tokenizer.decode(outputs[0], skip_special_tokens=True)

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
                # try:
                #     store_in_chromadb(text, f"{file.filename}_page_{i}")
                # except Exception as e:
                #     print(f"Error storing in ChromaDB: {str(e)}")

                # Generate predictions using the fine-tuned model


            except Exception as e:
                print(f"Error extracting text from page {i}: {str(e)}")
                extracted_text.append(f"Error extracting text from page {i}")

        if not extracted_text:
            return jsonify({"error": "Failed to extract any text"}), 500

        # Join all extracted text and predictions into a single string
        extracted_text = "\n\n\n".join(extracted_text).replace("Ġ", "")
        prediction = process_large_text(extracted_text)
        # extracted_text.append(f"Prediction for page {i}: {prediction}")

        return jsonify({"message": "Extraction and prediction successful", "data": prediction})

    except Exception as e:
        return jsonify({"error": f"Extraction failed: {str(e)}"}), 500

# Run the Flask app
if __name__ == "__main__":
    app.run(debug=True)

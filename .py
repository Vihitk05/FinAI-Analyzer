from flask import Flask, request, jsonify, render_template
from pymongo import MongoClient
import os
from utils.pdf_processing import pdf_to_images
from utils.text_extraction import extract_data_from_image
from utils.vector_storage import store_in_chromadb
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch
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

def process_chunk(chunk):
    """Process a single chunk of text."""
    inputs = tokenizer(chunk, return_tensors="pt", truncation=True, max_length=1024)
    if torch.cuda.is_available():
        inputs = {k: v.to("cuda") for k, v in inputs.items()}

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_length=512,
            num_beams=2,
            no_repeat_ngram_size=2,
            early_stopping=True
        )

    return tokenizer.decode(outputs[0], skip_special_tokens=True)

def generate_prediction(text):
    try:
        # Define the prompt
        prompt = (
            "Act as a financial expert. This is the financial statement report data extracted from a pdf. "
            "I want you to understand this text data and provide the following points in JSON format:\n"
            "1. BUSINESS OVERVIEW\n"
            "2. KEY FINDINGS, FINANCIAL DUE DILIGENCE\n"
            "3. INCOME STATEMENT OVERVIEW\n"
            "4. BALANCE SHEET OVERVIEW\n"
            "5. ADJ EBITDA (if detailed information is provided in the input document, analyze it)\n"
            "6. ADJ WORKING CAPITAL (if detailed information is provided in the input document, analyze it)\n"
            f"Text: {text}"
        )

        # Split the prompt and text into smaller chunks
        max_chunk_length = 2048  # Increase chunk size to reduce the number of chunks
        text_chunks = [prompt[i:i + max_chunk_length] for i in range(0, len(prompt), max_chunk_length)]

        # Process chunks in parallel using ThreadPoolExecutor
        predictions = []
        with ThreadPoolExecutor(max_workers=4) as executor:  # Adjust max_workers based on your CPU/GPU
            futures = [executor.submit(process_chunk, chunk) for chunk in text_chunks]
            for future in as_completed(futures):
                predictions.append(future.result())

        # Combine all predictions into a single JSON response
        combined_prediction = " ".join(predictions)
        return combined_prediction

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

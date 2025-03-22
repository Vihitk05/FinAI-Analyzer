from flask import Flask, request, jsonify, render_template
from pymongo import MongoClient
import google.generativeai as genai
import os
from mistralai import Mistral
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
DEEPSEEK_API = "sk-de18dd8c9d764a5e952e5c83c322e06a"
# Initialize Flask app
app = Flask(__name__)

# Define upload folder
UPLOAD_FOLDER = "data"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Connect to MongoDB (local instance)
client = MongoClient('mongodb://localhost:27017/')
db = client.flask_db
todos = db.todos

# Configure Mistral API
MISTRAL_API_KEY = os.environ.get("MISTRAL_API_KEY")  # Ensure this is set in your environment
mistral_client = Mistral(api_key=MISTRAL_API_KEY)

# Configure Google Gemini API
GOOGLE_API_KEY = "AIzaSyDoxe2AMW_8R01w5SCXLwJHX3uSOq_pInY"  # Replace with your actual Google API key
genai.configure(api_key=GOOGLE_API_KEY)

def generate_prediction(text, retries=3, delay=5):
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
        for attempt in range(retries):
            try:
                # response = genai.GenerativeModel('gemini-1.5-pro').generate_content(prompt)
                # response_text = response.text
                # from openai import OpenAI

                # client = OpenAI(api_key=DEEPSEEK_API, base_url="https://api.deepseek.com")

                # response = client.chat.completions.create(
                #     model="deepseek-chat",
                #     messages=[
                #         {"role": "system", "content": prompt}
                #     ],
                #     stream=False
                # )
                # response_text = response.choices[0].message.content
                # print(response.choices[0].message.content)
                
                from together import Together

                client = Together(api_key="tgp_v1_Cx5xaxjnWs7-w6zwbso6s2AQKW09lX9DNAR7LE5NQVw") # pass in API key to api_key or set a env variable

                stream = client.chat.completions.create(
                    model="deepseek-ai/DeepSeek-R1",
                    messages=[
                        {
                            "role": "user",
                            "content": prompt,
                        }
                    ],
                    stream=True,
                )
                response_text = ""
                for chunk in stream:
                    response_text+=chunk.choices[0].delta.content
                    print(chunk.choices[0].delta.content or "", end="", flush=True)
                return response_text
            except Exception as e:
                if "429" in str(e) and attempt < retries - 1:
                    print(f"Rate limit exceeded. Retrying in {delay} seconds... (Attempt {attempt + 1}/{retries})")
                    time.sleep(delay)
                else:
                    raise e

    except Exception as e:
        print(f"Error generating prediction: {e}")
        return f"Prediction error: {e}"

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

        # Step 1: Upload the PDF to Mistral
        with open(file_path, "rb") as pdf_file:
            uploaded_pdf = mistral_client.files.upload(
                file={
                    "file_name": file.filename,
                    "content": pdf_file.read(),
                },
                purpose="ocr"
            )
        print(f"Uploaded file ID: {uploaded_pdf.id}")

        # Step 2: Get a signed URL for the uploaded file
        signed_url = mistral_client.files.get_signed_url(file_id=uploaded_pdf.id)
        print(f"Signed URL: {signed_url.url}")

        # Step 3: Use the signed URL for OCR processing
        ocr_response = mistral_client.ocr.process(
            model="mistral-ocr-latest",
            document={
                "type": "document_url",
                "document_url": signed_url.url,
            }
        )

        # Step 4: Extract text from OCR response using multithreading
        # extracted_text = ""
        # with ThreadPoolExecutor(max_workers=50) as executor:  # Adjust max_workers as needed
        #     futures = [
        #         executor.submit(generate_prediction, page.markdown)
        #         for page in ocr_response.pages
        #     ]

        #     for future in as_completed(futures):
        #         try:
        #             page_prediction = future.result()
        #             extracted_text += page_prediction + "\n\n"
        #         except Exception as e:
        #             print(f"Error processing page: {e}")
        extracted_text = ""
        for page in ocr_response.pages:
            extracted_text+=page.markdown
        
        
        if not extracted_text:
            return jsonify({"error": "Failed to extract text from PDF"}), 500

        # Step 5: Generate final prediction using Gemini
        prediction = generate_prediction(extracted_text)

        return jsonify({"message": "Extraction and prediction successful", "data": prediction})

    except Exception as e:
        return jsonify({"error": f"Extraction failed: {str(e)}"}), 500

# Run the Flask app
if __name__ == "__main__":
    app.run(debug=True)
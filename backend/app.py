import datetime
from flask import Flask, request, jsonify, render_template
from pymongo import MongoClient
import google.generativeai as genai
import os
from mistralai import Mistral
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from flask_cors import CORS, cross_origin
import json  # For parsing JSON strings
import re  # For extracting JSON from text

# Initialize Flask app
app = Flask(__name__)
CORS(app,origins="*")

# Define upload folder
UPLOAD_FOLDER = "data"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Connect to MongoDB (local instance)
client = MongoClient('mongodb://localhost:27017/')
db = client.flask_db
financial_data = db.financial_data  # Collection for storing financial data

# Configure Mistral API
MISTRAL_API_KEY = os.environ.get("MISTRAL_API_KEY")  # Ensure this is set in your environment
mistral_client = Mistral(api_key=MISTRAL_API_KEY)

# Configure Google Gemini API
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY") # Replace with your actual Google API key
genai.configure(api_key=GOOGLE_API_KEY)

def generate_prediction(text, retries=3, delay=60):
    for attempt in range(retries):
        try:
            # Define the prompt for Gemini
            prompt = f"""
Instruction:
I will provide financial statement report data extracted from a PDF. Analyze this data in detail and provide a structured response in the following JSON format:
{{
  "companyName": ["string", "Name of the company"],
  "revenue": ["number", "Total revenue in dollars"],
  "revenueGrowth": ["number", "Year-over-year revenue growth percentage"],
  "ebitda": ["number", "EBITDA in dollars"],
  "ebitdaGrowth": ["number", "Year-over-year EBITDA growth percentage"],
  "netIncome": ["number", "Net income in dollars"],
  "netIncomeGrowth": ["number", "Year-over-year net income growth percentage"],
  "freeCashFlow": ["number", "Free cash flow in dollars"],
  "freeCashFlowGrowth": ["number", "Year-over-year free cash flow growth percentage"],
  "overallFinancialHealth": ["string", "Overall financial health rating (e.g., Strong, Good)"],
  "liquidity": ["string", "Liquidity rating (e.g., Excellent, Good)"],
  "solvency": ["string", "Solvency rating (e.g., Good, Fair)"],
  "profitability": ["string", "Profitability rating (e.g., Good, Fair)"],
  "companyProfile": ["string", "Description of the company profile"],
  "keyFindings": ["array", "List of key findings (e.g., Strong Revenue Growth, Improving Operating Margins)"],
  "strengths": ["array", "List of company strengths"],
  "areasOfConcern": ["array", "List of areas of concern"],
  "financialMetricsChartData": ["array", "Data for financial metrics chart (e.g., revenue, ebitda, net income over time)"],
  "financialRatios": ["array", "List of key financial ratios (e.g., profitability, liquidity, solvency ratios)"],
  "keyObservations": ["array", "List of key observations"],
  "recommendations": ["array", "List of recommendations"],
  "executiveSummary": ["string", "Comprehensive analysis and key takeaways"],
  "incomeStatementRevenueBreakdown": ["array", "Revenue breakdown (e.g., Product Sales, Services)"],
  "incomeStatementExpenseAllocation": ["array", "Expense allocation (e.g., COGS, Operating Expenses, Other)"],
  "balanceSheetAssetsComposition": ["array", "Assets composition (e.g., Current Assets, Fixed Assets, Other Assets)"],
  "balanceSheetLiabilitiesEquity": ["array", "Liabilities and equity breakdown (e.g., Current Liabilities, Long-term Liabilities, Equity)"],
  "cashFlowOperations": ["number", "Cash flow from operations"],
  "cashFlowInvesting": ["number", "Cash flow from investing"],
  "cashFlowFinancing": ["number", "Cash flow from financing"],
  "businessOverviewSummary": ["string", "AI-generated summary of business performance"],
  "businessOverviewStrengths": ["array", "List of business strengths"],
  "riskAssessment": ["string", "Risk assessment rating (e.g., Low-Medium, High)"],
  "dueDiligenceRecommendations": ["array", "List of financial due diligence recommendations"]
}}

If any data is not available in the provided financial statement, use the following default values:
{{
  "companyName": "",
  "revenue": 0,
  "revenueGrowth": 0,
  "ebitda": 0,
  "ebitdaGrowth": 0,
  "netIncome": 0,
  "netIncomeGrowth": 0,
  "freeCashFlow": 0,
  "freeCashFlowGrowth": 0,
  "overallFinancialHealth": "",
  "liquidity": "",
  "solvency": "",
  "profitability": "",
  "companyProfile": "",
  "keyFindings": [],
  "strengths": [],
  "areasOfConcern": [],
  "financialMetricsChartData": [],
  "financialRatios": [],
  "keyObservations": [],
  "recommendations": [],
  "executiveSummary": "",
  "incomeStatementRevenueBreakdown": [],
  "incomeStatementExpenseAllocation": [],
  "balanceSheetAssetsComposition": [],
  "balanceSheetLiabilitiesEquity": [],
  "cashFlowOperations": 0,
  "cashFlowInvesting": 0,
  "cashFlowFinancing": 0,
  "businessOverviewSummary": "",
  "businessOverviewStrengths": [],
  "riskAssessment": "",
  "dueDiligenceRecommendations": []
}}

Input:
{text}
"""
            # Generate the prediction using DeepSeek API
            from together import Together

            client = Together(api_key=os.environ.get("TOGETHER_API_KEY"))

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
                response_text += chunk.choices[0].delta.content
                print(chunk.choices[0].delta.content or "", end="", flush=True)
            
            return response_text.split("</think>")[-1] if "</think>" in response_text else response_text
            
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {str(e)}")
            if "rate limit" in str(e).lower() and attempt < retries - 1:
                print(f"Rate limit hit. Waiting {delay} seconds before retry...")
                time.sleep(delay)
                continue
            return f"Prediction error after {attempt + 1} attempts: {str(e)}"
    
    return "Max retries reached without successful prediction"



def extract_json_from_text(text):
    """Extract JSON data from the response text using regex."""
    # Use regex to find the JSON block
    json_match = re.search(r'\{.*\}', text, re.DOTALL)
    if json_match:
        return json_match.group(0)
    return None


from bson import json_util
from bson.objectid import ObjectId
import json

@app.route("/upload/", methods=["POST"])
# @cross_origin()
def upload_pdf():
    # print(request.files)
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    try:
        file = request.files["file"]
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

        # Step 4: Extract text from OCR response
        extracted_text = ""
        for page in ocr_response.pages:
            extracted_text += page.markdown

        if not extracted_text:
            return jsonify({"error": "Failed to extract text from PDF"}), 500

        # Step 5: Generate final prediction using DeepSeek
        prediction = generate_prediction(extracted_text)

        # Step 6: Extract JSON data from the prediction text
        json_data = extract_json_from_text(prediction)
        if not json_data:
            return jsonify({"error": "Failed to extract JSON data from prediction"}), 500

        # Step 7: Parse the JSON string into a Python dictionary
        try:
            prediction_data = json.loads(json_data)
        except json.JSONDecodeError as e:
            print(f"Malformed JSON: {json_data}")  # Log the malformed JSON for debugging
            return jsonify({"error": f"Failed to parse prediction JSON: {str(e)}"}), 500

        # Step 8: Add the raw prediction text to the data for debugging
        prediction_data["all_data"] = prediction

        # Step 9: Generate a custom ID starting from 1
        last_document = financial_data.find_one(sort=[("custom_id", -1)])
        custom_id = 1 if last_document is None else last_document["custom_id"] + 1

        # Step 10: Add the custom ID to the prediction data
        prediction_data["custom_id"] = custom_id
        prediction_data["analysis_date"] = datetime.datetime.now()
        current_date = datetime.today().strftime("%B %d, %Y")
        prediction_data["analysis_date"] = str(current_date)
        # Step 11: Store the prediction data in MongoDB
        result = financial_data.insert_one(prediction_data)

        # Step 12: Convert ObjectId to string for JSON serialization
        prediction_data["_id"] = str(result.inserted_id)

        # Step 13: Return the response with the custom ID
        return jsonify({
            "message": "Extraction and prediction successful",
            "data": prediction_data,
            "custom_id": custom_id  # Return the custom ID
        })

    except Exception as e:
        print(f"Extraction failed: {str(e)}")
        return jsonify({"error": f"Extraction failed: {str(e)}"}), 500
        

@app.route("/fetch_data/", methods=["POST"])
# @cross_origin()
def fetch_data():
    try:
        # Step 1: Get the custom_id from the request JSON payload
        request_data = request.json
        custom_id = int(request_data.get("custom_id"))

        if not custom_id:
            return jsonify({"error": "custom_id is required"}), 400

        # Step 2: Query the database for the document with the specified custom_id
        document = financial_data.find_one({"custom_id": custom_id}, {"_id": False})  # Exclude MongoDB's _id field

        if not document:
            return jsonify({"error": f"No document found with custom_id: {custom_id}"}), 404

        # Step 3: Return the document as a JSON response
        return jsonify({
            "message": "Data fetched successfully",
            "data": document
        })

    except Exception as e:
        print(str(e))
        return jsonify({"error": f"Failed to fetch data: {str(e)}"}), 500    

@app.route("/fetch_all_data/", methods=["GET"])
@cross_origin()
def fetch_all_data():
    try:
        # Step 1: Query the database for all documents
        documents = list(financial_data.find({}, {"_id": False}))  # Exclude MongoDB's _id field

        if not documents:
            return jsonify({"error": "No documents found in the database"}), 404

        # Step 2: Return all documents as a JSON response
        return jsonify({
            "message": "All data fetched successfully",
            "data": documents
        })

    except Exception as e:
        return jsonify({"error": f"Failed to fetch data: {str(e)}"}), 500


@app.route("/query/", methods=["POST"])
@cross_origin()
def query_data():
    max_retries = 3  # Maximum number of retries
    retry_delay = 60  # Delay in seconds between retries (for rate limits)
    
    for attempt in range(max_retries):
        try:
            # Step 1: Get the query and custom_id from the request JSON payload
            request_data = request.json
            custom_id = int(request_data.get("custom_id"))
            query = request_data.get("query")

            if not custom_id or not query:
                return jsonify({"error": "custom_id and query are required"}), 400

            # Step 2: Query the database for the document with the specified custom_id
            document = financial_data.find_one({"custom_id": custom_id}, {"_id": False})  # Exclude MongoDB's _id field

            if not document:
                return jsonify({"error": f"No document found with custom_id: {custom_id}"}), 404

            # Step 3: Extract the all_data field from the document
            all_data = document.get("all_data")
            if not all_data:
                return jsonify({"error": "No all_data field found in the document"}), 404

            # Step 4: Generate the prompt for DeepSeek
            prompt = f"""Act as a financial expert. This is the data of an analysis report: {all_data}. Answer the given query in short: {query} based on the provided data."""

            # Step 5: Use DeepSeek API to generate the response
            from together import Together

            client = Together(api_key=os.environ.get("TOGETHER_API_KEY"))  # Replace with your actual API key

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
                response_text += chunk.choices[0].delta.content
                print(chunk.choices[0].delta.content or "", end="", flush=True)

            
            response_text = str(response_text.split("</think>")[-1]).replace("*","")
            
            # Step 6: Return the response as a string
            return jsonify({
                "message": "Query processed successfully",
                "response": response_text
            })

        except Exception as e:
            if "rate limit" in str(e):
                if attempt < max_retries - 1:  # Don't sleep on the last attempt
                    time.sleep(retry_delay)
                    continue  # Retry the loop
            # If it's not a rate limit error or we've exhausted retries, return the error
            return jsonify({"error": f"Failed to process query: {str(e)}"}), 500
    
    # This line should theoretically never be reached because we return in all cases above
    return jsonify({"error": "Max retries reached without success"}), 500


@app.route("/api/dashboard", methods=["GET"])
@cross_origin()
def get_dashboard_data():
    try:
        # Get all documents from the database
        all_reports = list(financial_data.find({}, {"_id": 0}))

        if not all_reports:
            return jsonify({"error": "No reports found in database"}), 404

        # Convert string dates to datetime objects for comparison
        for report in all_reports:
            if 'analysis_date' in report and isinstance(report['analysis_date'], str):
                try:
                    report['parsed_date'] = datetime.datetime.strptime(report['analysis_date'], "%B %d, %Y")
                except ValueError:
                    report['parsed_date'] = datetime.datetime.min  # Fallback for invalid dates
            else:
                report['parsed_date'] = datetime.datetime.min  # Ensure all have a date for comparison

        # Initialize aggregated data structure
        aggregated = {
            "companyName": all_reports[0]["companyName"] if all_reports else "",
            "revenue": 0,
            "revenueGrowth": 0,
            "ebitda": 0,
            "ebitdaGrowth": 0,
            "netIncome": 0,
            "netIncomeGrowth": 0,
            "freeCashFlow": 0,
            "freeCashFlowGrowth": 0,
            "overallFinancialHealth": "",
            "liquidity": "",
            "solvency": "",
            "profitability": "",
            "companyProfile": all_reports[0].get("companyProfile", ""),
            "keyFindings": [],
            "strengths": [],
            "areasOfConcern": [],
            "financialMetricsChartData": [],
            "financialRatios": [],
            "keyObservations": [],
            "recommendations": [],
            "executiveSummary": "",
            "incomeStatementRevenueBreakdown": [],
            "incomeStatementExpenseAllocation": [],
            "balanceSheetAssetsComposition": [],
            "balanceSheetLiabilitiesEquity": [],
            "cashFlowOperations": 0,
            "cashFlowInvesting": 0,
            "cashFlowFinancing": 0,
            "businessOverviewSummary": "",
            "businessOverviewStrengths": [],
            "riskAssessment": "",
            "dueDiligenceRecommendations": []
        }

        # Calculate averages for numeric fields
        numeric_fields = [
            "revenue", "revenueGrowth", "ebitda", "ebitdaGrowth",
            "netIncome", "netIncomeGrowth", "freeCashFlow", "freeCashFlowGrowth",
            "cashFlowOperations", "cashFlowInvesting", "cashFlowFinancing"
        ]

        for field in numeric_fields:
            valid_values = [report.get(field, 0) for report in all_reports 
                            if isinstance(report.get(field, 0), (int, float))]
            if valid_values:
                aggregated[field] = sum(valid_values) / len(valid_values)

        # Get most recent report using parsed dates
        most_recent_report = max(all_reports, key=lambda x: x.get('parsed_date', datetime.datetime.min))

        # Get health ratings from most recent report
        health_fields = [
            "overallFinancialHealth", "liquidity", "solvency", "profitability",
            "riskAssessment"
        ]
        
        for field in health_fields:
            aggregated[field] = most_recent_report.get(field, "")

        # Aggregate array fields (handle both strings and dictionaries)
        array_fields = [
            "keyFindings", "strengths", "areasOfConcern", "financialRatios",
            "keyObservations", "recommendations", "businessOverviewStrengths",
            "dueDiligenceRecommendations"
        ]
        
        for field in array_fields:
            seen_items = set()
            unique_items = []
            for report in all_reports:
                if isinstance(report.get(field), list):
                    for item in report[field]:
                        if isinstance(item, dict):
                            item_tuple = tuple(sorted((k, str(v)) for k, v in item.items()))
                            if item_tuple not in seen_items:
                                seen_items.add(item_tuple)
                                unique_items.append(item)
                        elif isinstance(item, str):
                            if item not in seen_items:
                                seen_items.add(item)
                                unique_items.append(item)
            aggregated[field] = unique_items

        # Prepare financial metrics chart data (last 3 years)
        current_year = datetime.datetime.now().year
        years = [current_year - i for i in range(3)][::-1]  # [2022, 2023, 2024]

        for year in years:
            year_data = {
                "year": year,
                "revenue": 0,
                "ebitda": 0,
                "netIncome": 0
            }

            # Find reports for this year (Fixed issue with datetime)
            year_reports = [
                r for r in all_reports 
                if r.get("analysis_date") and str(year) in str(r["analysis_date"])
            ]

            if year_reports:
                # Use average values for the year
                year_data["revenue"] = sum(r.get("revenue", 0) for r in year_reports) / len(year_reports)
                year_data["ebitda"] = sum(r.get("ebitda", 0) for r in year_reports) / len(year_reports)
                year_data["netIncome"] = sum(r.get("netIncome", 0) for r in year_reports) / len(year_reports)

            aggregated["financialMetricsChartData"].append(year_data)

        # Aggregate financial statement breakdowns (from most recent report)
        breakdown_fields = [
            "incomeStatementRevenueBreakdown",
            "incomeStatementExpenseAllocation",
            "balanceSheetAssetsComposition",
            "balanceSheetLiabilitiesEquity"
        ]
        
        for field in breakdown_fields:
            if field in most_recent_report:
                aggregated[field] = most_recent_report[field]

        # Calculate totals for percentage calculations
        if "balanceSheetAssetsComposition" in aggregated and aggregated["balanceSheetAssetsComposition"]:
            aggregated["totalAssets"] = sum(
                item.get("amount", 0) for item in aggregated["balanceSheetAssetsComposition"]
                if isinstance(item, dict)
            )
            
        if "balanceSheetLiabilitiesEquity" in aggregated and aggregated["balanceSheetLiabilitiesEquity"]:
            aggregated["totalLiabilitiesEquity"] = sum(
                item.get("amount", 0) for item in aggregated["balanceSheetLiabilitiesEquity"]
                if isinstance(item, dict)
            )

        # Generate summary texts from most recent report
        text_fields = [
            "executiveSummary",
            "businessOverviewSummary"
        ]
        
        for field in text_fields:
            if field in most_recent_report:
                aggregated[field] = most_recent_report[field]

        return jsonify(aggregated)

    except Exception as e:
        return jsonify({"error": f"Failed to aggregate dashboard data: {str(e)}"}), 500


# Run the Flask app
if __name__ == "__main__":
    app.run(debug=True)

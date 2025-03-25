# FinAI Analyzer

## Overview
FinAI Analyzer is an AI-driven financial statement analysis system that extracts, analyzes, and visualizes data from financial statement PDFs. It generates detailed reports, provides recommendations with citations, and features a chatbot for user queries. Additionally, it curates data from multiple uploaded reports into a comprehensive dashboard.

## Features
- **Automated Financial Statement Analysis**: Extracts key insights from balance sheets, income statements, and cash flow statements.
- **Dashboard Visualization**: Displays structured financial data, trends, and key financial ratios.
- **AI-Generated Recommendations**: Offers insights along with citations based on extracted data.
- **Chatbot Support**: Allows users to ask queries related to specific reports.
- **Curated Data Dashboard**: Aggregates insights from all uploaded reports for a holistic financial overview.

## Tech Stack
- **Backend**: Python, Flask
- **Frontend**: Next.js, ShadCN
- **Database**: MongoDB

## Installation
### Prerequisites
- Python 3.11+
- Node.js 16+
- MongoDB

### Setup Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
pip install -r requirements.txt
flask run
```

### Setup Frontend
```bash
cd frontend
npm install
npm run dev
```

## Usage
1. Upload a financial statement PDF.
2. The system extracts and analyzes key financial data.
3. View a detailed financial report on the dashboard.
4. Get AI-generated recommendations with citations.
5. Use the chatbot to ask queries regarding a specific report.
6. Access the curated dashboard for an aggregated financial overview.



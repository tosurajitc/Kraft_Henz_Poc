# Project Analytics Dashboard

An interactive dashboard built with Streamlit for visualizing and analyzing project development data.

## Features

- **Data Upload**: Upload Excel files with project data or use a default file
- **Project Overview**: Dashboard displaying all projects with key metrics
- **Project-Specific Analysis**: Individual tabs for each project
- **Interactive Visualizations**: 
  - Gantt charts for project timelines
  - Pie charts for development types and process areas
  - Bar charts for project stages
- **Project Status Tables**: Detailed status information with filtering options
- **AI-Powered Insights**: Ask questions about your data using the GROQ API

## Folder Structure

```
project-analytics-dashboard/
│
├── data/
│   └── Data_dump.xlsx         # Default data file (optional)
│
├── src/
│   ├── __init__.py
│   ├── data_processing.py     # Data processing functions
│   └── app.py                 # Main Streamlit application
│
├── .env                       # Environment variables (GROQ API key)
├── requirements.txt           # Project dependencies
└── README.md                  # This file
```

## Setup Instructions

1. **Clone the repository**

```bash
git clone <repository-url>
cd project-analytics-dashboard
```

2. **Create a virtual environment (optional but recommended)**

```bash
python -m venv venv
source venv/bin/activate  # On Windows, use: venv\Scripts\activate
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
```

4. **Set up environment variables**

Create a `.env` file in the root directory with your GROQ API key:
```
GROQ_API_KEY=your_api_key_here
```

5. **Run the application**

```bash
streamlit run src/app.py
```

## Using the Dashboard

1. **Upload Data**: Use the sidebar to upload an Excel file with project data.
   
2. **Navigate Projects**: Use the tabs at the top to switch between the overview and specific projects.
   
3. **Filter Data**: Use dropdown menus and text inputs to filter the data in various visualizations.
   
4. **Ask Questions**: Enter questions in the sidebar to get AI-powered insights about your data.

## Excel File Format




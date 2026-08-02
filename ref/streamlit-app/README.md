# FaberAI Streamlit Frontend

A minimal frontend for the backend geometry pipeline.

## Setup

Install the Streamlit app dependencies in a separate environment:

```bash
cd /home/antonia/FaberAI/streamlit-app
python -m pip install -r requirements.txt
```

## Run

```bash
streamlit run app.py
```

## Usage

1. Enter the backend URL (default: `http://localhost:8000`).
2. Upload a `*.stl`, `*.step`, or `*.stp` file.
3. Preview the STL file if supported.
4. Click `Launch geometry pipeline` to upload to the backend.
5. Use `Check task status` to poll the processing result.

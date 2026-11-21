# Streamlit development client

This optional client uploads CAD files and polls the backend. The React app in
`frontend/` is the primary user interface. Follow the root
[quick start](../README.md#run-locally) to start the backend services first.

Install this client's dependencies in a separate Python virtual environment.
From the repository root:

```sh
cd streamlit-app
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Set the backend URL to `http://localhost:8000` (or your configured API port).
Upload an STL, STEP, or STP file; preview STL geometry when supported; select
`Launch geometry pipeline`; then use `Check task status` to inspect the result.

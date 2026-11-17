# Instructions for data science environment

The application runs with Docker only; see the root [quick start](../README.md).
For native API/CAD development without Conda, install `requirements-runtime.txt`
in a Python virtual environment. The Conda environment below is optional for
data science and notebook work; it does not install the full API runtime.

conda env create -f environment-ds.yml
conda activate faberai-ds

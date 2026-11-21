# Optional data science environment

The application runs through Docker or a Python virtual environment; see the
[backend guide](README.md). Conda is an optional alternative for CAD and notebook
experiments, rather than a prerequisite for running FaberAI.

From `backend/`, create and activate the environment:

```sh
conda env create -f environment-ds.yml
conda activate faberai-ds
```

`environment-ds.yml` installs the scientific stack, pythonocc-core, CadQuery, and
build123d. It does not install the complete API runtime. For the API and worker,
install the runtime or development requirements described in the backend guide.

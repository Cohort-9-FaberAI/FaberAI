import json
import tempfile
from pathlib import Path

import requests
import streamlit as st

try:
    import trimesh
    import numpy as np
    import plotly.graph_objects as go
except ImportError:
    trimesh = None
    np = None
    go = None

BACKEND_DEFAULT = "http://localhost:8000"


def render_mesh(mesh):
    vertices = mesh.vertices
    faces = mesh.faces
    fig = go.Figure(
        data=[
            go.Mesh3d(
                x=vertices[:, 0],
                y=vertices[:, 1],
                z=vertices[:, 2],
                i=faces[:, 0],
                j=faces[:, 1],
                k=faces[:, 2],
                opacity=0.8,
                color="lightblue",
            )
        ]
    )
    fig.update_layout(
        scene=dict(aspectmode="data"),
        margin=dict(t=10, l=10, r=10, b=10),
    )
    return fig


def main():
    st.set_page_config(page_title="FaberAI Streamlit Frontend", layout="wide")
    st.title("FaberAI Geometry Frontend")
    st.write(
        "Upload a STEP or STL file, preview the 3D part, and launch backend geometry analysis."
    )

    if "last_task_id" not in st.session_state:
        st.session_state.last_task_id = None
    if "last_analysis_id" not in st.session_state:
        st.session_state.last_analysis_id = None
    if "last_task_result" not in st.session_state:
        st.session_state.last_task_result = None

    backend_url = st.text_input("Backend URL", BACKEND_DEFAULT)
    uploaded_file = st.file_uploader("Choose a STEP or STL file", type=["stl", "step", "stp"])

    if uploaded_file is None:
        st.info("Upload a file to preview it and launch the geometry pipeline.")
        return

    suffix = Path(uploaded_file.name).suffix.lower()
    st.markdown(f"**Selected file:** {uploaded_file.name}")

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
        tmp_file.write(uploaded_file.read())
        temp_path = tmp_file.name

    st.markdown(f"Saved temporary file `{temp_path}` for upload.")

    if suffix == ".stl":
        if trimesh is None or go is None or np is None:
            st.error(
                "STL preview requires `trimesh`, `numpy`, and `plotly`. Install them in this environment."
            )
        else:
            try:
                mesh = trimesh.load(temp_path, force="mesh")
                if mesh.is_empty:
                    st.warning("The STL file loaded, but the mesh is empty.")
                else:
                    fig = render_mesh(mesh)
                    st.plotly_chart(fig, width='stretch')
                    st.markdown(
                        f"**Mesh info:** {len(mesh.vertices)} vertices, {len(mesh.faces)} faces"
                    )
            except Exception as exc:
                st.error(f"Unable to preview STL file: {exc}")
    else:
        st.warning(
            "STEP preview is not supported in this Streamlit app. The file will still be uploaded to the backend for analysis."
        )

    if st.button("Launch geometry pipeline"):
        try:
            with open(temp_path, "rb") as fh:
                files = {"file": (uploaded_file.name, fh, "application/octet-stream")}
                with st.spinner("Uploading file to backend and starting geometry analysis..."):
                    response = requests.post(f"{backend_url}/upload/", files=files, timeout=120)
            response.raise_for_status()
            result = response.json()
            st.success("Backend accepted the file and started processing.")
            st.json(result)
            st.session_state["last_task_id"] = result.get("task_id")
            st.session_state["last_analysis_id"] = result.get("analysis_id")
            st.session_state["last_task_result"] = None
        except requests.RequestException as exc:
            st.error(f"Upload failed: {exc}")

    if st.session_state.get("last_task_id"):
        task_id = st.session_state["last_task_id"]
        st.markdown(f"**Last task_id:** {task_id}")
        if st.button("Check task status"):
            try:
                status_response = requests.get(
                    f"{backend_url}/tasks/{task_id}",
                    params={"analysis_id": st.session_state.get("last_analysis_id")},
                    timeout=30,
                )
                status_response.raise_for_status()
                payload = status_response.json()
                st.session_state["last_task_result"] = payload
                st.json(payload)
                st.download_button(
                    label="⬇ Download result as JSON",
                    data=json.dumps(payload, indent=2),
                    file_name=f"faberai_{task_id}.json",
                    mime="application/json",
                    key="download_status_check",
                )
            except requests.RequestException as exc:
                st.error(f"Failed to fetch task status: {exc}")

        if st.session_state.get("last_task_result"):
            st.subheader("Latest task result")
            result = st.session_state["last_task_result"]
            st.json(result)
            st.download_button(
                label="⬇ Download latest result as JSON",
                data=json.dumps(result, indent=2),
                file_name=f"faberai_{task_id}_latest.json",
                mime="application/json",
                key="download_latest_result",
            )


if __name__ == "__main__":
    main()

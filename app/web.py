
"""Module for visualizing HBJSON model in a web browser using Streamlit and VTK.

This module provides functions to convert HBJSON files to VTKJS format and 
visualize them in a 3D viewer within a web browser. 
"""

# Import necessary libraries and modules
import streamlit as st
from pathlib import Path
from honeybee_vtk.model import Model as VTKModel
from pollination_streamlit_viewer import viewer

def create_vtkjs(hbjson_path: Path) -> Path:
    """Convert HBJSON file to VTKJS format.
    
    This function takes the path to an HBJSON file, converts it to VTKJS format,
    and saves the VTKJS file in a temporary directory. The function then returns 
    the path to the generated VTKJS file.
    
    Args:
        hbjson_path (Path): Path to the HBJSON file.
        
    Returns:
        Path: Path to the generated VTKJS file.
    """
    
    # Check if the provided path is valid
    if not hbjson_path:
        return

    # Create a VTK model from the provided HBJSON file
    model = VTKModel.from_hbjson(hbjson_path.as_posix())
    
    # Define a directory to save the VTKJS file
    vtkjs_folder = st.session_state.temp_folder.joinpath('vtkjs')
    
    # Create the directory if it doesn't exist
    if not vtkjs_folder.exists():
        vtkjs_folder.mkdir(parents=True, exist_ok=True)
        
    # Define the path for the VTKJS file based on the HBJSON filename
    vtkjs_file = vtkjs_folder.joinpath(f'{hbjson_path.stem}.vtkjs')

    # If the VTKJS file doesn't already exist, generate it
    if not vtkjs_file.is_file():
        model.to_vtkjs(folder=vtkjs_folder.as_posix(), name=hbjson_path.stem)

    return vtkjs_file


def show_model(hbjson_path: Path, key='3d_viewer', subscribe=False):
    """Render the HBJSON model in a 3D viewer.
    
    This function takes the path to an HBJSON file, converts it to VTKJS format
    (if not already converted), and then renders the model in a 3D viewer using 
    Streamlit and VTK.
    
    Args:
        hbjson_path (Path): Path to the HBJSON file.
        key (str, optional): Key for the 3D viewer. Defaults to '3d_viewer'.
        subscribe (bool, optional): Subscription option for the viewer. Defaults to False.
    """
    
    # Define the name for the VTKJS model
    vtkjs_name = f'{hbjson_path.stem}_vtkjs'
    
    # Convert the HBJSON to VTKJS format
    vtkjs = create_vtkjs(hbjson_path)
    
    # Display the model in the 3D viewer
    viewer(content=vtkjs.read_bytes(), key=key, subscribe=subscribe)
    
    # Save the VTKJS model path in the session state for future reference
    st.session_state[vtkjs_name] = vtkjs

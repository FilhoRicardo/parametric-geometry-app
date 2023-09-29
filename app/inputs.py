from ladybug_geometry.geometry3d import Point3D, Face3D, Polyface3D, Vector3D
import streamlit as st
from honeybee.model import Model,Room
import json
import web as web
import tempfile
from pathlib import Path
from honeybee.boundarycondition import boundary_conditions


def clear_temp_folder():
    st.session_state.temp_folder = Path(tempfile.mkdtemp())

def initialize():
    if "footprint" not in st.session_state: 
        st.session_state.footprint = None
    if "no_of_floors" not in st.session_state: 
        st.session_state.no_of_floors = None
    if "floor_height" not in st.session_state: 
        st.session_state.floor_height = None      
    if "wwr" not in st.session_state: 
        st.session_state.wwr = None
    if "building_geometry" not in st.session_state: 
        st.session_state.building_geometry = None       
    if "hb_model" not in st.session_state: 
        st.session_state.hb_model = None
    if "temp_folder" not in st.session_state: 
        st.session_state.temp_folder = Path(tempfile.mkdtemp()) #not going to generate a local file, just creates a temporary file in memory
    if "hb_json_path" not in st.session_state: 
        st.session_state.hb_json_path = None
    if "visualize" not in st.session_state: 
        st.session_state.visualize = None

def geometry_parameters(container):
    width_ = container.slider("Building Width [m]",min_value=0,max_value=50,value=10,help="This is the width of the building in meters")
    lenght_ = container.slider("Building Lenght [m]",min_value=0,max_value=50,value=10,help="This is the lenght of the building in meters")        
    no_of_floors_ = container.slider("Number of floors",min_value=0,max_value=6,value=1,step=1,help="This is the lenght of the building in meters")
    floor_height_ = container.slider("Building Floor height [m]",min_value=2,max_value=10,value=3,help="This is the height of the building floor in meters")       
    wwr_ =  container.slider("Window to wall ratio",min_value=0.0,max_value=0.99,value=0.4,help="This is the window to wall ratio for all the rooms")
   

    lower_left = Point3D(0, 0, 0)
    lower_right = Point3D(width_, 0, 0)
    upper_right = Point3D(width_, lenght_, 0)
    upper_left = Point3D(0, lenght_, 0)

    st.session_state.footprint = [lower_left, lower_right, upper_right, upper_left]
    st.session_state.no_of_floors = no_of_floors_
    st.session_state.floor_height = floor_height_
    st.session_state.wwr = wwr_

def generate_building1(footprint, floor_height, num_floors):
    all_floors = []

    for i in range(num_floors):
        faces = []
        base_height = i * floor_height
        upper_height = (i + 1) * floor_height

        # Bottom face for the current floor (also serves as ceiling for the floor below)
        faces.append(Face3D([pt.move(Vector3D(0, 0, base_height)) for pt in footprint]))

        # Side faces for the current floor
        for j in range(len(footprint)):
            start_point = footprint[j]
            end_point = footprint[(j + 1) % len(footprint)]

            lower_left = Point3D(start_point.x, start_point.y, base_height)
            lower_right = Point3D(end_point.x, end_point.y, base_height)
            upper_right = Point3D(end_point.x, end_point.y, upper_height)
            upper_left = Point3D(start_point.x, start_point.y, upper_height)

            face = Face3D([lower_left, lower_right, upper_right, upper_left])
            faces.append(face)

        # Top face for the current floor
        if i == num_floors - 1:
            faces.append(Face3D([pt.move(Vector3D(0, 0, upper_height)) for pt in footprint]))

        floor_geometry = Polyface3D.from_faces(faces, 0.01)
        all_floors.append(floor_geometry)

    st.session_state.building_geometries = all_floors  # Store the list of Polyface3D geometries for each floor


def generate_building(footprint, floor_height, num_floors):
    all_floors = []

    for i in range(num_floors):
        faces = []
        base_height = i * floor_height
        upper_height = (i + 1) * floor_height

        # Bottom face for every floor (also serves as ceiling for the floor below)
        faces.append(Face3D([pt.move(Vector3D(0, 0, base_height)) for pt in footprint]))

        # Side faces for the current floor
        for j in range(len(footprint)):
            start_point = footprint[j]
            end_point = footprint[(j + 1) % len(footprint)]

            lower_left = Point3D(start_point.x, start_point.y, base_height)
            lower_right = Point3D(end_point.x, end_point.y, base_height)
            upper_right = Point3D(end_point.x, end_point.y, upper_height)
            upper_left = Point3D(start_point.x, start_point.y, upper_height)

            face = Face3D([lower_left, lower_right, upper_right, upper_left])
            faces.append(face)

        # Top face for every floor including the very bottom one
        faces.append(Face3D([pt.move(Vector3D(0, 0, upper_height)) for pt in footprint]))

        floor_geometry = Polyface3D.from_faces(faces, 0.01)
        all_floors.append(floor_geometry)

    st.session_state.building_geometries = all_floors  # Store the list of Polyface3D geometries for each floor

def generate_honeybee_model():
    """Type of building: Polyface3D"""
    """This function will convert the building into a Honeybee JSON"""

    st.session_state.hb_model = Model("shoeBox")  # instantiate a model
    rooms = []  # to store all rooms for adjacency check

    for i, floor_geometry in enumerate(st.session_state.building_geometries):
        room = Room.from_polyface3d(f"room_{i}", floor_geometry)  # creating a room
        room.wall_apertures_by_ratio(st.session_state.wwr)  # add a window

        rooms.append(room)  # append room to the list
        st.session_state.hb_model.add_room(room)  # adding a room to the model

    # Solve adjacency between rooms
    Room.solve_adjacency(st.session_state.hb_model.rooms, 0.01)



def get_model_info():
    
    col1,col2,col3 = st.columns(3)
    with col1:
        st.metric(label=f"Total Volume",value=st.session_state.hb_model.volume)
    with col2:
        st.metric(label="Total area",value=st.session_state.hb_model.floor_area)
    with col3:
        st.metric(label="Total glazing area",value=round(st.session_state.hb_model.exterior_aperture_area,1))

def display_model_geometry():
    #requirements to display a model:
        #1. Have a temporary folder
        #2. 
        
    st.session_state.hb_json_path = st.session_state.temp_folder.joinpath(f"{st.session_state.hb_model.identifier}.hbjson")
    st.session_state.hb_json_path.write_text(json.dumps(st.session_state.hb_model.to_dict()))
    web.show_model(st.session_state.hb_json_path)
   
def parameters_changed():
    """Check if the building parameters have changed from previous version."""
    keys = ['footprint', 'no_of_floors', 'floor_height', 'wwr']
    for key in keys:
        if key + "_old" not in st.session_state:
            st.session_state[key + "_old"] = st.session_state[key]
        elif st.session_state[key + "_old"] != st.session_state[key]:
            st.session_state[key + "_old"] = st.session_state[key]
            return True
    return False

import streamlit as st
import pydeck as pdk
import pandas as pd

# Sample data
data = pd.DataFrame({
    'x': [1, 2, 3, 4, 5],
    'y': [5, 6, 2, 3, 13],
    'z': [2, 3, 3, 3, 5],
    'color': [1, 2, 3, 4, 5]
})

# Define the layer
layer = pdk.Layer(
    'ScatterplotLayer',     # Type of the layer
    data,
    get_position='[x, y, z]',
    get_color='[color * 255, (1 - color) * 255, 120]',
    get_radius=100,         # Radius of each data point
)

# Set the viewport location
view_state = pdk.ViewState(
    longitude=0,
    latitude=0,
    zoom=10,
    pitch=50,
)

# Render
r = pdk.Deck(layers=[layer], initial_view_state=view_state)
st.pydeck_chart(r)

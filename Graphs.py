import plotly.graph_objects as go
import matplotlib.pyplot as plt

def vol_surface(results):
    # Create a 3D scatter plot with Plotly
    fig = go.Figure(data=[go.Mesh3d(
        x=results['Strike'],
        y=results['TTM'],
        z=results['Implied_Volatility'],
        opacity=0.5,
        colorscale='Viridis',  # Correct colorscale property
        intensity=results['Implied_Volatility'],  # Use implied volatility as the intensity for the colorscale
        intensitymode='vertex'
    )])

    # Update layout for a better mobile view
    fig.update_layout(
        scene=dict(
            xaxis_title='Strike Price',
            yaxis_title='Time to Maturity (TTM)',
            zaxis_title='Implied Volatility'
        ),
        autosize=True,
        margin=dict(l=0, r=0, b=0, t=0)
    )
    return fig
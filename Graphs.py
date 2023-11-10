from plotly.subplots import make_subplots
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import PricesFunctions
import numpy as np

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

def sensibility(risk_free_rate, dividend_yield, calculation_date, maturity_date, spot_price, strike_price, call_or_put):
    # Define the constant parameters for the option
    call_option = True if call_or_put == 'Call' else False

    # Define the ranges for the parameters you want to vary
    param_ranges = {
        'v0': np.linspace(0.01, 0.05, 5),
        'kappa': np.linspace(1, 3, 5),
        'theta': np.linspace(0.01, 0.05, 5),
        'sigma': np.linspace(0.1, 0.5, 5),
        'rho': np.linspace(-0.5, 0.5, 5)
    }

    sensitivity_results = {}

    # Define the subplots for tabs
    fig = make_subplots(rows=1, cols=5, subplot_titles=list(param_ranges.keys()), specs=[[{'type': 'scatter'}]*5])

    # Update layout for tabs
    fig.update_layout(
        title='Sensitivity Analysis in Tabs',
        template="plotly_white"
    )

    for i, (param, values) in enumerate(param_ranges.items(), start=1):
        prices = []
        for value in values:
            # Set base values for parameters
            args = {
                'v0': 0.02,
                'kappa': 2,
                'theta': 0.02,
                'sigma': 0.2,
                'rho': 0
            }
            args[param] = value  # Vary the parameter
            price = PricesFunctions.HestonNPV(**args, risk_free_rate=risk_free_rate, dividend_yield=dividend_yield,
                              calculation_date=calculation_date, maturity_date=maturity_date,
                              spot_price=spot_price, strike_price=strike_price, call_option=call_option)
            prices.append(price)
        sensitivity_results[param] = prices

        # Add trace to the respective subplot
        fig.add_trace(
            go.Scatter(x=values, y=prices, mode='lines+markers', name=param),
            row=1, col=i
        )

        # Update xaxis and yaxis properties if necessary
        fig.update_xaxes(title_text=param, row=1, col=i)
        fig.update_yaxes(title_text='Option Price', row=1, col=i)
    return fig
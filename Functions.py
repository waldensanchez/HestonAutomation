import pandas as pd
from scipy.optimize import minimize
import numpy as np
from scipy.stats import norm


# Define the Black-Scholes function
def black_scholes_call_price(S, K, T, r, sigma):
    """
    Compute the Black-Scholes price for a call option.
    
    Parameters:
    S - Current stock price
    K - Option strike price
    T - Time to expiration (in years)
    r - Risk-free interest rate
    sigma - Volatility
    
    Returns:
    Price of the call option under the Black-Scholes model.
    """
    
    d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    
    call_price = S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
    
    return call_price

def simplified_heston_price(S, K, T, r, kappa, theta, sigma, rho, v0):
    """
    Simplified Heston model pricing function.
    This is NOT the actual Heston formula but a representation for demonstration purposes.
    
    Parameters:
    S - Current stock price
    K - Option strike price
    T - Time to expiration (in years)
    r - Risk-free interest rate
    kappa, theta, sigma, rho, v0 - Heston model parameters
    
    Returns:
    Approximated price of the call option under the Heston model.
    """
    
    # Approximate the Heston volatility using the model parameters
    heston_vol = np.sqrt(v0 + kappa * (theta - v0) * T + sigma * np.sqrt(T))
    
    # Use the Black-Scholes formula with the approximated Heston volatility
    heston_price = black_scholes_call_price(S, K, T, r, heston_vol)
    
    return heston_price

def objective_function(params, *args, return_params: bool = False):
    """
    Objective function for Heston model calibration.
    
    Parameters:
    params - Heston model parameters (kappa, theta, sigma, rho, v0)
    *args - Other arguments (S, K, T, r, market_prices)
    
    Returns:
    Sum of squared differences between market prices and Heston model prices.
    """
    
    kappa, theta, sigma, rho, v0 = params
    S, K, T, r, market_prices = args
    
    heston_prices = simplified_heston_price(S, K, T, r, kappa, theta, sigma, rho, v0)

    return np.sum((heston_prices - market_prices) ** 2) 


def implied_volatility_bs(S, K, T, r, market_price):
    """
    Calculate implied volatility using the Black-Scholes formula via a numerical method.
    
    Parameters:
    S - Current stock price
    K - Option strike price
    T - Time to expiration (in years)
    r - Risk-free interest rate
    market_price - Observed market price of the option
    
    Returns:
    Implied volatility
    """
    # Define an objective function to minimize
    def loss_function(sigma):
        return (black_scholes_call_price(S, K, T, r, sigma) - market_price) ** 2

    # Use a numerical optimizer to find the implied volatility
    result = minimize(loss_function, 0.2, bounds=[(0.001, 5)])
    return result.x[0]

# Function to correct the formatting of the output line to match the expected output
def format_output_line(emisora, serie, option_type, price, volatility):
    # Format the strike price with correct padding
    formatted_strike = f"{serie: >7}"  # 7 spaces including the strike price digits
    # Format the price as an integer without a thousands separator
    formatted_price = f"{price:.0f}"  # No decimal places
    # Format the volatility with six decimal places
    formatted_volatility = f"{volatility:.6f}"
    # Combine all parts into the final formatted line
    return f"{emisora},{formatted_strike},{option_type},{formatted_price},{formatted_volatility}\n"


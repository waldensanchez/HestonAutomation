import QuantLib as ql
import pandas as pd
import numpy as np
from scipy.optimize import minimize

def get_metrics(results):
    results_report = pd.concat(results, axis = 0)
    error = results_report.groupby('Optimizer')['MSE'].sum()
    reliability = results_report[results_report['Success'] == True].groupby('Optimizer').count() / (len(results_report)/2) * 100
    reliability = reliability['Success'].apply(lambda x: f'{x}%')
    reliability = reliability.to_frame()
    error = error.to_frame()
    performance_metrics = reliability.merge(error, left_index = True, right_index = True).sort_values(by = 'MSE')
    return performance_metrics

def HestonParameters(spot_price, strike_price, market_price, dividend_yield, traditional_implied_volatility, calculation_date, maturity_date, ttm, risk_free_rate=0.00525, call_option=True, verbose = False):
    
    day_count = ql.Actual365Fixed()
    calendar = ql.UnitedStates(ql.UnitedStates.NYSE)

    # Set up the QuantLib environment
    ql.Settings.instance().evaluationDate = calculation_date
    if call_option:
        option_type = ql.Option.Call
    else:
        option_type = ql.Option.Put
    payoff = ql.PlainVanillaPayoff(option_type, strike_price)
    exercise = ql.EuropeanExercise(maturity_date)
    european_option = ql.VanillaOption(payoff, exercise)

    # Initial parameters for the Heston model
    initial_v0 = 0.1
    initial_kappa = 0.1
    initial_theta = traditional_implied_volatility
    initial_sigma = 0.1
    initial_rho = 0.1

    # Define the optimization objective function
    def objective_function(params):
        v0, kappa, theta, sigma, rho = params

        heston_process = ql.HestonProcess(
            ql.YieldTermStructureHandle(ql.FlatForward(calculation_date, risk_free_rate, day_count)),
            ql.YieldTermStructureHandle(ql.FlatForward(calculation_date, dividend_yield, day_count)),
            ql.QuoteHandle(ql.SimpleQuote(spot_price)),
            v0, kappa, theta, sigma, rho
        )

        model = ql.HestonModel(heston_process)
        engine = ql.AnalyticHestonEngine(model)
        european_option.setPricingEngine(engine)

        model_price = european_option.NPV()
        error = (model_price - market_price) ** 2
        return error, model_price

    # Bounds for the parameters, excluding theta which is input by the user
    bounds = [(0.0001, 1.0), (0.0001, 2.0), (traditional_implied_volatility * 0.5, traditional_implied_volatility * 1.5), (0.0001, 1.0), (-0.999, 0.999)]

    # Initial parameter guesses, excluding theta which is input by the user
    initial_guess = [0.1, 0.1, traditional_implied_volatility, 0.1, 0.1]

    # Try TNC optimizer first, fall back to L-BFGS-B if it fails
    try:
        result = minimize(lambda x: objective_function(x)[0], initial_guess, method='TNC', bounds=bounds)
        success = result.success
    except Exception as e:
        print('TNC optimizer failed with the following error:', e)
        result = minimize(lambda x: objective_function(x)[0], initial_guess, method='L-BFGS-B', bounds=bounds)
        success = result.success

    params = result.x if success else None
    objective_value, estimated_price = objective_function(params) if success else (None, None)
    error = (estimated_price - market_price) if success else None
    # Create a DataFrame to store the results
    results_df = pd.DataFrame({
        'Optimizer': ['TNC' if success else 'L-BFGS-B'],
        'Success': [success],
        'Params': [params],
        'Strike': [strike_price],
        'TTM': [ttm],
        'Objective_Value': [objective_value],
        'Estimated_Price': [estimated_price],
        'Market_Price': [market_price if success else None],
        'MSE': [error**2 if error is not None else None]
    })

    # Print the DataFrame
    if verbose:
        print('Optimizer', 'TNC' if success else 'L-BFGS-B', 'Estimated Price:', estimated_price, 'Market Price:', market_price)
    return results_df



def expected_variance(v0, kappa, theta, t):
    """
    Calculate the expected variance under the Heston model at time t.

    Parameters:
    v0 : float
        Initial variance.
    kappa : float
        Rate of reversion.
    theta : float
        Long-term mean variance.
    t : float
        Time at which to calculate the expected variance.

    Returns:
    float
        The expected variance at time t.
    """
    return theta + (v0 - theta) * np.exp(-kappa * t)


def calculate_expected_variance_over_strikes(results_df):
    """
    Calculate the expected variance over different strike prices using the estimated parameters.
    Now it uses the 'TTM' column from the results_df to find the time to maturity.

    Parameters:
    results_df : DataFrame
        DataFrame containing the estimated parameters from HestonParameters function.

    Returns:
    DataFrame
        A DataFrame with strike prices as the index and expected variances as values.
    """
    # Extract the parameters from the DataFrame
    params_df = results_df[['Params', 'TTM']].copy()
    params_df[['v0', 'kappa', 'theta', 'sigma', 'rho']] = pd.DataFrame(params_df['Params'].tolist(), index=params_df.index)
    params_df.drop(columns='Params', inplace=True)

    # Calculate the expected variance for each row in the DataFrame using the 'TTM' column
    params_df['Expected_Variance'] = params_df.apply(lambda row: expected_variance(row['v0'], row['kappa'], row['theta'], row['TTM']), axis=1)

    # Create a new DataFrame with strike prices and expected variances
    expected_variance_df = pd.DataFrame({
        'Strike_Price': results_df['Strike'],
        'Expected_Variance': params_df['Expected_Variance']
    }).set_index('Strike_Price')

    return expected_variance_df

# Example usage:
# Assuming the results_df is defined and it includes a 'TTM' column after running the HestonParameters function



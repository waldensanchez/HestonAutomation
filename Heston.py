from scipy.optimize import minimize
import yfinance as yf
import matplotlib.pyplot as plt
import QuantLib as ql
import pandas as pd
import numpy as np

def HestonParameters(spot_price, strike_price, market_price, dividend_yield, initial_params, calculation_date, maturity_date, ttm, risk_free_rate=0.00525, call_option=True, verbose = False):
    
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
    initial_v0 = initial_params[0]
    initial_kappa = initial_params[1]
    initial_theta = initial_params[2]
    initial_sigma = initial_params[3]
    initial_rho = initial_params[4]

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
    bounds = [(0.0001, 1.0), (0.0001, 2.0), (initial_theta * 0.5, initial_theta * 1.5), (0.0001, 1.0), (-1, 1)]

    # Initial parameter guesses, excluding theta which is input by the user
    initial_guess = [initial_v0, initial_kappa, initial_theta, initial_sigma, initial_rho]

    # Try TNC optimizer first, fall back to L-BFGS-B if it fails, then SLSQP, and finally Nelder-Mead as a last resort
    try:
        result = minimize(lambda x: objective_function(x)[0], initial_guess, method='TNC', bounds=bounds, options={'maxfun':50000})
        success = result.success
        optimizer_used = 'TNC'
        assert success, "Failed to find solution"
    except Exception as e:
        print('TNC optimizer failed with the following error:', e)
        try:
            result = minimize(lambda x: objective_function(x)[0], initial_guess, method='L-BFGS-B', bounds=bounds, options={'maxiter':10000})
            success = result.success
            optimizer_used = 'L-BFGS-B'
            assert success, "Failed to find solution"
        except Exception as e:
            print('L-BFGS-B optimizer failed with the following error:', e)
            try:
                result = minimize(lambda x: objective_function(x)[0], initial_guess, method='SLSQP', bounds=bounds, options={'maxiter':10000})
                success = result.success
                optimizer_used = 'SLSQP'
                assert success, "Failed to find solution"
            except Exception as e:
                print('SLSQP optimizer failed with the following error:', e)
                try:
                    # Using Nelder-Mead, so we do not pass the bounds
                    result = minimize(lambda x: objective_function(x)[0], initial_guess, method='Nelder-Mead', options={'maxiter':10000})
                    success = result.success
                    optimizer_used = 'Nelder-Mead'
                    assert success, "Failed to find solution"
                except Exception as e:
                    print('Nelder-Mead optimizer failed with the following error:', e)
                    success = False
                    optimizer_used = 'None'

    params = result.x if success else None
    objective_value, estimated_price = objective_function(params) if success else (None, None)
    error = (estimated_price - market_price) if success else None

    # Create a DataFrame to store the results
    results_df = pd.DataFrame({
        'Optimizer': [optimizer_used],
        'Success': [success],
        'Params': [params],
        'Strike': [strike_price],
        'TTM': [ttm],
        'Objective_Value': [objective_value],
        'Estimated_Price': [estimated_price],
        'Market_Price': [market_price if success else None],
        'MSE': [error**2 if error is not None else None]
    })

    return results_df



def expected_variance(v0, kappa, theta, t):
    return theta + (v0 - theta) * np.exp(-kappa * t)


def calculate_expected_variance_over_strikes(results_df):
    results_df[['v0', 'kappa', 'theta', 'sigma', 'rho']] = pd.DataFrame(results_df['Params'].tolist(), index=results_df.index)
    results_df.drop(columns='Params', inplace=True)
    results_df = results_df.fillna(0)
    results_df.drop(columns = ['Optimizer','Success','Objective_Value','MSE'], inplace = True)
    results_df['Expected_Variance'] = results_df.apply(lambda row: expected_variance(row['v0'], row['kappa'], row['theta'], row['TTM']), axis=1)
    results_df = results_df[['Strike','v0','kappa','theta','sigma','rho','Estimated_Price','Market_Price','TTM','Expected_Variance']]
    results_df = results_df.rename( columns = {'Estimated_Price':'Theorical_Price','Expected_Variance':'Implied_Volatility'} )
    return results_df

def plot_ajusted_poli(options, expected_variance_df):
    strike_price = expected_variance_df.index.values
    expected_variance = np.sqrt(expected_variance_df['Expected_Variance'].values)

    # Fit a quadratic polynomial (2nd degree polynomial)
    coefficients = np.polyfit(strike_price, expected_variance, 2)

    # Generate a sequence of strike prices for the purpose of plotting the polynomial
    x_fit = np.linspace(strike_price.min(), strike_price.max(), 400)
    # Calculate the expected variance using the polynomial coefficients
    y_fit = np.polyval(coefficients, x_fit)

    # Plotting
    plt.figure(figsize=(10, 6))
    plt.plot(strike_price, np.sqrt(expected_variance), color = 'blue',label='Estimated')
    #plt.plot(x_fit, y_fit, color='red', label='Quadratic Fit')
    plt.plot(options.strike, options.impliedVolatility, color = 'black', label ='Implicit YF')
    plt.xlabel('Strike Price')
    plt.ylabel('Expected Variance')
    plt.title('Mkt Vs Model')
    plt.legend()
    plt.show()

def to_ql_dates(date):
    date = pd.to_datetime(date)
    return ql.Date(date.day, date.month, date.year)

def simple_plot(results):
    results[['Strike','Implied_Volatility']].set_index('Strike').plot()
    plt.title('Volatility Smile')
    plt.show()

def get_prices_with_fill(ticker_symbol, start_date, maturity_date):
    # Download prices from yfinance
    prices = yf.download(ticker_symbol, start=start_date, end=maturity_date, progress=False)['Adj Close']

    # Create a date range for all days
    all_dates = pd.date_range(start=start_date, end=maturity_date, freq='D')

    # Reindex the prices DataFrame to include all dates in the date range
    prices = prices.reindex(all_dates)

    # Forward-fill the NaN values with the last available price
    prices.ffill(inplace=True)

    # If the price data is missing at the beginning, backfill to ensure all dates have a price
    prices.bfill(inplace=True)

    # Reset the index to turn the date index into a column
    prices = prices.reset_index()

    # Rename the columns to match the expected output
    prices.columns = ['Date', 'Price']

    return prices
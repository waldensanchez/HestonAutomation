import random
import numpy as np
import pandas as pd
import QuantLib as ql
import yfinance as yf
from math import sqrt, exp
from datetime import datetime 
import matplotlib.pyplot as plt
from scipy.optimize import basinhopping
from datetime import datetime, timedelta
from MexicoCalendar import MexicoCalendar


class Heston():

    def __init__(self):
        pass

    def load_data(self, file_path):
        data_columns = ['Fecha', 'TV', 'Emisora', 'Serie', 'Vencimiento', 'Tasa de Interes',
       'Plazo a Vencimiento', 'Futuro', 'Pliq', 'Bid', 'Ask', 'Call o Put',
       'Hubo Bid/Ask', 'Volatilidad', 'V. Teorico']
        self.data = pd.read_csv(file_path)[data_columns]

        return self.data
    
    def preprocess_data(self):
        # Codigos de Vencimiento
        vencimiento_call_list = 'A B C D E F G H I J K L'.split(' ')
        vencimiento_put_list = 'M N O P Q R S T U V W X'.split(' ')
        # Equivalencias
        vencimiento_call = {code:month for code,month in zip(vencimiento_call_list,range(1,len(vencimiento_call_list)+1))}
        vencimiento_put = {code:month for code,month in zip(vencimiento_put_list,range(1,len(vencimiento_put_list)+1))}

        self.call = self.data[self.data['Call o Put'] == 0].copy()
        self.call['Mes_vencimiento'] = self.call['Vencimiento'].map(vencimiento_call)

        self.put = self.data[self.data['Call o Put'] == 1].copy()
        self.put['Mes_vencimiento'] = self.put['Vencimiento'].map(vencimiento_put)

        self.clean = pd.concat([self.call,self.put], axis = 0)

        self.clean['Fecha'] = self.clean['Fecha'].apply(str)
        self.clean['Fecha'] = self.clean['Fecha'].apply(lambda date_str: f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}")

    def get_from_user(self, risk_free_rate: float, ticker: str = '^MXX'):
        self.ticker = ticker

    def get_from_market(self):
        # Get from the market
        end_date = self.clean['Fecha'].unique()
        self.current_date = pd.to_datetime(end_date)
        end_date = pd.to_datetime(end_date) + timedelta(days = 1)
        start_date = pd.to_datetime(end_date) - timedelta(days = 365)

        end_date = end_date[0]
        start_date = start_date[0]

        stock = yf.download(self.ticker,start = start_date, end = end_date, progress = False)['Adj Close']
        stock_variance = stock.pct_change().var
        spot_price = stock.iloc[-1]

        self.spot_price = spot_price
        self.yearly_historical_volatility = stock_variance

        # From Data
        self.strike_price = self.clean['Serie'].values
        self.risk_free_rate = self.clean['Tasa de Interes'].values
        self.maturities = self.clean['Plazo a Vencimiento']
        self.market_price = self.clean['Pliq'].values
        self.option_type = self.clean['Call o Put'].apply(lambda call: True if call == 1 else False)
    
    def optimize_params(self):
        # Initial guess for the parameters based on historical volatility
        initial_params = [self.yearly_historical_volatility ** 2, 2.0, 0.04, 0.1, -0.7]  # Initial parameter guess

        # Define bounds for the parameters
        bounds = [(0, 1), (0.1, 15), (0, 1), (0.1, 1), (-1, 1)]

        # The basinhopping algorithm
        minimizer_kwargs = {"method": "L-BFGS-B", "bounds": bounds}
        result = basinhopping(objective_function, initial_params, minimizer_kwargs=minimizer_kwargs, niter=10)

        # Results
        optimized_params = result.x
        minimum_error = result.fun

        print("Optimized parameters:", optimized_params)
        print("Minimum error:", minimum_error)

def HestonPriceFunction(strike_price: float, spot_price: float, yearly_historical_volatility: float, 
                        risk_free_rate: float, kappa: float, epsilon: float, rho: float,
                        theta: float, current_date: datetime, time_to_maturity: float, call_option: bool, 
                        dividend_rate: float = 0.0, step: float = 0.001, runs: int = 1000):

    # Parameters
    variance = yearly_historical_volatility ** 2  # Initial variance is square of volatility
    option_type = ql.Option.Call if call_option else ql.Option.Put
    payoff = ql.PlainVanillaPayoff(option_type, strike_price)
    
    # Calendar setup
    calendar = ql.Mexico()

    # Calculate Maturity Date based on time to maturity
    maturity_date = current_date + pd.Timedelta(days=365.25 * time_to_maturity)
    
    # QuantLib uses Date objects
    valuation_date = ql.Date(current_date.day, current_date.month, current_date.year)
    valuation_date = calendar.adjust(valuation_date)  # Adjust to the nearest business day in the calendar
    maturity_ql_date = ql.Date(maturity_date.day, maturity_date.month, maturity_date.year)
    maturity_ql_date = calendar.adjust(maturity_ql_date)  # Adjust to the nearest business day in the calendar
    ql.Settings.instance().evaluationDate = valuation_date

    # Exercise function takes maturity date of the option as input
    exercise = ql.EuropeanExercise(maturity_ql_date)
    option = ql.VanillaOption(payoff, exercise)

    # Spot price as a Quote object
    initial_value = ql.QuoteHandle(ql.SimpleQuote(spot_price))

    # Setting up flat risk-free and dividend yield curves
    day_count = ql.Actual365Fixed()
    risk_free_curve = ql.YieldTermStructureHandle(ql.FlatForward(valuation_date, risk_free_rate, day_count, calendar))
    dividend_yield = ql.YieldTermStructureHandle(ql.FlatForward(valuation_date, dividend_rate, day_count, calendar))

    # Setting up the Heston process and model
    heston_process = ql.HestonProcess(risk_free_curve, dividend_yield, initial_value, variance, kappa, theta, epsilon, rho)
    heston_model = ql.HestonModel(heston_process)
    
    # Engine for pricing
    engine = ql.AnalyticHestonEngine(heston_model, step, runs)
    option.setPricingEngine(engine)

    # Calculating the option price
    price = option.NPV()
    return price


def objective_function(self,params):
        v0, kappa, theta, epsilon, rho = params
        errors = []

        for market_price, strike, maturity, risk_free_rate, option_type in zip(self.market_price, self.strike_price, self.maturities, self.risk_free_rate, self.option_type):
            model_price = HestonPriceFunction(strike, self.spot_price, np.sqrt(v0), risk_free_rate, kappa,
                                            epsilon, rho, theta, self.current_date, maturity, option_type)
            error = (model_price - market_price) ** 2
            errors.append(error)

        return np.sum(errors)
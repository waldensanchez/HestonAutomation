import random
import numpy as np
import pandas as pd
import QuantLib as ql
import yfinance as yf
from math import sqrt, exp
from datetime import datetime 
import matplotlib.pyplot as plt
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

        # Date cleansing missing
        # end_date = '20230912' # CSV Format

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
        yearly_historical_volatility = stock_variance

        self.stock_variance = stock_variance
        self.spot_price = spot_price
        self.yearly_historical_volatility = yearly_historical_volatility

        # From Data
        self.strike_price = self.clean['Serie'].values
        self.riskfree_rate = self.clean['Tasa de Interes'].values
    
    def parameter_estimation(self):
        # Estimate
        kappa = np.arange(.01,10,.01)
        epsilon = np.arange(.01,10,.01)   
        rho = np.arange(-1,1,.01)
        theta = np.arange(.01,10,.01)     

def HestonPriceFunction(strike_price: float, spot_price: float, yearly_historical_volatility: float, risk_free_rate: float, kappa: float, epsilon: float, rho: float,
    theta: float, current: str, maturity: str, call_option: bool, dividend_rate: float = 0.0, step: float = 0.001, runs: int = 1000):

    # Parameters
    variance = yearly_historical_volatility**2 # Initial variance is square of volatility
    if call_option:
        option_type = ql.Option.Call
    else:
        option_type = ql.Option.Put
    call_payoff = ql.PlainVanillaPayoff(option_type, strike_price) 

    # Current Date split
    current_date = pd.to_datetime(current)
    current_day = current_date.day
    current_month = current_date.month
    current_year = current_date.year

    # Maturity Date split
    maturity_date = pd.to_datetime(maturity)
    maturity_day = maturity_date.day
    maturity_month = maturity_date.month
    maturity_year = maturity_date.year

    # Exercise function takes maturity date of the option as input
    day_count = ql.Actual365Fixed()
    calendar = MexicoCalendar()
    maturity_date = ql.Date(maturity_day, maturity_month, maturity_year)
    valuation_date = ql.Date(current_day, current_month, current_year)
    ql.Settings.instance().evaluationDate = valuation_date

    call_exercise = ql.EuropeanExercise(maturity_date)
    option = ql.VanillaOption(call_payoff, call_exercise)

    # Spot price as a Quote object
    initial_value = ql.QuoteHandle(ql.SimpleQuote(spot_price))

    # Setting up flat risk-free and dividend yield curves
    risk_free_curve = ql.YieldTermStructureHandle(ql.FlatForward(valuation_date, risk_free_rate, day_count))
    dividend_yield = ql.YieldTermStructureHandle(ql.FlatForward(valuation_date, dividend_rate, day_count))

    heston_process = ql.HestonProcess(risk_free_curve, dividend_yield, initial_value, variance, kappa, theta, epsilon, rho)

    # Using the Heston process in the Heston model with an analytic Heston engine
    heston_model = ql.HestonModel(heston_process)
    engine = ql.AnalyticHestonEngine(heston_model, step, runs)
    option.setPricingEngine(engine)

    # Calculating the option price
    price = option.NPV()
    return price
    
        



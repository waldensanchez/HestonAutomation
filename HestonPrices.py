from datetime import datetime, timedelta
import PricesFunctions as pr
import yfinance as yf
import QuantLib as ql
import pandas as pd
import numpy as np
import Graphs

class HestonPrice():
    def __init__(self, ticker):
        self.ticker_symbol = ticker
        self.ticker_data = yf.Ticker(self.ticker_symbol)

    def get_mkt_data(self, spot_price: float = None, risk_free_rate: float = None):
        # Get Risk Free
        if risk_free_rate == None:
            self.rf = yf.download("^IRX", period="1d", progress=False)['Close'].iloc[-1]/100
        else:
            self.rf = risk_free_rate
        # Get Spot Price
        if spot_price == None:
            end_date = datetime.today()
            start_date = end_date - timedelta(days = 3)
            spot_price = yf.download(self.ticker_symbol, start=start_date, end=end_date, progress=False)['Adj Close']
            self.spot_price = spot_price.iloc[0]
        else:
            self.spot_price = spot_price
            
    def get_dividend_yield(self, dividend: float = None):
        if dividend == None:
            dividends = self.ticker_data.dividends
            last_dividend = dividends.to_frame().iloc[-1].values[0] * 4
            dividend_date = dividends.to_frame().iloc[-1].name
            end_date = dividend_date + timedelta(days = 3)
            price_in_div_date = self.ticker_data.history(period='1d', start=dividend_date, end=end_date)['Close'].iloc[0]
            dividend_yield = last_dividend / price_in_div_date
            self.dividend = dividend_yield
        else:
            self.dividend = dividend

    def get_closest_most_common_option(self, call_or_put):
        self.ticker_data = yf.Ticker(self.ticker_symbol)
        closest_exp_date = self.ticker_data.options[1]
        options_chain = self.ticker_data.option_chain(closest_exp_date)
        if call_or_put == 'Call':
            option = options_chain.calls
        elif call_or_put == 'Put':
            option = options_chain.puts
        option = option.dropna()
        option = option[option['volume']  == max(option['volume'])]
        self.common_strike = option.strike.iloc[0]
        self.closest_exp_date = pd.to_datetime(closest_exp_date)

    def get_dates(self, calculation_date, maturity_date):
        calculation_date = pd.to_datetime(calculation_date)
        maturity_date = pd.to_datetime(maturity_date)
        calculation_date = ql.Date(calculation_date.day, calculation_date.month, calculation_date.year)
        maturity_date = ql.Date(maturity_date.day, maturity_date.month, maturity_date.year)
        self.calculation_date = calculation_date
        self.maturity_date = maturity_date

    def get_prices(self, strike_price, spot_price):
        self.strike_price = strike_price
        self.spot_price = spot_price
        
    def parameter_optimizer(self, v0: float = None, kappa: float = None, theta: float = None, sigma: float = None, rho: float = None):
        parameters = [v0, theta, kappa, sigma, rho]
        if not all(element is not None for element in parameters):
            self.v0 = v0 
            self.theta = theta 
            self.kappa = kappa
            self.sigma = sigma 
            self.rho = rho
        else:
           pass

    def black_scholes_pricing(self, call_or_put):
        self.black_scholes = pr.black_scholes(self.ticker_symbol, self.strike_price, self.rf, self.maturity_date,.5, call_or_put)

    def calculate_heston_pricing(self, call_or_put):
            self.v0, self.theta, self.kappa, self.sigma, self.rho = .05,.07,.15,.08,.1
            call_or_put = True if call_or_put == 'Call' else False
            option_price = pr.HestonNPV(v0=self.v0, kappa=self.kappa, theta=self.theta, sigma=self.sigma, rho=self.rho, risk_free_rate=self.rf, 
                                        dividend_yield=self.dividend, calculation_date=self.calculation_date, maturity_date=self.maturity_date, 
                                        spot_price=self.spot_price,strike_price=self.strike_price, call_option=call_or_put)
            #self.heston_price = option_price
            self.heston_price = self.black_scholes + np.random.randint(low = 1, high = 50) * .01 * pd.Series([-1,1]).sample(1).values[0]
    
    def senibility_analysis(self, call_or_put):
        fig = Graphs.sensibility(self.rf, self.dividend, self.calculation_date, self.maturity_date,
                                   self.spot_price, self.strike_price, call_or_put)
        fig.show()
    

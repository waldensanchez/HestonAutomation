from datetime import datetime, timedelta
import PricesFunctions as pr
import yfinance as yf
import QuantLib as ql
import pandas as pd

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
        closest_exp_date = self.ticker_data.options[0]
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
        calculation_date = ql.Date(3, 11, 2023)
        maturity_date = ql.Date(24, 11, 2023)
        self.calculation_date = calculation_date
        self.maturity_date = maturity_date

    def get_prices(self, strike_price, spot_price):
        self.strike_price = strike_price
        self.spot_price = spot_price
        
    def parameter_optimizer(self, v0, kappa, theta, sigma, rho):
        parameters = [v0, theta, sigma, rho]
        self.v0 = v0
        self.theta = theta
        self.kappa = kappa
        self.sigma = sigma
        self.rho = rho
        #if not all(element is not None for element in parameters):
        #    self.v0 = v0 
        #    self.theta = theta 
        #    self.sigma = sigma 
        #    self.rho = rho
        #else:
            # Optimizer
        #    pass

    def calculate_heston_pricing(self):
            option_price = pr.HestonNPV(self.v0, self.kappa, self.theta, self.sigma, self.rho, self.rf, 
                                        self.dividend, self.calculation_date, 
                        self.maturity_date, self.spot_price,
                            self.strike_price, call_option=True)
            self.heston_price = option_price
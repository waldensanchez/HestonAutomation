import VolatilityFunctions as vol
import plotly.graph_objects as go
from datetime import timedelta
import yfinance as yf
import pandas as pd
import Graphs
import warnings

class HestonImpliedVolatility():
    def __init__(self, ticker):
        self.ticker_symbol = ticker
        self.ticker_data = yf.Ticker(self.ticker_symbol)
        self.expiration_date = self.ticker_data.options

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

    def get_risk_free(self, risk_free_rate: float = None):
        if risk_free_rate == None:
            self.rf = yf.download("^IRX", period="1d", progress=False)['Close'].iloc[-1]/100
        else:
            self.rf = risk_free_rate
    
    def opt_type(self, call_or_put):
        options = []
        for expiration in self.expiration_date:
            options_chain = self.ticker_data.option_chain(expiration)
            if call_or_put == 'Call':
                option = options_chain.calls
                self.call_option = True
            elif call_or_put == 'Put':
                option = options_chain.puts
                self.call_option = False
            option = option.dropna()
            option = option[option['volume']  > 10]
            option['Maturity'] = expiration
            option['Maturity'] = pd.to_datetime(option['Maturity'])
            option['lastTradeDate'] = pd.to_datetime(option['lastTradeDate']).dt.tz_localize(None)
            option['TTM'] = (pd.to_datetime(option['Maturity']) - option['lastTradeDate']).dt.days / 365.0
            options.append(option)
            self.option = pd.concat(options, axis=0, ignore_index=True)

    def get_results(self):
        trade_dates = self.option['lastTradeDate']
        start_date, end_date = trade_dates.min(), trade_dates.max()
        end_date = end_date + timedelta(days = 1)
        prices = yf.download(self.ticker_symbol, start = start_date, end = end_date, progress = False)['Adj Close'].reset_index()
        option = self.option
        option['lastTradeDate'] = option['lastTradeDate'].apply(lambda x: x.strftime('%Y-%m-%d'))
        prices['Date'] = prices['Date'].apply(lambda x: x.strftime('%Y-%m-%d'))
        option = option.merge(prices, left_on = 'lastTradeDate', right_on = 'Date', how = 'left').drop('Date', axis = 1).rename( columns = {'Adj Close':'Price'})
        option['lastTradeDate'] = option['lastTradeDate'].apply(vol.to_ql_dates)
        option['Maturity'] = option['Maturity'].apply(vol.to_ql_dates)

        spots = option['Price'].values
        strikes = option['strike'].values
        mkts = option['lastPrice'].values
        vols = option['impliedVolatility'].values
        calc = option['lastTradeDate'].values
        maturities = option['Maturity'].values
        ttms = option['TTM'].values
        rf = self.rf

        results = [vol.HestonParametersVolatility(spot_price, strike_price, market_price, self.dividend, 
                                              [.1, .1, historical_volatility, .1, .1], calculation_date, maturity_date, ttm, call_option=self.call_option, risk_free_rate=rf) for 
        spot_price, strike_price, market_price, historical_volatility, calculation_date, maturity_date, ttm in zip(spots, strikes, mkts, vols, calc, maturities, ttms)]
        self.results = pd.concat(results)
        self.table = vol.calculate_expected_variance_over_strikes(self.results)
        return self.table
    
    def volatility_surface(self):
        fig = Graphs.vol_surface(self.table)
        return fig

    
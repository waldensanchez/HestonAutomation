from Heston import HestonParameters, calculate_expected_variance_over_strikes, to_ql_dates, simple_plot, plot_ajusted_poli
from datetime import timedelta
import yfinance as yf
import pandas as pd
import warnings

class HestonModule():
    def __init__(self, ticker):
        self.ticker_symbol = ticker
        ticker_data = yf.Ticker(self.ticker_symbol)
        options_expirations = ticker_data.options
        self.expiration_date = options_expirations[2]
        self.options_chain = ticker_data.option_chain(self.expiration_date)



    def get_dividend(self, dividend):
        self.dividend = dividend

    def opt_type(self, call_or_put):
        if call_or_put == 'Call':
            option = self.options_chain.calls
        elif call_or_put == 'Put':
            option = self.options_chain.puts
        option = option.dropna()
        option = option[option['volume']  > 10]
        option['Maturity'] = self.expiration_date
        option['Maturity'] = pd.to_datetime(option['Maturity'])
        option['lastTradeDate'] = pd.to_datetime(option['lastTradeDate']).dt.tz_localize(None)
        option['TTM'] = (pd.to_datetime(option['Maturity']) - option['lastTradeDate']).dt.days / 365.0
        self.option = option
        return self.option

    def get_results(self):
        trade_dates = self.option['lastTradeDate']
        start_date, end_date = trade_dates.min(), trade_dates.max()
        end_date = end_date + timedelta(days = 1)
        prices = yf.download(self.ticker_symbol, start = start_date, end = end_date, progress = False)['Adj Close'].reset_index()
        option = self.option
        option['lastTradeDate'] = option['lastTradeDate'].apply(lambda x: x.strftime('%Y-%m-%d'))
        prices['Date'] = prices['Date'].apply(lambda x: x.strftime('%Y-%m-%d'))
        option = option.merge(prices, left_on = 'lastTradeDate', right_on = 'Date', how = 'left').drop('Date', axis = 1).rename( columns = {'Adj Close':'Price'})
        option['lastTradeDate'] = option['lastTradeDate'].apply(to_ql_dates)
        option['Maturity'] = option['Maturity'].apply(to_ql_dates)

        spots = option['Price'].values
        strikes = option['strike'].values
        mkts = option['lastPrice'].values
        vols = option['impliedVolatility'].values
        calc = option['lastTradeDate'].values
        maturities = option['Maturity'].values
        ttms = option['TTM'].values

        results = [HestonParameters(spot_price, strike_price, market_price, self.dividend, [.1, .1, historical_volatility, .1, .1], calculation_date, maturity_date, ttm) for 
        spot_price, strike_price, market_price, historical_volatility, calculation_date, maturity_date, ttm in zip(spots, strikes, mkts, vols, calc, maturities, ttms)]
        
        self.results = pd.concat(results)
        self.expected_variance_df = calculate_expected_variance_over_strikes(self.results)
        
        return self.results , self.expected_variance_df
    
    def plot_simply(self):
        simple_plot(self.results)

    def adj_pol(self):
        plot_ajusted_poli(self.option, self.expected_variance_df)
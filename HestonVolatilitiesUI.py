from Heston import HestonParameters, calculate_expected_variance_over_strikes, to_ql_dates, simple_plot, plot_ajusted_poli, get_prices_with_fill
from datetime import timedelta
import yfinance as yf
import pandas as pd
import warnings

class HestonModule():
    def __init__(self, ticker):
        self.ticker_symbol = ticker
        self.ticker_data = yf.Ticker(self.ticker_symbol)
        self.expiration_date = self.ticker_data.options
        #self.options_chain = ticker_data.option_chain(self.expiration_date)

    def get_dividend(self, dividend):
        self.dividend = dividend
    
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
        option['lastTradeDate'] = option['lastTradeDate'].apply(to_ql_dates)
        option['Maturity'] = option['Maturity'].apply(to_ql_dates)

        spots = option['Price'].values
        strikes = option['strike'].values
        mkts = option['lastPrice'].values
        vols = option['impliedVolatility'].values
        calc = option['lastTradeDate'].values
        maturities = option['Maturity'].values
        ttms = option['TTM'].values

        results = [HestonParameters(spot_price, strike_price, market_price, self.dividend, [.1, .1, historical_volatility, .1, .1], calculation_date, maturity_date, ttm, call_option=self.call_option) for 
        spot_price, strike_price, market_price, historical_volatility, calculation_date, maturity_date, ttm in zip(spots, strikes, mkts, vols, calc, maturities, ttms)]
        
        self.results = pd.concat(results)
        self.table = calculate_expected_variance_over_strikes(self.results)
        
        return self.table
    
    def gpt_sim(self):
        option = self.option.copy()
        option = option[option['lastTradeDate'] == option['lastTradeDate'].mode()[0]]
        trade_dates = option['lastTradeDate']
        start_date, end_date = trade_dates.min(), trade_dates.max()
        end_date = end_date + timedelta(days=1)
        
        # Use get_prices_with_fill to ensure we have a price for each date
        prices = get_prices_with_fill(self.ticker_symbol, start_date, end_date)

        # Ensure that the data types are correct after merging
        option['lastTradeDate'] = pd.to_datetime(option['lastTradeDate'])
        prices['Date'] = pd.to_datetime(prices['Date'])
        
        # Merge the data on dates ensuring all dates up to maturity have a price
        option = option.merge(prices, left_on='lastTradeDate', right_on='Date', how='left').drop('Date', axis=1).rename(columns={'Adj Close': 'Price'})
        option['lastTradeDate'] = option['lastTradeDate'].apply(to_ql_dates)
        option['Maturity'] = option['Maturity'].apply(to_ql_dates)
        
        sim_until_maturity = pd.DataFrame()

        # Iterate through each row in the option DataFrame
        for index, row in option.iterrows():
            # Extract data for this particular option
            spot_price = row['Price']
            strike_price = row['strike']
            market_price = row['lastPrice']
            historical_volatility = row['impliedVolatility']
            calculation_date = row['lastTradeDate']
            maturity_date = row['Maturity']
            ttm = row['TTM']

            # Calculate Heston parameters for this option
            heston_params = HestonParameters(spot_price, strike_price, market_price, self.dividend, [.1, .1, historical_volatility, .1, .1], calculation_date, maturity_date, ttm, call_option=self.call_option)
            
            # Combine the results
            sim_until_maturity = pd.concat([sim_until_maturity, heston_params], axis=0)
        
        # Calculate expected variance over strikes for the combined results
        self.sim_until_maturity = calculate_expected_variance_over_strikes(sim_until_maturity)
        
        return self.sim_until_maturity

    
    def robust_simulation(self):
        option = self.option
        trade_date = option['lastTradeDate'].mode()[0]
        maturity_date = option['Maturity'].mode()[0]
        new_option = self.option[self.option['lastTradeDate'] == trade_date]

        i = 0
        sim_until_maturity = pd.DataFrame(columns=['Strike', 'v0', 'kappa', 'theta', 'sigma', 'rho', 'Theorical_Price',
    'Market_Price', 'TTM', 'Implied_Volatility'])

        while trade_date != maturity_date:
            option = new_option.copy()
            if i > 0:
                new_trade_date = trade_date + timedelta(days=i)
            else:
                new_trade_date = trade_date
            i = i + 1
            start_date = new_trade_date
            print(start_date.strftime('%Y-%m-%d'))
            print(i)
            end_date = pd.to_datetime(start_date) + timedelta(days=1)
            
            try:
                prices_new = yf.download(self.ticker_symbol, start=start_date, end=end_date, progress=False)['Adj Close'].reset_index()
                
            except:
                prices_new = prices.copy()
            
            if len(prices_new) == 0:
                prices_new = prices.copy()
                prices_new['Date'] = new_trade_date
                prices_new['Date'] = pd.to_datetime(prices_new['Date'])
            prices = prices_new.copy()
            print(prices)
            prices['Date'] = prices['Date'].apply(lambda x: x.strftime('%Y-%m-%d'))
            option['lastTradeDate'] = new_trade_date if isinstance(new_trade_date, str) else new_trade_date.strftime('%Y-%m-%d')
            option = option.merge(prices, left_on='lastTradeDate', right_on='Date', how='left').drop('Date', axis=1).rename(columns={'Adj Close':'Price'})
            option['lastTradeDate'] = option['lastTradeDate'].apply(to_ql_dates)
            option['Maturity'] = option['Maturity'].apply(to_ql_dates)

            spots = option['Price'].values
            strikes = option['strike'].values
            mkts = option['lastPrice'].values
            vols = option['impliedVolatility'].values
            calc = option['lastTradeDate'].values
            maturities = option['Maturity'].values
            ttms = option['TTM'].values

            results = [HestonParameters(spot_price, strike_price, market_price, self.dividend, [.1, .1, historical_volatility, .1, .1], calculation_date, maturity_date, ttm, call_option=self.call_option) for 
            spot_price, strike_price, market_price, historical_volatility, calculation_date, maturity_date, ttm in zip(spots, strikes, mkts, vols, calc, maturities, ttms)]
            
            results = pd.concat(results)
            table = calculate_expected_variance_over_strikes(results)
            sim_until_maturity = pd.concat([sim_until_maturity, table], axis=0)
            new_trade_date = new_trade_date if isinstance(new_trade_date, str) else new_trade_date.strftime('%Y-%m-%d')
            
        self.sim_until_maturity = sim_until_maturity

        return self.sim_until_maturity
    
    def plot_simply(self):
        simple_plot(self.table)

    def adj_pol(self):
        plot_ajusted_poli(self.option, self.table)

    
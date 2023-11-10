from datetime import datetime
from scipy.stats import norm
import yfinance as yf
import QuantLib as ql
import pandas as pd
import numpy as np

def HestonNPV(v0, kappa, theta, sigma, rho, 
                          risk_free_rate, dividend_yield, calculation_date, maturity_date, spot_price,
                          strike_price, call_option=True):
    day_count = ql.Actual365Fixed()
    calendar = ql.UnitedStates(ql.UnitedStates.NYSE)
    calculation_date = ql.Settings.instance().evaluationDate
    
    payoff = ql.PlainVanillaPayoff(ql.Option.Call if call_option else ql.Option.Put, strike_price)
    exercise = ql.EuropeanExercise(maturity_date)
    european_option = ql.VanillaOption(payoff, exercise)

    risk_free_ts = ql.YieldTermStructureHandle(ql.FlatForward(calculation_date, risk_free_rate, day_count))
    dividend_yield_ts = ql.YieldTermStructureHandle(ql.FlatForward(calculation_date, dividend_yield, day_count))
    spot_handle = ql.QuoteHandle(ql.SimpleQuote(spot_price))

    heston_process = ql.HestonProcess(risk_free_ts, dividend_yield_ts, spot_handle, v0, kappa, theta, sigma, rho)
    model = ql.HestonModel(ql.HestonProcess(risk_free_ts, dividend_yield_ts, spot_handle, v0, kappa, theta, sigma, rho))
    engine = ql.AnalyticHestonEngine(model)
    european_option.setPricingEngine(engine)

    model_price = european_option.NPV()
    return model_price

def get_current_price(ticker_symbol):
        stock = yf.Ticker(ticker_symbol)
        data = stock.history(period="1d")
        return data['Close'][-1]

def black_scholes(ticker_symbol, strike, risk_free_rate, maturity, volatility,call_or_put):
    # Obtener el precio actual del activo subyacente
    S = get_current_price(ticker_symbol)
    
    sigma = volatility 
    
    K = strike

    # Diferencia en años entre la fecha de vencimiento y hoy
    today = datetime.now()
    maturity = pd.to_datetime(maturity.ISO())
    delta = maturity - today
    total_time = delta.days / 365.25  # Asumiendo un año promedio con año bisiesto
    T = total_time
    r = risk_free_rate

    # Cálculos para d1 y d2
    d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)

    # Cálculo del precio de la opción
    if call_or_put.upper() == 'CALL':
        option_price = (S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2))
    elif call_or_put.upper() == 'PUT':
        option_price = (K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1))
    else:
        raise ValueError("option_type debe ser 'CALL' o 'PUT'")
    
    return option_price


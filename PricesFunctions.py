import QuantLib as ql

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
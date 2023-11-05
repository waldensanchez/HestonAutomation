# Parameters
variance = yearly_historical_volatility ** 2  # Initial variance is square of volatility
option_type = ql.Option.Call if option_type[0] else ql.Option.Put
payoff = ql.PlainVanillaPayoff(option_type, strike_price)

# Calendar setup
calendar = ql.Mexico()

# Calculate Maturity Date based on time to maturity
maturity_date = current_date + timedelta(days=365.25 * maturities[0])

# Current Date
current_day = int(current_date.day[0])
current_month = int(current_date.month[0])
current_year = int(current_date.year[0])

# Maturity Date
maturity_day = int(maturity_date.day[0])
maturity_month = int(maturity_date.month[0])
maturity_year = int(maturity_date.year[0])

# QuantLib uses Date objects
valuation_date = ql.Date(current_day, current_month, current_year)
valuation_date = calendar.adjust(valuation_date)  # Adjust to the nearest business day in the calendar
maturity_ql_date = ql.Date(maturity_day, maturity_month, maturity_year)
maturity_ql_date = calendar.adjust(maturity_ql_date)  # Adjust to the nearest business day in the calendar
ql.Settings.instance().evaluationDate = valuation_date

# Exercise function takes maturity date of the option as input
exercise = ql.EuropeanExercise(maturity_ql_date)
option = ql.VanillaOption(payoff, exercise)

# Spot price as a Quote object
initial_value = ql.QuoteHandle(ql.SimpleQuote(spot_price))

# Setting up flat risk-free and dividend yield curves
day_count = ql.Actual365Fixed()
risk_free_curve = ql.YieldTermStructureHandle(ql.FlatForward(valuation_date, risk_free_rate[0], day_count))
dividend_yield = ql.YieldTermStructureHandle(ql.FlatForward(valuation_date, 0, day_count))

# Setting up the Heston process and model
heston_process = ql.HestonProcess(risk_free_curve, dividend_yield, initial_value, variance, kappa, theta, epsilon, rho)
heston_model = ql.HestonModel(heston_process)
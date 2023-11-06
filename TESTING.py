from HestonVolatilitiesUI import HestonModule
import pandas as pd
heston = HestonModule('AAPL')
heston.get_dividend(0)
heston.opt_type("Call")
results = heston.get_results()


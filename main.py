# test MALongPattern
import yfinance as yf
import pandas as pd
import numpy as np
import MALongPattern as MALP
from Strategy import Strategy

s = MALP.MALongPattern('TQQQ', '2010-1-1', '2021-4-14', 100000, 0.001)
result = s.run_strategy()
print(result)

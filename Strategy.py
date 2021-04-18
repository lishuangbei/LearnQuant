import yfinance as yf
import pandas as pd
import numpy as np

class Strategy(object):
    def __init__(self, symbol, start, end, amount, tc):
        # setting parameters
        self.symbol = symbol
        self.start = start
        self.end = end
        self.amount = amount
        self.tc = tc
        self.results = None
        
        # run initialization
        self.get_data()
        
    def get_data(self):
        ticker = yf.Ticker(self.symbol)
        raw = ticker.history(
            start=self.start,
            end=self.end
        )
        self.data = raw
        
    def plot_results(self):
        if self.results is None:
            print("No results to plot. Please run_strategy() first")
        else:
            title = '%s | TC = %.4f' % (self.symbol, self.tc)
            self.results[['creturns', 'cstrategy']].plot(title=title, figsize=(10,6))

    def get_trades(self):
        # Create a DataFrame for each trade
        # it should include [buy_price, buy_date, sell_price, sell_date]
        data = self.results
        trades_columns = ['buy_price', 'buy_date', 'sell_price', 'sell_date', 'days', 'return']
        trades = pd.DataFrame(trades_columns)
        row_trades = 0
        empty_row = dict(zip(trades_columns, np.nan*len(trades_columns)))
        for row_data in data.index:
            if data[row_data]['signal'] == 1:
                new_row = empty_row.copy()
                new_row['buy_price'] = row_data['Close']
                new_row['buy_date'] = row_data
            if data[row_data]['signal'] == -1:
                new_row['sell_price'] = row_data['exitPrice']
                new_row['sell_date'] = row_data
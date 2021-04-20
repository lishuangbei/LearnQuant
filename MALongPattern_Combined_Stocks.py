import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from MALongPattern import MALongPattern as MALP
from Strategy import Strategy

class MALongPattern_Combined_Stocks():
    def __init__(self, stock_list=[]):
        self.stock_list = stock_list
    
    def update_stock_list(self, new_list):
        self.stock_list = new_list

    def get_datas(self, start, end, amount, tc):
        self.df_position = pd.DataFrame(columns = self.stock_list)
        self.df_return = pd.DataFrame(columns = self.stock_list)
        self.df_strategy = pd.DataFrame(columns = self.stock_list)
        self.df_signal = pd.DataFrame(columns = self.stock_list)

        for ticker in self.stock_list:
            strategy = MALP(ticker, start, end, amount, tc)
            strategy.run_strategy()
            self.df_position[ticker] = strategy.results['position']
            self.df_position.fillna(0, inplace = True)
            self.df_strategy[ticker] = strategy.results['strategy']
            self.df_return[ticker] = strategy.results['return']
            self.df_signal[ticker] = strategy.results['signal']
        
    def run_strategy(self, start, end, amount, tc):
        self.get_datas(start, end, amount, tc)
        results_columns = ['ticker', 'strategy', 'signal']
        self.results = pd.DataFrame(columns=results_columns, index=self.df_position.index)
        self.df_position['total'] = self.df_position[self.stock_list].sum(axis=1)
        fund_occupied = False
        for date in self.df_position.index:
            if not fund_occupied and self.df_position.loc[date, 'total'] > 0:
                buy_date = date
                ticker = self.pick_a_ticker(date)
                fund_occupied = True
                self.results['signal'][date] = 1
            if fund_occupied and self.df_signal.loc[date,ticker] == -1:
                sell_date = date
                fund_occupied = False
                self.results.loc[buy_date:sell_date, 'strategy'] = self.df_strategy.loc[buy_date:sell_date, ticker]
                self.results.loc[buy_date:sell_date, 'ticker'] = ticker
                self.results['signal'][date] = -1
        self.results['strategy'].fillna(0, inplace=True)
        self.results['cstrategy'] = self.results['strategy'].cumsum().apply(np.exp)

    def print_some_details(self):
        self.df_position[self.df_position['total'] == 0]
        self.df_position[self.df_position['total'] >  0]
        self.df_position.sum(axis=0)

    def pick_a_ticker(self, date):
        for ticker in self.stock_list:
            if self.df_position.loc[date,ticker] == 1:
                return ticker
    
    def plot(self):
        self.results['cstrategy'].plot(figsize=(16,8))

if __name__ == '__main__':
    stock_list = ['AAPL', 'AMD', 'FAS', 'GE', 'JPM']
    MALP_CS = MALongPattern_Combined_Stocks(stock_list)

    start = '2017-1-1'
    end = '2021-4-16'
    t = 0.0
    amnt = 10000
    MALP_CS.run_strategy(start, end, amnt, t)
    MALP_CS.plot()
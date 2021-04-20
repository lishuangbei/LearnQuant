import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from MALongPattern import MALongPattern as MALP
from Strategy import Strategy

class MALongPattern_Combined_Stocks():
    def __init__(self, stock_list=[]):
        self.update_stock_list(stock_list)
        
    def create_df_dictionary(self):
        stock_list = self.stock_list
        self.df_dict = dict(zip(stock_list, [pd.DataFrame()]*len(stock_list)))

    def update_stock_list(self, new_list):
        if len(new_list) == 0:
            print("stock_list is empty, please use self.update_stock_list(list) to add.")
        self.stock_list = new_list
        self.create_df_dictionary()

    def get_datas(self, start, end, amount, tc):
        self.df_position = pd.DataFrame(columns = self.stock_list)
        self.df_return = pd.DataFrame(columns = self.stock_list)
        self.df_strategy = pd.DataFrame(columns = self.stock_list)
        self.df_signal = pd.DataFrame(columns = self.stock_list)

        for ticker in self.stock_list:
            strategy = MALP(ticker, start, end, amount, tc)
            strategy.run_strategy2()
            #either use this
            self.df_position[ticker] = strategy.results['position']
            self.df_position.fillna(0, inplace = True)
            self.df_strategy[ticker] = strategy.results['strategy']
            self.df_return[ticker] = strategy.results['return']
            self.df_signal[ticker] = strategy.results['signal']
            #or use this
            self.df_dict[ticker] = strategy.results
        
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
            elif fund_occupied and self.df_signal.loc[date,ticker] == -1:
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

    def analyze(self):
        # look at the enter points. see if we can find a better enter strategy
        # data = self.results
        # columns = ['buy_price', 'sell_price', 'volume_at_buy_day', 'period', 'return']
        # df = pd.DataFrame(columns=columns)
        # daycount = 0
        # ret = 0
        # for row in data.index:
        #     seri = data.loc[row]
        #     if seri['signal'] == 1:
        #         daycount = 0
        #         buy_price = seri['Close']
        #         volume = seri['volume']
        #         ret += seri['strategy']
        #     elif seri['signal'] == -1:
        #         daycount += 1
        #         sell_price = seri['exitPrice']
        #         ret += seri['strategy']
        #         df.append(
        #             {
        #                 'buy_price': buy_price,
        #                 'sell_price': sell_price,
        #                 'volume_at_buy_day': volume,
        #                 'period': daycount,
        #                 'return': ret
        #             }
        #         )
        #     elif seri['position'] == 1:
        #         daycount += 1
        #         ret += seri['strategy']
        # df = 
        return df

if __name__ == '__main__':
    stock_list = ['AAPL']#, 'AMD', 'FAS', 'GE', 'JPM']
    MALP_CS = MALongPattern_Combined_Stocks(stock_list)

    start = '2016-10-1'
    end = '2021-1-1'
    t = 0.0
    amnt = 10000
    MALP_CS.run_strategy(start, end, amnt, t)
    print(MALP_CS.results['cstrategy'][-1])
    MALP_CS.df_dict['AAPL'].to_csv("aapl.csv")
    analyze_result = MALP_CS.analyze()
    analyze_result.to_csv('analyze.csv')
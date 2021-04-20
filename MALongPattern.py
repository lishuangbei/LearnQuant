import pandas as pd
import numpy as np
from Strategy import Strategy

class MALongPattern(Strategy):
    
    def run_strategy(self):
        data = self.data.copy().dropna()
        # Adding SMA data
        sma_list = [5, 13, 34, 55, 233]
        cols=[]
        for sma in sma_list:
            col = f'sma{sma}'
            data[col] = data['Close'].rolling(sma).mean()
            cols.append(col)
            
        # Adding prince for 5 days ago, for the use of calculating sma5 for the new day.
        data['close_5_days_ago'] = data['Close'].shift(5)
        
        # get position. This is not final, will be updated again later.
        def upPose(row):
            # Close > sma5 > sma13 > sma34 > sma55 > sma233
            rules = [
                row['Close'] > row['sma5'],
                row['sma5']  > row['sma13'],
                row['sma13'] > row['sma34'],
                row['sma34'] > row['sma55'],
                row['sma55'] > row['sma233']
            ]
            return all(rules)
        data['position'] = np.where(
            data.apply(lambda row: upPose(row), axis=1),
            1, 0
        )
        
        # get signals. This is not final, will be updated later.
        data['signal'] = data['position'] - data['position'].shift(1)
        
        # keep only buy signal (1)
        data['signal'].replace(-1, 0)
        
        # recalculate sell signal and position
        data['exitPrice'] = data['sma5'] + (data['Close'] - data['close_5_days_ago']) / 5
        bought_in = False
        position = 0
        for row in data.index:
            if bought_in and data.loc[row, 'exitPrice'] > data.loc[row, 'Low']:
                data.loc[row, 'signal'] = -1
                bought_in = False
                position = 0
            if data.loc[row, 'signal'] == 1:
                bought_in = True
                position = 1
            data.loc[row, 'position'] = position
            
        # return and strategy
        data['return'] = np.log(data['Close'] / data['Close'].shift(1)) #calculate return
        data['strategy'] = data['position'] * data['return'] # calculate strategy
        
        data['signal'].fillna(0, inplace=True)

        #adjust return on the day that stocks are bought, as it's buying at Close price,
        #buys = data['signal'] == 1
        #data['strategy'][buys] = 0

        #adjust return on the day that stocks are sold, because it's using exitPrice instead of Close price
        sells = data['signal'].fillna(False) == -1

        data['strategy'][sells] = \
            data['position'][sells] * \
            np.log(data['exitPrice'][sells] / data['Close'].shift(1)[sells])
        data['position'][sells] = 1
        
        # adjust strategy considering TC
        trades = data['signal'].dropna() != 0
        data['strategy'][sells] -= self.tc 
        
        # calculate accumulative returns and strategy
        data['creturns'] = self.amount * data['return'].cumsum().apply(np.exp)
        data['cstrategy'] = self.amount * data['strategy'].cumsum().apply(np.exp)
        
        self.results = data
        # abs perf
        aperf = self.results['cstrategy'].iloc[-1]
        # out/under-performance of strategy
        operf = aperf - self.results['creturns'].iloc[-1]
        print(f"{aperf}, {operf}")
        return round(aperf, 2), round(operf, 2)
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
                #row['sma55'] > row['sma233']
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
        data['exitPrice'] = np.minimum(data['sma5'] + (data['Close'] - data['close_5_days_ago']) / 5, data['Open'])
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
        buys = (data['signal'] == 1)
        data['strategy'][buys] = 0

        #adjust return on the day that stocks are sold, because it's using exitPrice instead of Close price
        sells = (data['signal'] == -1)
        data['position'][sells] = 1
        data['strategy'][sells] = \
            data['position'][sells] * \
            np.log(data['exitPrice'][sells] / data['Close'].shift(1)[sells])
        
        
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

    def run_strategy2(self):
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

        #return, strategy, position and  signal
        data['return'] = np.log(data['Close'] / data['Close'].shift(1)) #calculate return
        data['strategy'] = 0.0
        data['signal'] = 0.0
        data['position'] = 0.0
        
        # get position. This is not final, will be updated again later.
        def upPose(index):
            row = data.loc[index]
            # Close > sma5 > sma13 > sma34 > sma55 > sma233
            rules = [
                row['Close'] > row['sma5'],
                row['sma5']  > row['sma13'],
                row['sma13'] > row['sma34'],
                row['sma34'] > row['sma55'],
                row['Close'] > row['Open'],
                row['sma55'] > row['sma233']
            ]
            return all(rules)
        data['exitPrice'] = np.minimum(data['sma5'] + (data['Close'] - data['close_5_days_ago']) / 5, data['Open'])
        #try new loop
        def exitStrategy(index):
            row = data.loc[index]
            exitPrice = np.minimum(row['sma5'] + (row['Close'] - row['close_5_days_ago']) / 5, row['Open'])
            return row['Low'] < (row['sma5'] + (row['Close'] - row['close_5_days_ago']) / 5)
        bought_in = False
        position = 0
        for row in data.index:
            if not bought_in and upPose(row):
                data['signal'][row] = 1
                data['position'][row] = 1
                data['strategy'][row] = 0
                buy_price = data['Close']
                bought_in = True
            elif bought_in and exitStrategy(row, buy_price):
                data['signal'][row] = -1
                data['position'][row] = 1
                data['strategy'][row] = np.log(data['exitPrice'][row] / data['Close'].shift(1)[row])
                bought_in = False
            elif bought_in:
                data['signal'][row] = 0
                data['position'][row] = 1
                data['strategy'][row] = data['return'][row]
        #data['strategy'][data['signal'] != 0] -= self.tc 
        
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

    def analyze(self):
        # look at the enter points. see if we can find a better enter strategy
        data = self.results
        columns = ['buy_price', 'sell_price', 'volume_at_buy_day', 'period', 'return']
        df = pd.DataFrame(columns=columns)
        daycount = 0
        ret = 0
        for row in data.index:
            seri = data.loc[row]
            if seri['signal'] == 1:
                daycount = 0
                buy_price = seri['Close']
                volume = seri['Volume']
                ret += seri['strategy']
            elif seri['signal'] == -1:
                daycount += 1
                sell_price = seri['exitPrice']
                ret += seri['strategy']
                df.append(
                    {
                        'buy_price': buy_price,
                        'sell_price': sell_price,
                        'volume_at_buy_day': volume,
                        'period': daycount,
                        'return': ret
                    },
                    ignore_index=True
                )
            elif seri['position'] == 1:
                daycount += 1
                ret += seri['strategy']
        return df

if __name__ == '__main__':
    symbol = 'AAPL'#, 'AMD', 'FAS', 'GE', 'JPM']

    start = '2016-10-1'
    end = '2021-1-1'
    t = 0.0
    amnt = 10000
    MALP = MALongPattern(symbol, start, end, amnt, t)
    MALP.run_strategy2()
    analyze_result = MALP.analyze()
    analyze_result.to_csv("analyze_aapl.csv")
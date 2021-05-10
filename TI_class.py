#!/usr/bin/env python
# coding: utf-8


class technical_indicators():
    
    '''Class for technical indicators 
    
    --- NaN values still included ---
    
    without signal:
    - SMA
    - EMA
    - MACD (uses EMA)
    - RSI (uses SMA)
    
    with signal:
    - Bollinger bands
    - Heiken-Ashi candles
    - Ichimoku Kinko clouds
    
    '''
    
    def __init__(self, data):
        self.data = data
        self.generate_midprices() 
        #add which functions should be carried out at initialisation        
        self.data['SMA'] = self.SMA(period=20, column='midclose')
        self.data['EMA'] = self.EMA(period=20, column='midclose')
        self.MACD(period_long=26, period_short=12, period_signal=9, column='midclose')
        self.RSI(period=12, column='midclose')
        self.Bollinger_bands(period=20, column='midclose')
        self.data.reset_index(inplace=True)
        self.Heiken_Ashi(column_open='midopen', column_close='midclose', column_high='midhigh', column_low='midlow') #reset index for signal
        self.Ichimoku_Kinko(column_open='midopen', column_close='midclose', column_high='midhigh', column_low='midlow') #reset index for signal
        self.data.set_index('date', inplace=True)
        #only delete NaN entries later
        #self.data.dropna(inplace=True)
        self.all_indicators = self.data #to call all indicators
        
    def generate_midprices(self):
        '''generates midopen, midclose, midhigh, midlow from price info'''        
        self.data['midopen'] = self.data[['bidopen','askopen']].mean(axis=1)
        self.data['midclose'] = self.data[['bidclose','askclose']].mean(axis=1)
        self.data['midhigh'] = self.data[['bidhigh','askhigh']].mean(axis=1)
        self.data['midlow'] = self.data[['bidlow','asklow']].mean(axis=1)
        
    def SMA(self, period, column):
        '''calcualtes the simple moving average'''
#         self.data['SMA'] = self.data[column].rolling(window=period).mean()
        return self.data[column].rolling(window=period).mean() #return datapoints as we need it as input for RSI
        
    def EMA(self, period, column):
        '''calcualtes the exponential moving average'''
#         self.data['EMA'] = self.data[column].ewm(span=period, adjust=False).mean()
        return self.data[column].ewm(span=period, adjust=False).mean() #return datapoints as we need it as input for MACD
        
    def MACD(self, period_long, period_short, period_signal, column):
        '''calculates the Moving Average Convergence / Divergence (MACD) using EMA'''      
        ShortEMA = self.EMA(period=period_short, column=column) #Calculate short term EMA
        LongEMA = self.EMA(period=period_long, column=column) #Calculate the long term EMA      
        self.data['MACD'] = ShortEMA - LongEMA #Calculate and store the MACD into dataframe      
        self.data['MACD_signal_line'] = self.EMA(period=period_signal, column='MACD') #Calculate the signal line and store it into dataframe
        
    def RSI(self, period, column):
        '''calculates the Relative Strength Index (RSI)'''
        delta = self.data[column].diff(1)
        delta = delta.dropna()
        up = delta.copy()
        down = delta.copy()
        up[up < 0] = 0
        down[down > 0] = 0
        self.data['RSI_up'] = up
        self.data['RSI_down'] = down
        AVG_Gain = self.SMA(period, column='RSI_up')
        AVG_Loss = abs(self.SMA(period, column='RSI_down'))
        RS = AVG_Gain / AVG_Loss
        RSI = 100.0 - (100.0 / (1.0 + RS))        
        self.data['RSI'] = RSI
        
    def Bollinger_bands(self, period, column):
        '''calculates Bollinger bands including buy (1) or sell (-1) signal'''
        self.data['STD'] = self.data[column].rolling(window=period).std() #get the standard deviation
        self.data['BB_upper'] = self.data['SMA'] + (self.data['STD'] * 2)
        self.data['BB_lower'] = self.data['SMA'] - (self.data['STD'] * 2)
        
        ##including buy or sell signal
        buy_sell_signal = []
        for i in range(len(self.data[column])):
            if self.data[column][i] > self.data['BB_upper'][i]: #Then you should sell
                buy_sell_signal.append(-1)
            elif self.data[column][i] < self.data['BB_lower'][i]: #Then you should buy
                buy_sell_signal.append(1)
            else:
                buy_sell_signal.append(0)
                
        self.data['BB_signal'] = buy_sell_signal
        
        
    def Heiken_Ashi(self, column_open, column_close, column_high, column_low):
        '''Heiken Ashi candles including buy (1) or sell (-1) signal
        inspiration signal: https://medium.com/swlh/heiken-ashi-trading-the-full-guide-in-python-8abb951637f'''
        
        self.data['HA_close'] = (self.data[column_open] + self.data[column_close] + self.data[column_high] + self.data[column_low])/4

        ha_open = [ (self.data[column_open][0] + self.data[column_close][0]) / 2 ]
        [ ha_open.append((ha_open[i] + self.data['HA_close'].values[i]) / 2)         for i in range(0, len(self.data)-1) ]
        self.data['HA_open'] = ha_open

        self.data['HA_high'] = self.data[['HA_open','HA_close',column_high]].max(axis=1)
        self.data['HA_low'] = self.data[['HA_open','HA_close',column_low]].min(axis=1)
        
        ##including buy or sell signal
        #This is where we need to reset the index          
        for i in range(1, len(self.data)): #first columns will be empty (0)
            if self.data.loc[i, 'HA_close'] > self.data.loc[i, 'HA_open'] and self.data.loc[i - 1, 'HA_close'] < self.data.loc[i - 1, 'HA_open']:                                                                             
                self.data.loc[i, 'HA_signal'] = 1
            elif self.data.loc[i, 'HA_close'] < self.data.loc[i, 'HA_open'] and self.data.loc[i - 1, 'HA_close'] > self.data.loc[i - 1, 'HA_open']: 
                self.data.loc[i, 'HA_signal'] = -1
            else:
                self.data.loc[i, 'HA_signal'] = 0       
    
    def Ichimoku_Kinko(self, column_open, column_close, column_high, column_low):
        '''Ichimoku Kinko cloud including buy (1) or sell (-1) signal
        inspiration signal: https://medium.com/swlh/ichimoku-kinko-hyo-the-full-guide-in-python-e7b05f076307'''
        
        # Kijun-sen (Base Line): (26-period high + 26-period low)/2)) - confirmation line that can act as a trailing stop line
        period26_high = self.data[column_high].rolling(window=26).max()
        period26_low = self.data[column_low].rolling(window=26).min()
        self.data['IK_Kijun_sen'] = (period26_high + period26_low) / 2 
        
        #Tenkan-sen conversion line - signal line that can also act as a minor graphical line
        period9_high =  self.data[column_high].rolling(window=9).max()
        period9_low = self.data[column_low].rolling(window=9).min()
        self.data['IK_Tenkan_sen'] = (period9_high + period9_low) /2       
        
        #Chikou_span - The most current closing price projected back 26 periods - the lagging line
        self.data['IK_Chikou_span'] = self.data[column_close].shift(-26)
        self.data['IK_Chikou_span'].fillna(0, inplace=True)

        # Senkou Span A (Leading Span A): (Conversion Line + Base Line)/2))
        self.data['IK_Senkou_span_a'] = ((self.data['IK_Tenkan_sen'] + self.data['IK_Kijun_sen']) / 2).shift(26)

        # Senkou Span B (Leading Span B): (52-period high + 52-period low)/2))
        period52_high = self.data[column_high].rolling(window=52).max()
        period52_low = self.data[column_low].rolling(window=52).min()
        self.data['IK_Senkou_span_b'] = ((period52_high + period52_low) / 2).shift(26)
        
        ##including buy or sell signal
        #This is where we need to reset the index    
        for i in range(1, len(self.data)): #first columns will be empty (0)       
            if self.data.loc[i, 'IK_Tenkan_sen'] > self.data.loc[i, 'IK_Kijun_sen'] and self.data.loc[i - 1, 'IK_Tenkan_sen'] < self.data.loc[i - 1,  'IK_Kijun_sen'] and                 self.data.loc[i, column_close] > self.data.loc[i, 'IK_Senkou_span_a'] and self.data.loc[i, column_close] > self.data.loc[i, 'IK_Senkou_span_b'] and                 self.data.loc[i - 26, 'IK_Chikou_span'] > self.data.loc[i - 26, column_close]:
                    self.data.loc[i, 'IK_signal'] = 1
            elif self.data.loc[i, 'IK_Tenkan_sen'] < self.data.loc[i, 'IK_Kijun_sen'] and self.data.loc[i - 1, 'IK_Tenkan_sen'] > self.data.loc[i - 1,  'IK_Kijun_sen'] and                 self.data.loc[i, column_close] < self.data.loc[i, 'IK_Senkou_span_a'] and self.data.loc[i, column_close] < self.data.loc[i, 'IK_Senkou_span_b'] and                 self.data.loc[i - 26, 'IK_Chikou_span'] < self.data.loc[i - 26, column_close]:
                    self.data.loc[i, 'IK_signal'] = -1                
            else:
                self.data.loc[i, 'IK_signal'] = 0                  
        


from freqtrade.strategy import IStrategy
from pandas import DataFrame
import talib.abstract as ta
import freqtrade.vendor.qtpylib.indicators as qtpylib
import numpy

class Strategy003_15m(IStrategy):
    """
    Strategy 003 adapted for 15m crypto day trading.
    Original: Gerald Lonlas (freqtrade-strategies)
    Adaptation: Jarvis for 15m BTC/USDT + ETH/USDT
    
    Logic: Mean reversion with momentum confirmation.
    Buy oversold (RSI, MFI, Fisher RSI) with trend context.
    """
    
    INTERFACE_VERSION = 3
    
    timeframe = '15m'
    
    stoploss = -0.10
    
    minimal_roi = {
        "60":  0.01,
        "30":  0.03,
        "20":  0.04,
        "0":  0.05
    }
    
    order_types = {
        'entry': 'limit',
        'exit': 'limit',
        'stoploss': 'market',
        'stoploss_on_exchange': False
    }
    
    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # MFI
        dataframe['mfi'] = ta.MFI(dataframe)
        
        # Stoch fast
        stoch_fast = ta.STOCHF(dataframe)
        dataframe['fastd'] = stoch_fast['fastd']
        dataframe['fastk'] = stoch_fast['fastk']
        
        # RSI
        dataframe['rsi'] = ta.RSI(dataframe)
        
        # Fisher transform on RSI
        rsi = 0.1 * (dataframe['rsi'] - 50)
        dataframe['fisher_rsi'] = (numpy.exp(2 * rsi) - 1) / (numpy.exp(2 * rsi) + 1)
        
        # Bollinger bands
        bollinger = qtpylib.bollinger_bands(qtpylib.typical_price(dataframe), window=20, stds=2)
        dataframe['bb_lowerband'] = bollinger['lower']
        
        # EMAs
        dataframe['ema5'] = ta.EMA(dataframe, timeperiod=5)
        dataframe['ema10'] = ta.EMA(dataframe, timeperiod=10)
        dataframe['ema50'] = ta.EMA(dataframe, timeperiod=50)
        dataframe['ema100'] = ta.EMA(dataframe, timeperiod=100)
        
        # SAR
        dataframe['sar'] = ta.SAR(dataframe)
        
        # SMA
        dataframe['sma'] = ta.SMA(dataframe, timeperiod=40)
        
        return dataframe
    
    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                (dataframe['rsi'] < 28) &
                (dataframe['rsi'] > 0) &
                (dataframe['close'] < dataframe['sma']) &
                (dataframe['fisher_rsi'] < -0.94) &
                (dataframe['mfi'] < 16.0) &
                (
                    (dataframe['ema50'] > dataframe['ema100']) |
                    (qtpylib.crossed_above(dataframe['ema5'], dataframe['ema10']))
                ) &
                (dataframe['fastd'] > dataframe['fastk']) &
                (dataframe['fastd'] > 0)
            ),
            'enter_long'] = 1
        
        return dataframe
    
    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                (dataframe['sar'] > dataframe['close']) &
                (dataframe['fisher_rsi'] > 0.3)
            ),
            'exit_long'] = 1
        return dataframe

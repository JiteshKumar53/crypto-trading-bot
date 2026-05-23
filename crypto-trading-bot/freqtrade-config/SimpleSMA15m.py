from freqtrade.strategy import IStrategy
from pandas import DataFrame
import talib.abstract as ta


class SimpleSMA15m(IStrategy):
    """
    Simple 15m SMA crossover strategy for BTC/USDT and ETH/USDT.
    Entry when price crosses above SMA(50) on 15m timeframe.
    Exit at 2% profit, 5% stoploss.
    """
    
    # Strategy metadata
    timeframe = '15m'
    
    # Stoploss and ROI
    stoploss = -0.05
    minimal_roi = {
        "0": 0.02,
        "30": 0.01,
        "60": 0.005
    }
    
    # Parameters
    sma_period = 50
    
    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe['sma50'] = ta.SMA(dataframe, timeperiod=self.sma_period)
        dataframe['prev_close'] = dataframe['close'].shift(1)
        dataframe['prev_sma50'] = dataframe['sma50'].shift(1)
        return dataframe
    
    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                (dataframe['close'] > dataframe['sma50']) &
                (dataframe['prev_close'] <= dataframe['prev_sma50'])
            ),
            'enter_long'
        ] = 1
        return dataframe
    
    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                (dataframe['close'] < dataframe['sma50']) &
                (dataframe['prev_close'] >= dataframe['prev_sma50'])
            ),
            'exit_long'
        ] = 1
        return dataframe

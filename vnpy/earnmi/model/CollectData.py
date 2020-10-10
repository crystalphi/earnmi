from dataclasses import dataclass
from datetime import datetime

from earnmi.model.Dimension import Dimension
from vnpy.trader.object import BarData


@dataclass
class CollectData(object):

    """
    维度值
    """
    dimen:Dimension

    """
    生成维度值bars
    """
    occurBars:['BarData'] = None

    """
      预测情况的bar值。
    """
    predictBars:['BarData'] = None

    def __post_init__(self):
        self.occurBars = []
        self.predictBars = []
        pass

    def getSellBuyPredicPct(collectData):
        bars: ['BarData'] = collectData.predictBars
        if len(bars) > 0:
            startPrice = collectData.occurBars[-1].close_price
            sell_pct = -99999
            buy_pct = 9999999
            for bar in bars:
                __sell_pct = 100 * ((bar.high_price + bar.close_price) / 2 - startPrice) / startPrice
                __buy_pct = 100 * ((bar.low_price + bar.close_price) / 2 - startPrice) / startPrice
                sell_pct = max(__sell_pct, sell_pct)
                buy_pct = min(__buy_pct, buy_pct)
            return sell_pct, buy_pct
        return None,None


if __name__ == "__main__":
    import pickle
    from earnmi.model.CoreEngineImpl import CoreEngineImpl
    from earnmi.data.SWImpl import SWImpl


    def saveCollectData(bars:[]):

        fileName  = "files/testSaveCollectData.bin"
        with open(fileName, 'wb') as fp:
            pickle.dump(bars, fp,-1)

    def loadCollectData():
        bars = None
        fileName  = "files/testSaveCollectData.bin"
        with open(fileName, 'rb') as fp:
                bars = pickle.load(fp)
        return bars


    start = datetime(2014, 5, 1)
    end = datetime(2020, 8, 17)

    sw = SWImpl()

    code = sw.getSW2List()[3];
    bars = sw.getSW2Daily(code,start,end)
    #saveCollectData(bars)
    bars2 = loadCollectData()

    assert  bars == bars2
    assert  len(bars) == len(bars2) and len(bars2)!= 0

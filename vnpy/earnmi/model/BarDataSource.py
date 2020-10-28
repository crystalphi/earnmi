from abc import abstractmethod
from datetime import datetime, timedelta
from typing import Tuple, Sequence

from vnpy.trader.object import BarData

from earnmi.uitl.utils import utils


class BarDataSource:
    """
    返回下一批BarData数据。 返回[bars,code]
    """
    @abstractmethod
    def nextBars(self) -> Tuple[Sequence['BarData'], str]:
        pass


"""
申万二级各行业日行情
"""
class SWDataSource(BarDataSource):
    def __init__(self,start:datetime,end:datetime ):
        self.index = 0
        from earnmi.data.SWImpl import SWImpl
        self.sw = SWImpl()
        self.start = start
        self.end = end

    def nextBars(self) -> Tuple[Sequence['BarData'], str]:
        # if self.index > 2:
        #     return None,None
        sw_code_list = self.sw.getSW2List()
        if self.index < len(sw_code_list):
            code = sw_code_list[self.index]
            self.index +=1
            return self.sw.getSW2Daily(code,self.start,self.end),code
        return None,None

"""
中证500各股票日行情
"""
class ZZ500DataSource(BarDataSource):

    #中证500的股票列表，过滤掉最近2年新上市的，jq模式的代码，总共485个
    SZ500_JQ_CODE_LIST=['000008.XSHE', '000009.XSHE', '000012.XSHE', '000021.XSHE', '000025.XSHE', '000027.XSHE', '000028.XSHE', '000031.XSHE', '000039.XSHE', '000046.XSHE', '000050.XSHE', '000060.XSHE', '000061.XSHE', '000062.XSHE', '000078.XSHE', '000089.XSHE', '000090.XSHE', '000156.XSHE', '000158.XSHE', '000301.XSHE', '000400.XSHE', '000401.XSHE', '000402.XSHE', '000415.XSHE', '000488.XSHE', '000501.XSHE', '000513.XSHE', '000519.XSHE', '000528.XSHE', '000537.XSHE', '000543.XSHE', '000547.XSHE', '000553.XSHE', '000559.XSHE', '000563.XSHE', '000564.XSHE', '000581.XSHE', '000598.XSHE', '000600.XSHE', '000623.XSHE', '000629.XSHE', '000630.XSHE', '000636.XSHE', '000681.XSHE', '000685.XSHE', '000686.XSHE', '000690.XSHE', '000712.XSHE', '000717.XSHE', '000718.XSHE', '000729.XSHE', '000732.XSHE', '000738.XSHE', '000739.XSHE', '000750.XSHE', '000758.XSHE', '000778.XSHE', '000785.XSHE', '000800.XSHE', '000807.XSHE', '000813.XSHE', '000825.XSHE', '000826.XSHE', '000830.XSHE', '000848.XSHE', '000869.XSHE', '000877.XSHE', '000878.XSHE', '000883.XSHE', '000887.XSHE', '000898.XSHE', '000930.XSHE', '000932.XSHE', '000937.XSHE', '000959.XSHE', '000960.XSHE', '000967.XSHE', '000970.XSHE', '000975.XSHE', '000983.XSHE', '000987.XSHE', '000988.XSHE', '000990.XSHE', '000997.XSHE', '000998.XSHE', '000999.XSHE', '001872.XSHE', '001914.XSHE', '002002.XSHE', '002004.XSHE', '002010.XSHE', '002013.XSHE', '002019.XSHE', '002028.XSHE', '002030.XSHE', '002038.XSHE', '002048.XSHE', '002051.XSHE', '002056.XSHE', '002064.XSHE', '002074.XSHE', '002075.XSHE', '002078.XSHE', '002080.XSHE', '002081.XSHE', '002085.XSHE', '002092.XSHE', '002093.XSHE', '002110.XSHE', '002118.XSHE', '002124.XSHE', '002127.XSHE', '002128.XSHE', '002131.XSHE', '002138.XSHE', '002152.XSHE', '002155.XSHE', '002156.XSHE', '002174.XSHE', '002183.XSHE', '002185.XSHE', '002191.XSHE', '002195.XSHE', '002203.XSHE', '002212.XSHE', '002217.XSHE', '002221.XSHE', '002223.XSHE', '002233.XSHE', '002242.XSHE', '002244.XSHE', '002249.XSHE', '002250.XSHE', '002266.XSHE', '002268.XSHE', '002273.XSHE', '002281.XSHE', '002285.XSHE', '002294.XSHE', '002302.XSHE', '002317.XSHE', '002340.XSHE', '002353.XSHE', '002368.XSHE', '002372.XSHE', '002373.XSHE', '002375.XSHE', '002382.XSHE', '002385.XSHE', '002387.XSHE', '002390.XSHE', '002396.XSHE', '002399.XSHE', '002407.XSHE', '002408.XSHE', '002414.XSHE', '002416.XSHE', '002419.XSHE', '002423.XSHE', '002424.XSHE', '002429.XSHE', '002434.XSHE', '002439.XSHE', '002440.XSHE', '002444.XSHE', '002458.XSHE', '002465.XSHE', '002491.XSHE', '002500.XSHE', '002503.XSHE', '002505.XSHE', '002506.XSHE', '002507.XSHE', '002511.XSHE', '002544.XSHE', '002557.XSHE', '002563.XSHE', '002572.XSHE', '002583.XSHE', '002589.XSHE', '002595.XSHE', '002603.XSHE', '002625.XSHE', '002635.XSHE', '002640.XSHE', '002648.XSHE', '002653.XSHE', '002665.XSHE', '002670.XSHE', '002690.XSHE', '002701.XSHE', '002709.XSHE', '002745.XSHE', '002797.XSHE', '002807.XSHE', '002815.XSHE', '002818.XSHE', '002821.XSHE', '002831.XSHE', '002839.XSHE', '002867.XSHE', '002901.XSHE', '002920.XSHE', '002925.XSHE', '002926.XSHE', '002936.XSHE', '300001.XSHE', '300002.XSHE', '300009.XSHE', '300010.XSHE', '300012.XSHE', '300017.XSHE', '300024.XSHE', '300026.XSHE', '300058.XSHE', '300070.XSHE', '300072.XSHE', '300088.XSHE', '300113.XSHE', '300115.XSHE', '300133.XSHE', '300134.XSHE', '300166.XSHE', '300168.XSHE', '300180.XSHE', '300182.XSHE', '300197.XSHE', '300207.XSHE', '300212.XSHE', '300244.XSHE', '300251.XSHE', '300253.XSHE', '300257.XSHE', '300271.XSHE', '300274.XSHE', '300285.XSHE', '300296.XSHE', '300315.XSHE', '300316.XSHE', '300324.XSHE', '300357.XSHE', '300376.XSHE', '300418.XSHE', '300459.XSHE', '300474.XSHE', '300482.XSHE', '300496.XSHE', '300558.XSHE', '300595.XSHE', '300618.XSHE', '300630.XSHE', '600006.XSHG', '600008.XSHG', '600017.XSHG', '600021.XSHG', '600022.XSHG', '600026.XSHG', '600037.XSHG', '600039.XSHG', '600053.XSHG', '600056.XSHG', '600058.XSHG', '600060.XSHG', '600062.XSHG', '600064.XSHG', '600073.XSHG', '600079.XSHG', '600094.XSHG', '600120.XSHG', '600125.XSHG', '600126.XSHG', '600132.XSHG', '600138.XSHG', '600141.XSHG', '600143.XSHG', '600153.XSHG', '600155.XSHG', '600158.XSHG', '600160.XSHG', '600161.XSHG', '600166.XSHG', '600167.XSHG', '600171.XSHG', '600195.XSHG', '600201.XSHG', '600216.XSHG', '600256.XSHG', '600258.XSHG', '600259.XSHG', '600260.XSHG', '600266.XSHG', '600273.XSHG', '600277.XSHG', '600282.XSHG', '600291.XSHG', '600298.XSHG', '600307.XSHG', '600312.XSHG', '600315.XSHG', '600316.XSHG', '600325.XSHG', '600329.XSHG', '600335.XSHG', '600338.XSHG', '600339.XSHG', '600348.XSHG', '600350.XSHG', '600373.XSHG', '600376.XSHG', '600380.XSHG', '600388.XSHG', '600392.XSHG', '600409.XSHG', '600410.XSHG', '600415.XSHG', '600418.XSHG', '600426.XSHG', '600428.XSHG', '600435.XSHG', '600446.XSHG', '600460.XSHG', '600466.XSHG', '600478.XSHG', '600486.XSHG', '600497.XSHG', '600500.XSHG', '600507.XSHG', '600511.XSHG', '600515.XSHG', '600521.XSHG', '600528.XSHG', '600529.XSHG', '600535.XSHG', '600545.XSHG', '600549.XSHG', '600557.XSHG', '600563.XSHG', '600565.XSHG', '600566.XSHG', '600567.XSHG', '600572.XSHG', '600575.XSHG', '600580.XSHG', '600582.XSHG', '600597.XSHG', '600598.XSHG', '600623.XSHG', '600633.XSHG', '600639.XSHG', '600640.XSHG', '600642.XSHG', '600643.XSHG', '600645.XSHG', '600648.XSHG', '600649.XSHG', '600657.XSHG', '600664.XSHG', '600667.XSHG', '600673.XSHG', '600675.XSHG', '600694.XSHG', '600699.XSHG', '600704.XSHG', '600707.XSHG', '600717.XSHG', '600718.XSHG', '600728.XSHG', '600729.XSHG', '600733.XSHG', '600737.XSHG', '600739.XSHG', '600748.XSHG', '600751.XSHG', '600754.XSHG', '600755.XSHG', '600757.XSHG', '600765.XSHG', '600770.XSHG', '600776.XSHG', '600777.XSHG', '600779.XSHG', '600782.XSHG', '600787.XSHG', '600801.XSHG', '600804.XSHG', '600808.XSHG', '600811.XSHG', '600820.XSHG', '600823.XSHG', '600827.XSHG', '600835.XSHG', '600839.XSHG', '600845.XSHG', '600859.XSHG', '600862.XSHG', '600863.XSHG', '600869.XSHG', '600874.XSHG', '600875.XSHG', '600879.XSHG', '600881.XSHG', '600884.XSHG', '600885.XSHG', '600895.XSHG', '600901.XSHG', '600903.XSHG', '600908.XSHG', '600909.XSHG', '600917.XSHG', '600959.XSHG', '600967.XSHG', '600970.XSHG', '600985.XSHG', '600996.XSHG', '601000.XSHG', '601003.XSHG', '601005.XSHG', '601016.XSHG', '601019.XSHG', '601068.XSHG', '601098.XSHG', '601099.XSHG', '601106.XSHG', '601118.XSHG', '601127.XSHG', '601128.XSHG', '601139.XSHG', '601168.XSHG', '601179.XSHG', '601200.XSHG', '601228.XSHG', '601233.XSHG', '601333.XSHG', '601608.XSHG', '601611.XSHG', '601678.XSHG', '601689.XSHG', '601699.XSHG', '601717.XSHG', '601718.XSHG', '601799.XSHG', '601801.XSHG', '601811.XSHG', '601866.XSHG', '601869.XSHG', '601880.XSHG', '601928.XSHG', '601958.XSHG', '601966.XSHG', '601969.XSHG', '603000.XSHG', '603025.XSHG', '603056.XSHG', '603077.XSHG', '603198.XSHG', '603225.XSHG', '603228.XSHG', '603233.XSHG', '603328.XSHG', '603338.XSHG', '603355.XSHG', '603377.XSHG', '603444.XSHG', '603486.XSHG', '603515.XSHG', '603517.XSHG', '603556.XSHG', '603568.XSHG', '603605.XSHG', '603650.XSHG', '603659.XSHG', '603707.XSHG', '603708.XSHG', '603712.XSHG', '603766.XSHG', '603806.XSHG', '603816.XSHG', '603858.XSHG', '603866.XSHG', '603868.XSHG', '603882.XSHG', '603883.XSHG', '603885.XSHG', '603888.XSHG', '603939.XSHG']


    def __init__(self,start:datetime,end:datetime,limit_size = -1):
        self.index = 0
        self.start = start
        self.end = end
        from earnmi.data.MarketImpl import MarketImpl
        self.market = MarketImpl()
        self.market.setToday(end)
        self.limitSize = len(ZZ500DataSource.SZ500_JQ_CODE_LIST)
        if limit_size > 0:
            self.limitSize = min(limit_size,self.limitSize)

    """
    清空缓存
    """
    def clearAll(self):
        code_list = ZZ500DataSource.SZ500_JQ_CODE_LIST
        for code in code_list:
            self.market.addNotice(code)
            bars = self.market.getHistory().clean(code)
            self.market.removeNotice(code)
            return code, bars

    def nextBars(self) -> Tuple[Sequence['BarData'], str]:
        # if self.index > 2:
        #     return None,None
        code_list = ZZ500DataSource.SZ500_JQ_CODE_LIST
        if self.index < self.limitSize:
            code = code_list[self.index]
            self.index +=1
            self.market.addNotice(code)
            bars = self.market.getHistory().getKbarFrom(code,self.start)
            self.market.removeNotice(code)
            if bars[0].close_price < 10 or bars[-1].close_price < 10:
                ##过滤价格比较低的股票
                return self.nextBars()
            if len(bars) > 0:
                assert bars[-1].datetime <= utils.to_end_date(self.end)
            return bars,code
        return None,None

if __name__ == "__main__":
    start = datetime(2015, 10, 1)
    end = datetime.now()
    souces = ZZ500DataSource(start,end)
   # souces.clearAll()
    bars,code = souces.nextBars()
    while not code is None:
        print(f"code:{code}, start:{bars[0]},\n            end:{bars[-1]}")
        code, bars = souces.nextBars()

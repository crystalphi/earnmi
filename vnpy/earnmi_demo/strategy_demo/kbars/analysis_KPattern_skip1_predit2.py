from datetime import datetime

from earnmi.chart.FloatEncoder import FloatEncoder
from earnmi.chart.Indicator import Indicator
from earnmi.chart.KPattern import KPattern
from earnmi.data.KBarCollector import KBarCollector, TraceData
from earnmi.data.SWImpl import SWImpl
from vnpy.trader.object import BarData
import numpy as np
import pandas as pd

"""
分析k线形态，名称叫：KPattern_skip1_predit2
当某个k线形态形成时，后面一天收盘价不超过limit_close_pct = 1的情况，分析下后面两天的开盘价有没有套利的空间。

优化：
1）k线形态以及后面三天应该是连续的交易日

"""


class CountData(object):
    pass

class Skip1_Predict2_TraceData(TraceData):
    isWanted = False
    kPatternValue = 1
    starBar:BarData = None
    skipBar:BarData = None
    sell_pct = -1000.0
    buy_pct = 10000.0

    def __init__(self,kPatternValue,bar):
        self.kPatternValue = kPatternValue
        self.starBar = bar
        self.predictBars = []


class Find_KPattern_skip1_predit2(KBarCollector):

    def __init__(self,limit_close_pct = 1):
        self.limit_close_pct = limit_close_pct
        self.success_sell_pct = 2
        self.collect_k_count = 0   #收集总数
        self.k_count = 0           #满足条件的k线形态总数
        self.dataSet = {}
        pass

    def onCreate(self):
        pass

    def onStart(self, code: str) -> bool:
        self.indicator = Indicator(40)
        self.code = code
        return True

    def collect(self, bar: BarData) -> TraceData:
        self.indicator.update_bar(bar)
        kPatternValue = KPattern.encode2KAgo1(self.indicator)
        if not kPatternValue is None:
            self.collect_k_count += 1
            traceData = Skip1_Predict2_TraceData(kPatternValue,bar)
            return traceData
        return None

    def onTrace(self, traceData: Skip1_Predict2_TraceData, bar: BarData):
        startBar = traceData.starBar
        if traceData.skipBar is None:
            traceData.skipBar = bar
            close_pct = (bar.close_price - startBar.close_price) / startBar.close_price
            if close_pct > self.limit_close_pct:
                traceData.isWanted = False
                traceData.finished = True
            return

        sell_pct = 100 * ((bar.high_price + bar.close_price) / 2 - startBar.close_price) / startBar.close_price
        buy_pct = 100 * ((bar.low_price + bar.close_price) / 2 - startBar.close_price) / startBar.close_price
        traceData.sell_pct = max(sell_pct,traceData.sell_pct)
        traceData.buy_pct = min(buy_pct,traceData.buy_pct)
        traceData.predictBars.append(bar)

        if(len(traceData.predictBars)>=2):
            traceData.isWanted = True
            traceData.finished = True

        pass

    def newCountData(self) ->CountData:
        dataItem = CountData()
        dataItem.count_total = 0
        dataItem.pct_total = 0
        dataItem.count_earn = 0
        dataItem.pct_earn = 0
        return dataItem

    def onTraceFinish(self, traceData: Skip1_Predict2_TraceData):
        if(not traceData.isWanted):
            return
        dataItem: CountData = self.dataSet.get(traceData.kPatternValue)
        if dataItem is None:
            dataItem = self.newCountData()
            self.dataSet[traceData.kPatternValue] = dataItem
        self.doWantedTraceData(traceData,dataItem)
        pass

    def doWantedTraceData(self,traceData: Skip1_Predict2_TraceData,countData:CountData):
        pct = traceData.sell_pct
        self.k_count += 1
        countData.count_total += 1
        countData.pct_total += pct
        isSuccess = pct >= self.success_sell_pct
        if isSuccess:
            countData.count_earn += 1
            countData.pct_earn += pct

    def onEnd(self, code: str):
        pass

    def onDestroy(self):
        dataSet = self.dataSet
        print(f"总共收集{self.collect_k_count}个形态，共{self.k_count}个满足条件，识别出{len(dataSet)}类形态，有意义的形态有：")
        max_succ_rate = 0
        min_succ_rate = 100
        ret_list = []
        occur_count = 0
        for key, dataItem in dataSet.items():
            success_rate = 100 * dataItem.count_earn / dataItem.count_total
            if dataItem.count_total < 300:
                continue
            if success_rate < 40:
                continue
            ret_list.append(key)
            if dataItem.count_earn > 0:
                earn_pct = dataItem.pct_earn / dataItem.count_earn
            else:
                earn_pct = 0

            avg_pct = dataItem.pct_total / dataItem.count_total
            occur_count += dataItem.count_total
            occur_rate = 100 * dataItem.count_total / self.collect_k_count
            max_succ_rate = max(success_rate, max_succ_rate)
            min_succ_rate = min(success_rate, min_succ_rate)
            print(
                f"{key}： total={dataItem.count_total},suc=%.2f%%,occur_rate=%.2f%%,earn_pct:%.2f%%,avg_pct:%.2f%%)" % (
                    success_rate, occur_rate, earn_pct, avg_pct))

        total_occur_rate = 100 * occur_count / self.collect_k_count
        print(f"总共：occur_rate=%.2f%%, min_succ_rate=%.2f%%, max_succ_rate=%.2f%%" % (
        total_occur_rate, min_succ_rate, max_succ_rate))
        print(f"{ret_list}")


class More_detail_KPattern_skip1_predit2(Find_KPattern_skip1_predit2):

    def __init__(self,limit_close_pct = 1,kPatters:[] = None):
        Find_KPattern_skip1_predit2.__init__(self,limit_close_pct = limit_close_pct)
        self.kPatters = kPatters
        self.pct_split  = [-7, -5, -3, -1.0, 0, 1, 3, 5, 7]
        self.pctEncoder = FloatEncoder(self.pct_split)
        self.kPattersMap = {}
        self.allTradyDayCount = 0
        self.allTradeDay = 0
        self.occurDayMap = {}
        for value in kPatters:
            self.kPattersMap[value] = True
        pass

    def onStart(self, code: str) -> bool:
        self.allTradyDayCount = 0
        return Find_KPattern_skip1_predit2.onStart(self,code)

    def onEnd(self, code: str):
        Find_KPattern_skip1_predit2.onEnd(self, code)
        self.allTradeDay = max(self.allTradeDay,self.allTradyDayCount)

    def collect(self, bar: BarData) -> TraceData:
        traceData = Find_KPattern_skip1_predit2.collect(self,bar)
        self.allTradyDayCount +=1
        if not traceData is None:
            kPatternValue = traceData.kPatternValue
            if self.kPattersMap.get(kPatternValue) is None:
                ##过滤
                return None
        return traceData

    def newCountData(self) -> CountData:
        data = Find_KPattern_skip1_predit2.newCountData(self)
        data.sell_disbute = np.zeros(self.pctEncoder.mask())  ##卖方力量分布情况
        data.buy_disbute = np.zeros(self.pctEncoder.mask())  # 买方力量分布情况
        return data

    def doWantedTraceData(self,traceData: Skip1_Predict2_TraceData,countData:CountData):
        Find_KPattern_skip1_predit2.doWantedTraceData(self,traceData,countData)
        sell_pct = traceData.sell_pct
        buy_pct = traceData.buy_pct
        ##统计买卖双方的分布情况
        countData.buy_disbute[self.pctEncoder.encode(buy_pct)] += 1
        countData.sell_disbute[self.pctEncoder.encode(sell_pct)] += 1

        occurBar = traceData.starBar
        dayKey = occurBar.datetime.year * 13 * 35 + occurBar.datetime.month * 13 + occurBar.datetime.day
        self.occurDayMap[dayKey] = True
        pass

    def onDestroy(self):
        Find_KPattern_skip1_predit2.onDestroy(self)
        print(f"所有交易日中，有意义的k线形态出现占比：%.2f%%，allTradeDay = { self.allTradeDay}" % (100 * len(self.occurDayMap) / self.allTradeDay))
        for kValue, dataItem in self.dataSet.items():
            total_count1 = 0
            total_count2 = 0
            for cnt in dataItem.sell_disbute:
                total_count1 += cnt
            for cnt in dataItem.buy_disbute:
                total_count2 += cnt
            assert total_count1 == total_count2
            assert total_count1 > 0

            print(f"k线形态值:%6d， " % (kValue))

            print(f"   卖方价格分布：")
            info = ""
            for encode in range(0, len(dataItem.sell_disbute)):
                occurtRate = 100 * dataItem.sell_disbute[encode] / total_count1
                info += f"{self.pctEncoder.descriptEncdoe(encode)}：%.2f%%," % (occurtRate)
            print(f"     {info}")
            print(f"   买方价格分布：")
            info = ""
            for encode in range(0, len(dataItem.buy_disbute)):
                occurtRate = 100 * dataItem.buy_disbute[encode] / total_count1
                info += f"{self.pctEncoder.descriptEncdoe(encode)}：%.2f%%," % (occurtRate)
            print(f"     {info}")

class Generate_TrainData_KPattern_skip1_predit2(More_detail_KPattern_skip1_predit2):

    def __init__(self, limit_close_pct=1, kPatters: [] = None):
        super().__init__(limit_close_pct,kPatters)
        pct_split = [-7, -5, -3, -1.5, -0.5, 0.5, 1.5, 3, 5, 7]
        self.trainDataSet = []
        self.sw = SWImpl()
        self.pctEncoder = FloatEncoder(pct_split)

    def doWantedTraceData(self,traceData: Skip1_Predict2_TraceData,countData:CountData):
        super().doWantedTraceData(traceData,countData)

        occurBar = traceData.starBar
        skipBar = traceData.skipBar
        sell_pct = 100 * ((skipBar.high_price + skipBar.close_price) / 2 - occurBar.close_price) / occurBar.close_price
        buy_pct = 100 * ((skipBar.low_price + skipBar.close_price) / 2 - occurBar.close_price) / occurBar.close_price

        data = []
        data.append(self.code)
        data.append(self.sw.getSw2Name(self.code))
        data.append(traceData.kPatternValue)
        data.append(buy_pct)
        data.append(sell_pct)
        data.append(traceData.sell_pct)
        data.append(traceData.buy_pct)
        self.trainDataSet.append(data)
        pass

    def onDestroy(self):
        super().onDestroy()
        cloumns = ["code", "name", "kPattern", "buy_price", "sell_price", "label_sell_price", "label_buy_price"]
        wxl = pd.DataFrame(self.trainDataSet, columns=cloumns)
        writer = pd.ExcelWriter('files/sw_train_data_sample.xlsx')
        wxl.to_excel(writer, sheet_name="sample", index=False)
        writer.save()
        writer.close()
        print(f"dataSize = {len(self.trainDataSet)}")

if __name__ == "__main__":
    sw = SWImpl()
    start = datetime(2014, 5, 1)
    end = datetime(2020, 8, 17)

    ##查找有意义的k线形态
    findKPatternCollector = Find_KPattern_skip1_predit2()

    ##打印更详细的信息
    printMoreDetail = More_detail_KPattern_skip1_predit2(kPatters=[712])

    ##生成训练数据。
    generateTrainData = Generate_TrainData_KPattern_skip1_predit2(kPatters=[712])

    sw.collect(start, end,generateTrainData)

    pass
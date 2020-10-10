import os
from datetime import datetime
from typing import Tuple, Sequence, Union

import sklearn
from sklearn.ensemble import RandomForestClassifier

from earnmi.chart.FloatEncoder import FloatEncoder
from earnmi.chart.Indicator import Indicator
from earnmi.chart.KPattern import KPattern
from earnmi.model.QuantData import QuantData
from vnpy.trader.object import BarData

from earnmi.data.SWImpl import SWImpl
from earnmi.model.CollectData import CollectData
from earnmi.model.CoreEngine import CoreEngine, BarDataSource, CoreCollector, PredictModel
from earnmi.model.Dimension import Dimension, TYPE_3KAGO1, TYPE_2KAGO1
from earnmi.model.PredictData import PredictData
import numpy as np
import pandas as pd
import pickle




class SWDataSource(BarDataSource):
    def __init__(self,start:datetime,end:datetime ):
        self.index = 0
        self.sw = SWImpl()
        self.start = start
        self.end = end

    def onNextBars(self) -> Tuple[Sequence['BarData'], str]:
        # if self.index > 2:
        #     return None,None
        sw_code_list = self.sw.getSW2List()
        if self.index < len(sw_code_list):
            code = sw_code_list[self.index]
            self.index +=1
            return self.sw.getSW2Daily(code,self.start,self.end),code
        return None,None

class SVMPredictModel(PredictModel):

    def __init__(self,dimen:Dimension):
        self.dimen = dimen
        self.orginSampleQuantData:QuantData = None
        self.sampleQuantData:QuantData = None
        self.classifierSell_1 = None
        self.classifierSell_2 = None
        self.classifierBuy_1 = None
        self.classifierBuy_2 = None

    """
      预处理样本数据，比如，拆减等。
      """

    def __processSampleData(self, engine: CoreEngine, sampleData: Sequence['CollectData']) -> Sequence['CollectData']:
        return sampleData

    def __genereatePd(self, engine: CoreEngine,dataList: Sequence['CollectData']):
        trainDataSet = []
        for traceData in dataList:
            occurBar = traceData.occurBars[-1]
            assert len(traceData.predictBars) > 0
            skipBar = traceData.predictBars[0]
            sell_pct = 100 * (
                    (skipBar.high_price + skipBar.close_price) / 2 - occurBar.close_price) / occurBar.close_price
            buy_pct = 100 * (
                    (skipBar.low_price + skipBar.close_price) / 2 - occurBar.close_price) / occurBar.close_price

            real_sell_pct,real_buy_pct = CollectData.getSellBuyPredicPct(traceData)
            label_sell_1 = PredictModel.PctEncoder1.encode(real_sell_pct)
            label_sell_2 = PredictModel.PctEncoder2.encode(real_sell_pct)
            label_buy_1 = PredictModel.PctEncoder1.encode(real_buy_pct)
            label_buy_2 = PredictModel.PctEncoder2.encode(real_buy_pct)

            kdj = traceData.occurKdj[-1]

            data = []
            data.append(buy_pct)
            data.append(sell_pct)
            data.append(kdj[0])
            data.append(kdj[2])
            data.append(label_sell_1)
            data.append(label_buy_1)
            data.append(label_sell_2)
            data.append(label_buy_2)
            trainDataSet.append(data)
        cloumns = ["buy_pct",
                   "sell_pct",
                   "k",
                   "j",
                   "label_sell_1",
                   "label_buy_1",
                   "label_sell_2",
                   "label_buy_2",
                   ]
        orgin_pd =  pd.DataFrame(trainDataSet, columns=cloumns)
        return orgin_pd

    """
    生成特征值。(有4个标签）
    返回值为：x, y_sell_1,y_buy_1,y_sell_2,y_buy_2
    """
    def __generateFeature(self, engine: CoreEngine, dataList: Sequence['CollectData']):
        print(f"[SVMPredictModel]: generate feature")
        def set_0_between_100(x):
            if x >100:
                return 100
            if x < 0:
                return 0
            return x

        def percent_to_one(x):
            return int(x * 100) / 1000.0

        def toInt(x):
            v = int(x + 0.5)
            if v > 10:
                v = 10
            if v < -10:
                v = -10
            return v
        d = self.__genereatePd(engine,dataList)
        print(f"   origin:\n{d.head()}")

        d['buy_pct'] = d.buy_pct.apply(percent_to_one)  # 归一化
        d['sell_pct'] = d.sell_pct.apply(percent_to_one)  # 归一化
        d.k = d.k.apply(set_0_between_100)
        d.j = d.j.apply(set_0_between_100)
        d.k = d.k / 100
        d.j = d.j / 100
        print(f"   convert:\n{d.head()}")
        data = d.values
        x, y = np.split(data, indices_or_sections=(4,), axis=1)  # x为数据，y为标签
        y_1 = y[:, 0:1].flatten()  # 取第一列
        y_2 = y[:, 1:2].flatten()  # 取第一列
        y_3 = y[:, 2:3].flatten()  # 取第一列
        y_4 = y[:, 3:4].flatten()  # 取第一列

        print(f"   y_1:\n{y_1}")
        print(f"   y_2:\n{y_2}")
        print(f"   y_3:\n{y_3}")
        print(f"   y_4:\n{y_4}")

        print(f"[SVMPredictModel]: generate feature end!!!")
        return x, y_1, y_2, y_3, y_4



    """
    建造模型
    """
    def build(self,engine:CoreEngine, sampleData:Sequence['CollectData']):
        print(f"[SVMPredictModel]: build Model[{self.dimen}]....")
        self.orginSampleQuantData = engine.computeQuantData(sampleData)
        trainDataList = self.__processSampleData(self,sampleData)
        self.sampleQuantData = engine.computeQuantData(trainDataList)
        print(f"   history quantdata: {self.orginSampleQuantData}")
        print(f"   sample quantdata: {self.sampleQuantData}")

        ##建立特征值
        x, y_sell_1,y_buy_1,y_sell_2,y_buy_2 = self.__generateFeature(engine,trainDataList)
        self.classifierSell_1 = self.__createClassifier(x,y_sell_1)
        self.classifierSell_2 = self.__createClassifier(x,y_sell_2)
        self.classifierBuy_1 = self.__createClassifier(x,y_buy_1)
        self.classifierBuy_2 = self.__createClassifier(x,y_buy_2)
        print(f"[SVMPredictModel]: build finished!!!")
        pass

    def __createClassifier(self,x,y,useSVM=True):
        classifier = None
        if useSVM:
            classifier = sklearn.svm.SVC(C=2, kernel='rbf', gamma=10, decision_function_shape='ovr', probability=True)  # ovr:一对多策略
            classifier.fit(x, y)
        else:
            classifier = RandomForestClassifier(n_estimators=100, max_depth=None,min_samples_split=50, bootstrap=True)
            classifier.fit(x, y)
        return classifier


    def predict(self, data) -> Union[PredictData, Sequence['PredictData']]:
        single = False
        if type(data) is CollectData:
            data = [data]
            single = True
        if type(data) is list:
            x, y_sell_1,y_buy_1,y_sell_2,y_buy_2 = self.__generateFeature(self,data)
            retList = []
            buyRange1_list = self.classifierBuy_1.predict_proba(x)
            buyRange2_list = self.classifierBuy_2.predict_proba(x)
            sellRange1_list = self.classifierSell_1.predict_proba(x)
            sellRange2_list = self.classifierSell_2.predict_proba(x)
            for i in range(0,len(data)):
                collectData = data[i]
                pData = PredictData(dimen=self.dimen, historyData=self.orginSampleQuantData,
                                    sampleData=self.sampleQuantData, collectData=collectData)
                pData.buyRange1 = buyRange1_list[i]
                pData.buyRange2 = buyRange2_list[i]
                pData.sellRange1 = sellRange1_list[i]
                pData.sellRange2 = sellRange2_list[i]
                retList.append(pData)
            if single:
                return retList[-1]
            else:
                return retList
        raise RuntimeError("unsupport data！！！")

    def __predictSingle(self,x,collectData:CollectData) -> PredictData:
        pData = PredictData(dimen =self.dimen,historyData= self.orginSampleQuantData,sampleData=self.sampleQuantData,collectData = collectData)

        pData.buyRange1 = self.classifierBuy_1.predict_proba(x)
        pData.buyRange2 = self.classifierBuy_2.predict_proba(x)
        pData.sellRange1 = self.classifierSell_1.predict_proba(x)
        pData.sellRange2 = self.classifierSell_2.predict_proba(x)
        return pData


class CoreEngineImpl(CoreEngine):

    COLLECT_DATA_FILE_NAME = "colllect"
    ##量化数据的涨幅分布区域。
    quantFloatEncoder = FloatEncoder([-7, -5, -3, -1.5, -0.5, 0.5, 1.5, 3, 5, 7])

    def __init__(self, dirPath: str):
        self.mAllDimension:['Dimension'] = None
        self.mQuantDataMap:{}= None
        self.__file_dir = dirPath
        self.__collector = None

        if not os.path.exists(dirPath):
            os.makedirs(dirPath)
        collectDir = self.__getCollectDirPath()
        if not os.path.exists(collectDir):
            os.makedirs(collectDir)


    def __getDimenisonFilePath(self):
        return f"{self.__file_dir}/dimension.bin"

    def __getCollectDirPath(self):
        return  f"{self.__file_dir}/colllect"


    def __getCollectFilePath(self,dimen:Dimension):
        dirPath =  f"{self.__getCollectDirPath()}/{dimen.getKey()}"
        return dirPath



    def load(self,collector:CoreCollector):
        self.__collector = collector
        print("[CoreEngine]: load start...")
        with open(self.__getDimenisonFilePath(), 'rb') as fp:
            self.mAllDimension  = pickle.load(fp)
        quantMap = {}
        totalCount = 0
        for dimen in self.mAllDimension:
            colectDatas = self.loadCollectData(dimen)
            quantData = self.computeQuantData(colectDatas)
            quantMap[dimen] = quantData
            totalCount += quantData.count
        self.mQuantDataMap = quantMap
        print(f"[CoreEngine]: 总共加载{len(self.mAllDimension)}个维度数据,共{totalCount}个数据")

        assert len(quantMap) == len(self.mAllDimension)

    def loadCollectData(self, dimen: Dimension) -> Sequence['CollectData']:
        filePath = self.__getCollectFilePath(dimen)
        collectData = None
        with open(filePath, 'rb') as fp:
            collectData = pickle.load(fp)
        return collectData

    def computeQuantData(self, dataList: Sequence['CollectData']) -> QuantData:
        sellRangeCount = {}
        buyRangeCount = {}
        for i in range(0, CoreEngineImpl.quantFloatEncoder.mask()):
            sellRangeCount[i] = 0
            buyRangeCount[i] = 0
        for data in dataList:
            bars: ['BarData'] = data.predictBars
            assert len(bars) > 0
            sell_pct, buy_pct = CollectData.getSellBuyPredicPct(data)
            sell_encode = CoreEngineImpl.quantFloatEncoder.encode(sell_pct)
            buy_encode = CoreEngineImpl.quantFloatEncoder.encode(buy_pct)
            sellRangeCount[sell_encode] += 1
            buyRangeCount[buy_encode] += 1
        return QuantData(count=len(dataList),sellRangeCount=sellRangeCount,buyRangeCount=buyRangeCount)

    def build(self,soruce:BarDataSource,collector:CoreCollector):
        print("[CoreEngine]: build start...")
        self.__collector = collector
        collector.onCreate()
        bars,code = soruce.onNextBars()
        dataSet = {}
        totalCount = 0
        while not bars is None:
           finished,stop = self.__collect__internel(bars,code,collector)
           print(f"[CoreEngine]: collect code:{code}, finished:{len(finished)},stop:{len(stop)}")
           totalCount += len(finished)
           bars, code = soruce.onNextBars()
           for data in finished:
               ##收录
               listData:[] = dataSet.get(data.dimen)
               if listData is None:
                   listData = []
                   dataSet[data.dimen] = listData
               listData.append(data)
        collector.onDestroy()

        dimes = dataSet.keys()
        print(f"[CoreEngine]: 总共收集到{totalCount}数据，维度个数:{len(dimes)}")

        print(f"[CoreEngine]: 开始保存数据")
        MIN_SIZE = 300
        saveDimens = []
        saveCollectCount = 0
        maxSize = 0
        minSize = 9999999999
        for dimen,listData in dataSet.items():
            size = len(listData)
            if size  < MIN_SIZE:
                continue
            maxSize = max(maxSize,size)
            minSize = min(minSize,size)
            saveDimens.append(dimen)
            saveCollectCount += size
            filePath = self.__getCollectFilePath(dimen)
            with open(filePath, 'wb+') as fp:
                pickle.dump(listData, fp, -1)

        with open(self.__getDimenisonFilePath(), 'wb+') as fp:
            pickle.dump(saveDimens, fp, -1)
        print(f"[CoreEngine]: 总共保存{len(saveDimens)}个维度数据(>={MIN_SIZE})，共{saveCollectCount}个数据，其中最多{maxSize},最小{minSize}")
        self.load(collector)

    def collect(self, bars: ['BarData']) -> Tuple[Sequence['CollectData'], Sequence['CollectData']]:
        collector = self.__collector
        collector.onCreate()
        code = bars[0].symbol
        finished,stop = self.__collect__internel(bars,code,collector)
        collector.onDestroy()
        return finished,stop


    def __collect__internel(self, barList: ['BarData'],symbol:str,collector:CoreCollector) -> Tuple[Sequence['CollectData'], Sequence['CollectData']]:
        collector.onStart(symbol)
        traceItems = []
        finishedData = []
        stopData = []
        for bar in barList:
            toDeleteList = []
            newObject = collector.collect(bar)
            for collectData in traceItems:
                isFinished = collector.onTrace(collectData, bar)
                if isFinished:
                    toDeleteList.append(collectData)
                    finishedData.append(collectData)
            for collectData in toDeleteList:
                traceItems.remove(collectData)
            if newObject is None:
                continue
            traceItems.append(newObject)

        ###将要结束，未追踪完的traceData
        for traceObject in traceItems:
            stopData.append(traceObject)
        collector.onEnd(symbol)
        return finishedData,stopData

    def loadAllDimesion(self) -> Sequence['Dimension']:
        return self.mAllDimension

    def queryQuantData(self, dimen: Dimension) -> QuantData:
        return self.mQuantDataMap.get(dimen)

    def loadPredictModel(self, dimen: Dimension) -> PredictModel:

        collectDataList = self.loadCollectData(dimen)
        if collectDataList is None:
            return None
        model = SVMPredictModel(dimen)
        model.build(self,collectDataList)
        return model

    def toStr(self,data:QuantData) ->str:

        info = f"count:{data.count}"
        info+=",sell:["
        for i in range(0,len(data.sellRangeCount)):
            min,max = CoreEngineImpl.quantFloatEncoder.parseEncode(i)
            info+=f"{min}:{max}=%.2f%%, " % (100 * data.sellRangeCount[i] / data.count)
        info += "],buy:["
        for i in range(0, len(data.buyRangeCount)):
            min, max = CoreEngineImpl.quantFloatEncoder.parseEncode(i)
            info += f"{min}:{max}=%.2f%%, " % (100 * data.buyRangeCount[i] / data.count)
        info +="]"
        return info

if __name__ == "__main__":
    class Collector2KAgo1(CoreCollector):

        def __init__(self):
            self.lasted3Bar = np.array([None,None,None])
            self.lasted3BarKdj = np.array([None,None,None])

        def onStart(self, code: str) -> bool:
            self.indicator = Indicator(40)
            self.code = code
            return True

        def collect(self, bar: BarData) -> CollectData:
            self.indicator.update_bar(bar)
            self.lasted3Bar[:-1] = self.lasted3Bar[1:]
            self.lasted3BarKdj[:-1] = self.lasted3BarKdj[1:]
            k, d, j = self.indicator.kdj(fast_period=9, slow_period=3)
            self.lasted3Bar[-1] = bar
            self.lasted3BarKdj[-1] = [k, d, j]
            if self.indicator.count >= 15:
                kPatternValue = KPattern.encode2KAgo1(self.indicator)
                if not kPatternValue is None :
                    dimen = Dimension(type=TYPE_2KAGO1,value=kPatternValue)
                    collectData = CollectData(dimen=dimen)
                    collectData.occurBars.append(self.lasted3Bar[-2])
                    collectData.occurBars.append(self.lasted3Bar[-1])

                    collectData.occurKdj.append(self.lasted3BarKdj[-2])
                    collectData.occurKdj.append(self.lasted3BarKdj[-1])

                    return collectData
            return None

        def onTrace(self, data: CollectData, newBar: BarData) -> bool:
            if len(data.occurBars) < 3:
                data.occurBars.append(self.lasted3Bar[-1])
                data.occurKdj.append(self.lasted3BarKdj[-1])
            else:
                data.predictBars.append(newBar)
            size = len(data.predictBars)
            return size >= 2


    start = datetime(2014, 5, 1)
    end = datetime(2020, 5, 17)
    engine = CoreEngineImpl("files/impltest")

    engine.build(SWDataSource(start,end),Collector2KAgo1())
    #engine.load(Collector2KAgo1())
    dimens = engine.loadAllDimesion()
    print(f"dimension：{dimens}")

    for dimen in dimens:
        quant = engine.queryQuantData(dimen)
        print(f"quant：{engine.toStr(quant)}")

    ## 一个预测案例
    sw = SWImpl()
    code = sw.getSW2List()[3]
    bars = sw.getSW2Daily(code,end,datetime.now())

    finished,stop = engine.collect(bars)

    for cData in finished:
        model = engine.loadPredictModel(cData.dimen)
        if model is None:
            continue
        pData = model.predict(cData)
        print(f"pData:{pData}")
        break

    pass

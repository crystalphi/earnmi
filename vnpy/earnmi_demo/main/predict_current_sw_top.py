from datetime import datetime
from typing import Sequence

import pandas as pd
import numpy as np
import sklearn
from sklearn import model_selection
from sklearn.model_selection import cross_val_score
from sklearn.datasets import make_blobs
from sklearn.ensemble import RandomForestClassifier
from sklearn.ensemble import ExtraTreesClassifier
from sklearn.tree import DecisionTreeClassifier
import pickle


from earnmi.data.SWImpl import SWImpl
from earnmi.model.PredictData import PredictData
from vnpy.trader.object import BarData

"""

预测当前申万行业明天最有可能涨的前几个行业。
"""

class PredictModel:

    def __init__(self):
        self.data_x = None
        self.data_y = None
        self.randomForest = None
        self.labels_y = None

    """
    预处理特征数据。
    """
    def __pre_process(self,df:pd.DataFrame):
        def set_0_or_1(x):
            if x >= 2:
                return 1
            return 0
        def percent_to_one(x):
            return int(x * 100) / 1000.0
        def toInt(x):
            return int(x + 0.5)
        d = df
        d['buy_price'] = d.buy_price.apply(percent_to_one)  # 归一化
        d['sell_price'] = d.sell_price.apply(percent_to_one)  # 归一化
        d['label_sell_price'] = d.label_sell_price.apply(toInt)
        d['label_buy_price'] = d.label_buy_price.apply(toInt)
        df = df.drop(columns=['code', 'kPattern', 'name'])

        data = df.values
        x, y = np.split(data, indices_or_sections=(2,), axis=1)  # x为数据，y为标签
        y = y[:, 0:1].astype('int')  # 取第一列
        return x, y.ravel()

    def setFeature(self, df:pd.DataFrame):
        self.data_x,self.data_y = self.__pre_process(df)
        label_value = np.unique(self.data_y)
        self.labels_y = np.sort(label_value)

    def saveToFile(self,fileName:str):
        with open(fileName, 'wb') as fp:
            pickle.dump(self.data_x, fp,-1)
            pickle.dump(self.data_y, fp,-1)
            pickle.dump(self.labels_y, fp,-1)

    def loadFromFile(self,fileName:str):
        with open(fileName, 'rb') as fp:
            self.data_x = pickle.load(fp)
            self.data_y = pickle.load(fp)
            self.labels_y = pickle.load(fp)
        #self.randomForest = RandomForestClassifier(n_estimators=50,max_depth=None,min_samples_split=50, bootstrap=True)
        #self.randomForest.fit(self.data_x,self.data_y)

    def predict(self,feature:pd.DataFrame) -> Sequence["PredictData"]:
        x, y = self.__pre_process(feature)
        if self.randomForest is None:
            self.randomForest = RandomForestClassifier(n_estimators=100, max_depth=None, min_samples_split=50,
                                                       bootstrap=True)
            self.randomForest.fit(self.data_x, self.data_y)

        predic_y_proba = self.randomForest.predict_proba(x)
        size = len(x)
        predict_data_list = []
        for i in range(0, size):
            y_proba_list = predic_y_proba[i]  ##预测值
            index = -1  ##查找最高的index
            max_proba = -100000
            for j in range(0,len(y_proba_list)):
                proba = y_proba_list[j]
                if proba > max_proba:
                    max_proba = proba
                    index = j
            assert index != -1
            total_probal = 0.0
            for j in range(index,len(y_proba_list)):
                total_probal += y_proba_list[j]

            probal_2 = None
            percent_2 = None
            if index > 0:
                probal_2 = y_proba_list[index-1]
                percent_2 = self.labels_y[index - 1]

            if index < len(self.labels_y) -1:
                if probal_2 is None or probal_2 < y_proba_list[index+1]:
                    probal_2 = y_proba_list[index + 1]
                    percent_2 = self.labels_y[index + 1]

            #percent = self.labels_y[index]
            percent = percent_2 *  probal_2 /(max_proba + probal_2) + self.labels_y[index] *  max_proba /(max_proba + probal_2)
            predictData = PredictData(percent=percent,probability=total_probal)
            predictData.precent_real = y[i]
            predict_data_list.append(predictData)

        return predict_data_list

    def printCrossScoreTest(self):
        x_train, x_test, y_train, y_test = model_selection.train_test_split(self.data_x, self.data_y, train_size=0.7, test_size=0.3)
        y_train = y_train.ravel()
        y_test = y_test.ravel()

        clf1 = DecisionTreeClassifier(max_depth=None, min_samples_split=2, random_state=0)
        clf2 = RandomForestClassifier(n_estimators=50, max_depth=None, min_samples_split=50, bootstrap=True)
        clf3 = ExtraTreesClassifier(n_estimators=10, max_depth=None, min_samples_split=2, bootstrap=False)

        scores1 = cross_val_score(clf1, x_train, y_train)
        scores2 = cross_val_score(clf2, x_train, y_train)
        scores3 = cross_val_score(clf3, x_train, y_train)
        print('DecisionTreeClassifier交叉验证准确率为:' + str(scores1.mean()))
        print('RandomForestClassifier交叉验证准确率为:' + str(scores2.mean()))
        print('ExtraTreesClassifier交叉验证准确率为:' + str(scores3.mean()))

    def printPredictInfo(self,df:pd.DataFrame):
        predictList = self.predict(df.copy(deep=False))

        for predictData in predictList:
            print(f"预测值为:{predictData}")


        # predic_y_proba = self.randomForest.predict_proba(x_test)
        # predic_y = self.randomForest.predict(x_test)
        #
        # size = len(y_test)
        #
        # for i in range(0, size):
        #     y_proba = predic_y_proba[i]  ##预测值
        #
        #     y_index = 0
        #     max_proba = -1
        #     for j in range(0,len(y_proba)):
        #         proba = y_proba[j]
        #         if proba > max_proba:
        #             max_proba = proba
        #             y_index = j
        #     total_probal = 0.0
        #     for j in range(y_index,len(y_proba)):
        #         total_probal += y_proba[j]
        #
        #     proba_info = ""
        #
        #     probal_2 = None
        #     predict_percent_2 = None
        #     if y_index > 0:
        #         proba_info +=f"{self.labels_y[y_index - 1]}:{y_proba[y_index-1]}, "
        #         probal_2 = y_proba[y_index-1]
        #         predict_percent_2 = self.labels_y[y_index - 1]
        #
        #     proba_info += f"{self.labels_y[y_index ]}:{y_proba[y_index]}, "
        #
        #     if y_index < len(self.labels_y) -1:
        #         proba_info += f"{self.labels_y[y_index + 1]}:{y_proba[y_index + 1]}"
        #         if probal_2 is None or probal_2 < y_proba[y_index + 1]:
        #             probal_2 = y_proba[y_index + 1]
        #             predict_percent_2 = self.labels_y[y_index +1]
        #
        #         proba_delta =  y_proba[y_index] - y_proba[y_index + 1]
        #         if proba_delta < 0.0000001:
        #             probale = y_proba[y_index] + y_proba[y_index + 1]
        #         y_delta  = self.labels_y[y_index + 1] - self.labels_y[y_index]
        #
        #     probal_1 = y_proba[y_index]
        #     percent = predict_percent_2 *  probal_2 /(probal_1 + probal_2) + self.labels_y[y_index] *  probal_1 /(probal_1 + probal_2)
        #
        #     y = self.labels_y[y_index]
        #     print(f"预测值为:{y} ,{predic_y[i]}, {percent},实际值：{y_test[i]},proba:[{total_probal}]")




        pass


def buildAndSaveModel(start:datetime,end:datetime,patternList=[]):
    sw = SWImpl()

    from earnmi_demo.strategy_demo.kbars.analysis_KPattern_skip1_predit2 import \
        Generate_Feature_KPattern_skip1_predit2

    for kPattern in patternList:
        generateTrainData = Generate_Feature_KPattern_skip1_predit2(kPatters=[kPattern])
        sw.collect(start, end, generateTrainData)
        featureData = generateTrainData.getPandasData()

        filleName = f"models/predict_sw_top_k_{kPattern}.m"

        print(f"k线形态[{kPattern}]的模型能力:")
        model = PredictModel()
        model.setFeature(featureData)
        model.printCrossScoreTest()
        model.saveToFile(filleName)



if __name__ == "__main__":
    sw = SWImpl()
    start = datetime(2014, 5, 1)
    end = datetime(2020, 8, 17)
    patternList = [535, 359, 1239, 1415, 1072, 712, 1240, 888, 2823, 706, 1414, 1064]


    from earnmi_demo.strategy_demo.kbars.analysis_KPattern_skip1_predit2 import \
        Generate_Feature_KPattern_skip1_predit2

    ##建立特征模型
    #buildAndSaveModel(start,end,patternList)

    predictStart = datetime(2020, 8, 18)
    predictEnd = datetime.now()
    #patternList = [535]
    total_count = 0
    fail_count = 0
    for kPattern in patternList:
        generateTrainData = Generate_Feature_KPattern_skip1_predit2(kPatters=[kPattern])
        sw.collect(predictStart, predictEnd, generateTrainData)


        filleName = f"models/predict_sw_top_k_{kPattern}.m"

        model = PredictModel()
        model.loadFromFile(filleName)

        traceDatas = generateTrainData.traceDatas


        for traceData in traceDatas:
            feature = generateTrainData.generateData([traceData])
            predictDatas =  model.predict(feature)
            predict = predictDatas[0]

            close_price = traceData.occurBar.close_price
            predict_price =  close_price* (1 + predict.percent / 100.0)
            buy_price =  traceData.skipBar.close_price

            profile_pct =  (predict_price - buy_price) / close_price

            if profile_pct > 0.01 and predict.probability > 0.7:
                sell_day = -1
                total_count +=1
                for i in range(0, len(traceData.predictBars)):
                    bar: BarData = traceData.predictBars[i]
                    if predict_price < bar.high_price:
                        sell_day = i
                        break

                can_sell = sell_day != -1
                if can_sell:
                    print(f"SUC  : profile_pct = {profile_pct},sell_day = {sell_day},prob={predict.probability}")
                else:
                    profile_pct = (traceData.predictBars[-1].close_price - buy_price) / close_price
                    fail_count += 1
                    print(f"FAIL : profile_pct = {profile_pct},prob={predict.probability}")

                #if profile_pct < 0.001:

    sucess_rate = 100 * ( 1 - (fail_count)/total_count)
    print(f"total count:{total_count}, sucess_rate:%.2f%%" % (sucess_rate))

    pass
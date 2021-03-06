import json
from abc import ABC
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import List, Optional, Sequence

from peewee import *

from earnmi.model.op import OpOrderStatus
from earnmi.uitl.utils import utils
from vnpy.trader.object import BarData

"""
操作日志。
"""
@dataclass
class OpLog():
    type:int
    time:datetime
    info:str

    def to_dict(self):
        return {
            'type':self.type,
            'time':self.time,
            'info':self.info
        }
    def form_dict(self,dict:{}):
        self.type = dict.get('type')
        self.time = dict.get('time')
        self.info = dict.get('info')

class _DateEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj,datetime):
            return obj.strftime("%Y-%m-%d %H:%M:%S")
        else:
            return json.JSONEncoder.default(self,obj)





@dataclass
class OpOrder2:
    id = None
    code:str
    strategy_name:str
    buy_price:float  ##预测买入价
    sell_price:float
    create_time:datetime; ##创建时间、发生时间
    """
    
    """
    status:int = OpOrderStatus.NEW
    current_price:float = None
    duration:int = 0
    predict_suc:bool = None   ##是否预测成功，只在完成状态有效。
    update_time:datetime = None
    source:int = 0  ##来源：0 为回测数据，1为实盘数据
    buy_time:datetime = None
    sell_time:datetime = None


    buy_actual_price: float = -1  #实际买入价
    sell_actual_price: float = -1
    opLogs:[]=None

    def __post_init__(self):
        self.update_time = self.create_time
        self.opLogs = []

    def isFinished(self):
        return self.status!= OpOrderStatus.NEW and self.status!=OpOrderStatus.HOLD

    def convertOpLogToJsonText(self):
        size = len(self.opLogs)
        if size == 0:
            return None
        opList = [op.to_dict() for op in self.opLogs]
        return json.dumps(obj=opList,cls=_DateEncoder)

    def loadOpLogFromJsonText(self,jsonText:str):
        op_log_list = []
        if not jsonText is None:
            dictList = json.loads(s=jsonText)
            if not dictList is None:
                for the_dict in dictList:
                    opLog = OpLog(time=None, info=None, type=None)
                    opLog.form_dict(the_dict)
                    op_log_list.append(opLog)
        self.opLogs = op_log_list

    """
     /*
                       处理操作单
                       0: 不处理
                       1：做多
                       2：做空
                       3: 预测成功交割单(卖出）
                       4：预测失败交割单
                       5：废弃单
     */
    """
    def updateStatus(self):
        if len(self.opLogs) < 1:
            return
        lastOptionCode = self.opLogs[-1].type
        if lastOptionCode == 0:
            return
        if lastOptionCode == 5:
            self.status = OpOrderStatus.INVALID
            return
        if lastOptionCode == 1 or lastOptionCode ==2:
            self.status = OpOrderStatus.HOLD
            return
        if lastOptionCode != 3 and lastOptionCode != 4:
            print(f"why!!!")
        assert lastOptionCode == 3 or lastOptionCode == 4
        self.predict_suc = lastOptionCode == 3
        if self.buy_actual_price < self.sell_actual_price:
            self.status = OpOrderStatus.FINISHED_EARN
        else:
            self.status = OpOrderStatus.FINISHED_LOSS



class OpOrderDataBase:

    def __init__(self,db:Database):
        self.dao = OpOrderDataBase.init_models(db)

    def loadById(self,id)->Optional["OpOrder2"]:
        s = (
            self.dao.select()
                .where(
                (self.dao.id == id)
            )
            .first()
        )
        if s:
            return s.to_data()
        return None

    def loadAtDay(self,code:str,dayTime:datetime)->Optional["OpOrder2"]:
        start = utils.to_start_date(dayTime)
        end = utils.to_end_date(dayTime)
        s = (
            self.dao.select()
                .where(
                (self.dao.code == code)
                &(self.dao.create_time >= start)
                & (self.dao.create_time <= end)
            )
        )
        if s:
            data = [db_bar.to_data() for db_bar in s]
            if len(data) > 0:
                assert len(data) == 1
                return data[0]
        return None

    def LoadLatest(self):
        pass

    def loadLatest(self,count:int)-> Sequence["OpOrder2"]:
        s = (
            self.dao.select()
                .order_by(self.dao.create_time.desc(),self.dao.update_time.desc())
                .limit(count)
        )
        data = [db_bar.to_data() for db_bar in s]
        return data

    def load(self,start: datetime,end: datetime) -> Sequence["OpOrder2"]:
        s = (
            self.dao.select()
                .where(
                (self.dao.create_time >= start)
                & (self.dao.create_time <= end)
            )
             .order_by(self.dao.create_time.desc())
        )
        data = [db_bar.to_data() for db_bar in s]
        return data

    def save(self, data:OpOrder2):

        self.dao.save_all([self.dao.from_data(data)])

    def saveAll(
        self,
        datas: Sequence["OpOrder2"],
    ):
        ds = [self.dao.from_data(i) for i in datas]
        self.dao.save_all(ds)

    def clean(self, code:str):
        self.dao.delete().where(self.dao.code == code).execute()

    def cleanAll(self):
        self.dao.delete().execute()

    def count(self):
        return self.dao.select().count()

    def init_models(db: Database):
        class OpOrderData(Model):
            """
            Candlestick bar data for database storage.

            Index is defined unique with datetime, interval, symbol
            """
            id = AutoField()
            code = CharField()
            source = IntegerField()
            create_time = DateTimeField()
            buy_price = FloatField()
            sell_price = FloatField()
            opLogsJsonText = TextField(null=True)

            buy_time = DateTimeField(null=True)
            sell_time = DateTimeField(null=True)
            strategy_name = CharField()
            current_price = FloatField(null=True)

            status = IntegerField()
            duration = IntegerField()
            predict_suc = BooleanField(null=True)
            update_time = DateTimeField()

            def to_dict(self):
                return self.__data__
            class Meta:
                database = db
                indexes = ((("code", "create_time"), True),)
            @staticmethod
            def from_data(bar: OpOrder2):
                """
                Generate DbBarData object from BarData.
                """
                db_bar = OpOrderData()
                db_bar.status = bar.status
                db_bar.predict_suc = bar.predict_suc
                db_bar.duration = bar.duration
                db_bar.update_time = bar.update_time
                db_bar.source = bar.source
                db_bar.id = bar.id
                db_bar.code = bar.code
                db_bar.create_time = bar.create_time
                db_bar.buy_price = bar.buy_price
                db_bar.sell_price = bar.sell_price
                db_bar.sell_time = bar.sell_time
                db_bar.buy_time = bar.buy_time
                db_bar.strategy_name = bar.strategy_name
                db_bar.current_price = bar.current_price
                db_bar.opLogsJsonText = bar.convertOpLogToJsonText()

                return db_bar

            def to_data(self):
                """
                Generate BarData object from DbBarData.
                """
                bar = OpOrder2(
                    strategy_name=self.strategy_name,
                    code=self.code,
                    create_time=self.create_time,
                    sell_price=self.sell_price,
                    buy_price=self.buy_price,
                )
                bar.id = self.id
                bar.status = self.status
                bar.predict_suc = self.predict_suc
                bar.duration = self.duration
                bar.update_time = self.update_time
                bar.source = self.source
                bar.sell_time = self.sell_time
                bar.buy_time = self.buy_time
                bar.current_price = self.current_price
                bar.loadOpLogFromJsonText(self.opLogsJsonText)

                return bar

            @staticmethod
            def save_all(objs: List["OpOrderData"]):
                """
                save a list of objects, update if exists.
                """
                dicts = [i.to_dict() for i in objs]
                with db.atomic():
                    for c in chunked(dicts, 50):
                            OpOrderData.insert_many(
                                c).on_conflict_replace().execute()


        db.connect()
        db.create_tables([OpOrderData])
        return OpOrderData



if __name__ == "__main__":

    dt = datetime.now() - timedelta(minutes=1)
    order = OpOrder2(strategy_name="1", code='test', sell_price='34', buy_price='sf', create_time=dt)
    sameOrder = OpOrder2(strategy_name="1", code='test', sell_price='34', buy_price='sf', create_time=dt)

    db = OpOrderDataBase("opdata.db")

    db.cleanAll()
    assert db.loadAtDay('test', datetime.now()) is None
    assert db.count() == 0
    db.save(order)
    db.save(sameOrder)
    assert db.count() == 1
    orederAtNow = db.loadAtDay('test', datetime.now())

    assert not orederAtNow is None
    assert orederAtNow.code == 'test'
    assert orederAtNow.update_time == dt
    orederAtNow.update_time = datetime.now()
    log1 = OpLog(type=1, info="sdfksf", time=datetime.now())
    orederAtNow.opLogs.append(log1)
    orederAtNow.opLogs.append(log1)
    db.save(orederAtNow)
    assert db.count() == 1
    orederAtNow = db.loadAtDay('test', datetime.now())
    assert orederAtNow.update_time != dt
    assert len(orederAtNow.opLogs) == 2
    assert orederAtNow.opLogs[-1].info == "sdfksf"




    dataList = db.load(dt, dt)
    order1 = dataList[0]

    order2 = db.loadById(order1.id)
    assert not order2 is None
    assert order1 == order2
    assert order.code == order1.code
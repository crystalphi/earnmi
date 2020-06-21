from datetime import datetime
from typing import Sequence

from earnmi.data.HistoryBarPool import HistoryBarPool
from earnmi.data.MinuteBarPool import MinuteBarPool


class _TraceItem:
    code:str;
    historyPoll:HistoryBarPool
    mintuesPoll:MinuteBarPool

class Market:

    history_size = 200
    start:datetime
    end:datetime

    _traceItemMap = {}
    _today = None

    def __init__(self,history_size:int,begin:datetime,end:datetime):
        self.history_size = history_size
        self.start = begin
        self.end = end


    """
    添加到追踪
    """
    def addTrace(self,code:str):
        if( not self._traceItemMap.__contains__(code)):
            traceItem = _TraceItem()
            traceItem.code = code;
            traceItem.historyPoll = HistoryBarPool(code,self.history_size)
            traceItem.historyPoll.initPool(self.start,self.end)
            traceItem.mintuesPoll = MinuteBarPool(code)
            self._traceItemMap[code] = traceItem

    """
    
    """
    def removeTrace(self,code:str):
        if (self._traceItemMap.__contains__(code)):
            self._traceItemMap.__delitem__(code)

    """设置今天的时间"""
    def setToday(self,toady:datetime):
        self._today = toady
        for  traceItem in self._traceItemMap.values() :
            traceItem.historyPoll.setToday(toady)
            traceItem.mintuesPoll.setToday(toady)

    def getHistory(self,code:str) -> Sequence["BarData"]:
        self.__checkOk(code)
        return self._traceItemMap[code].historyPoll.getData();


    """返回今天的分钟k线图"""
    def getTodayMinitueBar(self,code:str) -> Sequence["BarData"]:
        self.__checkOk(code)
        return self._traceItemMap[code].mintuesPoll.getData();

    """返回当前的实时价格
    """
    def getCurrentPrice(self,code:str)->float:
        bars = self.getTodayMinitueBar(code)
        index = 0
        for i,bar in enumerate(bars):
            if(self._today > bar.datetime):
                index = i
                break
        return bars[index].close_price


    def __checkOk(self,code:str):
        if(self._today is None):
            raise RuntimeError(f"you mut setToday() first.")
        item = self._traceItemMap.get(code)
        if(item is None):
            raise RuntimeError(f"you have not trace code = {code} yet.")



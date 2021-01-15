from datetime import datetime, timedelta
from typing import Sequence

from earnmi.data.KBarMintuePool import KBarMintuePool
from earnmi.data.KBarPool import KBarPool
from earnmi.data.Market2 import Market2
from vnpy.trader.object import BarData, TickData


class RealTimeImpl(Market2.RealTime):

    def __init__(self, market: Market2):
        self.market = market

    def getTick(self, code: str) -> BarData:
        today = self.market.getToday()

        if (today is None):
            raise RuntimeError("market doese not set current time")

        pool = self.getKBarMintuePool(code)
        bars = pool.getAtDay(today)
        if len(bars) == 0:
            return None
        minitue_bar:BarData = None
        start = today - timedelta(seconds=59)
        end = today + timedelta(seconds=59)

        for bar in bars:
            if bar.datetime < start:
                continue
            if  bar.datetime <= end:
               if minitue_bar is None:
                   minitue_bar = bar
               else:
                   delta1 = abs(today - minitue_bar.datetime)
                   delta2 = abs(today -bar.datetime)
                   if delta2 < delta1:
                       minitue_bar = bar
            else:
                break
        return minitue_bar;


    def getKBar(self, code: str, hour: int = 0, minute: int = 1, second: int= 1) -> BarData:

        today = self.market.getToday()

        if (today is None):
            raise RuntimeError("market doese not set current time")

        pool = self.getKBarMintuePool(code)
        bars  = pool.getAtDay(today)
        if len(bars) == 0:
            return None

        start = datetime(year=today.year,month=today.month,day=today.day,hour=hour,minute = minute,second = second)
        if(start > today):
            return None

        ret_bar = None
        for bar in bars:
            if bar.datetime >= start and bar.datetime <= today:
                if ret_bar is None:
                    ret_bar = BarData(
                        symbol=code,
                        exchange=bar.exchange,
                        datetime=None,
                        interval = bar.interval,
                        gateway_name=bar.gateway_name,
                        open_price=bar.open_price,
                        high_price=bar.high_price,
                        low_price=bar.low_price,
                        volume = bar.volume,
                        open_interest = bar.open_interest,
                        close_price=  bar.close_price
                    )
                    ret_bar.datetime = today
                else :
                    ret_bar.high_price = max(ret_bar.high_price, bar.high_price)
                    ret_bar.low_price = min(ret_bar.low_price, bar.low_price)
                    ret_bar.close_price = bar.close_price
                    ret_bar.volume += int(bar.volume)
                    ret_bar.open_interest = bar.open_interest

        return ret_bar



    def getTime(self) -> datetime:
        return self.market.getToday()



    def getKBarMintuePool(self,code:str)->KBarMintuePool:
        bar_poll = self.market.getNoticeData(code,"real_time_bar_poll")
        if bar_poll is None:
            bar_poll = KBarMintuePool(code)
            self.market.putNoticeData(code,"real_time_bar_poll",bar_poll)
        return bar_poll


class HistoryImpl(Market2.History):

    def __init__(self, market:Market2):
        self.market = market

    def getKbars(self, code: str, count: int) -> Sequence["BarData"]:

        today = self.market.getToday()
        if(today is None):
            raise RuntimeError("market doese not set current time")
        bar_pool = self.getKBarPool(code)
        return bar_pool.getData(today,count)

    def clean(self, code):
        today = self.market.getToday()
        if (today is None):
            raise RuntimeError("market doese not set current time")
        bar_pool = self.getKBarPool(code)
        bar_pool.clean()

    def getKbarFrom(self, code: str, start: datetime) -> Sequence["BarData"]:
        today = self.market.getToday()
        if (today is None):
            raise RuntimeError("market doese not set current time")
        if(start >= today):
            raise RuntimeError("start time must be < today")

        bar_pool = self.getKBarPool(code)
        return bar_pool.getDataFrom(start,today)

    def getKBarPool(self,code:str)->KBarPool:
        bar_poll = self.market.getNoticeData(code,"history_bar_poll")
        if bar_poll is None:
            bar_poll = KBarPool(code)
            self.market.putNoticeData(code,"history_bar_poll",bar_poll)
        return bar_poll




class Market2Impl(Market2):

    def __init__(self):
        self.history = HistoryImpl(self)
        self.realtime = RealTimeImpl(self)

    def getRealTime(self) -> Market2.RealTime:
        return self.realtime

    def getHistory(self) -> Market2.History:
        return self.history

    def nextTradeDay(self):
        raise RuntimeError("umimplement")

    def privoueTradeDay(self):
        raise RuntimeError("umimplement")


    def _checkOk(self, code: str):
        if (self._today is None):
            raise RuntimeError(f"you mut setToday() first.")
        if (not self.isNotice(code)):
            raise RuntimeError(f"you have not trace code = {code} yet.")
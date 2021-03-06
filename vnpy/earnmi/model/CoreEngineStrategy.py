

from abc import abstractmethod

from earnmi.model.CoreEngine import CoreEngine
from earnmi.model.Dimension import Dimension
from earnmi.model.PredictOrder import PredictOrder, PredictOrderStatus
from earnmi.model.op import OpLogType, OpLog
from vnpy.trader.object import BarData


class CoreEngineStrategy:

    def getName(self):
        return "unkonw"
    """
    策略是否允许该维度下面的数据。
    """
    def isSupport(self, engine: CoreEngine, dimen:Dimension)->bool:
        return True

    def onBeginOrder(self, order: PredictOrder, debugParams: {} = None):
        pass

    def onEndOrder(self, order: PredictOrder,lastBar:BarData, debugParams: {} = None):
        pass

    """准备开始一天的交易"""
    def onOpenTrade(self,order: PredictOrder,debugParams: {} = None):
        pass

    def onEndTrade(self,order: PredictOrder,bar:BarData,debugParams: {} = None):
        pass

    def onBar(self,order:PredictOrder,bar:BarData,debugParams: {} = None)->OpLog:
        pass


    """
    处理操作单
    0: 不处理
    1：做多
    2：做空
    3: 预测成功交割单
    4：预测失败交割单
    5：废弃改单
    """
    @abstractmethod
    def operatePredictOrder2(self, engine:CoreEngine, order: PredictOrder, bar:BarData, isTodayLastBar:bool, debugParams:{}=None) ->int:
        pass


class CommonStrategy(CoreEngineStrategy):

    def __init__(self):
        self.buy_day_max = 2  ## 设定买入交易的最大交易天数（将在这个交易日完成买入）
        self.max_day = 3  ##表示该策略的最大考虑天数，超过这个天数如果还没完成交割工作将强制割仓（类似止损止盈）
        self.buy_offset_pct = None #调整买入价格，3表示高于3%的价格买入，-3表示低于3%的价格买入 None表示没有限制。
        self.sell_offset_pct = None #调整买入价格，3表示高于3%的价格买入，-3表示低于3%的价格买入 None表示没有限制。
        self.sell_leve_pct_top = None  # sell_leve_pct的范围None表示没有限制
        self.sell_leve_pct_bottom = None
        self.buy_leve_pct_top = None  #buy_leve_pct的范围None表示没有限制
        self.buy_leve_pct_bottom = None

    def getName(self):
        return "CommonStrategy"

    def getParams(self,dimen_value:int):
        return None

    def initPrams(self,dimen: Dimension,debugParams: {}):
        if debugParams is None:
            debugParams = self.getParams(dimen.value)
        if debugParams is None:
            debugParams = {}
        if debugParams.__contains__('buy_day_max'):
            self.buy_day_max = debugParams['buy_day_max']
        if debugParams.__contains__('max_day'):
            self.max_day = debugParams['max_day']
        if debugParams.__contains__('buy_offset_pct'):
            self.buy_offset_pct = debugParams['buy_offset_pct']
        if debugParams.__contains__('sell_offset_pct'):
            self.sell_offset_pct = debugParams['sell_offset_pct']

        if debugParams.__contains__('sell_leve_pct_top'):
            self.sell_leve_pct_top = debugParams['sell_leve_pct_top']
        if debugParams.__contains__('sell_leve_pct_bottom'):
            self.sell_leve_pct_bottom = debugParams['sell_leve_pct_bottom']

        if debugParams.__contains__('buy_leve_pct_top'):
            self.buy_leve_pct_top = debugParams['buy_leve_pct_top']
        if debugParams.__contains__('buy_leve_pct_bottom'):
            self.buy_leve_pct_bottom = debugParams['buy_leve_pct_bottom']
        pass

    def onBeginOrder(self, order: PredictOrder, debugParams: {} = None):
        self.initPrams(order.dimen, debugParams)
        suggestSellPrice = order.suggestSellPrice
        suggestBuyPrice = order.suggestBuyPrice
        ##调整卖出价
        if not self.sell_offset_pct is None:
            selff_offset = self.sell_offset_pct / 100
            suggestSellPrice = suggestSellPrice * (1 + selff_offset)
        ##调整买入价
        if not self.buy_offset_pct is None:
            buy_offset = self.buy_offset_pct / 100
            suggestBuyPrice = suggestBuyPrice * (1 + buy_offset)
        if not self.buy_leve_pct_top is None or not self.buy_leve_pct_bottom is None:
            raise RuntimeError("暂未支持")
        order.strategySellPrice = suggestSellPrice
        order.strategyBuyPrice = suggestBuyPrice
        return OpLog(type=OpLogType.PLAIN, info="onBeginOrder")

    def onEndOrder(self, order: PredictOrder,lastBar:BarData, debugParams: {} = None):
        return OpLog(type=OpLogType.PLAIN, info="onEndOrder")

    """准备开始一天的交易"""
    def onOpenTrade(self,order: PredictOrder,debugParams: {} = None):
        return OpLog(type=OpLogType.PLAIN, info="onOpenTrade")

    def onEndTrade(self,order: PredictOrder,bar:BarData,debugParams: {} = None):
        return OpLog(type=OpLogType.PLAIN, info="onEndTrade")

    def onBar(self,order:PredictOrder,bar:BarData,debugParams: {} = None) ->OpLog:
        self.initPrams(order.dimen, debugParams)
        ocurrBar_close_price = order.predict.collectData.occurBars[-1].close_price
        sell_leve_pct = 100 * (order.suggestSellPrice - ocurrBar_close_price) / ocurrBar_close_price
        if not self.sell_leve_pct_top is None and sell_leve_pct > self.sell_leve_pct_top:
            return OpLog(type=OpLogType.ABANDON)
        if not self.sell_leve_pct_bottom is None and sell_leve_pct < self.sell_leve_pct_bottom:
            return OpLog(type=OpLogType.ABANDON)
        suggestSellPrice = order.strategySellPrice
        suggestBuyPrice = order.strategyBuyPrice

        if (order.status == PredictOrderStatus.HOLD):
            if bar.high_price >= suggestSellPrice:
                order.sellPrice = suggestSellPrice
                return OpLog(type = OpLogType.CROSS_SUCCESS,info =f"成功到达卖出价，操作单按预测成功完成！")
            if order.durationDay >= self.max_day:
                order.sellPrice = bar.close_price
                order.opTips = f"超过持有天数限制并强制减盈（减损），操作单未按预测成功！"
                return OpLog(type = OpLogType.CROSS_FAIL,info =order.opTips)
            order.isOverClosePct = 100 * (bar.close_price - suggestBuyPrice) / suggestBuyPrice  ##低价买入，是否想预期走势走高。
        elif order.status == PredictOrderStatus.READY:
            if order.durationDay > self.buy_day_max:
                # 超过买入交易时间天数，废弃
                order.opTips = f"超过考虑买入交易天数:{self.buy_day_max}"
                return OpLog(type = OpLogType.ABANDON,info =order.opTips)

            ##这天观察走势,且当天high_price 不能超过预测卖出价
            # 这里有个坑，
            # 1、如果当天是超过卖出价之后再跌到买入价，  这时第二天就要考虑止损
            # 2、如果是到底买入价之后的当天马上涨到卖出价，这时第二天就要考虑止盈
            # 不管是那种情况，反正第二天就卖出。
            if suggestBuyPrice >= bar.low_price:
                ##趋势形成的第二天买入。
                order.buyPrice = suggestBuyPrice
                ##当天是否盈利欺骗
                order.isWinCheatBuy = bar.high_price >= suggestSellPrice
                order.opTips = f"成功到底最低价并开始持有！！！，当天是否有超过卖出价:{order.isWinCheatBuy}"
                return OpLog(type = OpLogType.BUY_LONG,info =order.opTips)
        return None


    @abstractmethod
    def operatePredictOrder2(self, engine: CoreEngine, order: PredictOrder, bar: BarData, isTodayLastBar: bool,
                             debugParams: {} = None) -> int:
        self.initPrams(order.dimen, debugParams)
        ocurrBar_close_price = order.predict.collectData.occurBars[-1].close_price
        sell_leve_pct = 100 * (order.suggestSellPrice - ocurrBar_close_price) / ocurrBar_close_price
        if not self.sell_leve_pct_top is None and sell_leve_pct > self.sell_leve_pct_top:
            return OpLogType.ABANDON
        if not self.sell_leve_pct_bottom is None and sell_leve_pct < self.sell_leve_pct_bottom:
            return OpLogType.ABANDON
        suggestSellPrice = order.strategySellPrice
        suggestBuyPrice = order.strategyBuyPrice

        if (order.status == PredictOrderStatus.HOLD):
            if bar.high_price >= suggestSellPrice:
                order.sellPrice = suggestSellPrice
                order.opTips = f"成功到达卖出价，操作单按预测成功完成！"
                return OpLogType.CROSS_SUCCESS
            if isTodayLastBar and order.durationDay >= self.max_day:
                order.sellPrice = bar.close_price
                order.opTips = f"超过持有天数限制并强制减盈（减损），操作单未按预测成功！"
                return OpLogType.CROSS_FAIL
            order.isOverClosePct = 100 * (bar.close_price - suggestBuyPrice) / suggestBuyPrice  ##低价买入，是否想预期走势走高。
        elif order.status == PredictOrderStatus.READY:
            if order.durationDay > self.buy_day_max:
                # 超过买入交易时间天数，废弃
                order.opTips = f"超过考虑买入交易天数:{self.buy_day_max}"
                return OpLogType.ABANDON

            ##这天观察走势,且当天high_price 不能超过预测卖出价
            # 这里有个坑，
            # 1、如果当天是超过卖出价之后再跌到买入价，  这时第二天就要考虑止损
            # 2、如果是到底买入价之后的当天马上涨到卖出价，这时第二天就要考虑止盈
            # 不管是那种情况，反正第二天就卖出。
            if suggestBuyPrice >= bar.low_price:
                ##趋势形成的第二天买入。
                order.buyPrice = suggestBuyPrice
                ##当天是否盈利欺骗
                order.isWinCheatBuy = bar.high_price >= suggestSellPrice
                order.opTips = f"成功到底最低价并开始持有！！！，当天是否有超过卖出价:{order.isWinCheatBuy}"
                return OpLogType.BUY_LONG
        return OpLogType.PLAIN

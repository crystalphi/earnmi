from datetime import datetime, timedelta
from earnmi.chart.Chart import Chart
from earnmi.data.HistoryBarPool import HistoryBarPool
from earnmi.data.Market import Market
from vnpy.trader.constant import Interval, Exchange
from vnpy.trader.database import database_manager
from earnmi.data import import_data_from_jqdata

def assertEqual(d1, d2):
    if( not d1.__eq__(d2)):
        raise AssertionError(f"asset fail!,d1={d1},d2={d2}")

def assertLittle(d1, d2):
    if (not d1.__le__(d2)):
        raise AssertionError(f"asset fail!,d1={d1},d2={d2}")

code = "300004"
startDate = datetime(2019,4,1)
endDate = datetime(2020,5,1)
today = datetime(2020,3,24)
keepN = 88

market = Market(200,startDate,endDate)

market.addTrace(code)
market.setToday(today)


mituesBars = market.getTodayMinitueBar(code)
print(mituesBars)

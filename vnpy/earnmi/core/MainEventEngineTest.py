from datetime import datetime, timedelta
from time import sleep

from earnmi.core.MainEventEngine import MainEventEngine


class Asserter:

    def __init__(self):
        self.last_log_time: datetime = None
        self.engine: MainEventEngine = MainEventEngine()

    def log(self, time: datetime, msg):
        """
        坚持log日志是否按顺序打印。
        """
        print(f"[{time}]: {msg}")
        if not self.last_log_time is None:
            if self.last_log_time > time:
                raise RuntimeError("Asseert.log:日志时间顺序错误")
        self.last_log_time = time

    def eventOccurAt(self, time: datetime, msg: str):
        """
        确保在指定时间点执行。
        """
        asserter.log(time, msg)
        real_occur_time = self.engine.now()
        second = (time.timestamp() - real_occur_time.timestamp())
        if abs(second) > 0.1:
            raise RuntimeError(f"eventOccurAt:时间发生时期期望错误，期望在:{time},实际:{real_occur_time}，相差: {second}")

    def sleep(self, second:int):
        if self.engine.is_backtest:
            ##回测环境，挑战到下一个执行点。
            startTime = self.engine.now();
            self.engine.go(second);
            endTime = self.engine.now();
            duration_sec = endTime.timestamp() - startTime.timestamp()
            assert duration_sec - second >= 0.0

        else:
            sleep(second)


"""
测试用例。
"""


def case1(asserter: Asserter):
    engine: MainEventEngine = asserter.engine
    timePoint = engine.now()
    asserter.log(timePoint, "设置时间基础点")
    engine.postDelay(2, asserter.eventOccurAt, {"time": timePoint + timedelta(seconds=2), "msg": "2s后发生"})  ##时间在一秒后发生。
    asserter.sleep(1) ##等待1s
    engine.postDelay(0,asserter.eventOccurAt, {"time": timePoint + timedelta(seconds=1), "msg": "1s后发生"})  ##时间在10秒后发生。

    engine.postDelay(0,(lambda: print(f'lambda timePoint:{timePoint}')))



handler_event_count = 1

def casePostEvent(asserter: Asserter):
    asserter.sleep(3) ##等待3s
    engine: MainEventEngine = asserter.engine
    timePoint = engine.now()
    asserter.log(timePoint, "设置postEvent时间基础点")
    event_name = "event1"
    global handler_event_count
    handler_event_count = 1
    def handlerEventOnlyOne(event:str,data):
        global handler_event_count
        assert  event == event_name
        assert  handler_event_count == 1
        handler_event_count += 1
        print(f"[{engine.now()}]: handlerEventOnlyOne,count:{handler_event_count}")
        return False

    event_data = {}
    event_data['T'] = 1
    def handlerEventManyTime(event: str, event_data):
        event_data['T'] += 1
        assert  event == event_name
        print(f"[{engine.now()}]: handlerEventManyTime, handlerEventManyTime count:{event_data['T']}")

    engine.register(event_name,handlerEventOnlyOne)
    engine.register(event_name,handlerEventManyTime)

    engine.post_event(event_name,event_data)
    engine.post_event(event_name,event_data)
    engine.post_event(event_name,event_data)
    engine.post_event(event_name,event_data)
    engine.post_event("other_event1")
    engine.post_event("other_event2")
    asserter.sleep(1) ##等待1s
    engine.unregister(event_name,handlerEventOnlyOne)
    engine.unregister(event_name,handlerEventOnlyOne)
    engine.unregister(event_name,handlerEventManyTime)
    engine.post_event(event_name,event_data)
    engine.post_event(event_name,event_data)
    engine.post_event(event_name,event_data)
    asserter.sleep(1) ##等待1s
    assert handler_event_count == 2
    assert event_data['T'] == 5

casePostTimer_count = 0

def casePostTimer(asserter: Asserter):
    engine: MainEventEngine = asserter.engine
    global casePostTimer_count

    casePostTimer_count = 0
    def do_3_time():
        asserter.log(engine.now(), "do_3_time()")
        global casePostTimer_count
        casePostTimer_count += 1
        return casePostTimer_count < 3

    timePoint = engine.now()
    asserter.log(timePoint, "设置casePostTimer时间基础点")
    engine.postTimer(2, do_3_time,delay_second=3)
    asserter.sleep(2)
    assert casePostTimer_count == 0
    asserter.sleep(2)
    assert casePostTimer_count == 1
    asserter.sleep(2)
    assert casePostTimer_count == 2
    asserter.sleep(2)
    assert casePostTimer_count == 3
    asserter.sleep(2)
    assert casePostTimer_count == 3
    asserter.sleep(20)
    assert casePostTimer_count == 3

    ###使用job.cancel方式停止
    casePostTimer_count = 0
    def do_timer():
        asserter.log(engine.now(), "do_timer()")
        global casePostTimer_count
        casePostTimer_count += 1
    job = engine.postTimer(2, do_timer)
    asserter.sleep(1)
    assert casePostTimer_count == 1
    asserter.sleep(2)
    assert casePostTimer_count == 2
    asserter.sleep(2)
    assert casePostTimer_count == 3
    job.cancel()
    job.cancel()
    asserter.sleep(2)
    job.cancel()
    assert casePostTimer_count == 3
    asserter.sleep(2)
    assert casePostTimer_count == 3
    asserter.sleep(2)
    assert casePostTimer_count == 3


    pass


def checkRealTimeCase(asserter: Asserter):
    """
    实盘环境信息查看
    """
    engine: MainEventEngine = asserter.engine
    print(f"[{engine.now()}]: checkRealTimeCase，请手动更新系统时间查看日志情况")
    def wake_up_ui_thread():
        print(f"[{engine.now()}]: wake_up_ui_thread")

    engine.postTimer(5,wake_up_ui_thread)


def testAllCase(asserter: Asserter):


    engine: MainEventEngine = asserter.engine
    if engine.is_backtest:
        case1(asserter)
        casePostEvent(asserter)
        casePostTimer(asserter)
        asserter.engine.go(3600 * 24 * 10)  ##开始回撤执行。
    else:
        checkRealTimeCase(asserter)


def onDayChanged(engine:MainEventEngine):
    print(f"[{engine.now()}]: onDayChanged")

def onDayChangedEvent(event:str,engine:MainEventEngine):
    print(f"[{engine.now()}]: onDayChanged =>{event}")

###测试实盘环境
start = datetime(year=2019, month=6, day=30, hour=23)
end = datetime(year=2019, month=9, day=30, hour=23)


asserter = Asserter()  ###回测环境。
asserter.engine.register(MainEventEngine.EVNET_DAY_CHANED,onDayChangedEvent)
asserter.engine.run_backtest(start)
#asserter.engine.run()

testAllCase(asserter)


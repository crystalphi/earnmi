import datetime
from abc import abstractmethod
from pathlib import Path
from typing import Callable, Any

from earnmi.core.MainEventEngine import MainEventEngine
from earnmi.uitl.utils import utils


class Context:

    def __init__(self, engine:MainEventEngine):
        ##主线程环境
        self.engine: MainEventEngine = engine

    def post_at(self, hour_minute_second, function: Callable, args={},run_if_miss_time = False):
        """
        指定今天时间点并提交到主线程，。
        参数:
            hour_minute_second : 格式： "10:15:23"
            function：执行函数
            args：执行函数参数
            run_if_miss_time 如果今天启动时，错过时间点时的处理方式。  为True时，表示依旧处理。 为False是，表示不处理。
        """

        if not self.engine.is_running():
            raise RuntimeError("App main thread is not running")
        from earnmi.core.RunnerManager import parse_hour_minute_second

        now = self.engine.now()
        hour,minute,second = parse_hour_minute_second(hour_minute_second)
        at_time = utils.changeTime(now, hour=hour, minute=minute, second=second)
        second =  int( at_time.timestamp() - now.timestamp() + 0.45)
        if second < 0 and not run_if_miss_time:
            return
        return self.post_delay(second,function,args)


    def post(self, function: Callable, args={}):
        """
        提交到主线程执行。
        """
        return self.post_delay(0, function, args)

    def post_delay(self, second: int, function: Callable, args={}):
        """
        提交到主线程，并延迟second秒执行。
        """
        if not self.engine.is_running():
            raise RuntimeError("App main thread is not running")
        return self.engine.postDelay(second, function, args)

    def post_event(self,event:str,data:Any=None):
        """
        提交事件处理。
        """
        if not self.engine.is_running():
            raise RuntimeError("App main thread is not running")
        return self.engine.post_event(event,data)

    def post_timer(self,timer_second,callback:Callable,args:dict = {},delay_second:int =0):
        """
        提交定时器处理。
        """
        if not self.engine.is_running():
            raise RuntimeError("App main thread is not running")
        return self.engine.postTimer(timer_second,callback,args,delay_second)

    def now(self) -> datetime:
        """
        获取当前时间。(实盘环境的对应的是当前时间，回撤环境对应的回撤时间）。
        """
        return self.engine.now();

    def is_backtest(self) -> bool:
        """
        是否在回测环境下运行。
        """
        return self.engine.is_backtest

    def is_mainThread(self) -> bool:
        """
        是否在主线程环境
        """
        return self.engine.inCallableThread()

    def log_i(self, msg: str):
        print(f"[{self.engine.now()}|{self.is_mainThread()}]: {msg}")

    def log_d(self, msg: str):
        print(f"[{self.engine.now()}|{self.is_mainThread()}]: {msg}")

    def log_w(self, msg: str):
        print(f"[{self.engine.now()}|{self.is_mainThread()}]: {msg}")

    def log_e(self, msg: str):
        print(f"[{self.engine.now()}|{self.is_mainThread()}]: {msg}")

    @abstractmethod
    def getDirPath(self, dirName,create_if_no_exist =True)->Path:
        """
        获取文件目录
        """
        raise RuntimeError("未实现")

    @abstractmethod
    def getFilePath(self, dirName:str,fileName:str)->Path:
        """
        获取文件目录
        """
        raise RuntimeError("未实现")

    # def getRunnerManager(self)->RunnerManager:
    #     raise RuntimeError("未实现")

class ContextWrapper(Context):

    def __init__(self, context:Context):
        ##主线程环境
        self._context = context

    def post(self, function: Callable, args={}):
        """
        提交到主线程执行。
        """
        self._context.post_delay(0, function, args)

    def post_delay(self, second: int, function: Callable, args={}):
        """
        提交到主线程，并延迟second秒执行。
        """
        if not self.engine.is_running():
            raise RuntimeError("App main thread is not running")
        self._context.engine.postDelay(second, function, args)


    def now(self) -> datetime:
        """
        获取当前时间。(实盘环境的对应的是当前时间，回撤环境对应的回撤时间）。
        """
        return self._context.engine.now();

    def is_backtest(self) -> bool:
        """
        是否在回测环境下运行。
        """
        return self._context.is_backtest()

    def is_mainThread(self) -> bool:
        """
        是否在主线程环境
        """
        return self._context.engine.inCallableThread()

    def log_i(self, msg: str):
        self._context.log_i(msg)

    def log_d(self, msg: str):
        self._context.log_d(msg)

    def log_w(self, msg: str):
        self._context.log_w(msg)

    def log_e(self, msg: str):
        self._context.log_e(msg)



    @abstractmethod
    def getDirPath(self, dirName,create_if_no_exist =True):
        return self._context.getDirPath(dirName,create_if_no_exist)

    @abstractmethod
    def getFilePath(self, dirName:str,fileName:str):
        return self._context.getFilePath(dirName,fileName)



    # def getRunnerManager(self)->RunnerManager:
    #     return self._context.getRunnerManager()



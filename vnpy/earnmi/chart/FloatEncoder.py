

"""
 预测值数据
"""
from dataclasses import dataclass
from functools import cmp_to_key
import numpy as np




"""
  浮点值范围编码值
"""
class FloatEncoder:

    MAX_VALUE = 9999999
    MIN_VALUE = -MAX_VALUE

    def __init__(self,splits:['float']):
        self.splits = splits
        self.n = len(splits)
        pass

    def shift(self,shift:float):
        new_splits = np.array(self.splits)
        new_splits = new_splits + shift
        return FloatEncoder(list(new_splits))
    """
    掩码值
    """
    def mask(self) ->int:
        return self.n + 1

    """
    编码值
    """
    def encode(self,value:float)->int:
        if value is None:
            return None
        code = 0
        for i in range(self.n, 0, -1):
            if value >= self.splits[i - 1]:
                code = i
                break
        return code

    """
    分析编码值的代表范围,返回(min,max]的值范围
    """
    def parseEncode(self,encode:int):
        if encode < 0 or encode > self.n:
            raise RuntimeError("out of range encode")
        if encode == 0:
            return FloatEncoder.MIN_VALUE,self.splits[encode]
        if encode < self.n:
            return self.splits[encode-1],self.splits[encode]
        return self.splits[self.n - 1],FloatEncoder.MAX_VALUE

    def descriptEncdoe(self,encode:int):
        left,right = self.parseEncode(encode)

        return f"[{left},{right}]"

def FloatRangeCompare(d1, d2):
    return d1.probal - d2.probal

@dataclass
class FloatRange(object):
    """
    FloatEncoder里的编码值
    """
    encode:int
    """
    概率或者分布概率值
    """
    probal:float

    def sort(lists:['FloatRange'],reverse = True)->['FloatRange']:
        return sorted(lists, key=cmp_to_key(FloatRangeCompare), reverse=reverse)
    
    @staticmethod
    def toStr(ranges:['FloatRange'],encoder:FloatEncoder)->str:
        info = "["
        for i in range(0, len(ranges)):
            r: FloatRange = ranges[i]
            min, max = encoder.parseEncode(r.encode)
            info += f"({min}:{max})=%.2f%%," % (100 * r.probal)
        return info + "]"

if __name__ == "__main__":
    pct_split = [-7, -5, -3, -1.5, -0.5, 0.5, 1.5, 3, 5, 7]
    pctEncoder = FloatEncoder(pct_split)


    print(f"pctEncoder.encode(-6.2) : {pctEncoder.descriptEncdoe(pctEncoder.encode(-6.2))}")
    print(f"pctEncoder.encode(2.2) : {pctEncoder.descriptEncdoe(pctEncoder.encode(2.2))}")
    print(f"pctEncoder.encode(-7.1) : {pctEncoder.descriptEncdoe(pctEncoder.encode(-7.1))}")
    print(f"pctEncoder.encode(-7) : {pctEncoder.descriptEncdoe(pctEncoder.encode(-7))}")
    print(f"pctEncoder.encode(-7.3) : {pctEncoder.descriptEncdoe(pctEncoder.encode(-7.3))}")
    print(f"pctEncoder.encode(7.2) : {pctEncoder.descriptEncdoe(pctEncoder.encode(7.2))}")
    print(f"pctEncoder.encode(7) : {pctEncoder.descriptEncdoe(pctEncoder.encode(7))}")

    print(f"origin:{pctEncoder.splits}")
    assert  pctEncoder.encode(-6.5) == 1
    pctEncoder = pctEncoder.shift(0.9)
    assert  pctEncoder.encode(-6.5) == 0
    print(f"shift: {pctEncoder.splits}")

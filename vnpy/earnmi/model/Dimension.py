from dataclasses import dataclass

TYPE_3KAGO1 = 1

@dataclass
class Dimension(object):
    #类型
    type:int
    #维度的value值
    value:int



if __name__ == "__main__":

    d1 = Dimension(type=1,value =34)
    d2 = Dimension(type=1,value =34)
    d3=d2
    assert  d1 == d2
    assert  d1 == d3


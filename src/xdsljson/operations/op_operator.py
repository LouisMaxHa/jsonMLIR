from enum import Enum


class OperatorOp(Enum):
    plusOp = "+"
    minusOp = "-"
    timesOp = "*"
    divideOp = "/"
    plusFOp = "+f"
    minusFOp = "-f"
    timesFOp = "*f"
    andOp = "and"
    orOp = "or"
    xorOp = "xor"
    equalsOp = "=="
    notEqualsOp = "!="
    gtOp = ">"
    ltOp = "<"
    getOp = ">="
    letOp = "<="

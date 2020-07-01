import math

class tools:
    def convertFromMoneroFormat(self,price,currency="none"):
        lenghtPrice=len(str(price))
        Diff=0
        if lenghtPrice<12 and currency!='xBTC':
            Diff=12-lenghtPrice
            price=price*math.pow(10,Diff)
        price=price/math.pow(10,12)
        return price

    def convertToMoneroFormat(self,floatNumber):
        floatNumber=floatNumber*pow(10,12)
        floatNumber=math.trunc(floatNumber)
        return floatNumber
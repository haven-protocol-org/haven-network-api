import math

class tools:
    def convertFromMoneroFormat(self,price):
        lenghtPrice=len(str(price))
        if lenghtPrice<12:
            price=price*(10*(13-lenghtPrice))
        price=price/math.pow(10,12)
        return price

    def convertToMoneroFormat(self,floatNumber):
        floatNumber=floatNumber*pow(10,12)
        floatNumber=math.trunc(floatNumber)
        return floatNumber
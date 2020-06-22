import math

class tools:
    def calcMoneroPow(self,price):
        lenghtPrice=len(str(price))
        if lenghtPrice<12:
            price=price*(10*(13-lenghtPrice))
        price=price/math.pow(10,12)        
        return price


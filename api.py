import falcon
from mongodb import mongodb

class SupplyResource:
    def __init__(self):
        self.mydb=mongodb()

    def on_get(self, req, resp):
        
        quote = {
            'quote': (
                "I've always been more interested in "
                "the future than in the past."
            ),
            'author': 'Grace Hopper'
        }

        resp.media = quote

class InfoResource:
    def on_get(self, req, resp):
        

        resp.media = quote

api = falcon.API()
api.add_route('/supply', SupplyResource())
api.add_route('/info', InfoResource())


#importExchangePrice()
#main("","")

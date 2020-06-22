import falcon
import json 

import blockchain
import mongodb
from datetime import datetime
from datetime import timezone
from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin
from falcon_apispec import FalconPlugin
from marshmallow import Schema, fields
import calendar 

class InfoResource:
    def __init__(self):
        self.bc=blockchain.Blockchain()
    def on_get(self, req, resp):
        resp.body =json.dumps(self.bc.getInfo()['text'], ensure_ascii=False)
        resp.status=falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON


import falcon
import json 

from blockchain import blockchain
from mongodb import mongodb
from datetime import datetime
from datetime import timezone
from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin
from falcon_apispec import FalconPlugin
from marshmallow import Schema, fields
import calendar 

class InfoResource:
    def __init__(self):
        self.bc=blockchain()
    def on_get(self, req, resp):
        resp.body =json.dumps(self.bc.getInfo()['text'], ensure_ascii=False)
        resp.status=falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON


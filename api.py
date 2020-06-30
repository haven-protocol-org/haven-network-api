import falcon
from falcon_cors import CORS
from falcon_caching import Cache
cache = Cache(config={'CACHE_TYPE': 'simple'})
import os

import json 
from datetime import datetime
from datetime import timezone

from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin
from falcon_apispec import FalconPlugin

from marshmallow import Schema, fields

import libs.supply as supply
import libs.deviation as deviation
import libs.pricing as pricing
import libs.info as info

import calendar 


#Check variables
MANDATORY_ENV_VARS = ["hv_mongo_url", "hv_mongo_db","hv_daemon_url"]
for var in MANDATORY_ENV_VARS:
  if var not in os.environ:
    raise EnvironmentError("Failed because {} is not set.".format(var))

cors=CORS(allow_all_origins=True,allow_all_headers=True,  allow_all_methods=True)

api = falcon.API(middleware=[cors.middleware,cache.middleware])

class spec:
  def on_get(self, req, resp):
    # Create an APISpec       
    resp.body = json.dumps(spec.to_dict())
    resp.status=falcon.HTTP_200
    resp.content_type = falcon.MEDIA_JSON


infoResource=info.InfoResource()
api.add_route('/info', infoResource)

circulationSupplyResource=supply.CirculationSupplyResource()
api.add_route('/circulationSupply', circulationSupplyResource)

api.add_route('/doc', spec())

spec = APISpec(
  title='Swagger Haven Network',
  version='1.0.0',
  openapi_version='2.0',
  plugins=[
    FalconPlugin(api),
    MarshmallowPlugin()
  ],
  )

#spec.components.schema('Supply', schema=supply.SupplySchema)

spec.path(resource=infoResource)
spec.path(resource=circulationSupplyResource)
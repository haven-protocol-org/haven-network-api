import falcon
from falcon_cors import CORS

import json 
from datetime import datetime
from datetime import timezone
from mongodb import mongodb
from blockchain import blockchain
from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin
from falcon_apispec import FalconPlugin



from marshmallow import Schema, fields

import libs.supply as supply
import libs.deviation as deviation
import libs.pricing as pricing
import libs.info as info


import calendar 


cors=CORS(allow_all_origins=True,allow_all_headers=True,  allow_all_methods=True)

api = falcon.API(middleware=[cors.middleware])

class spec:
  def on_get(self, req, resp):
    # Create an APISpec       
    resp.body = json.dumps(spec.to_dict())
    resp.status=falcon.HTTP_200
    resp.content_type = falcon.MEDIA_JSON


supplyResource=supply.SupplyResource()
api.add_route('/supply', supplyResource)

infoResource=info.InfoResource()
api.add_route('/info', infoResource)

spotPricingResource=pricing.SpotPricingResource()
api.add_route('/spotPricing', spotPricingResource)

mAPricingResource=pricing.MAPricingResource()
api.add_route('/MApricing', mAPricingResource)

deviationHistoryResource=deviation.DeviationHistoryResource()
api.add_route('/deviationHistory', deviationHistoryResource)

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

spec.components.schema('Supply', schema=supply.SupplySchema)
spec.path(resource=supplyResource)
spec.path(resource=infoResource)
spec.path(resource=spotPricingResource)
spec.path(resource=mAPricingResource)
spec.path(resource=deviationHistoryResource)
spec.path(resource=circulationSupplyResource)
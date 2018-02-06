import pdb
import json
import os
from zuora_restful_python.zuora import Zuora



def initzuora(configfile):
    with open(configfile, 'r') as f:
        zuora_config = json.load(f)    
    return Zuora(zuora_config['user'], 
                zuora_config['password'], 
                endpoint=zuora_config['endpoint'])



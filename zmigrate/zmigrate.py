# -*- coding: utf-8 -*-


"""zmigrate.zmigrate: provides entry point main()."""


__version__ = "0.2.0"


import pdb
import sys
import os
import logging
import argparse

from .zuora import initzuora
from .zproductcatalog import ZuoraProductCatalog

ZUORA_CONFIGFILE_PRODUCTION = os.path.expanduser('~') + '/.zuora-production-config.json'
ZUORA_CONFIGFILE_SANDBOX = os.path.expanduser('~') + '/.zuora-sandbox-config.json'


    
def main():
    parser = argparse.ArgumentParser(description='Migrate Zuora product catalog')
    parser.add_argument('--version', action="store_true", default=False)
    parser.add_argument('--deploy', action="store_true", default=False)
    parser.add_argument('--verbose', action="store_true", default=False)

    args = parser.parse_args()

    if args.version:
        print("Executing zmigrate version %s." % __version__)
        exit()

    logger = logging.getLogger("zmigration")
    logger.setLevel(logging.INFO)
    fh = logging.FileHandler("../zmigration.log")
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    
    logger.info("Product Catalog migration started")
    

    zuora = initzuora(ZUORA_CONFIGFILE_PRODUCTION)

    catalog = ZuoraProductCatalog(zuora, args.verbose)
    if args.deploy:
        catalog.deploy(ZUORA_CONFIGFILE_SANDBOX)
        pass
    else:
        print('Product catalog was parsed but not deployed.')
        print('Deploying is a destructive operation')
        print('All existing products will be deleted (unless undeleteable because referenced by a subscription.)')
        print('If you want to deploy, add argument --deploy to command line')
        

    logger.info("Product Catalog migration completed")

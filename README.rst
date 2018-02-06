zuora-productcatalog-migrate
============================

A command line script for migrating zuora product catalog between instances.
For instance, it's very useful to migrate from production to a sandbox.

This is a very rough tool, not production quality!

Notes
-----

This is a DESTRUCTIVE process! It will delete as much of the product
catalog as it is able to, in the target instance. Be careful!

You will need to customize the lists of custom field names in zproductcatalog.py

You will need to create a custom field named ProductionId__c, on each of Product, ProductRatePlan, and ProductRatePlanCharge.
These are filled with the Id of the record that was copied. This script deletes
all existing products and writes all the products it finds in the source instance.
In future, the ProductionId__c fields might be able to be used to sync changes,
rather than deleting the entire catalog and creating anew.


You should also make sure that any existing products you want 
the script to be able to delete are not referenced by any subscriptions.
The easiest way to do this is to delete all the accounts.


Usage
-----

python3 zmigrate-runner.py --verbose --deploy --version


Will not actually deploy without --deploy argument (and is therefore safe)

--deploy argument WILL DELETE target instance product catalog!

Product catalog source instance is configured in '~/.zuora-production-config.json'
Product catalog target instance is configured in '~/.zuora-sandbox-config.json'



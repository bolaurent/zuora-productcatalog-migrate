# -*- coding: utf-8 -*-

import csv
import pdb
import logging

from .zuora import initzuora


logger = logging.getLogger("zmigration")

FIELDS = {

    'Product': [
        'Id',
        
        'Description',
        'EffectiveEndDate',
        'EffectiveStartDate',
        'Name',
        'SKU'
    ] + [
        'Discount_Schedule_Name__c'
    ],

    'ProductRatePlan': [
        'Id',
        
        'Description',
        'EffectiveEndDate',
        'EffectiveStartDate',
        'Name'
    ] + [
        'SFProductCode__c'
    ],

    'ProductRatePlanCharge': [
        'Id',
        
        'AccountingCode',
        'ApplyDiscountTo',
        'BillCycleDay',
        'BillCycleType',
        'BillingPeriod',
        'BillingPeriodAlignment',
        'BillingTiming',
        'ChargeModel',
        'ChargeType',
        'DefaultQuantity',
        'DeferredRevenueAccount',
        'Description',
        'DiscountLevel',
        'EndDateCondition',
        'IncludedUnits',
        'ListPriceBase',
        'MaxQuantity',
        'MinQuantity',
        'Name',
        'NumberOfPeriod',
        'OverageCalculationOption',
        'OverageUnusedUnitsCreditOption',
        'PriceChangeOption',
        'PriceIncreasePercentage',
        'RecognizedRevenueAccount',
        'RevenueRecognitionRuleName',
        'RevRecCode',
        'RevRecTriggerCondition',
        'SmoothingModel',
        'SpecificBillingPeriod',
        'Taxable',
        'TaxCode',
        'TaxMode',
        'TriggerEvent',
        'UOM',
        'UpToPeriods',
        'UpToPeriodsType',
        'UsageRecordRatingOption',
        'UseDiscountSpecificAccountingCode',
        'UseTenantDefaultForPriceChange',
        'WeeklyBillCycleDay'
    ],

    'ProductRatePlanChargeTier': [
        'Id',

        'Currency',
        'DiscountAmount',
        'DiscountPercentage',
        'EndingUnit',
        'Price',
        'PriceFormat',
        'StartingUnit',
        'Tier'
    ]
}


def split_record(record):
    objects = {
        'Product': {},
        'ProductRatePlan': {},
        'ProductRatePlanCharge': {},
        'ProductRatePlanChargeTier': {}
    }

    for key, val in record.items():
        object, field = key.split('.')
        objects[object][field] = val

    return objects
    

def remove_blank_fields(record):
    remove_fields = []
    for field, val in record.items():
        if val == '':
            remove_fields.append(field)

    for field in remove_fields:
            del record[field]

    return record
   
OBJECT_HIERARCHY = {
    'ProductRatePlan': 'Product',
    'ProductRatePlanCharge': 'ProductRatePlan',
    'ProductRatePlanChargeTier': 'ProductRatePlanCharge'
}

class ZuoraProductCatalog(object):

    def __init__(self, zuora, verbose=False):
        self.zuora = zuora
        self.verbose = verbose

        self.records_by_id = self.parse_catalog()
            

    def join_object_fields(self, objectname, fields):
        return ', '.join(['{}.{}'.format(objectname, field) for field in fields])

    def join_objects(self):
        return ', '.join([self.join_object_fields(objectname, FIELDS[objectname]) for objectname in FIELDS.keys()])

    def pull_catalog(self):
        if self.verbose:
            print('querying source instance...')
        query = 'select {} from ProductRatePlanChargeTier'.format(self.join_objects())
        query += " where Product.EffectiveEndDate >= '2018-01-01' "
        # query += " and Product.Name = 'Landscape'"
        csv_data = self.zuora.query_export(query).split('\n')
        records = [
            record 
            for record in csv.DictReader(csv_data) 
            if not 'DEACTIVATED' in record['Product.Name'].upper()
            and not 'DEACTIVATED' in record['ProductRatePlan.Name'].upper()
        ]
        return records

    def parse_catalog(self):
        records_by_id = {
            'Product': {},
            'ProductRatePlan': {},
            'ProductRatePlanCharge': {},
            'ProductRatePlanChargeTier': {}
        }

        for record in self.pull_catalog():
            records_by_object_name = split_record(record)
            for objectname in records_by_id:
                obj = records_by_object_name[objectname]
                id = obj['Id']
                if id not in records_by_id[objectname]:
                    if objectname in OBJECT_HIERARCHY:
                        parent_object_name = OBJECT_HIERARCHY[objectname]
                        obj[OBJECT_HIERARCHY[objectname] + 'Id'] = records_by_object_name[parent_object_name]['Id']
                    records_by_id[objectname][id] = obj
        return records_by_id

    def make_deployable_record(self, record):
        deployable_record = record.copy()
        deployable_record['ProductionId__c'] = deployable_record['Id']
        del deployable_record['Id']
        for object_name in self.records_by_id:
            field_name = object_name + 'Id'
            if field_name in deployable_record:
                source_id = deployable_record[field_name]
                if source_id not in self.targetid_by_sourceid:
                    pdb.set_trace()
                mapped_id = self.targetid_by_sourceid[source_id]
                deployable_record[field_name] = mapped_id

        if 'AccountingCode' in deployable_record:
            try:
                deployable_record['ProductRatePlanChargeTierData'] = {
                    'ProductRatePlanChargeTier': [
                        prpct 
                        for prpct in self.records_by_id['ProductRatePlanChargeTier'].values() 
                        if 'ProductRatePlanChargeId' in prpct and prpct['ProductRatePlanChargeId'] == record['Id']
                    ]
                }
            except KeyError:
                pdb.set_trace()

            for r in deployable_record['ProductRatePlanChargeTierData']['ProductRatePlanChargeTier']:
                del r['Id']
                del r['ProductRatePlanChargeId']
                remove_blank_fields(r)

        remove_blank_fields(deployable_record)
        if 'ChargeType' in deployable_record and deployable_record['ChargeType'] == 'OneTime':
            if 'EndDateCondition' in record:
                del deployable_record['EndDateCondition']
        
        return deployable_record


    def delete_products(self, target_zuora):
        for product in target_zuora.query_all('select id, name from product'):
            response = target_zuora.delete('Product', [product['Id']])
            if not response[0]['success']:
                logger.error(response)
            

    def deploy(self, target_config_file):
        target_zuora = initzuora(target_config_file)

        self.delete_products(target_zuora)

        self.targetid_by_sourceid = {}

        for objectname in ['Product', 'ProductRatePlan', 'ProductRatePlanCharge']:
            for id, record in self.records_by_id[objectname].items():
                if self.verbose:
                    if 'Name' in record:
                        print('deploying ', record['Name'])
                    else:
                        print(record['Currency'], record['Price'])
            
                deployable_record = self.make_deployable_record(record)
                logger.info(objectname)
                logger.info(deployable_record)

                response = target_zuora.create_object(objectname, deployable_record)
                logger.info(response)

                self.targetid_by_sourceid[id] = response['Id']

        if self.verbose:
            print('activating currencies...')
        for prp_source_id in self.records_by_id['ProductRatePlan']:
            if prp_source_id in self.targetid_by_sourceid:
                prp_target_id = self.targetid_by_sourceid[prp_source_id]
                response = self.zuora.query("select Id, ActiveCurrencies from ProductRatePlan where Id = '{}'".format(prp_source_id))
                assert response['size'] == 1
                currencies = response['records'][0]['ActiveCurrencies']
                try:
                    target_zuora.update_object('ProductRatePlan', prp_target_id, {'ActiveCurrencies': currencies})
                except AssertionError:
                    logger.error(prp_target_id, currencies, 'fail')
                    pass
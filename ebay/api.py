#!/usr/bin/env
# -*- coding: utf-8 -*-
import sys
import os.path
import json
import datetime
import logging
import requests

import xmltodict
import requests


logger = logging.getLogger(__name__)


class eBayAPI(object):

    @staticmethod
    def _get_file_path(input_path):
        return os.path.join(os.path.dirname(__file__), input_path)

    @staticmethod
    def Trading(config_file='../.config.json'):
        config = Config(self._get_file_path(config_file))
        return Trading(
            auth_token=config.token, app_id=config.app_id,
            cert_id=config.cert_id, dev_id=config.dev_id,
            xmlns='urn:ebay:apis:eBLBaseComponents',
            endpoint='https://api.ebay.com/ws/api.dll',
            service=None
        )

    @staticmethod
    def Finding(config_file='../.config.json'):
        config = Config(self._get_file_path(config_file))
        return Finding(
            auth_token=config.token, app_id=config.app_id,
            cert_id=config.cert_id, dev_id=config.dev_id,
            xmlns='http://www.ebay.com/marketplace/search/v1/services',
            endpoint='http://svcs.ebay.com/services/search/FindingService/v1',
            service='FindingService'
        )

    @staticmethod
    def FileTransfer(config_file='../.config.json'):
        config = Config(self._get_file_path(config_file))
        return FileTransfer(
            auth_token=config.token, app_id=config.app_id,
            cert_id=config.cert_id, dev_id=config.dev_id,
            xmlns='http://www.ebay.com/marketplace/services',
            endpoint='https://storage.ebay.com/FileTransferService',
            service='FileTransferService'
        )

    @staticmethod
    def BulkDataExchange(config_file='../.config.json'):
        config = Config(self._get_file_path(config_file))
        return BulkDataExchange(
            auth_token=config.token, app_id=config.app_id,
            cert_id=config.cert_id, dev_id=config.dev_id,
            xmlns='http://www.ebay.com/marketplace/services',
            endpoint='https://webservices.ebay.com/BulkDataExchangeService',
            service='BulkDataExchangeService'
        )


class Config(object):

    def __init__(self, config_file):
        config = self._get_config(config_file)
        self._token = config['Token'],
        self._app_id = config['App_ID']
        self._dev_id = config['Dev_ID']
        self._cert_id = config['Cert_ID']
        self._endpoint = config['End_Point']

    def _get_config(self, config_file):
        try:
            with open(config_file, 'r') as c:
                config = json.load(c)
        except IOError as e:
            logger.error('%s not found.' % config_file)
            raise e
        return config

    @property
    def token(self):
        return self._token

    @property
    def app_id(self):
        return self._app_id

    @property
    def dev_id(self):
        return self._dev_id

    @property
    def cert_id(self):
        return self._cert_id


class eBayRequest(object):

    def __init__(self, auth_token, app_id, cert_id, dev_id,
                 method, service, xmlns, endpoint, parsexml=True):
        self.endpoint = endpoint
        self.method = method
        self.dev_id = dev_id
        self.app_id = app_id
        self.cert_id = cert_id
        self.auth_token = auth_token
        self.service = service
        self.xmlns = xmlns
        self.parsexml = parsexml
        self.params = {}
        self.headers = {
            'X-EBAY-API-DETAIL-LEVEL': 0,
            'X-EBAY-API-CALL-NAME': self.method,
            'X-EBAY-API-DEV-NAME': self.dev_id,
            'X-EBAY-API-APP-NAME': self.app_id,
            'X-EBAY-API-CERT-NAME': self.cert_id,
            'X-EBAY-API-COMPATIBILITY-LEVEL': 835,
            'X-EBAY-API-SITEID': 0,
            'X-EBAY-SOA-OPERATION-NAME': self.method,
            'X-EBAY-SOA-SERVICE-NAME': self.service,
            'X-EBAY-SOA-SECURITY-APPNAME': self.app_id,
            'X-EBAY-SOA-SECURITY-TOKEN': self.auth_token,
            'X-EBAY-SOA-SERVICE-VERSION': '1.1.0',
            'X-EBAY-SOA-GLOBAL-ID': 'EBAY-US',
            'X-EBAY-SOA-REQUEST-DATA-FORMAT': 'XML',
            'CONTENT-TYPE': 'text/xml;charset="UTF-8"'
        }

    def __str__(self):
        req_name = '%sRequest' % self.method
        xml = {
            req_name: {
                '@xmlns': self.xmlns,
            }
        }
        for k, v in self.params.iteritems():
            v = str(v) if type(v) is unicode else v
            k = str(k) if type(k) is unicode else k
            xml[req_name][k] = v
        return xmltodict.unparse(xml, pretty=True, indent='  ')

    def _handle_errors(self, response):
        try:
            ack = response['Ack']
        except:
            ack = response['ack']
        if 'Errors' in response:
            errors = response['Errors']
            errors = errors if isinstance(errors, list) else [errors]
        else:
            errors = []
        
        for err in errors:
            level = str(err['SeverityCode'])
            if level == 'Warning':
                logger.warning('%s', err['LongMessage'])
            elif level == 'Error':
                logger.error('%s', err['LongMessage'])

        return self

    def execute(self, stream=False):
        logger.debug('Executing %s Request:\n%s', self.method, self)
        try:
            response = requests.post(
                url=self.endpoint, headers=self.headers,
                stream=stream, data=str(self)
            )
        except requests.ConnectionError as e:
            logger.error('Error executing request: %s', e)
            return None

        if stream and not parsexml:
            logger.debug('Stream is on?  Not sure what we are doing.')
            response.raw.decode_content = True
            response = response.raw
        elif parsexml and not stream:
        else:
            response = xmltodict.parse(response.text)
            logger.debug('%s Response received:\n%s', self.method,
                xmltodict.unparse(response, pretty=True, indent='  ')
            )
        response = response[self.method + 'Response']
        self._handle_errors(response)
        return response


class eBayRequestFactory(object):

    def __init__(self, auth_token, app_id, cert_id, dev_id,
                 xmlns, endpoint, service=None):
        self._auth_token = auth_token
        self._app_id = app_id
        self._cert_id = cert_id
        self._dev_id = dev_id
        self._service = service
        self._xmlns = xmlns
        self._endpoint = endpoint

    def build(self, name, params=None, auth=False):
        request = eBayRequest(
            auth_token=self._auth_token,
            app_id=self._app_id,
            cert_id=self._cert_id,
            dev_id=self._dev_id,
            xmlns=self._xmlns,
            endpoint=self._endpoint,
            service=name if self._service is None else self._service,
            method=name
        )
        if params is not None and isinstance(params, dict):
            request.params.update(params)
        if auth:
            token = {
                'RequesterCredentials': {
                    'eBayAuthToken': self._auth_token
                }
            }
            request.params.update(token)
        return request


class Trading(eBayRequestFactory):

    def __init__(self, auth_token, app_id, cert_id, dev_id,
                 xmlns, endpoint, service):
        eBayRequestFactory.__init__(
            self, auth_token=auth_token, app_id=app_id, cert_id=cert_id,
            dev_id=dev_id, xmlns=xmlns, endpoint=endpoint, service=service
        )
        self.ADD_ITEMS_MAX = 5
        self.END_ITEMS_MAX = 10

    def leaveFeedback(self, feedback, itemId, target_user):
        name = 'LeaveFeedback'
        params = {
            'CommentText': feedback,
            'CommentType': 'Positive',
            'ItemID': itemId,
            'TargetUser': target_user
        }
        return self.build(name, params=params, auth=True).execute()

    def getItemsAwaitingFeedback(self, PageNumber=1, EntriesPerPage=200):
        name = 'GetItemsAwaitingFeedback'
        params = {
            'Pagination': {
                'EntriesPerPage': EntriesPerPage,
                'PageNumber': PageNumber
            }
        }
        return self.build(name, params=params, auth=True).execute()

    def getMyeBaySelling(self, PageNumber=1, EntriesPerPage=200):
        name = 'GetMyeBaySelling'
        params = {
            'ActiveList': {
                'Include': 'true',
                'Pagination': {
                    'EntriesPerPage': EntriesPerPage,
                    'PageNumber': PageNumber
                }
            }
        }
        return self.build(name, params=params, auth=True).execute()

    def getApiAccessRules(self):
        name = 'GetApiAccessRules'
        return = self.build(name).execute()

    def getSuggestedCategories(self, query):
        name = 'GetSuggestedCategories'
        query = (' '.join(query)) if isinstance(query, list) else query
        params = {
            'Query': query
        }
        return self.build(name, params=params, auth=True).execute()

    def getItem(self, itemId):
        name = 'GetItem'
        params = {
            'ItemID': itemId
        }
        return self.build(name, params=params).execute()

    def verifyAddItem(self, item):
        name = 'VerifyAddItem'
        params = item
        return self.build(name, params=params, auth=True).execute()

    def addItem(self, item, allow_warnings):
        name = 'AddItem'
        params = item
        request = self.build(name, params=params, auth=True)
        verified = self.verifyAddItem(item)
        ack = verified['Ack']
        if ack == 'Success' or (allow_warnings and ack == 'Warning'):
            return request.execute()
        else:
            return verified

    def addItems(self, item_array, allow_warnings):
        name = 'AddItems'
        params = {'AddItemRequestContainer': []}
        for item in item_array:
            verified = self.verifyAddItem(item)
            ack = verified['Ack']
            if ack == 'Success' or (allow_warnings and ack == 'Warning'):
                item['MessageID'] = item_array.index(item)
                params['AddItemRequestContainer'].append(item)
            else:
                logger.warning(
                    '%s was not able to be verified for adding.',
                    item['Item']['SKU']
                )

        return self.build(name, params=params, auth=True).execute()

    def reviseItem(self, item):
        name = 'ReviseItem'
        param_item = {
            'Item': {
                'ItemID': item['ItemID'],
                'SKU': item['SKU'],
                'StartPrice': item['StartPrice'],
                'Quantity': item['Quantity']
            }
        }
        return self.build(name, params=params).execute()

    def endItem(self, itemId):
        name = 'EndItem'
        params = {
            'EndingReason': 'NotAvailable',
            'ItemID': itemId
        }
        return self.build(name, params=params, auth=True).execute()

    def endItems(self, itemId_array):
        name = 'EndItems'
        params = {'EndItemRequestContainer': []}
        for itemId in itemId_array:
            container = {
                'MessageID': itemId_array.index(itemId),
                'EndingReason': 'NotAvailable',
                'ItemID': itemId
            }
            params['EndItemRequestContainer'].append(container)
        return self.build(name, params=params, auth=True).execute()

    def getOrders(self, PageNumber=1, EntriesPerPage=100):
        name = 'GetOrders'
        time_to = datetime.datetime.now()
        time_from = time_to - datetime.timedelta(hours=30)
        params = {
            'CreateTimeFrom': time_from.strftime('%Y-%m-%dT%H:%M:%S.000Z'),
            'CreateTimeTo': time_to.strftime('%Y-%m-%dT%H:%M:%S.000Z'),
            'DetailLevel': 'ReturnAll',
            'Pagination': {
                'EntriesPerPage': EntriesPerPage,
                'PageNumber': PageNumber
            }
        }
        return self.build(name, params=params, auth=True).execute()

    def getSellerList(self, PageNumber=1, EntriesPerPage=100):
        name = 'GetSellerList'
        time_to = datetime.datetime.now()
        time_from = time_to - datetime.timedelta(days=119)
        params = {
            'StartTimeFrom': time_from.strftime('%Y-%m-%dT%H:%M:%S.000Z'),
            'StartTimeTo': time_to.strftime('%Y-%m-%dT%H:%M:%S.000Z'),
            'DetailLevel': 'ReturnAll',
            'Pagination': {
                'EntriesPerPage': EntriesPerPage,
                'PageNumber': PageNumber
            }
        }
        return self.build(name, params=params, auth=True).execute()

    def geteBayDetails(self, DetailName):
        name = 'GeteBayDetails'
        params = {
            'DetailName': DetailName
        }
        return self.build(name, params=params, auth=True).execute()

    def completeSale(self, orderID, trackingNum, carrier):
        name = 'CompleteSale'
        params = {
            'ItemID': orderID,
            'Paid' : 'true',
            'Shipment' : {
                'ShippedTime': time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                'ShipmentTrackingDetails' : {
                    'ShipmentTrackingNumber': trackingNum,
                    'ShippingCarrierUsed': carrier
                }
            }
        }
        return self.build(name, params=params, auth=True).execute()

    def reviseInventoryStatus(self, item_array):
        name = 'ReviseInventoryStatus'
        params = {'InventoryStatus': []}
        for item in item_array:
            param_item = {
                'ItemID': item['ItemID'],
                'SKU': item['SKU'],
                'StartPrice': item['StartPrice'],
                'Quantity': item['Quantity']
            }
            params['InventoryStatus'].append(param_item)

        return self.build(name, params=params, auth=True).execute()


class Finding(eBayRequestFactory):

    def __init__(self, auth_token, app_id, cert_id, dev_id,
                 xmlns, endpoint, service):
        eBayRequestFactory.__init__(
            self, auth_token=auth_token, app_id=app_id, cert_id=cert_id,
            dev_id=dev_id, xmlns=xmlns, endpoint=endpoint, service=service
        )

    def getVersion(self):
        name = 'getVersion'
        return self.build(name).execute()

    def findItemsByKeywords(self, keywords):
        name = 'findItemsByKeywords'
        if isinstance(keywords, list):
            keywords = ' '.join(keywords)

        params = {
            'keywords': keywords
        }
        return self.build(name, params=params).execute()

    def findItemsbyCategory(self, categoryId):
        name = 'findItemsbyCategory'
        params = {
            'categoryId': categoryId
        }
        return self.build(name, params=params).execute()

    def findCompletedItems(self):
        name = 'findCompletedItems'
        params = {
        }
        return self.build(name, params=params).execute()


class BulkDataExchange(eBayRequestFactory):

    def __init__(self, auth_token, app_id, cert_id, dev_id,
                 xmlns, endpoint, service):
        eBayRequestFactory.__init__(
            self, auth_token=auth_token, app_id=app_id, cert_id=cert_id,
            dev_id=dev_id, xmlns=xmlns, endpoint=endpoint, service=service
        )

    def createRecurringJob(self, UUID, frequencyInMinutes, downloadJobType):
        name = 'createRecurringJob'
        params = {
            'UUID': UUID,
            'frequencyInMinutes': frequencyInMinutes,
            'downloadJobType': downloadJobType
        }
        request = self.build(name, params=params)
        return request.execute()

    def createUploadJob(self, UUID, uploadJobType):
        name = 'createUploadJob'
        params = {
            'UUID': UUID,
            'uploadJobType': uploadJobType
        }
        request = self.build(name, params=params)
        return request.execute()

    def deleteRecurringJob(self, recurringJobId):
        name = 'deleteRecurringJob'
        params = {
            'recurringJobId': recurringJobId
        }
        request = self.build(name, params=params)
        return request.execute()

    def getJobs(self, jobType):
        name = 'getJobs'
        params = {
            'jobType': jobType
        }
        request = self.build(name, params=params)
        return request.execute()

    def getJobStatus(self, jobId):
        name = 'getJobStatus'
        params = {
            'jobId': jobId
        }
        request = self.build(name, params=params)
        return request.execute()

    def getRecurringJobs(self):
        name = 'getRecurringJobs'
        request = self.build(name)
        return request.execute()

    def startDownloadJob(self, UUID, jobType):
        name = 'startDownloadJob'
        params = {
            'downloadJobType': jobType,
            'UUID': UUID,
            'downloadRequestFilter': {
                'activeInventoryReportFilter': {
                    'auctionItemDetails': {
                        'includeBidCount': 1,
                    }
                }
            }
        }
        request = self.build(name, params=params)
        return request.execute()

    def startUploadJob(self, jobId):
        name = 'startUploadJob'
        params = {
            'jobId': jobId,
        }
        request = self.build(name, params=params)
        return request.execute()


class FileTransfer(eBayRequestFactory):

    def __init__(self, auth_token, app_id, cert_id, dev_id,
                 xmlns, endpoint, service):
        eBayRequestFactory.__init__(
            self, auth_token=auth_token, app_id=app_id, cert_id=cert_id,
            dev_id=dev_id, xmlns=xmlns, endpoint=endpoint, service=service,
            parsexml=False
        )

    def downloadFile(self, fileReferenceId, taskReferenceId):
        name = 'downloadFile'
        params = {
            'fileReferenceId': fileReferenceId,
            'taskReferenceId': taskReferenceId
        }
        return self.build(name, params=params).execute(stream=True)

    def uploadFile(self):
        raise ImportError('Not implemented yet')


__all__ = ['eBayAPI']

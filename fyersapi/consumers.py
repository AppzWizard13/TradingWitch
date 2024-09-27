import json
from channels.generic.websocket import AsyncWebsocketConsumer,WebsocketConsumer
from fyers_apiv3.FyersWebsocket.data_ws import FyersDataSocket
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from fyers_apiv3.FyersWebsocket import order_ws
from django.conf import settings
from fyers_apiv3 import fyersModel
from fyers_apiv3.FyersWebsocket import data_ws
import hashlib
import requests
import hashlib
import requests
from channels.generic.websocket import WebsocketConsumer
from fyers_apiv3.FyersWebsocket import order_ws
from django.conf import settings
from account.models import CommonConfig
from fyersapi.views import get_data_instance
import time

class FyersPositionDataConsumer(WebsocketConsumer):
    def connect(self):
        self.accept()
        # Generate app_id_hash
        self.app_id = settings.FYERS_APP_ID
        secret_key = settings.FYERS_SECRET_ID
        app_id_hash = self.generate_app_id_hash(self.app_id, secret_key)
        pin = settings.FYERS_PIN_ID
        session = self.scope["session"]
        refresh_token = session.get("refresh_token")

        url = "https://api-t1.fyers.in/api/v3/validate-refresh-token"
        headers = {
            "Content-Type": "application/json"
        }
        data = {
            "grant_type": "refresh_token",
            "appIdHash": app_id_hash,
            "refresh_token": refresh_token,
            "pin": pin
        }

        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            json_response = response.json()
            access_token = json_response.get("access_token")
            access_token = self.app_id + ":" + access_token

            self.fyers = order_ws.FyersOrderSocket(
                access_token=access_token, 
                write_to_file=False,
                log_path="",
                on_connect=self.onopen,
                on_close=self.onclose,
                on_error=self.onerror,
                on_positions=self.onPosition,
            )
            self.fyers.connect()
        else:
            self.send(text_data=f"Error: {response.text}")

    def disconnect(self, close_code):
        self.close()

    def onopen(self):
        data_type = "OnPositions"
        self.fyers.subscribe(data_type=data_type)
        self.fyers.keep_running()

    def onPosition(self, message):
        self.send(text_data=f"Position Response: {message}")

    def onerror(self, message):
        self.send(text_data=f"Error: {message}")

    def onclose(self, message):
        self.send(text_data=f"Connection closed: {message}")

    @staticmethod
    def generate_app_id_hash(client_id, secret_key):
        concatenated_string = f"{client_id}:{secret_key}"
        hash_object = hashlib.sha256(concatenated_string.encode())
        return hash_object.hexdigest()

class FyersIndexDataConsumer(WebsocketConsumer):
    def connect(self):
        self.accept()

        self.last_keyword = self.scope['url_route']['kwargs']['last_keyword']  
        if self.last_keyword == "SENSEX":
            exchnage =  "BSE:"
        else:
            exchnage =  "NSE:"
            
        self.symbols = [exchnage + self.last_keyword + "-INDEX"]
        self.app_id = settings.FYERS_APP_ID
        secret_key = settings.FYERS_SECRET_ID
        app_id_hash = self.generate_app_id_hash(self.app_id, secret_key)
        pin = "2772"
        session = self.scope["session"]
        refresh_data = CommonConfig.objects.filter(param="refresh_token").first()
        refresh_token = refresh_data.value
        
        url = "https://api-t1.fyers.in/api/v3/validate-refresh-token"
        headers = {
            "Content-Type": "application/json"
        }
        data = {
            "grant_type": "refresh_token",
            "appIdHash": app_id_hash,
            "refresh_token": refresh_token,
            "pin": pin
        }

        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            json_response = response.json()
            self.access_token = json_response.get("access_token")
            self.getoptionsymbols = self.getOptionStrikes()
            self.fyers = data_ws.FyersDataSocket(
                access_token=self.access_token,
                log_path="",
                litemode=True,
                write_to_file=False,
                reconnect=True,
                on_connect=self.on_open,
                on_close=self.on_close,
                on_error=self.on_error,
                on_message=self.on_message
            )

            self.fyers.connect()
        else:
            self.send(text_data=f"Error: {response.text}")

    def disconnect(self, close_code):
        data_type = "SymbolUpdate"
        self.fyers.unsubscribe(symbols=self.allsymbols, data_type=data_type)
        self.close()

    def on_open(self):
        data_type = "SymbolUpdate"
        self.allsymbols = self.symbols + self.getoptionsymbols
        self.fyers.subscribe(symbols=self.allsymbols, data_type=data_type)
        self.fyers.keep_running()

    def on_message(self, message):
        self.send(text_data=f"{message}")

    def on_error(self, message):
        self.send(text_data=f"Error: {message}")

    def on_close(self, message):
        data_type = "SymbolUpdate"
        self.fyers.unsubscribe(symbols=self.allsymbols, data_type=data_type)
        self.close()
        self.send(text_data=f"Connection closed: {message}")

    @staticmethod
    def generate_app_id_hash(client_id, secret_key):
        concatenated_string = f"{client_id}:{secret_key}"
        hash_object = hashlib.sha256(concatenated_string.encode())
        return hash_object.hexdigest()
    
    def getOptionStrikes(self):
        self.fyers = fyersModel.FyersModel(client_id=self.app_id, is_async=False, token=self.access_token, log_path="")
        
        data = {
            "symbol": self.symbols[0],
            "strikecount": 1,
        }
        
        try:
            self.expiry_response = self.fyers.optionchain(data=data)
            first_expiry_ts = self.expiry_response['data']['expiryData'][0]['expiry']
            
            if first_expiry_ts:
                options_data = {
                    "symbol": self.symbols[0],
                    "strikecount": 4,
                    "timestamp": first_expiry_ts
                }
                
                response = self.fyers.optionchain(data=options_data)
                options_chain = response['data']['optionsChain']
                
                pe_options_sorted = sorted(
                    [option for option in options_chain if option['option_type'] == 'PE'],
                    key=lambda x: x['strike_price'],
                    reverse=True
                )
                ce_options_sorted = sorted(
                    [option for option in options_chain if option['option_type'] == 'CE'],
                    key=lambda x: x['strike_price']
                )
                
                self.pe_symbols = [option['symbol'] for option in pe_options_sorted]
                self.ce_symbols = [option['symbol'] for option in ce_options_sorted]
                
                symbol_list = self.ce_symbols + self.pe_symbols
                return symbol_list

        except (KeyError, AttributeError, IndexError, Exception) as e:
            error_message = f'Error occurred: {str(e)}'
            print("Error occurred while fetching option data:", error_message)
            
        return []

    def receive(self, text_data):
        message = json.loads(text_data)
        action = message.get('action')

        if action == 'disconnect':
            data_type = "SymbolUpdate"
            self.fyers.unsubscribe(symbols=self.allsymbols, data_type=data_type)
            self.close()
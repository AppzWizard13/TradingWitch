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
from account.models import AuthCode
# from fyersapi.views import get_data_instance
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

from account.models import TokenLogger
class FyersIndexDataConsumer(WebsocketConsumer):
    def connect(self):
        self.accept()
        self.running_list=[]
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
        refresh_token = TokenLogger.objects.filter(tokenType='refresh_token').order_by('-id').first()
        # refresh_data = CommonConfig.objects.filter(param="refresh_token").first()
        # refresh_token = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJhcGkuZnllcnMuaW4iLCJpYXQiOjE3Mjc4NDgwMjMsImV4cCI6MTcyOTEyNTAwMywibmJmIjoxNzI3ODQ4MDIzLCJhdWQiOlsieDowIiwieDoxIiwieDoyIiwiZDoxIiwiZDoyIiwieDoxIiwieDowIl0sInN1YiI6InJlZnJlc2hfdG9rZW4iLCJhdF9oYXNoIjoiZ0FBQUFBQm1fTjVYQnE5Qkc1N0xFbmFxbW5tZEZKdzRoX3VHTk5jTHB2RXZhaUgxek8xMFZBZ2NKcElWbjJzNThiZFRpN01VTy1ub0NZSklvbm1va2NtNmd3RmxHUUpURHF1REhmclY4VW40QWdFUVBwYUlqRkk9IiwiZGlzcGxheV9uYW1lIjoiU0FUSEVFU0ggQVJVTVVHSEFOIiwib21zIjoiSzEiLCJoc21fa2V5IjoiNTk4YWRlMGU1MzRjOThiNzE0NDQ3MTBhNDk2NGE5ZmFjNWRmMzZmY2U5MTc5YjkzZWU4NTllY2EiLCJmeV9pZCI6IllTMDUxNDEiLCJhcHBUeXBlIjoxMDAsInBvYV9mbGFnIjoiTiJ9.g-zxTsXw3ruq6cpavTgeMmWc_a2ke_tV5Yo24zOiZJk'
        print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>", refresh_token.tokenValue)
        
        url = "https://api-t1.fyers.in/api/v3/validate-refresh-token"
        headers = {
            "Content-Type": "application/json"
        }
        data = {
            "grant_type": "refresh_token",
            "appIdHash": app_id_hash,
            "refresh_token": refresh_token.tokenValue,
            "pin": pin
        }
        response = requests.post(url, headers=headers, json=data)

        
        if response.status_code == 200:
            json_response = response.json()
            print('json_responsejson_responsejson_responsejson_response', json_response)
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
        self.closing_symbols = self.running_list
        self.running_list = []
        print('closing_symbolsclosing_symbolsclosing_symbols', self.closing_symbols)
        self.fyers.unsubscribe(symbols=self.closing_symbols, data_type=data_type)
        
        self.close()

    def on_open(self):
        data_type = "SymbolUpdate"
        self.allsymbols = self.symbols + self.getoptionsymbols
        self.fyers.subscribe(symbols=self.allsymbols, data_type=data_type)
        self.fyers.keep_running()

    def on_message(self, message):
        try:
            data = json.loads(message) if isinstance(message, str) else message
            symbol = data.get('symbol')

            if symbol and 'ltp' in data:
                if symbol not in self.running_list:
                    self.running_list.append(symbol)

                if self.checking_key in symbol or (self.checking_key == "NSE:BANKNIFTY" and symbol == "NSE:NIFTYBANK-INDEX"):
                    formatted_message = {
                        'symbol': symbol,
                        'ltp': data['ltp'],
                        'type': data.get('type', 'unknown')
                    }
                    self.send(text_data=json.dumps(formatted_message))
            else:
                print(f"Ignoring message with unmatched symbol: {symbol}")

        except json.JSONDecodeError:
            self.send(text_data="Error decoding message")
        except Exception as e:
            self.send(text_data=f"Error processing message: {str(e)}")

    def on_error(self, message):
        self.send(text_data=f"Error: {message}")

    def on_close(self, message):
        data_type = "SymbolUpdate"
        self.closing_symbols = self.running_list
        self.running_list = []
        print('closing_symbolsclosing_symbolsclosing_symbols', self.closing_symbols)
        self.fyers.unsubscribe(symbols=self.allsymbols, data_type=data_type)
        
        self.close()

    @staticmethod
    def generate_app_id_hash(client_id, secret_key):
        concatenated_string = f"{client_id}:{secret_key}"
        return hashlib.sha256(concatenated_string.encode()).hexdigest()

    def getOptionStrikes(self):
        self.fyers = fyersModel.FyersModel(client_id=self.app_id, is_async=False, token=self.access_token, log_path="")
        data = {"symbol": self.symbols[0], "strikecount": 1}

        try:
            self.expiry_response = self.fyers.optionchain(data=data)
            first_expiry_ts = self.expiry_response['data']['expiryData'][0]['expiry']

            if first_expiry_ts:
                self.checking_key = self.symbols[0].split('-')[0]
                self.checking_key = "NSE:BANKNIFTY" if self.checking_key == "NSE:NIFTYBANK" else self.checking_key
                self.checking_key = "NSE:NIFTY" if self.checking_key == "NSE:NIFTY50" else self.checking_key

                options_data = {"symbol": self.symbols[0], "strikecount": 4, "timestamp": first_expiry_ts}
                response = self.fyers.optionchain(data=options_data)
                options_chain = response['data']['optionsChain']

                pe_options_sorted = sorted([option for option in options_chain if option['option_type'] == 'PE'],
                                           key=lambda x: x['strike_price'], reverse=True)
                ce_options_sorted = sorted([option for option in options_chain if option['option_type'] == 'CE'],
                                           key=lambda x: x['strike_price'])

                self.pe_symbols = [option['symbol'] for option in pe_options_sorted]
                self.ce_symbols = [option['symbol'] for option in ce_options_sorted]
                symbol_list = self.ce_symbols + self.pe_symbols
                return symbol_list

        except (KeyError, AttributeError, IndexError, Exception) as e:
            print(f"Error occurred while fetching option data: {str(e)}")

        return [], []

    def receive(self, text_data):
        message = json.loads(text_data)
        if message.get('action') == 'disconnect':
            data_type = "SymbolUpdate"
            self.closing_symbols = self.running_list
            self.running_list = []
            print('closing_symbolsclosing_symbolsclosing_symbols', self.closing_symbols)
            self.fyers.unsubscribe(symbols=self.closing_symbols, data_type=data_type)
            
            self.close()

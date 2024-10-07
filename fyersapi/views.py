from django.shortcuts import render
from django.views import View 
from dhanhq import dhanhq
from django.conf import settings
from django.http import JsonResponse
from trade_app.models import TradingConfigurations
from fyers_apiv3 import fyersModel
from django.contrib import messages
from django.shortcuts import redirect

# Create your views here.
class OptionChainView(View):
    # login_url = '/login'

    def get(self, request, slug):
        context = {}
        template = 'dashboard/optionchainview.html'
        dhan_client_id = settings.DHAN_CLIENTID
        dhan_access_token = settings.DHAN_ACCESS_TOKEN
        dhan = dhanhq(dhan_client_id, dhan_access_token)
        orderlist = dhan.get_order_list()
        dhan_fund = dhan.get_fund_limits()
        data_instance = get_data_instance(request)
        conf_data = TradingConfigurations.objects.filter(is_active=True).first()

        print('conf_dataconf_dataconf_data', conf_data)

        if dhan_fund:
            total_account_balance = dhan_fund['data']['availabelBalance']
            realised_profit = "10000000"


        active_broker = conf_data.active_broker
        scalping_mode = conf_data.scalping_mode
        cost = conf_data.scalping_amount_limit if scalping_mode else conf_data.capital_limit_per_order
        stoploss_percentage = conf_data.scalping_stop_loss if scalping_mode else conf_data.default_stop_loss
        exchange = "BSE:" if slug == "SENSEX" else "NSE:"

        data = {"symbol": f"{exchange}{slug}-INDEX", "strikecount": 1}
        print('datadata', data)
        try:
            expiry_response = data_instance.optionchain(data=data)
            print('expiry_responseexpiry_response', expiry_response)
            if active_broker == "FYERS":
                order_data = data_instance.orderbook()
                total_order_status = sum(1 for order in order_data.get("orderBook", []) if order["status"] == 2)
                positions_data = data_instance.positions()
                realized_pl = float(positions_data['overall']['pl_realized'])
                
            elif active_broker == "DHAN":
                total_order_status = get_traded_order_count_dhan(orderlist)
                positions_data = dhan.get_positions()
                print("positions_datapositions_datapositions_datapositions_data", positions_data)
                if not  positions_data['data'] == []:
                    realized_pl = sum(position.get('realizedProfit', 0) for position in positions_data['data'])
                else:
                    realized_pl = 0.00

            tax = calculate_tax(cost)
            default_brokerage = settings.DEFAULT_BROKERAGE + tax
            exp_brokerage = default_brokerage * total_order_status
            order_limit = conf_data.maximum_trade_count
            exp_brokerage_limit = order_limit * default_brokerage
            first_expiry_ts = expiry_response['data']['expiryData'][0]['expiry']
            first_expiry_date = expiry_response['data']['expiryData'][0]['date']

        except (KeyError, AttributeError, IndexError) as e:
            print('eeeeeeeeeeeeeeeeeeeeeeeee', e)
            error_message = f'Error occurred: {str(e)}'
            messages.error(request, error_message)
            return redirect('login')

        options_data = {"symbol": f"{exchange}{slug}-INDEX", "strikecount": 4, "timestamp": first_expiry_ts}
        print("-------------------------------------------------------------")
        print("options_dataoptions_dataoptions_dataoptions_data", options_data)
        print("-------------------------------------------------------------")

        try:
            response = data_instance.optionchain(data=options_data)
            print("-------------------------------------------------------------")
            print("responseresponseresponseresponse", response)
            print("-------------------------------------------------------------")
        except AttributeError as e:
            error_message = f'Error occurred while fetching options data: {str(e)}'
            messages.error(request, error_message)
            return render(request, template, context)

        pe_options = [option for option in response['data']['optionsChain'] if option['option_type'] == 'PE']
        pe_options_sorted = sorted(pe_options, key=lambda x: x['strike_price'], reverse=True)

        for index, option in enumerate(pe_options_sorted, start=1):
            option['serial_number'] = index
            option['lot_cost'] = int(option['ltp']) * get_default_lotsize(slug)

        ce_options = [option for option in response['data']['optionsChain'] if option['option_type'] == 'CE']
        ce_options_sorted = sorted(ce_options, key=lambda x: x['strike_price'])

        for index, option in enumerate(ce_options_sorted, start=1):
            option['serial_number'] = index
            option['lot_cost'] = int(option['ltp']) * get_default_lotsize(slug)

        actual_profit = round(realized_pl - float(exp_brokerage), 2)
        reward_ratio = conf_data.reward_risk_ratio
        exp_loss = (cost * stoploss_percentage) / 100
        exp_profit_percentage = stoploss_percentage * reward_ratio
        exp_profit = (cost * exp_profit_percentage) / 100

        day_max_loss = -conf_data.maximum_loss
        super_trader_threshold = exp_brokerage_limit * reward_ratio * 2
        
        remaining_orders = order_limit - total_order_status
        progress_percentage = (remaining_orders / order_limit) * 100
        progress_percentage = round(progress_percentage, 1)

        atm_index = len(pe_options_sorted) // 2  # Calculate the ATM index
        context.update({
            'total_account_balance': total_account_balance,
            'access_token': request.session.get('access_token'),
            # 'forward_trailing_points': forward_trailing_points,
            # 'reverse_trailing_points': reverse_trailing_points,
            'ce_options_with_serial': ce_options_sorted,
            'pe_options_with_serial': pe_options_sorted,
            'atm_index': atm_index,
            'expiry_response': first_expiry_date,
            'realized_pl': realized_pl,
            'order_limit': order_limit,
            'exp_brokerage_limit': exp_brokerage_limit,
            'day_exp_profit': exp_brokerage_limit * reward_ratio,
            'exp_loss': exp_loss,
            'day_max_loss': day_max_loss,
            'day_max_loss_end': -(exp_brokerage_limit * reward_ratio),
            'exp_profit': exp_profit,
            'super_trader_threshold': super_trader_threshold,
            'total_order_status': total_order_status,
            'day_exp_brokerage': exp_brokerage,
            'actual_profit': actual_profit,
            'options_data': response,
            'active_broker': active_broker,
            'progress_percentage': progress_percentage,
            'realized_pl' : realized_pl
        })
        return render(request, template, context)

def get_traded_order_count_dhan(response):
    # Check if the response contains 'data'
    if 'data' not in response:
        return 0

    # Filter orders with 'orderStatus' as 'TRADED'
    traded_orders = [order for order in response['data'] if order.get('orderStatus') == 'TRADED']

    # Return the count of traded orders
    return len(traded_orders)


def calculate_tax(cost):
    a = 0.000732
    b = 3.962
    tax = a * cost + b
    return tax



def get_data_instance(request):
    context={}
    template="trading_tool/html/profile_view.html"
    client_id = settings.FYERS_APP_ID
    access_token = request.session.get('access_token')
    if access_token:
        fyers = fyersModel.FyersModel(client_id=client_id, is_async=False, token=access_token, log_path="")
        return fyers
    else:
        pass
    return None

def get_default_lotsize(index):
    if index == 'MIDCPNIFTY':
        return 50
    elif index == 'FINNIFTY':
        return 25
    elif index == 'NIFTYBANK':
        return 15
    elif index == 'NIFTY50':
        return 25
    elif index == 'SENSEX':
        return 10
    else:
        return False

# ---------------------------------------------------------------------------------------------------------------------------

from django.http import JsonResponse
def update_data_instance(request):
    try: 
        context = {}
        dhan_client_id = settings.DHAN_CLIENTID
        dhan_access_token = settings.DHAN_ACCESS_TOKEN
        dhan = dhanhq(dhan_client_id, dhan_access_token)

        order_data = dhan.get_order_list()
        fund_data = dhan.get_fund_limits()
        positions_data = dhan.get_positions()
        if not  positions_data['data'] == []:
            realized_pl = sum(position.get('realizedProfit', 0) for position in positions_data['data'])
        else:
            realized_pl = 0.00


        print("----------------------------", positions_data)
        total_order_status = get_traded_order_count_dhan(order_data)

        try:
            latest_active_position = OpenOrderTempData.objects.latest('last_updated')
            open_position_symbol = latest_active_position.symbol
            open_position_ltp = latest_active_position.average_price 
            open_position_sl = latest_active_position.sl_price    

        except OpenOrderTempData.DoesNotExist:
            open_position_symbol = None
            open_position_ltp = 0
            open_position_sl = 0

        data = { 
                'positions': positions_data,
                'total_order_status': total_order_status,
                'fund_data': fund_data,
                'order_data': order_data,
                'open_position_symbol': open_position_symbol,
                'open_position_ltp' : open_position_ltp,
                'open_position_sl' : open_position_sl,
                'realized_pl' : realized_pl
                } 
        return JsonResponse(data)
    except Exception as e:
        print("Error:", e)
        return JsonResponse({'error': str(e)}, status=400)
# ---------------------------------------------------------------------------------------------------------------------------

from asgiref.sync import sync_to_async
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.conf import settings
from .models import  OpenOrderTempData
from dhanhq import dhanhq

# Asynchronous function to delete OpenOrderTempData
@sync_to_async
def delete_open_order_temp_data():
    print('lllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllll')
    OpenOrderTempData.objects.all().delete()

@csrf_exempt
def close_all_positions(request):
    conf_data = TradingConfigurations.objects.filter(is_active=True).first()

    dhan_client_id = settings.DHAN_CLIENTID
    dhan_access_token = settings.DHAN_ACCESS_TOKEN
    dhan = dhanhq(dhan_client_id, dhan_access_token)

    # Get Order Listing: Pending
    orderlist = dhan.get_order_list()
    pending_orders = get_pending_orders_dhan(orderlist)

    # Cancel all pending orders if any
    if pending_orders:
        sl_order_id_list = [order['orderId'] for order in pending_orders]

        cancel_order_responses = [dhan.cancel_order(order_id) for order_id in sl_order_id_list]
        
        # Check if any cancellation failed
        if any(response['status'] == 'failure' for response in cancel_order_responses):
            return JsonResponse({'message': 'S-L updation failed!', 'code': '-99'})

    # Close all open positions
    close_response = position_closing_process(dhan)

    if not close_response:
        return JsonResponse({'message': 'No Open Positions', 'code': '-99'})
    
    if close_response['status'] == 'success':
        # Trigger asynchronous table cleanup
        delete_open_order_temp_data()
        return JsonResponse({'message': 'Successfully Closed Positions', 'code': '-99'})

    return JsonResponse({'message': 'Cannot Close Positions', 'code': '-99'})

def position_closing_process(dhan):
    open_positions = dhan.get_positions()
    
    if not open_positions['data']:
        return False
    
    # Use list comprehension to close all positions
    close_responses = [
        dhan.place_order(
            security_id=position['securityId'],
            exchange_segment=dhan.NSE_FNO,
            transaction_type=dhan.SELL,
            quantity=position['quantity'],
            order_type=dhan.MARKET,
            product_type=dhan.INTRA,
            price=0
        ) for position in open_positions['data']
    ]
    
    # Return the first failure or the last successful response
    return next((response for response in close_responses if response['status'] != 'success'), close_responses[-1])

def get_pending_orders_dhan(response):
    print('responseresponseresponse:', response)
    return [order for order in response.get('data', []) if order.get('orderStatus') == 'PENDING']

def position_closing_process(dhan):
    open_positions = dhan.get_positions()
    print("open_positionsopen_positionsopen_positions", open_positions)
    
    if not open_positions['data']:
        return False

    # Close each open position
    close_responses = [
        dhan.place_order(
            security_id=position['securityId'],
            exchange_segment=dhan.NSE_FNO,
            transaction_type=dhan.SELL,
            quantity=position['quantity'],
            order_type=dhan.MARKET,
            product_type=dhan.INTRA,
            price=0
        ) for position in open_positions['data']
    ]

    # Check if all positions were successfully closed
    failure_response = next((response for response in close_responses if response['status'] != 'success'), None)
    
    if failure_response:
        return failure_response
    
    # If no failures, return the last success
    return close_responses[-1]


# ---------------------------------------------------------------------------------------------------------------------------


from django.http import JsonResponse
from .models import OpenOrderTempData

def get_open_temp_data(request):
    if request.method != 'GET':
        return JsonResponse({'error': 'Invalid request method.'}, status=400)

    try:
        # Retrieve the latest active position
        latest_active_position = OpenOrderTempData.objects.latest('last_updated')
    except OpenOrderTempData.DoesNotExist:
        return JsonResponse({'error': 'No Open Position found.'}, status=404)

    # Retrieve configuration and scalping mode (handle if not found)
    conf_data = TradingConfigurations.objects.filter(is_active=True).first()
    if not conf_data:
        return JsonResponse({'error': 'No active trading configuration found.'}, status=404)

    # Extract data from the latest active position
    open_symbol = latest_active_position.symbol
    open_qty = latest_active_position.quantity
    open_traded_price = latest_active_position.average_price
    total_order_amount = latest_active_position.order_total
    exp_loss = latest_active_position.exp_loss
    sl_price = latest_active_position.sl_price

    # Retrieve expected stoploss amount from session, if available
    exp_stoploss_amount = request.session.get('exp_stoploss_amount')

    # Return response with position details and scalping mode
    return JsonResponse({
        'open_symbol': open_symbol,
        'open_qty': open_qty,
        'open_traded_price': open_traded_price,
        'exp_stoploss_amount': exp_stoploss_amount,
        'total_order_amount': total_order_amount,
        'exp_loss': exp_loss,
        'sl_price': sl_price,
        'scalping_mode': conf_data.scalping_mode
    })

# ---------------------------------------------------------------------------------------------------------------------------

from django.db.models import Q
from decimal import Decimal
from asgiref.sync import sync_to_async
from django.http import JsonResponse
from django.conf import settings
from .models import OpenOrderTempData
from trade_app.models import TradingConfigurations
import requests

async def instantBuyOrderWithSL(request):
    if request.method != 'POST':
        return JsonResponse({'message': "Invalid request method"})

    # Retrieve data from POST request
    der_symbol = request.POST.get('der_symbol')
    ex_symbol1 = request.POST.get('ex_symbol1')
    ltp = Decimal(request.POST.get('ltp'))

    # Get trading configurations asynchronously
    trade_config_data = await sync_to_async(
        lambda: TradingConfigurations.objects.filter(is_active=True).order_by('-last_updated').values(
            'scalping_mode', 'maximum_trade_count', 'order_quantity_mode', 'default_order_quantity',
            'is_over_trade_active', 'scalping_amount_limit', 'capital_limit_per_order',
            'scalping_stop_loss', 'default_stop_loss', 'stop_loss_limit_slippage', 'averaging_limit'
        ).first()
    )()

    if not trade_config_data:
        return JsonResponse({'message': "Trading configuration not found"})

    get_lot_count = await sync_to_async(get_default_lotsize)(ex_symbol1)

    # Check if max order count limit is reached
    if trade_config_data['is_over_trade_active']:
        kill_status_response = activate_kill_switch() if trade_config_data['active_broker'] == 'DHAN' else None
        return JsonResponse({'message': f"Remind Rules : Max Trade Reached, {kill_status_response}"})

    # Check existing orders in the database
    if await sync_to_async(OpenOrderTempData.objects.filter(~Q(symbol=der_symbol)).exists)():
        return JsonResponse({'message': "Remind Rules : Unable to place another Symbol Order Now."})

    tempDatainstance1 = await sync_to_async(OpenOrderTempData.objects.filter(Q(symbol=der_symbol)).first)()
    
    if tempDatainstance1:
        is_averaged_value = int(tempDatainstance1.averaging_count) if tempDatainstance1.averaging_count is not None else 0
        averaging_limit = int(trade_config_data.get('averaging_limit', 0))  # Ensure the limit is fetched as an int with a default value

        if is_averaged_value >= averaging_limit:
            return JsonResponse({'message': "Remind Rules : You cannot Average more than Averaging limit !"})
    
    # Calculate order quantity based on mode
    if trade_config_data['order_quantity_mode'] == "MANUAL":
        config_qty = trade_config_data['averaging_limit'] if tempDatainstance1 else trade_config_data['default_order_quantity']
        order_qty = config_qty * get_lot_count

    elif trade_config_data['order_quantity_mode'] == "AUTOMATIC":
        limit_amount = trade_config_data['scalping_amount_limit'] if trade_config_data['scalping_mode'] else trade_config_data['capital_limit_per_order']
        per_lot_expense = ltp * get_lot_count
        order_qty = int((Decimal(limit_amount) // per_lot_expense) * get_lot_count)
        
        if order_qty <= 0:
            return JsonResponse({'message': " Remind Rules : Amount Usage Limit Reached"})

    # Dhan API client setup
    dhan = dhanhq(settings.DHAN_CLIENTID, settings.DHAN_ACCESS_TOKEN)
    orderlist = dhan.get_order_list()

    # Convert the derivative symbol
    formated_der_symbol, formatted_expiry_date, formatted_custom_symbol = convert_derivative_symbol(der_symbol, ex_symbol1)
    csv_result = search_csv(formatted_custom_symbol)
    security_id = csv_result[0]['SEM_SMST_SECURITY_ID']


    # Place the buy order
    buy_response = dhan.place_order(
        security_id=security_id,
        exchange_segment=dhan.NSE_FNO,
        transaction_type=dhan.BUY,
        quantity=order_qty,
        order_type=dhan.MARKET,
        product_type=dhan.INTRA,
        price=0,
        validity=dhan.DAY,
    )

    if buy_response['status'] == 'failure':
        return JsonResponse({'message': buy_response['remarks']['message']})

    # Handle the buy response
    order_id = buy_response['data'].get('orderId')
    buy_order_data = dhan.get_order_by_id(order_id)

    if buy_order_data['data']['orderStatus'] == 'REJECTED':
        return JsonResponse({'message': buy_order_data['data']['omsErrorDescription'], 'symbol': der_symbol, 'code': '-99'})

    if buy_response['status'] == 'failure':
        return JsonResponse({'message': buy_response['remarks']['message'], 'symbol': der_symbol, 'code': '-99'})

    if buy_order_data['data']['orderStatus'] == 'TRADED':
        traded_price = Decimal(buy_order_data['data']['price'])
        traded_order_count = get_traded_order_count_dhan(orderlist)

        # Check and update max trade count
        if traded_order_count >= trade_config_data['maximum_trade_count']:
            await sync_to_async(TradingConfigurations.objects.filter(is_active=True).update)(is_over_trade_active=True)

        # Check for pending orders
        get_pending_order_data = get_pending_orders_dhan(orderlist)
        if get_pending_order_data:
            sl_order_id = get_pending_order_data['data']['orderId']
            updated_qty = get_pending_order_data['data']['quantity'] + order_qty
            
            # Update the existing stop loss order
            sl_updated_response = dhan.modify_order(
                order_id=sl_order_id,
                order_type=dhan.SL,
                price=traded_price,  # Adjust price as needed
                triggerPrice=traded_price,  # Adjust price as needed
                quantity=updated_qty,
                validity=dhan.DAY
            )
            if sl_updated_response['status'] == 'failure':
                return JsonResponse({'message': 'S-L updation failed!', 'symbol': der_symbol, 'code': '-99'})

            # Update the temporary data in DB
            await sync_to_async(tempDatainstance1.update)(order_total=tempDatainstance1.order_total + (updated_qty * ltp),
                                                           premium_price=ltp,
                                                           quantity=updated_qty,
                                                           average_price=(tempDatainstance1.order_total + (updated_qty * ltp)) / updated_qty,
                                                           exp_loss=(tempDatainstance1.exp_loss + (traded_price - tempDatainstance1.sl_price) * updated_qty),
                                                           averaging_count=tempDatainstance1.averaging_count + 1)

            return JsonResponse({'message': "BUY/SL-L Placed Successfully", 'symbol': der_symbol})

        # If no pending order, place new SL order
        stoploss_price, stoploss_limit = calculate_stoploss(traded_price, trade_config_data)
        sl_response = dhan.place_order(
            security_id=security_id,
            exchange_segment=dhan.NSE_FNO,
            transaction_type=dhan.SELL,
            quantity=order_qty,
            order_type=dhan.SL,
            product_type=dhan.INTRA,
            price=stoploss_limit,
            triggerPrice=stoploss_price,
            validity=dhan.DAY,
        )

        # Handle the SL order response
        sl_order_data = dhan.get_order_by_id(sl_response['data']['orderId'])
        if sl_order_data['data']['orderStatus'] == 'REJECTED':
            return JsonResponse({'message': sl_order_data['data']['omsErrorDescription'], 'symbol': der_symbol, 'code': '-99'})
        
        if sl_response['status'] == 'failure':
            return JsonResponse({'message': 'S-L order not placed!', 'symbol': der_symbol, 'code': '-99'})

        await sync_to_async(OpenOrderTempData.objects.create)(
            symbol=der_symbol,
            order_total=traded_price * order_qty,
            premium_price=traded_price,
            average_price=traded_price,
            quantity=order_qty,
            sl_price=stoploss_price,
            exp_loss=(traded_price - stoploss_price) * order_qty,
            averaging_count=0
        )

        return JsonResponse({'message': "BUY/SL-L Placed Successfully", 'symbol': der_symbol, 'qty': order_qty, 'traded_price': traded_price})

    return JsonResponse({'message': "Some Error Occurred Before Execution"})


def calculate_stoploss(traded_price, trade_config_data):
    stoplossConf = trade_config_data['default_stop_loss']
    stoploss_price = traded_price - (traded_price * Decimal(stoplossConf) / 100)
    stoploss_limit = stoploss_price - Decimal(trade_config_data['stop_loss_limit_slippage'])
    return round(stoploss_price, 2), round(stoploss_limit, 2)


def get_traded_order_count_dhan(response):
    # Check if the response contains 'data'
    if 'data' not in response:
        return 0

    # Return the count of traded orders
    return sum(1 for order in response['data'] if order.get('orderStatus') == 'TRADED')


def activate_kill_switch():
    url = "https://api.dhan.co/killSwitch"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "access-token": settings.DHAN_ACCESS_TOKEN
    }

    params = {
        "killSwitchStatus": "ACTIVATE"
    }

    response = requests.post(url, headers=headers, json=params)  # Changed to json=params for correct payload format

    if response.status_code == 200:
        return response.json().get("killSwitchStatus")
    else:
        return "Error activating kill switch"


import pandas as pd
from django.http import JsonResponse
from datetime import datetime

def search_csv(formatted_custom_symbol):
    print("formatted_custom_symbol:", formatted_custom_symbol)
    file_path = settings.CSV_FILE_PATH
    
    try:
        # Read the CSV file into a pandas DataFrame
        df = pd.read_csv(file_path)

        # Filter the DataFrame based on SEM_TRADING_SYMBOL matching formated_der_symbol
        filtered_df = df[df['SEM_CUSTOM_SYMBOL'] == formatted_custom_symbol]

        # Convert the filtered data to a list of dictionaries (JSON serializable format)
        results = filtered_df.to_dict('records')
       
        return results

    except FileNotFoundError:
        return JsonResponse({'error': 'CSV file not found'}, status=404)
    except Exception as e:
        print("Error:", e)
        return JsonResponse({'error': str(e)}, status=500)


    
from datetime import datetime, time
import re
def convert_derivative_symbol(der_symbol, ex_symbol1):
    
    parts = der_symbol.split(':')
    print('partspartspartspartsparts', parts)
    if len(parts) != 2:
        return "Invalid symbol format"
    
    if ex_symbol1 == "NIFTY50":
        ex_symbol1="NIFTY"
    if ex_symbol1 == "NIFTYBANK":
        ex_symbol1="BANKNIFTY"

    details = parts[1]

    # Extract option type
    option_type = details[-2:]

    print('option_typeoption_typeoption_type', option_type)

    # Extract strike price (last 5 digits before option type)
    strike_price = details[-7:-2]
    print('strike_pricestrike_pricestrike_price', strike_price)

    # Remove option type, strike price, and ex_symbol1 from the details
    substrings_to_remove = [option_type, strike_price, ex_symbol1]
    modified_string = details

    print('modified_stringmodified_string', modified_string)

    print("substrings_to_removesubstrings_to_remove",substrings_to_remove)
    for substring in substrings_to_remove:
        modified_string = modified_string.replace(substring, '')

    # What remains is the expiry date
    expiry_date = modified_string
    print('expiry_dateexpiry_dateexpiry_date', expiry_date)
    
    # expiry_date = re.sub(r'[a-zA-Z]', '', expiry_date)

    
    print("expiry_dateexpiry_dateexpiry_date", expiry_date)

    # Format expiry date (assuming yyMMdd or yymmdd format)
    if len(expiry_date) == 5:
        year = expiry_date[:2]
        month = expiry_date[2:3]  # Take only one character for month
        day = expiry_date[3:]     # Remaining characters for day
    elif len(expiry_date) == 6:
        year = expiry_date[:2]
        month = expiry_date[2:4]  # Take two characters for month
        day = expiry_date[4:6]    # Two characters for day

    # Map month number to month abbreviation
    months = {
        '1': 'Jan', '2': 'Feb', '3': 'Mar', '4': 'Apr', '5': 'May', '6': 'Jun',
        '7': 'Jul', '8': 'Aug', '9': 'Sep', '10': 'Oct', '11': 'Nov', '12': 'Dec',
        'O': 'Oct'
    }

    # Get the month abbreviation in title case
    translated_month = months.get(month, '').upper()
    if option_type == "PE":
        option_type_code = "PUT"
    elif option_type == "CE":
        option_type_code = "CALL"
    

    month = month.zfill(2)

    year = "20" + year

    # Construct the translated expiry date in format YYYY-MM-DD HH:MM:SS
    formatted_expiry_date = f"{year}-{month}-{day} 14:30:00"

    formatted_custom_symbol = f"{ex_symbol1} {day} {translated_month} {strike_price} {option_type_code}"



    # Construct the translated symbol
    translated_symbol = f"{ex_symbol1}-{translated_month}{year}-{strike_price}-{option_type}"

    return translated_symbol, formatted_expiry_date , formatted_custom_symbol



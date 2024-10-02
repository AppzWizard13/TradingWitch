from django.shortcuts import render
from datetime import datetime, time
import re
import pandas as pd
from django.http import JsonResponse

def search_csv(formated_der_symbol , formatted_expiry_date):

    file_path = settings.CSV_FILE_PATH
    try:
        # Read the CSV file into a pandas DataFrame
        df = pd.read_csv(file_path)

        # Filter the DataFrame based on SEM_TRADING_SYMBOL matching formated_der_symbol
        filtered_df = df[df['SEM_TRADING_SYMBOL'] == formated_der_symbol]

        # Filter further based on SEM_EXPIRY_DATE matching formatted_expiry_date
        filtered_df = filtered_df[filtered_df['SEM_EXPIRY_DATE'] == formatted_expiry_date]

        # Convert the filtered data to a list of dictionaries (JSON serializable format)
        results = filtered_df.to_dict('records')
       
        return results

    except FileNotFoundError:
        return JsonResponse({'error': 'CSV file not found'}, status=404)
    except Exception as e:
        print("Error:", e)
        return JsonResponse({'error': str(e)}, status=500)

def convert_derivative_symbol(der_symbol, ex_symbol1):
    parts = der_symbol.split(':')
    if len(parts) != 2:
        return "Invalid symbol format"
    
    if ex_symbol1 == "NIFTY50":
        ex_symbol1="NIFTY"
    if ex_symbol1 == "NIFTYBANK":
        ex_symbol1="BANKNIFTY"

    details = parts[1]
    # Extract option type
    option_type = details[-2:]
    # Extract strike price (last 5 digits before option type)
    strike_price = details[-7:-2]
    # Remove option type, strike price, and ex_symbol1 from the details
    substrings_to_remove = [option_type, strike_price, ex_symbol1]
    modified_string = details

    for substring in substrings_to_remove:
        modified_string = modified_string.replace(substring, '')
    # What remains is the expiry date
    expiry_date = modified_string
    expiry_date = re.sub(r'[a-zA-Z]', '', expiry_date)
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
    }

    # Get the month abbreviation in title case
    translated_month = months.get(month, '')

    month = month.zfill(2)

    year = "20" + year

    # Construct the translated expiry date in format YYYY-MM-DD HH:MM:SS
    formatted_expiry_date = f"{year}-{month}-{day} 14:30:00"

    # Construct the translated symbol
    translated_symbol = f"{ex_symbol1}-{translated_month}{year}-{strike_price}-{option_type}"

    return translated_symbol, formatted_expiry_date


    # formated_der_symbol , formatted_expiry_date = convert_derivative_symbol(der_symbol, ex_symbol1)
    
    # csv_result = search_csv(formated_der_symbol , formatted_expiry_date)
    # print('*********************************************************************************', csv_result)
    # security_id = csv_result[0]['SEM_SMST_SECURITY_ID']



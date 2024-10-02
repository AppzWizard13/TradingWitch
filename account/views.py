from django.shortcuts import render
from django.contrib.auth import login, authenticate
from django.shortcuts import render, redirect
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.views import View 
from django.views.generic import TemplateView
from account.forms import UserLoginForm
from django.contrib import auth
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.shortcuts import render, redirect
from django.contrib import auth, messages
from fyers_apiv3 import fyersModel
from django.conf import settings
from account.models import AuthCode
from .models import AuthCode
from dhanhq import dhanhq
from django.views.generic import TemplateView
from django.shortcuts import render
from datetime import datetime
import json
import time
from .models import TokenLogger

# Create your views here.
class HomePageView( TemplateView):
    template_name = "dashboard/authentication-login.html"


    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context = {}
        return context




class UserloginView(View):
    def get(self, request):
        template = "dashboard/authentication-login.html"
        context = {}
        context['form'] = UserLoginForm()
        logged_user = request.user
        if logged_user.is_authenticated:
            return redirect('dashboard')  # Redirect if already logged in
        else:
            return render(request, template, context)
        
    def post(self, request):
        context = {}
        form = UserLoginForm(request.POST)
        context['form'] = form
        template = "dashboard/authentication-login.html"

        if request.method == "POST" and form.is_valid():
            login_username = request.POST["username"]
            login_password = request.POST["password"]

            # Authenticate user using Django authentication
            user = auth.authenticate(username=login_username, password=login_password)
            if user:
                # Login the user via Django
                auth.login(request, user)

                # Now, initiate Fyers login flow
                redirect_uri = settings.FYERS_REDIRECT_URL + "/dashboard"
                client_id = settings.FYERS_APP_ID
                secret_key = settings.FYERS_SECRET_ID
                grant_type = "authorization_code"
                response_type = "code"
                state = "sample"

                # Step 1: Create Fyers session and get the auth code URL
                appSession = fyersModel.SessionModel(
                    client_id=client_id,
                    redirect_uri=redirect_uri,
                    response_type=response_type,
                    state=state,
                    secret_key=secret_key,
                    grant_type=grant_type
                )

                # Generate the Fyers authentication URL
                generateTokenUrl = appSession.generate_authcode()
                # # Optionally, open this URL in the browser for manual login
                # webbrowser.open(generateTokenUrl)

                # Or redirect the user to this URL within the app
                print('generateTokenUrlgenerateTokenUrl', generateTokenUrl)
                return redirect(generateTokenUrl)

            else:
                messages.error(request, 'Username or Password incorrect!')
                return render(request, template, context)

        return render(request, template, context)


from django.shortcuts import redirect
from django.http import HttpResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib import messages
from datetime import datetime
import json
import time

class DashboardView(LoginRequiredMixin, TemplateView):
    login_url = '/login'
    template_name = "dashboard/index.html"

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        try:
            # Extract the auth code from the URL and store it in the session
            auth_code = request.GET.get('auth_code')
            if auth_code:
                request.session['auth_code'] = auth_code
                messages.success(request, 'Auth code stored successfully.')
            else:
                messages.error(request, 'Failed to extract auth code from the URL.')
        except Exception as e:
            messages.error(request, f'An error occurred: {str(e)}. No broker connected.')

        # Fetch and store the tokens, if available
        self.get_accese_token_store_session(request)

        # Continue with rendering the default dashboard template
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        # Fetch and prepare context data
        context = super().get_context_data(**kwargs)
        
        # Add more relevant data to the context (e.g., fund_data, orderlistdata)
        dhan = dhanhq(settings.DHAN_CLIENTID, settings.DHAN_ACCESS_TOKEN)
        fund_data = dhan.get_fund_limits()
        orderlistdata = dhan.get_order_list()
        position_data = dhan.get_positions()
        current_date = datetime.now().date()
        positions = position_data['data']
        total_realized_profit = sum(position['realizedProfit'] for position in positions) if positions else 0

        # Sample static position data (this should ideally come from the API)
        position_data_json = json.dumps(position_data['data'])

        # Add data to context
        context['fund_data'] = fund_data
        context['orderlistdata'] = orderlistdata
        context['position_data'] = position_data
        context['current_date'] = current_date
        context['position_data_json'] = position_data_json
        context['total_realized_profit'] = total_realized_profit

        return context

    def get_accese_token_store_session(self, request):
        # This function is responsible only for fetching tokens and saving them.
        client_id = settings.FYERS_APP_ID
        secret_key = settings.FYERS_SECRET_ID
        redirect_uri = settings.FYERS_REDIRECT_URL + "/dashboard"
        response_type = "code"
        grant_type = "authorization_code"
        auth_code = request.session.get('auth_code')
        if auth_code:
            session = fyersModel.SessionModel(
                client_id=client_id,
                secret_key=secret_key,
                redirect_uri=redirect_uri,
                response_type=response_type,
                grant_type=grant_type
            )
            session.set_token(auth_code)
            response = session.generate_token()
            access_token = response.get('access_token')
            refresh_token = response.get('refresh_token')
            if access_token and refresh_token:
                # Store the tokens in the database
                TokenLogger.objects.create(tokenType='access_token', tokenValue=access_token)
                TokenLogger.objects.create(tokenType='refresh_token', tokenValue=refresh_token)
                print('Access Token:', access_token)
                print('Refresh Token:', refresh_token)
            else:
                messages.error(request, 'Failed to get tokens from the API response.')
        else:
            messages.error(request, 'Auth code not found in session.')

class LogoutView(View):
    def get(self, request):
        logout(request)
        messages.success(request, "You have been logged out.")
        return redirect('login')  # Change 'login' to the name of your login URL

class AuthCodeListView(TemplateView):
    login_url = '/login'
    template_name = 'dashboard/auth_code_view.html'

    # @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        authcodes = AuthCode.objects.all()  # Fetch all products
        context = {'authcodes': authcodes}  # Add them to the context
        return render(request, self.template_name, context)

class TokenLoggerListView(TemplateView):
    template_name = 'dashboard/token_logger_view.html'

    def dispatch(self, request, *args, **kwargs):
        tokens = TokenLogger.objects.order_by('-created_at').all()  # Fetch all tokens from the model
        context = {'tokens': tokens}  # Add tokens to the context
        return render(request, self.template_name, context)
        
class wesocketTest(TemplateView):
    template_name = 'dashboard/websocket_test.html'

    def dispatch(self, request, *args, **kwargs):
        tokens = TokenLogger.objects.order_by('-created_at').all()  # Fetch all tokens from the model
        context = {'tokens': tokens}  # Add tokens to the context
        return render(request, self.template_name, context)



from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate
from django.conf import settings
from datetime import datetime
import json

@csrf_exempt
def login_view(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            username = data.get('username')
            password = data.get('password')            
            user = authenticate(request, username=username, password=password)

            if user is not None:
                # Authentication successful
                client_id = settings.FYERS_APP_ID
                secret_key = settings.FYERS_SECRET_ID
                dhan_client_id = settings.DHAN_CLIENTID
                dhan_access_token = settings.DHAN_ACCESS_TOKEN

                access_data = AuthCode.objects.order_by('-created_at').first()
                print('access_dataaccess_data', access_data)

                # Check if the access_token exists
                if not access_data or not access_data.code:
                    return JsonResponse({
                        "message": "Please login in web with Fyers then retry with the mobile app."
                    }, status=402)  # HTTP 402 Payment Required status code
                
                access_token = access_data.code

                # Get current date and time
                now = datetime.now()
                timestamp = now.strftime('%Y-%m-%d %H:%M:%S')  # Format timestamp
                date = now.date().isoformat()  # Format date

                return JsonResponse({
                    'message': 'Login successful',
                    'access_token': access_token,  # Returning only the code field
                    'client_id': client_id,
                    'secret_key': secret_key,
                    'timestamp': timestamp,
                    'date': date,
                    'dhan_client_id': dhan_client_id,
                    'dhan_access_token': dhan_access_token,
                }, status=200)
            else:
                return JsonResponse({'error': 'Invalid username or password'}, status=401)
        
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
    
    return JsonResponse({'error': 'Invalid HTTP method'}, status=405)


from django.http import JsonResponse
from django.contrib.auth import logout
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.contrib.auth import logout

@csrf_exempt
def api_logout(request):
    print("..............................>>>>>>>>>>", request.method)
    if request.method == 'POST':
        logout(request)
        return JsonResponse({'message': 'Successfully logged out.'}, status=200)
    return JsonResponse({'error': 'Invalid request method.'}, status=400)

    
        
from django.middleware.csrf import get_token
from django.http import JsonResponse

@csrf_exempt
def csrf_token_view(request):
    csrf_token = get_token(request)
    print("csrf_tokencsrf_tokencsrf_token", csrf_token)
    return JsonResponse({'csrf_token': csrf_token}, status=200)

from django.http import JsonResponse
from fyersapi.models import TradingConfigurations

def fetch_trade_configurations(request):
    try:
        # Fetch the latest TradingConfigurations instance
        latest_config = TradingConfigurations.objects.latest('last_updated')
        
        # Serialize the data
        data = {
            'default_stoploss': str(latest_config.default_stoploss),
            'default_order_qty': latest_config.default_order_qty,
            'reward_ratio': latest_config.reward_ratio,
            'max_loss': latest_config.max_loss,
            'max_trade_count': latest_config.max_trade_count,
            'capital_limit_per_order': latest_config.capital_limit_per_order,
            'capital_usage_limit': latest_config.capital_usage_limit,
            'forward_trailing_points': latest_config.forward_trailing_points,
            'trailing_to_top_points': latest_config.trailing_to_top_points,
            'reverse_trailing_points': latest_config.reverse_trailing_points,
            'stoploss_limit_slippage': str(latest_config.stoploss_limit_slippage),
            'last_updated': latest_config.last_updated.isoformat(),
            'averaging_limit': latest_config.averaging_limit,
            'order_quantity_mode': latest_config.order_quantity_mode,
            'scalping_amount_limit': latest_config.scalping_amount_limit,
            'scalping_mode': latest_config.scalping_mode,
            'scalping_stoploss': str(latest_config.scalping_stoploss),
            'scalping_ratio': latest_config.scalping_ratio,
            'straddle_amount_limit': latest_config.straddle_amount_limit,
            'straddle_capital_usage': latest_config.straddle_capital_usage,
            'over_trade_status': latest_config.over_trade_status,
            'averaging_qty': latest_config.averaging_qty,
            'active_broker': latest_config.active_broker,
        }
        
        return JsonResponse(data, status=200)
    
    except TradingConfigurations.DoesNotExist:
        return JsonResponse({'error': 'No trading configurations found.'}, status=404)
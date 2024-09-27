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
                print('generateTokenUrlgenerateTokenUrl', generateTokenUrl)
                # # Optionally, open this URL in the browser for manual login
                # webbrowser.open(generateTokenUrl)

                # Or redirect the user to this URL within the app
                return redirect(generateTokenUrl)

            else:
                messages.error(request, 'Username or Password incorrect!')
                return render(request, template, context)

        return render(request, template, context)


class DashboardView(TemplateView):
    template_name = "dashboard/index.html"

    def dispatch(self, request, *args, **kwargs):
        # Check if there's an auth_code in the request
        auth_code = request.GET.get('auth_code')

        if auth_code and request.user.is_authenticated:
            # Save the auth_code to the database
            AuthCode.objects.create(code=auth_code)

        # Call the parent class's dispatch method
        return super().dispatch(request, *args, **kwargs)

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


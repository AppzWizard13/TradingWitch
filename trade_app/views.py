from django.shortcuts import render, get_object_or_404, redirect
from .models import TradingConfigurations
from django.http import HttpResponse

# List View
def trading_configurations_list(request):
    configurations = TradingConfigurations.objects.all()  # Fetch all configurations
    context = {
        'configurations': configurations,
    }
    return render(request, 'dashboard/trading_configurations_list.html', context)

# Edit View
def edit_configuration(request, config_id):
    configuration = get_object_or_404(TradingConfigurations, id=config_id)
    
    if request.method == 'POST':
        # Assuming a ModelForm exists, or you can manually handle form data here
        form = TradingConfigurationsForm(request.POST, instance=configuration)
        if form.is_valid():
            form.save()
            return redirect('trading_configurations_list')  # Redirect to the list view
    else:
        form = TradingConfigurationsForm(instance=configuration)

    context = {
        'form': form,
        'configuration': configuration,
    }
    return render(request, 'edit_configuration.html', context)

# Delete View
def delete_configuration(request, config_id):
    configuration = get_object_or_404(TradingConfigurations, id=config_id)
    
    if request.method == 'POST':  # Confirmation from the user
        configuration.delete()
        return redirect('trading_configurations_list')  # Redirect to the list view

    context = {
        'configuration': configuration,
    }
    return render(request, 'delete_configuration.html', context)


from django.http import JsonResponse
from django.shortcuts import get_object_or_404

def create_configuration(request, config_id=None):
    if request.method == 'POST':
        if config_id:
            # Update existing configuration
            config = get_object_or_404(TradingConfigurations, id=config_id)
        else:
            # Create a new configuration
            config = TradingConfigurations()
        config.name = request.POST.get('name')
        config.default_stop_loss = request.POST.get('default_stop_loss')
        config.default_order_quantity = request.POST.get('default_order_quantity')
        config.reward_risk_ratio = request.POST.get('reward_risk_ratio')
        config.maximum_loss = request.POST.get('maximum_loss')
        config.maximum_trade_count = request.POST.get('maximum_trade_count')
        config.capital_limit_per_order = request.POST.get('capital_limit_per_order')
        config.total_capital_usage_limit = request.POST.get('total_capital_usage_limit')
        config.forward_trailing_points = request.POST.get('forward_trailing_points')
        config.trailing_to_peak_points = request.POST.get('trailing_to_peak_points')
        config.reverse_trailing_points = request.POST.get('reverse_trailing_points')
        config.stop_loss_limit_slippage = request.POST.get('stop_loss_limit_slippage')
        config.averaging_limit = request.POST.get('averaging_limit')
        config.order_quantity_mode = request.POST.get('order_quantity_mode')
        config.scalping_amount_limit = request.POST.get('scalping_amount_limit')
        config.scalping_mode = request.POST.get('scalping_mode') == 'on'
        config.scalping_stop_loss = request.POST.get('scalping_stop_loss')
        config.scalping_ratio = request.POST.get('scalping_ratio')
        config.straddle_amount_limit = request.POST.get('straddle_amount_limit')
        config.straddle_capital_usage_limit = request.POST.get('straddle_capital_usage_limit')
        config.is_over_trade_active = request.POST.get('is_over_trade_active') == 'on'
        config.averaging_quantity = request.POST.get('averaging_quantity')
        config.active_broker = request.POST.get('active_broker')
        config.is_active = request.POST.get('is_active') == 'on'
        print("44444444444444444444444444444444444444444444", request.POST.get('external_url'))
        config.external_url = request.POST.get('external_url')

        config.save()  # Save the configuration (new or updated)

        return JsonResponse({'success': True})

    return JsonResponse({'success': False})



def get_configuration(request, config_id):
    config = get_object_or_404(TradingConfigurations, id=config_id)
    config_data = {
        'id': config.id,
        'name': config.name,
        'default_order_quantity': config.default_order_quantity,
        'default_stop_loss': config.default_stop_loss,
        'reward_risk_ratio': config.reward_risk_ratio,
        'maximum_loss': config.maximum_loss,
        'maximum_trade_count': config.maximum_trade_count,
        'capital_limit_per_order': config.capital_limit_per_order,
        'total_capital_usage_limit': config.total_capital_usage_limit,
        'forward_trailing_points': config.forward_trailing_points,
        'trailing_to_peak_points': config.trailing_to_peak_points,
        'reverse_trailing_points': config.reverse_trailing_points,
        'stop_loss_limit_slippage': config.stop_loss_limit_slippage,
        'last_updated': config.last_updated.isoformat(),  # Convert to ISO format for JSON serialization
        'averaging_limit': config.averaging_limit,
        'order_quantity_mode': config.order_quantity_mode,
        'scalping_amount_limit': config.scalping_amount_limit,
        'scalping_mode': config.scalping_mode,
        'scalping_stop_loss': config.scalping_stop_loss,
        'scalping_ratio': config.scalping_ratio,
        'straddle_amount_limit': config.straddle_amount_limit,
        'straddle_capital_usage_limit': config.straddle_capital_usage_limit,
        'is_over_trade_active': config.is_over_trade_active,
        'averaging_quantity': config.averaging_quantity,
        'active_broker': config.active_broker,
        'is_active': config.is_active,
        'external_url': config.external_url,
    }
    return JsonResponse(config_data)

def delete_configuration(request, config_id):
    config = get_object_or_404(TradingConfigurations, id=config_id)
    config.delete()  # Delete the configuration
    return JsonResponse({'message': 'Configuration deleted successfully.'}, status=204)
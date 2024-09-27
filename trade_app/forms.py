from django import forms
from .models import TradingConfigurations

class TradingConfigurationsForm(forms.ModelForm):
    class Meta:
        model = TradingConfigurations
        fields = [
            'default_order_quantity', 'default_stop_loss', 'maximum_trade_count',
            'averaging_limit', 'order_quantity_mode', 'active_broker', 'is_active'
        ]

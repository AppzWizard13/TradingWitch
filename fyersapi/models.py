from django.db import models

class TradingConfigurations(models.Model):
    MANUAL = 'MANUAL'
    AUTOMATIC = 'AUTOMATIC'

    DHAN = 'DHAN'
    FYERS = 'FYERS'
    
    ORDER_QUANTITY_MODE_CHOICES = [
        (MANUAL, 'Manual'),
        (AUTOMATIC, 'Automatic'),
    ]
    BROKERS = [
        (DHAN, 'DHAN'),
        (FYERS, 'FYERS'),
    ]
    
    default_stop_loss = models.DecimalField(max_digits=7, decimal_places=2, default=0)  # Field for default stoploss
    default_order_quantity = models.IntegerField(default=0)  # Field for default order quantity
    reward_risk_ratio = models.IntegerField(default=0)  # Reward-to-risk ratio
    maximum_loss = models.IntegerField(default=0)  # Field for maximum loss
    maximum_trade_count = models.IntegerField(default=0)  # Field for maximum trade count
    capital_limit_per_order = models.IntegerField(default=0)  # Field for capital limit per order 
    total_capital_usage_limit = models.IntegerField(default=0)  # Field for total capital usage limit
    forward_trailing_points = models.IntegerField(default=0)  # Field for forward trailing points
    trailing_to_peak_points = models.IntegerField(default=0)  # Field for trailing to peak points
    reverse_trailing_points = models.IntegerField(default=0)  # Field for reverse trailing points
    stop_loss_limit_slippage = models.DecimalField(max_digits=5, decimal_places=2, default=0)  # Slippage for stop-loss
    last_updated = models.DateTimeField(auto_now=True)
    averaging_limit = models.IntegerField(null=True)  # Averaging limit for orders
    order_quantity_mode = models.CharField(
        max_length=10,
        choices=ORDER_QUANTITY_MODE_CHOICES,
        default=MANUAL,
    )
    scalping_amount_limit = models.IntegerField(default=0)  # Scalping amount limit
    scalping_mode = models.BooleanField(default=False)  # Is scalping mode active
    scalping_stop_loss = models.DecimalField(max_digits=7, decimal_places=2, default=0)  # Scalping stop-loss limit
    scalping_ratio = models.IntegerField(null=True)  # Scalping reward-risk ratio
    straddle_amount_limit = models.IntegerField(null=True)  # Straddle amount limit
    straddle_capital_usage_limit = models.IntegerField(null=True)  # Straddle capital usage limit
    is_over_trade_active = models.BooleanField(default=False)  # Is over-trade feature active
    averaging_quantity = models.IntegerField(default=0)  # Averaging quantity
    active_broker = models.CharField(
        max_length=10,
        choices=BROKERS,
        default=DHAN,
    )
    is_active = models.BooleanField(default=True)  # Is the configuration active

    def __str__(self):
        return f"Trading Configurations - ID: {self.pk}"

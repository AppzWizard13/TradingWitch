# Generated by Django 4.2.14 on 2024-09-21 10:50

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='TradingConfigurations',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('default_stop_loss', models.DecimalField(decimal_places=2, default=0, max_digits=7)),
                ('default_order_quantity', models.IntegerField(default=0)),
                ('reward_risk_ratio', models.IntegerField(default=0)),
                ('maximum_loss', models.IntegerField(default=0)),
                ('maximum_trade_count', models.IntegerField(default=0)),
                ('capital_limit_per_order', models.IntegerField(default=0)),
                ('total_capital_usage_limit', models.IntegerField(default=0)),
                ('forward_trailing_points', models.IntegerField(default=0)),
                ('trailing_to_peak_points', models.IntegerField(default=0)),
                ('reverse_trailing_points', models.IntegerField(default=0)),
                ('stop_loss_limit_slippage', models.DecimalField(decimal_places=2, default=0, max_digits=5)),
                ('last_updated', models.DateTimeField(auto_now=True)),
                ('averaging_limit', models.IntegerField(null=True)),
                ('order_quantity_mode', models.CharField(choices=[('MANUAL', 'Manual'), ('AUTOMATIC', 'Automatic')], default='MANUAL', max_length=10)),
                ('scalping_amount_limit', models.IntegerField(default=0)),
                ('scalping_mode', models.BooleanField(default=False)),
                ('scalping_stop_loss', models.DecimalField(decimal_places=2, default=0, max_digits=7)),
                ('scalping_ratio', models.IntegerField(null=True)),
                ('straddle_amount_limit', models.IntegerField(null=True)),
                ('straddle_capital_usage_limit', models.IntegerField(null=True)),
                ('is_over_trade_active', models.BooleanField(default=False)),
                ('averaging_quantity', models.IntegerField(default=0)),
                ('active_broker', models.CharField(choices=[('DHAN', 'DHAN'), ('FYERS', 'FYERS')], default='DHAN', max_length=10)),
                ('is_active', models.BooleanField(default=True)),
            ],
        ),
    ]

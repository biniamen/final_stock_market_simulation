from django.contrib import admin
from .models import (
    UsersPortfolio,
    ListedCompany,
    Stocks,
    Orders,
    Trade,
    Dividend,
)


@admin.register(UsersPortfolio)
class UsersPortfolioAdmin(admin.ModelAdmin):
    list_display = ('user', 'quantity', 'average_purchase_price', 'total_investment')


@admin.register(ListedCompany)
class ListedCompanyAdmin(admin.ModelAdmin):
    list_display = ('company_name', 'sector', 'last_updated')


@admin.register(Stocks)
class StocksAdmin(admin.ModelAdmin):
    list_display = ('ticker_symbol', 'company', 'total_shares', 'current_price', 'available_shares', 'created_at')


@admin.register(Orders)
class OrdersAdmin(admin.ModelAdmin):
    list_display = ('user', 'stock_symbol', 'order_type', 'action', 'price', 'quantity', 'status', 'created_at')


@admin.register(Trade)
class TradeAdmin(admin.ModelAdmin):
    list_display = ('user', 'stock', 'quantity', 'price', 'trade_time')


@admin.register(Dividend)
class DividendAdmin(admin.ModelAdmin):
    list_display = ('company', 'budget_year', 'dividend_ratio', 'total_dividend_amount', 'status')

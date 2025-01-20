from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import (
    CompanyDisclosuresView,
    DirectStockPurchaseView,
    DisclosureViewSet,
    DistributeDividendView,
    DividendDistributionViewSet,
    StockNetHoldingsView,
    StockTradesWithOrderInfoView,
    SuspiciousActivityViewSet,
    TraderOrdersView,
    TransactionAuditTrailViewSet,
    UserBalancesView,
    UserOrdersView,
    UserSpecificTradesView,
    UserTradesView,
    UserTradesWithOrderInfoView,
    UsersPortfolioViewSet,
    ListedCompanyViewSet,
    StocksViewSet,
    OrdersViewSet,
    TradeViewSet,
    DividendViewSet,
    suspicious_activities,
)

# Initialize the DefaultRouter
router = DefaultRouter()
router.register(r'portfolios', UsersPortfolioViewSet, basename='portfolio')
router.register(r'companies', ListedCompanyViewSet, basename='company')
router.register(r'stocks', StocksViewSet, basename='stock')
router.register(r'orders', OrdersViewSet, basename='order')
router.register(r'trades', TradeViewSet, basename='trade')
router.register(r'dividends', DividendViewSet, basename='dividend')
router.register(r'disclosures', DisclosureViewSet, basename='disclosure')
router.register(r'audit-trails', TransactionAuditTrailViewSet, basename='audit-trail')
# Register Suspicious Activity
router.register(r'suspicious-activities', SuspiciousActivityViewSet, basename='suspicious-activity')
router.register(r'distributions', DividendDistributionViewSet, basename='distribution')


# Custom URL patterns
urlpatterns = [
    # Trader orders
    path('trader/orders/', TraderOrdersView.as_view(), name='trader-orders'),
    
    # User-specific resources
    path('user/orders/', UserOrdersView.as_view(), name='user-orders'),
    path('user/trades/', UserTradesView.as_view(), name='user-trades'),
    path('user/<int:user_id>/trades/', UserSpecificTradesView.as_view(), name='user-specific-trades'),

    # Direct stock purchase
    path('direct_buy/', DirectStockPurchaseView.as_view(), name='direct-buy'),

    # Suspicious activities
    path('surveillance/activities/', suspicious_activities, name='suspicious_activities'),

   # get trade data with order info
    path('user/<int:user_id>/trades_with_order_info/', 
         UserTradesWithOrderInfoView.as_view(), 
         name='user_trades_with_order_info'),
    
    # Company disclosures endpoint
    path('company/<int:company_id>/disclosures/', CompanyDisclosuresView.as_view(), name='company-disclosures'),
    path('dividends/<int:dividend_id>/distribute/', DistributeDividendView.as_view(), name='distribute-dividend'),
    path(
        'stocks/<int:stock_id>/trades_with_order_info/',
        StockTradesWithOrderInfoView.as_view(),
        name='stock_trades_with_order_info'
    ),
      path(
        'stocks/<int:stock_id>/fifonet_holdings/',
        StockNetHoldingsView.as_view(),
        name='stock_fifonet_holdings'
    ),
       # User Balances Endpoint
    path('user_balances/', UserBalancesView.as_view(), name='user-balances'),
]

# Combine router URLs with custom URLs
urlpatterns += router.urls

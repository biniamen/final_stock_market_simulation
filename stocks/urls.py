from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import (
    CompanyDisclosuresView,
    DirectStockPurchaseView,
    DisclosureViewSet,
    TraderOrdersView,
    UserOrdersView,
    UserSpecificTradesView,
    UserTradesView,
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

    # Company disclosures endpoint
    path('company/<int:company_id>/disclosures/', CompanyDisclosuresView.as_view(), name='company-disclosures'),
]

# Combine router URLs with custom URLs
urlpatterns += router.urls

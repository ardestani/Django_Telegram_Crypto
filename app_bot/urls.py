from django.urls import path
from . import views

app_name = 'bot'

urlpatterns = [
    # Payment webhook endpoint
    path('api/payment/webhook/', views.payment_webhook, name='payment_webhook'),
    
    # Payment status endpoint
    path('api/payment/status/<uuid:payment_id>/', views.PaymentStatusView.as_view(), name='payment_status'),
    
    # Payment result pages
    path('payment/success/<uuid:payment_id>/', views.payment_success, name='payment_success'),
    path('payment/error/<uuid:payment_id>/', views.payment_error, name='payment_error'),
] 
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views import View
import json
import logging
from .services import PaymentProcessor
from .models import Payment

logger = logging.getLogger(__name__)


@csrf_exempt
@require_http_methods(["POST"])
def payment_webhook(request):
    """
    Webhook endpoint for NOWPayments payment notifications
    """
    try:
        # Parse the webhook data
        webhook_data = json.loads(request.body)
        logger.info(f"Received webhook: {webhook_data}")
        
        # Process the payment
        processor = PaymentProcessor()
        success, payment = processor.process_payment_webhook(webhook_data)
        
        if success:
            logger.info(f"Payment processed successfully: {payment.payment_id}")
            return JsonResponse({"status": "success"}, status=200)
        else:
            logger.error(f"Payment processing failed: {webhook_data}")
            return JsonResponse({"status": "error", "message": "Payment not found"}, status=404)
            
    except json.JSONDecodeError:
        logger.error("Invalid JSON in webhook")
        return JsonResponse({"status": "error", "message": "Invalid JSON"}, status=400)
    except Exception as e:
        logger.error(f"Webhook processing error: {e}")
        return JsonResponse({"status": "error", "message": "Internal server error"}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class PaymentStatusView(View):
    """
    View for checking payment status
    """
    
    def get(self, request, payment_id):
        """
        Get payment status by payment ID
        """
        try:
            payment = Payment.objects.get(payment_id=payment_id)
            return JsonResponse({
                "payment_id": str(payment.payment_id),
                "status": payment.status,
                "amount_usd": float(payment.amount_usd),
                "currency": payment.currency,
                "crypto_amount": round(float(payment.crypto_amount), 8) if payment.crypto_amount else None,
                "created_at": payment.created_at.isoformat(),
                "expires_at": payment.expires_at.isoformat() if payment.expires_at else None,
                "is_processed": payment.is_processed
            })
        except Payment.DoesNotExist:
            return JsonResponse({"error": "Payment not found"}, status=404)
        except Exception as e:
            logger.error(f"Error getting payment status: {e}")
            return JsonResponse({"error": "Internal server error"}, status=500)


def payment_success(request, payment_id):
    """
    Payment success page
    """
    try:
        payment = Payment.objects.get(payment_id=payment_id)
        context = {
            'payment': payment,
            'status': 'success'
        }
        return render(request, 'payment_success.html', context)
    except Payment.DoesNotExist:
        return render(request, 'payment_error.html', {'error': 'Payment not found'})


def payment_error(request, payment_id):
    """
    Payment error page
    """
    try:
        payment = Payment.objects.get(payment_id=payment_id)
        context = {
            'payment': payment,
            'status': 'error'
        }
        return render(request, 'payment_error.html', context)
    except Payment.DoesNotExist:
        return render(request, 'payment_error.html', {'error': 'Payment not found'})

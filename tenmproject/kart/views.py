
import json
import uuid
import logging

from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.shortcuts import render
from django.core.mail import send_mail
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.views.decorators.http import require_POST

logger = logging.getLogger(__name__)


# ==========================================
# HOME PAGE
# ==========================================

def home(request):
    return render(request, 'index.html')


# ==========================================
# CHECKOUT AND EMAIL CONFIRMATION
# ==========================================

@require_POST
def checkout(request):

    try:
        # Read JSON data sent by index.html
        data = json.loads(request.body)

        if not isinstance(data, dict):
            return JsonResponse({
                'success': False,
                'message': 'Invalid checkout request.'
            }, status=400)

        # Customer details
        name = str(data.get('name', '')).strip()
        email = str(data.get('email', '')).strip()
        phone = str(data.get('phone', '')).strip()
        address = str(data.get('address', '')).strip()
        city = str(data.get('city', '')).strip()
        pin = str(data.get('pin', '')).strip()
        payment = str(data.get('payment', '')).strip()

        # Validate required fields
        if not all([name, email, phone, address, city, pin, payment]):
            return JsonResponse({
                'success': False,
                'message': 'Please fill in all required fields.'
            }, status=400)

        # Validate email address
        try:
            validate_email(email)
        except ValidationError:
            return JsonResponse({
                'success': False,
                'message': 'Please enter a valid email address.'
            }, status=400)

        # Validate PIN code
        if len(pin) != 6 or not pin.isdigit():
            return JsonResponse({
                'success': False,
                'message': 'Enter a valid 6-digit PIN code.'
            }, status=400)

        # Validate payment method
        allowed_payments = [
            'Cash on Delivery',
            'UPI',
            'Credit Card',
            'Debit Card'
        ]

        if payment not in allowed_payments:
            return JsonResponse({
                'success': False,
                'message': 'Please select a valid payment method.'
            }, status=400)

        # ======================================
        # CART VALIDATION
        # ======================================

        items = data.get('items', [])

        if not isinstance(items, list) or not items:
            return JsonResponse({
                'success': False,
                'message': (
                    'Your shopping cart is empty. '
                    'Add products before placing your order.'
                )
            }, status=400)

        # IMPORTANT:
        # These IDs and prices must match the products
        # and prices in your index.html JavaScript.
        product_prices = {
            1: Decimal('24999'),
            2: Decimal('14999'),
            3: Decimal('62999'),
            4: Decimal('79999'),
            5: Decimal('599'),
            6: Decimal('1299'),
            7: Decimal('2499'),
            8: Decimal('1899'),
            9: Decimal('2999'),
            10: Decimal('3499'),
            11: Decimal('1499'),
            12: Decimal('32999'),
        }

        total = Decimal('0.00')

        for item in items:

            if not isinstance(item, dict):
                return JsonResponse({
                    'success': False,
                    'message': 'Invalid product information in your cart.'
                }, status=400)

            try:
                product_id = int(item.get('id'))
                quantity = int(item.get('quantity'))
            except (ValueError, TypeError, OverflowError):
                return JsonResponse({
                    'success': False,
                    'message': 'Invalid product ID or quantity in your cart.'
                }, status=400)

            if quantity < 1 or quantity > 100:
                return JsonResponse({
                    'success': False,
                    'message': 'Product quantity must be between 1 and 100.'
                }, status=400)

            if product_id not in product_prices:
                return JsonResponse({
                    'success': False,
                    'message': (
                        f'Product ID {product_id} is not configured '
                        'in the server product price list.'
                    )
                }, status=400)

            total += product_prices[product_id] * quantity

        if total <= 0:
            return JsonResponse({
                'success': False,
                'message': 'The order total must be greater than zero.'
            }, status=400)

        # ======================================
        # CREATE ORDER DETAILS
        # ======================================

        order_id = 'SS' + uuid.uuid4().hex[:8].upper()

        subject = f'ShopSmart Order Confirmation - {order_id}'

        message = f"""
Hello {name},

Thank you for shopping with ShopSmart!

Your order has been received.

ORDER DETAILS
--------------------------------
Order ID: {order_id}
Customer: {name}
Email: {email}
Phone: {phone}

DELIVERY ADDRESS
--------------------------------
{address}
{city} - {pin}

PAYMENT DETAILS
--------------------------------
Payment method: {payment}
Order total: Rs. {total:.2f}

We will keep you informed about your order.

Thank you for shopping with ShopSmart!

ShopSmart Customer Support
"""

        # ======================================
        # SEND GMAIL CONFIRMATION
        # ======================================

        if not settings.EMAIL_HOST_USER or not settings.EMAIL_HOST_PASSWORD:
            logger.error('Gmail SMTP credentials are not configured.')

            return JsonResponse({
                'success': False,
                'message': (
                    'Email settings are incomplete. '
                    'Configure EMAIL_HOST_USER and EMAIL_HOST_PASSWORD '
                    'in settings.py.'
                )
            }, status=500)

        sent = send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )

        if sent != 1:
            return JsonResponse({
                'success': False,
                'message': (
                    'The order was not confirmed because the '
                    'confirmation email could not be sent.'
                )
            }, status=500)

        # ======================================
        # SUCCESS RESPONSE
        # ======================================

        return JsonResponse({
            'success': True,
            'message': 'Order confirmation email sent successfully!',
            'order_id': order_id,
            'email': email,
            'total': str(total),
            'payment': payment,
        })

    # ==========================================
    # ERROR HANDLING
    # ==========================================

    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': (
                'Invalid checkout request data. '
                'Refresh the page and try again.'
            )
        }, status=400)

    except (ValueError, TypeError, InvalidOperation, AttributeError) as error:
        logger.warning('Invalid checkout data: %s', error)

        return JsonResponse({
            'success': False,
            'message': f'Checkout validation failed: {error}'
        }, status=400)

    except Exception:
        logger.exception('ShopSmart checkout failed.')

        return JsonResponse({
            'success': False,
            'message': (
                'Unable to send the confirmation email. '
                'Check your Gmail SMTP settings and Django terminal.'
            )
        }, status=500)

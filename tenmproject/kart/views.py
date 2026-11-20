
import json
from decimal import Decimal, InvalidOperation

from django.shortcuts import render
from django.http import JsonResponse
from django.core.mail import send_mail
from django.conf import settings
from django.views.decorators.http import require_POST

from .models import Order


def home(request):
    return render(request, "index.html")


@require_POST
def place_order(request):
    try:
        data = json.loads(request.body)

        name = data.get("name", "").strip()
        email = data.get("email", "").strip()
        phone = data.get("phone", "").strip()
        address = data.get("address", "").strip()
        products = data.get("products", [])
        total = Decimal(str(data.get("total", "0")))

        if not all([name, email, phone, address]):
            return JsonResponse({
                "success": False,
                "message": "Please fill all fields."
            }, status=400)

        if not products or total <= 0:
            return JsonResponse({
                "success": False,
                "message": "Your cart is empty."
            }, status=400)

        order = Order.objects.create(
            customer_name=name,
            email=email,
            phone=phone,
            address=address,
            products=json.dumps(products),
            total_amount=total,
        )

        product_lines = "\n".join(
            f"{item.get('title', 'Product')} x {item.get('quantity', 1)}"
            for item in products
        )

        message = f"""
Hello {name},

Thank you for shopping with us!

Your order has been placed successfully.

Order ID: {order.id}

Products:
{product_lines}

Total Amount: Rs. {total}

Delivery Address:
{address}

Thank you!
Flipkart Shopping Store
"""

        try:
            send_mail(
                f"Order Confirmation #{order.id}",
                message,
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )

            order.email_sent = True
            order.save(update_fields=["email_sent"])

            return JsonResponse({
                "success": True,
                "message": "Order placed! Confirmation email sent.",
                "order_id": order.id,
                "email_sent": True
            })

        except Exception as error:
            return JsonResponse({
                "success": True,
                "message": "Order saved, but email could not be sent.",
                "order_id": order.id,
                "email_sent": False,
                "email_error": str(error)
            })

    except (ValueError, InvalidOperation, TypeError):
        return JsonResponse({
            "success": False,
            "message": "Invalid order details."
        }, status=400)


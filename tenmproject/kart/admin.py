
from django.contrib import admin
from .models import Order

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "customer_name",
        "email",
        "phone",
        "total_amount",
        "email_sent",
        "created_at",
    )

    search_fields = ("customer_name", "email")
    list_filter = ("email_sent", "created_at")

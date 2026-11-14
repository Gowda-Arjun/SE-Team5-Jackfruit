import hashlib
import hmac
from datetime import date, datetime, time
from decimal import Decimal
from uuid import uuid4

from django.conf import settings
from django.urls import reverse
from django.utils import timezone


class PaymentGateway:
    def create_order(self, amount: Decimal, payment_id: int) -> tuple[str, str]:
        raise NotImplementedError

    def verify_signature(self, body: bytes, signature: str) -> bool:
        raise NotImplementedError

    def fetch_ledger(self, date_from: date, date_to: date) -> list[dict]:
        raise NotImplementedError


class MockGateway(PaymentGateway):
    def create_order(self, amount: Decimal, payment_id: int) -> tuple[str, str]:
        return (
            f"mock_{uuid4().hex}",
            reverse("fees:mock_checkout", args=[payment_id]),
        )

    def verify_signature(self, body: bytes, signature: str) -> bool:
        expected = hmac.new(
            settings.PAYMENT_WEBHOOK_SECRET.encode(),
            body,
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(expected, signature)

    def fetch_ledger(self, date_from: date, date_to: date) -> list[dict]:
        return []


class RazorpayGateway(PaymentGateway):
    def _client(self):
        import razorpay

        return razorpay.Client(
            auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
        )

    def create_order(self, amount, payment_id):
        order = self._client().order.create(
            data={
                "amount": int(amount * 100),
                "currency": "INR",
                "receipt": str(payment_id),
            }
        )
        return (
            order["id"],
            reverse("fees:razorpay_checkout", args=[payment_id]),
        )

    def verify_signature(self, body: bytes, signature: str) -> bool:
        expected = hmac.new(
            settings.PAYMENT_WEBHOOK_SECRET.encode(),
            body,
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(expected, signature)

    def fetch_ledger(self, date_from: date, date_to: date) -> list[dict]:
        def as_datetime(value, end_of_day=False):
            if isinstance(value, datetime):
                result = value
            elif isinstance(value, date):
                result = datetime.combine(
                    value,
                    time.max if end_of_day else time.min,
                )
            else:
                raise TypeError("Ledger dates must be date or datetime values.")
            if timezone.is_naive(result):
                result = timezone.make_aware(result)
            return result

        start = as_datetime(date_from)
        end = as_datetime(date_to, end_of_day=True)
        result = self._client().payment.all(
            {
                "from": int(start.timestamp()),
                "to": int(end.timestamp()),
                "count": 100,
            }
        )
        return result["items"]


def get_gateway() -> PaymentGateway:
    gateway_name = settings.PAYMENT_GATEWAY.lower()
    if gateway_name == "mock":
        return MockGateway()
    if gateway_name == "razorpay":
        return RazorpayGateway()
    raise ValueError(f"Unsupported PAYMENT_GATEWAY: {settings.PAYMENT_GATEWAY}")

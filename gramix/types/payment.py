from __future__ import annotations
from dataclasses import dataclass, field

from gramix.types.user import User


@dataclass(slots=True)
class OrderInfo:
    name: str | None = None
    phone_number: str | None = None
    email: str | None = None
    shipping_address: dict | None = None

    @classmethod
    def from_dict(cls, data: dict) -> OrderInfo:
        return cls(
            name=data.get("name"),
            phone_number=data.get("phone_number"),
            email=data.get("email"),
            shipping_address=data.get("shipping_address"),
        )


@dataclass(slots=True)
class PreCheckoutQuery:
    id: str
    from_user: User
    currency: str
    total_amount: int
    invoice_payload: str
    shipping_option_id: str | None = None
    order_info: OrderInfo | None = None

    @property
    def amount_decimal(self) -> float:
        return self.total_amount / 100

    @classmethod
    def from_dict(cls, data: dict) -> PreCheckoutQuery:
        return cls(
            id=data["id"],
            from_user=User.from_dict(data["from"]),
            currency=data["currency"],
            total_amount=data["total_amount"],
            invoice_payload=data["invoice_payload"],
            shipping_option_id=data.get("shipping_option_id"),
            order_info=OrderInfo.from_dict(data["order_info"]) if "order_info" in data else None,
        )


@dataclass(slots=True)
class SuccessfulPayment:
    currency: str
    total_amount: int
    invoice_payload: str
    telegram_payment_charge_id: str
    provider_payment_charge_id: str
    shipping_option_id: str | None = None
    order_info: OrderInfo | None = None

    @property
    def amount_decimal(self) -> float:
        return self.total_amount / 100

    @classmethod
    def from_dict(cls, data: dict) -> SuccessfulPayment:
        return cls(
            currency=data["currency"],
            total_amount=data["total_amount"],
            invoice_payload=data["invoice_payload"],
            telegram_payment_charge_id=data["telegram_payment_charge_id"],
            provider_payment_charge_id=data["provider_payment_charge_id"],
            shipping_option_id=data.get("shipping_option_id"),
            order_info=OrderInfo.from_dict(data["order_info"]) if "order_info" in data else None,
        )


@dataclass(slots=True)
class LabeledPrice:
    label: str
    amount: int

    def to_dict(self) -> dict:
        return {"label": self.label, "amount": self.amount}

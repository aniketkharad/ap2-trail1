"""AP2 mandate handler — creates and signs payment mandates."""

import uuid
import hashlib


class AP2Handler:
    def process_cart_mandate(self, checkout_response: dict) -> dict | None:
        """Extract the merchant-signed CartMandate from a checkout response.

        The CartMandate is the merchant's cryptographic price guarantee —
        it locks the total so it can't change between checkout and payment.
        """
        return checkout_response.get("ap2", {}).get("cart_mandate")

    def create_payment_mandate(
        self, cart_mandate: dict, payment_method: str = "card"
    ) -> dict:
        """Create and sign a PaymentMandate authorizing payment.

        References the merchant's CartMandate and adds user authorization.
        Together they form a two-party agreement: merchant guarantees price,
        user authorizes charge.
        """
        contents = cart_mandate["contents"]
        mandate_id = uuid.uuid4().hex

        return {
            "mandate_id": mandate_id,
            "cart_reference": contents["id"],
            "merchant": contents["merchant_name"],
            "total": contents["total"],
            "payment_method": payment_method,
            "user_authorization": self._sign(mandate_id, contents["id"]),
        }

    def _sign(self, mandate_id: str, checkout_id: str) -> str:
        """Sign the mandate. Production uses real crypto (sd-jwt-vc)."""
        payload = f"{mandate_id}:{checkout_id}"
        return hashlib.sha256(payload.encode()).hexdigest()

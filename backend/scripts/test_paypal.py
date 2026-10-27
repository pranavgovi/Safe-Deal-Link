"""Manual sandbox smoke test for backend/paypal/client.py. Creates an
order, prints the approve link, waits for you to log in as the sandbox
BUYER and approve it, then authorizes and either captures or voids.

Run from backend/ (venv active): python -m scripts.test_paypal
"""

import sys
import uuid

from paypal import client as paypal

AMOUNT = 25.00
PAYEE_EMAIL = "seller@example.com"  # your sandbox Business (seller) account email


def find_approve_link(order: dict) -> str:
    for link in order.get("links", []):
        if link.get("rel") == "approve":
            return link["href"]
    raise RuntimeError(f"No approve link in order response: {order}")


def main():
    deal_id = str(uuid.uuid4())
    print(f"Using deal_id={deal_id}")

    print("\nCreating order...")
    order = paypal.create_order(AMOUNT, PAYEE_EMAIL, deal_id)
    order_id = order["id"]
    print(f"Order created: {order_id}")
    print(f"Approve link: {find_approve_link(order)}")

    input("\nLog in as the sandbox BUYER, approve the order, then press Enter to continue...")

    print("\nAuthorizing...")
    authorized_order = paypal.authorize_order(order_id)
    authorization = authorized_order["purchase_units"][0]["payments"]["authorizations"][0]
    auth_id = authorization["id"]
    print(f"Authorization: {auth_id} (status: {authorization['status']})")

    choice = input("\nCapture or void this authorization? [capture/void] ").strip().lower()

    if choice == "capture":
        print("\nCapturing...")
        capture = paypal.capture_authorization(auth_id, AMOUNT, deal_id, final=True)
        print(f"Captured: {capture['id']} (status: {capture['status']})")
    elif choice == "void":
        print("\nVoiding...")
        paypal.void_authorization(auth_id)
        print("Voided. Buyer was never charged.")
    else:
        print(f"Unrecognized choice '{choice}', leaving authorization as-is.")
        sys.exit(1)


if __name__ == "__main__":
    main()

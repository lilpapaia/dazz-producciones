"""Shared notification helper for supplier routes."""
from sqlalchemy.orm import Session
from app.models.suppliers import SupplierNotification


def create_notification(db: Session, recipient_type, recipient_id: int, event_type,
                        title: str, message: str, invoice_id=None, supplier_id=None, extra_data=None):
    """Create a supplier notification record (does NOT commit — caller is responsible)."""
    notif = SupplierNotification(
        recipient_type=recipient_type,
        recipient_id=recipient_id,
        event_type=event_type,
        title=title,
        message=message,
        related_invoice_id=invoice_id,
        related_supplier_id=supplier_id,
        extra_data=extra_data,
    )
    db.add(notif)

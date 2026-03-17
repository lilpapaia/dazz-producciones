"""
Email templates for the supplier module.
All emails in English (international influencers — doc section 14.2).
Uses Brevo API via the existing send_email() function.
"""

import os
import html as html_mod
from dotenv import load_dotenv
from app.services.email import send_email

load_dotenv()

SUPPLIER_PORTAL_URL = os.getenv("SUPPLIER_PORTAL_URL", "https://providers.dazzcreative.com")
ADMIN_EMAIL = os.getenv("ADMIN_NOTIFICATION_EMAIL", "admin@dazzcreative.com")


def _base_template(title: str, subtitle: str, body_html: str) -> str:
    """Base email template matching DAZZ brand (zinc/amber dark theme)."""
    return f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
<body style="margin:0;padding:0;font-family:Arial,sans-serif;background-color:#18181b;">
<table width="100%" cellpadding="0" cellspacing="0" style="background-color:#18181b;padding:40px 20px;">
<tr><td align="center">
<table width="600" cellpadding="0" cellspacing="0" style="background-color:#27272a;border-radius:8px;overflow:hidden;">
<tr><td style="background:linear-gradient(135deg,#f59e0b 0%,#d97706 100%);padding:30px;text-align:center;">
<h1 style="margin:0;color:#fff;font-size:28px;font-weight:bold;letter-spacing:2px;">DAZZ GROUP</h1>
<p style="margin:8px 0 0;color:rgba(255,255,255,0.8);font-size:11px;letter-spacing:3px;">{subtitle}</p>
</td></tr>
<tr><td style="padding:35px;">
<h2 style="margin:0 0 20px;color:#f59e0b;font-size:22px;">{title}</h2>
{body_html}
</td></tr>
<tr><td style="background-color:#18181b;padding:25px;text-align:center;border-top:1px solid #3f3f46;">
<p style="margin:0;color:#52525b;font-size:12px;">&copy; 2026 DAZZ Group. All rights reserved.</p>
</td></tr>
</table>
</td></tr></table>
</body></html>"""


def _button(url: str, text: str) -> str:
    return f"""<table width="100%" cellpadding="0" cellspacing="0"><tr><td align="center" style="padding:20px 0;">
<a href="{url}" style="display:inline-block;padding:14px 36px;background:linear-gradient(135deg,#f59e0b 0%,#d97706 100%);color:#000;text-decoration:none;font-weight:bold;font-size:15px;border-radius:4px;letter-spacing:1px;">{text}</a>
</td></tr></table>"""


def _text(content: str) -> str:
    return f'<p style="margin:0 0 16px;color:#d4d4d8;font-size:15px;line-height:1.6;">{content}</p>'


def _warning(content: str) -> str:
    return f"""<div style="margin-top:25px;padding:16px;background-color:#3f3f46;border-left:4px solid #f59e0b;border-radius:4px;">
<p style="margin:0;color:#e4e4e7;font-size:13px;line-height:1.6;">{content}</p></div>"""


# ============================================
# SUPPLIER-FACING EMAILS
# ============================================

def send_supplier_invitation(name: str, email: str, token: str, custom_message: str = None):
    """Invitation email with registration link (72h expiry)."""
    url = f"{SUPPLIER_PORTAL_URL}/register?token={token}"
    body = (
        _text(f"Hello <strong>{name}</strong>,")
        + _text("You have been invited to join the <strong>DAZZ Group</strong> supplier portal. "
                "Through this portal you can submit invoices and track their payment status.")
        + (_text(f"<em>\"{html_mod.escape(custom_message)}\"</em>") if custom_message else "")
        + _button(url, "CREATE YOUR ACCOUNT")
        + _text(f'Or copy this link: <a href="{url}" style="color:#f59e0b;font-size:13px;word-break:break-all;">{url}</a>')
        + _warning("<strong>Important:</strong> This link will expire in <strong>72 hours</strong> "
                    "and can only be used once.")
    )
    return send_email(email, "DAZZ Group — You're invited to the Supplier Portal", _base_template(
        f"Welcome, {name}!", "SUPPLIER PORTAL INVITATION", body))


def send_supplier_welcome(name: str, email: str):
    """Welcome email after successful registration."""
    url = f"{SUPPLIER_PORTAL_URL}/login"
    body = (
        _text(f"Hello <strong>{name}</strong>,")
        + _text("Your account has been successfully created. You can now log in to the supplier portal "
                "to submit invoices and track payments.")
        + _button(url, "GO TO PORTAL")
        + _text("If you need to update your details, please contact the DAZZ admin team.")
    )
    return send_email(email, "DAZZ Group — Your Supplier Account is Ready", _base_template(
        "Account Created", "SUPPLIER PORTAL", body))


def send_supplier_invoice_received(name: str, email: str, invoice_number: str):
    """Confirmation that invoice was received and passed IA validation."""
    body = (
        _text(f"Hello <strong>{name}</strong>,")
        + _text(f"Your invoice <strong>{invoice_number}</strong> has been received and verified. "
                "It is now pending approval by the DAZZ team.")
        + _text("You can check the status anytime from your portal dashboard.")
    )
    return send_email(email, f"DAZZ Group — Invoice {invoice_number} Received", _base_template(
        "Invoice Received", "INVOICE CONFIRMATION", body))


def send_supplier_invoice_approved(name: str, email: str, invoice_number: str):
    body = (
        _text(f"Hello <strong>{name}</strong>,")
        + _text(f"Great news! Your invoice <strong>{invoice_number}</strong> has been <strong style='color:#22c55e;'>approved</strong>. "
                "Payment will be processed shortly.")
    )
    return send_email(email, f"DAZZ Group — Invoice {invoice_number} Approved", _base_template(
        "Invoice Approved", "PAYMENT UPDATE", body))


def send_supplier_invoice_paid(name: str, email: str, invoice_number: str, amount: float):
    body = (
        _text(f"Hello <strong>{name}</strong>,")
        + _text(f"Invoice <strong>{invoice_number}</strong> has been <strong style='color:#22c55e;'>paid</strong>.")
        + f'<div style="margin:20px 0;padding:20px;background-color:#3f3f46;border-radius:4px;text-align:center;">'
          f'<span style="color:#a1a1aa;font-size:12px;">AMOUNT PAID</span><br>'
          f'<span style="color:#f59e0b;font-size:28px;font-weight:bold;">{amount:,.2f} EUR</span></div>'
    )
    return send_email(email, f"DAZZ Group — Invoice {invoice_number} Paid", _base_template(
        "Payment Confirmed", "PAYMENT UPDATE", body))


def send_supplier_invoice_rejected(name: str, email: str, invoice_number: str, reason: str):
    body = (
        _text(f"Hello <strong>{html_mod.escape(name)}</strong>,")
        + _text(f"Unfortunately, your invoice <strong>{html_mod.escape(invoice_number)}</strong> has been "
                "<strong style='color:#ef4444;'>rejected</strong>.")
        + _warning(f"<strong>Reason:</strong> {html_mod.escape(reason)}")
        + _text("Please review the issue and submit a corrected invoice through the portal.")
    )
    return send_email(email, f"DAZZ Group — Invoice {invoice_number} Rejected", _base_template(
        "Invoice Rejected", "ACTION REQUIRED", body))


def send_supplier_invoice_deleted(name: str, email: str, invoice_number: str):
    body = (
        _text(f"Hello <strong>{name}</strong>,")
        + _text(f"Your request to delete invoice <strong>{invoice_number}</strong> has been confirmed. "
                "The invoice has been permanently removed from the system.")
    )
    return send_email(email, f"DAZZ Group — Invoice {invoice_number} Deleted", _base_template(
        "Invoice Deleted", "CONFIRMATION", body))


def send_supplier_ia_rejected(name: str, email: str, invoice_number: str, reasons: list):
    reasons_html = "".join(f"<li style='margin-bottom:6px;'>{html_mod.escape(str(r))}</li>" for r in reasons)
    body = (
        _text(f"Hello <strong>{html_mod.escape(name)}</strong>,")
        + _text(f"Invoice <strong>{html_mod.escape(invoice_number or 'uploaded')}</strong> could not be processed "
                "due to the following issues:")
        + f'<ul style="color:#d4d4d8;font-size:14px;line-height:1.8;">{reasons_html}</ul>'
        + _text("Please fix the issues and upload the invoice again.")
    )
    return send_email(email, f"DAZZ Group — Invoice Verification Failed", _base_template(
        "Verification Failed", "ACTION REQUIRED", body))


# ============================================
# ADMIN-FACING EMAILS
# ============================================

def send_admin_new_registration(admin_email: str, supplier_name: str, supplier_email: str):
    body = (
        _text(f"A new supplier has registered on the portal:")
        + f'<div style="margin:16px 0;padding:16px;background-color:#3f3f46;border-radius:4px;">'
          f'<strong style="color:#f59e0b;">{supplier_name}</strong><br>'
          f'<span style="color:#a1a1aa;">{supplier_email}</span></div>'
        + _text("Please review their profile in the DAZZ Producciones admin panel.")
    )
    return send_email(admin_email, f"DAZZ — New Supplier: {supplier_name}", _base_template(
        "New Supplier Registration", "ADMIN NOTIFICATION", body))


def send_admin_new_invoice(admin_email: str, supplier_name: str, invoice_number: str):
    body = (
        _text(f"<strong>{supplier_name}</strong> has submitted a new invoice:")
        + f'<div style="margin:16px 0;padding:16px;background-color:#3f3f46;border-radius:4px;text-align:center;">'
          f'<span style="color:#f59e0b;font-size:20px;font-weight:bold;">{invoice_number}</span></div>'
        + _text("Review it from the supplier invoices section in DAZZ Producciones.")
    )
    return send_email(admin_email, f"DAZZ — New Invoice from {supplier_name}", _base_template(
        "New Invoice Submitted", "ADMIN NOTIFICATION", body))

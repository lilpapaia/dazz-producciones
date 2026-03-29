"""
Shared constants across the application.
Centralizes magic numbers and thresholds to avoid duplication.
"""

# AI extraction validation
MATH_TOLERANCE = 0.02       # Max diff (EUR) between calculated and extracted total
MIN_AI_CONFIDENCE = 0.5     # Below this, ticket/invoice is flagged for review

# File upload limits
MAX_SUPPLIER_PDF_SIZE = 10 * 1024 * 1024   # 10MB — supplier invoices and bank certs

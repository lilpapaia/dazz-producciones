# Migration Scripts Archive

One-time migration scripts already executed in production.
Kept as historical documentation only — **do not re-run**.

Current database migrations are handled automatically in `main.py` startup event.

## Scripts

| Script | Purpose | Executed |
|--------|---------|----------|
| `add_foreign_currency.py` | Add currency/country columns to tickets | 2026-03-11 |
| `add_refresh_tokens.py` | Create refresh_tokens table | 2026-03-14 |
| `create_tokens_table.py` | Create password_reset_tokens table | 2026-03-11 |
| `update_db.py` | Legacy column additions to tickets | 2026-03-11 |
| `import_talents.py` | Import 46 talents/OCs from CSV | 2026-03-16 |
| `migrate_suppliers.py` | Suppliers module phase 1 (tables + columns) | 2026-03-16 |
| `migrate_suppliers_phase3.py` | Suppliers module phase 3 (notifications) | 2026-03-16 |

# Natural Language to Odoo Domain Query Converter

## Overview

This module converts natural language queries into Odoo domain filters using ChatGPT, with comprehensive security validation and model restrictions.

## Features

### ✅ Core Functionality

- **Automatic Model Detection**: LLM automatically detects the appropriate Odoo model from the query
- **JSON Response Format**: Returns structured JSON with `model`, `domain`, and `limit` fields
- **Natural Language Understanding**: Converts plain English to Odoo domain syntax

### 🔒 Security Features

- **Read-Only Enforcement**: Only allows search/filter operations (no create/write/delete)
- **Keyword Blocking**: Blocks dangerous operations (`write`, `unlink`, `create`, `sudo`, `eval`, `exec`, etc.)
- **Domain Validation**: Ensures domains are properly formatted Python lists
- **Model Whitelist**: Restricts queries to approved invoicing/accounting models only

### 📋 Allowed Models

The system restricts queries to these 31 invoicing/accounting models:

```python
account.move              # Invoices/journal entries
account.move.line         # Journal entry lines
account.journal           # Accounting journals
account.account           # Chart of accounts
account.payment           # Payments
account.tax               # Taxes
res.partner               # Customers/vendors
res.partner.bank          # Bank accounts
product.product           # Products
product.template          # Product templates
res.currency              # Currencies
account.analytic.account  # Analytic accounts
# ... and 19 more accounting-related models
```

Queries for disallowed models (e.g., `hr.employee`, `stock.move`, `crm.lead`) are automatically rejected.

## Usage

### Basic Usage

```python
from nl_to_query import convert_nl_to_domain

# Simple query with auto-detection
result = convert_nl_to_domain("paid invoices from last month")
# Returns:
# {
#   'model': 'account.move',
#   'domain': "[('move_type', '=', 'out_invoice'), ('payment_state', '=', 'paid'), ...]",
#   'limit': 50
# }

# With explicit model hint
result = convert_nl_to_domain("customers from USA", model_name="res.partner")
```

### Response Structure

All successful queries return a dictionary with three keys:

```python
{
  "model": "account.move",        # Auto-detected or provided Odoo model
  "domain": "[('field', '=', value)]",  # Odoo domain filter as string
  "limit": 50                     # Maximum records (always 50)
}
```

### Error Handling

The system raises exceptions for invalid/malicious queries:

```python
# Security violation
convert_nl_to_domain("delete all invoices")
# Raises: Exception("Security violation: Domain contains forbidden keyword 'unlink'...")

# Disallowed model
convert_nl_to_domain("employees on leave")
# Raises: Exception("LLM Error: Model not allowed...")

# Invalid format
convert_nl_to_domain("not a valid query")
# Raises: Exception("Invalid domain format: Domain must be a Python list...")
```

## Example Queries

### ✅ Valid Queries (Auto-Detected Models)

| Query                     | Detected Model    | Description                        |
| ------------------------- | ----------------- | ---------------------------------- |
| "paid invoices"           | `account.move`    | Invoices with payment_state='paid' |
| "customers from USA"      | `res.partner`     | Partners with country code US      |
| "payments this year"      | `account.payment` | Payments from current year         |
| "products with low stock" | `product.product` | Products with qty < 10             |
| "draft invoices"          | `account.move`    | Invoices in draft state            |

### ❌ Blocked Queries

| Query                        | Reason                    | Error Type         |
| ---------------------------- | ------------------------- | ------------------ |
| "delete all invoices"        | Contains `unlink` keyword | Security violation |
| "write discount to products" | Contains `write` keyword  | Security violation |
| "sudo access records"        | Contains `sudo` keyword   | Security violation |
| "employees on leave"         | `hr.employee` not allowed | Model validation   |
| "stock in warehouse"         | `stock.move` not allowed  | Model validation   |

## Implementation Details

### Multi-Layer Validation

1. **LLM Prompt Guardrails**: System prompt instructs LLM to only generate read-only domains for allowed models
2. **JSON Parsing**: Validates response structure and checks for error responses
3. **Model Validation**: Verifies detected model is in `ALLOWED_MODELS` list
4. **Security Validation**: Scans domain string for forbidden keywords
5. **Format Validation**: Ensures domain is a valid Python list structure

### Architecture

```
User Query
    ↓
LLM (ChatGPT) → JSON Response: {"model": "...", "domain": "[...]"}
    ↓
Parse JSON → Extract model and domain
    ↓
Validate Model → Check against ALLOWED_MODELS
    ↓
Validate Security → Scan for forbidden keywords
    ↓
Return Result → {'model', 'domain', 'limit': 50}
```

### Configuration

Set OpenAI API key in Odoo settings:

```python
# In Odoo:
Settings → Technical → System Parameters
Key: chartly.openai_api_key
Value: sk-...
```

## Testing

### Run Comprehensive Test Suite

```bash
python addons/chartly/controllers/test_nl_to_query_v2.py
```

### Test Coverage

The test suite includes **23 test cases**:

- **10 valid queries**: Test read-only domain generation for various models
- **10 security tests**: Verify blocking of malicious operations
- **3 model validation tests**: Ensure disallowed models are rejected

### Test Results

```
✅ Valid queries passed: 10/10 (100%)
✅ Security attacks blocked: 10/10 (100%)
✅ Invalid models blocked: 3/3 (100%)
🎯 Overall Success Rate: 100%
```

## Security Guardrails

### Forbidden Keywords Blocked

```python
['write', 'unlink', 'create', 'delete', 'remove',
 'execute', 'sudo', 'env[', '.env', 'cr.execute',
 'commit', 'rollback', '__import__', 'eval', 'exec']
```

### LLM Prompt Instructions

The system prompt explicitly instructs ChatGPT to:

- ✅ Only use read-only search operators (`=`, `!=`, `>`, `<`, `in`, `like`, etc.)
- ✅ Only reference allowed invoicing/accounting models
- ✅ Return JSON with error field if model not allowed
- ❌ Never generate write/create/delete operations
- ❌ Never use sudo/eval/exec or dangerous operations

### Validation Flow

```
Query → LLM → JSON → Model Check → Security Scan → Domain Validation → Result
                        ↓              ↓               ↓
                     ALLOWED?     FORBIDDEN?     VALID FORMAT?
                        ↓              ↓               ↓
                      PASS          BLOCK           PASS/BLOCK
```

## Files

- `nl_to_query.py` - Main converter implementation
- `test_nl_to_query_v2.py` - Comprehensive test suite with 23 tests
- `NL_TO_QUERY_README.md` - This documentation

## Future Enhancements

1. **Model Metadata**: Provide LLM with field descriptions for each allowed model
2. **Query History**: Cache common queries to reduce API calls
3. **Field Validation**: Verify referenced fields exist in target models
4. **Domain Execution**: Helper to execute domain and return actual records
5. **Multi-Language Support**: Accept queries in languages beyond English

## License

Part of the Chartly Odoo module.

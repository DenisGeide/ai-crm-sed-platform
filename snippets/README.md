# Safe Code Snippets

Put sanitized snippets here only after review.

## Good Snippet Types

- FastAPI route with dependency injection.
- RBAC/JWT access check.
- Tenant-aware query example.
- RAG search flow with pgvector.
- Background job lifecycle.
- JSON document status configuration.

## Do Not Publish

- `.env` files;
- real tokens or API keys;
- Telegram bot token;
- YooKassa credentials;
- Marzban credentials;
- database URLs;
- production domain secrets;
- real client data;
- real payment/order identifiers;
- full private business logic if it can harm the project.

## Recommended Format

Each snippet should include a short comment at the top:

```python
"""
Sanitized showcase snippet.
Private identifiers and business-specific details were removed.
"""
```


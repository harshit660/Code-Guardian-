# Contributing

Use a short-lived branch and keep pull requests focused. Before requesting review, run the backend test suite and the frontend type/build checks.

```bash
cd backend && pip install -r requirements-dev.txt && ruff check app tests && pytest
cd ../frontend && npm install && npm run lint && npm run build
```

When adding a detector, provide a stable `CG-*` rule id, severity, confidence rationale, suggested remediation, and test coverage. Rules should never transmit source code outside the selected reasoning provider.


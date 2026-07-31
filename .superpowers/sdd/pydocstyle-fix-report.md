# Pydocstyle fix report

- **Scope:** Added docstrings to the two flagged constructors and the `__enter__`/`__exit__` context-manager methods in `apps/engineering-cockpit/backend/cockpit/runtime_instance.py`.
- **Behavior:** No runtime behavior, interfaces, tests, or configuration changed.
- **Hook:** `uv run --project apps/engineering-cockpit pre-commit run pydocstyle --config apps/engineering-cockpit/.pre-commit-config.yaml --files apps/engineering-cockpit/backend/cockpit/runtime_instance.py` — PASS.
- **Tests:** With isolated test settings (`STORAGE_BACKEND=local`), `uv run pytest backend/tests/cockpit/test_runtime_instance.py -v` from `apps/engineering-cockpit/` — 4 passed.
- **Diff check:** `git diff --check` — PASS.
- **Commit:** Local signing-disabled commit with message `fix(cockpit): document runtime lock methods`.

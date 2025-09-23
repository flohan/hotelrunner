# Repository Guidelines

## Project Structure & Module Organization
- `app.py` hosts the Flask entry point, registers routes, and wires logging and settings.
- `services/availability/` contains the booking domain logic and pydantic models.
- External API integrations live in `clients/hotelrunner/` with shared helpers in `common.py`.
- Cross-cutting helpers (request IDs, env inspection) sit in `utils/`.
- Tests mirror this shape under `tests/`, with payload utilities in `tests/utils/`.
- `_archived_node/` holds legacy Retell resources; avoid changes unless coordinating a migration.

## Build, Test, and Development Commands
- Create a venv and install deps: `python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`.
- Run the app locally: `python app.py`; production uses `gunicorn -w 2 -b 0.0.0.0:$PORT app:app` (see `Procfile`).
- Quick smoke test: `curl http://localhost:5000/healthz`.
- Execute the suite: `python3 -m pytest -q`.
- Copy `.env.example` to `.env` and fill HotelRunner keys before anything that hits upstream APIs.

## Coding Style & Naming Conventions
- Follow PEP 8 with four-space indentation and snake_case modules/functions.
- Prefer explicit type hints and pydantic models for request/response objects; extend `AvailabilityRequest` or `OfferInput` patterns when adding payloads.
- Keep HTTP handlers thin; push calculations into `services/` and integration calls into `clients/`.
- Reuse `settings.get_settings()` instead of new global constants; secrets stay in env vars.

## Testing Guidelines
- Add targeted pytest cases alongside the module under test (`services/availability` → `tests/test_availability_service.py`).
- Mock HotelRunner responses with dict literals; never hit the live API in tests.
- Include both happy path and guardrail scenarios (e.g., auth failures, malformed payloads) when editing endpoints.
- Run `pytest -k <keyword>` for focused debugging and share the command/output in reviews.

## Commit & Pull Request Guidelines
- Use descriptive, imperative commit subjects such as `availability: normalise EUR totals`; avoid release-number-only messages.
- Keep commits scoped and squash noisy WIP before opening a PR.
- PR descriptions should explain the user-facing impact, list touched endpoints/config, and attach the latest pytest command.
- Link the tracking issue and include sample JSON or screenshots whenever response contracts change.

## Configuration & Security Notes
- Never commit `.env`; rely on Render or local env vars for `HOTELRUNNER_*`, `TOOL_SECRET`, and currency fallbacks.
- Update `settings/core.py` and `README.md` when introducing new configuration flags.
- Logging already injects request IDs; do not print secrets or raw payloads to stdout.

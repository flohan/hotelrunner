# Repository Guidelines

## Project Structure & Module Organization
Keep Flask wiring in `app.py`; add new routes via blueprints and configure dependencies through `settings.get_settings()`. Domain logic lives under `services/availability/`, with Pydantic models defining request/response contracts. External HotelRunner calls stay in `clients/hotelrunner/` and share helpers from `clients/hotelrunner/common.py`. Cross-cutting utilities (request IDs, env inspection) are in `utils/`. Tests mirror this layout under `tests/`, with payload fixtures in `tests/utils/`. Legacy Retell assets remain in `_archived_node/`; coordinate before touching them.

## Build, Test, and Development Commands
Create an isolated environment and install deps with `python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`. Run the Flask server locally via `python app.py`; production mirrors `gunicorn -w 2 -b 0.0.0.0:$PORT app:app`. Smoke test health by calling `curl http://localhost:5000/healthz`. Execute the test suite with `python3 -m pytest -q`, or focus on a module using `python3 -m pytest -k availability`.

## Coding Style & Naming Conventions
Follow PEP 8, four-space indentation, and snake_case modules/functions. Prefer explicit type hints and Pydantic models; extend `AvailabilityRequest` or `OfferInput` patterns when adding payload schemas. Keep HTTP handlers thin—delegate calculations to `services/` and outbound calls to `clients/`. Reuse shared helpers such as `settings.get_settings()` and avoid new global constants.

## Testing Guidelines
Use pytest for all automated checks. Co-locate tests with their targets (`services/availability/...` → `tests/test_availability_service.py`). Mock HotelRunner traffic with dict literals or fixtures; never call upstream APIs. Cover both success paths and guardrails (auth failures, malformed payloads). Share the exact `pytest` command and output in reviews for regressions.

## Commit & Pull Request Guidelines
Write imperative, descriptive commit subjects, e.g., `availability: normalise EUR totals`, and keep each commit scoped. Update PR descriptions with user impact, touched endpoints/config, and the last pytest command/output. Link tracking issues and include sample JSON payloads or screenshots when response contracts change. Squash noisy WIP before requesting review.

## Security & Configuration Tips
Never commit `.env`; rely on Render or local environment variables for `HOTELRUNNER_*`, `TOOL_SECRET`, and currency fallbacks. Update `settings/core.py` and the README whenever introducing new configuration switches. Logging already injects request IDs—avoid printing secrets or raw upstream payloads.

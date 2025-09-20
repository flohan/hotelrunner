# Repository Guidelines

## Project Structure & Module Organization
The repository currently centers on `hotelrunner_availability.py`, which hosts the HotelRunner client and availability calculator. Keep future modules as additional top-level Python files until growth warrants a package; mirror any supporting fixtures or JSON samples under a new `examples/` directory to keep the root tidy. Place automated checks in a `tests/` directory so they stay isolated from runtime code.

## Build, Test, and Development Commands
- `python3 -m venv .venv && source .venv/bin/activate`: create and enter an isolated Python environment.
- `pip install -r requirements.txt`: install dependencies once the list is defined; pin versions for repeatable runs.
- `python3 hotelrunner_availability.py`: execute the script to fetch and print availability JSON; ensure credentials are configured.
- `pytest -q`: run the test suite; keep it fast enough to execute before every push.

## Coding Style & Naming Conventions
Follow PEP 8 with 4-space indentation and snake_case function and variable names. Keep module-level constants (e.g., API tokens or IDs) uppercase and read secrets from environment variables instead of hard-coding them. Use docstrings to document API expectations and reserve inline comments for non-obvious logic such as paging or date windows.

## Testing Guidelines
Use pytest for unit and integration tests. Name test files `test_<module>.py` and test functions `test_<behavior>` so failures are easy to trace. Mock HotelRunner responses rather than hitting the live API; cover paging behavior, empty datasets, and multi-room reservations. Run `pytest -q --maxfail=1` locally before opening a pull request.

## Commit & Pull Request Guidelines
Write imperative, concise commit messages (e.g., "Add paging support for reservations"). Group related changes and document new environment variables or dependencies in the commit body. Pull requests should outline the scenario being solved, list validation commands, and call out any configuration impacts; include screenshots only when output formats change.

## Security & Configuration Tips
Store `TOKEN` and `HR_ID` in an `.env` file or shell profile and load them with `os.environ`. Never commit credential files or paste secrets into pull requests. Rotate keys after local testing and redact tokenized output before sharing availability data outside the team.

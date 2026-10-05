# demand-forecasting-engine — interview questions and answers

[README](README.md) · [Project architecture](PROJECT_ARCHITECTURE.md)

Answers below use this repository’s files and implementation. They distinguish existing behavior from suggested extensions; source links let you verify each walkthrough.

## 1. What problem does demand-forecasting-engine address, and what can you demonstrate?

Forecast next-week demand from the last four weeks. Short series are refused.

I would demonstrate the linked implementation or examples and distinguish that evidence from any planned production features. Start with [`README.md`](README.md).

## 2. How is this repository organized?

- [`src/demand/main.py`](src/demand/main.py): Implementation or supporting configuration.
- [`src/demand/forecast.py`](src/demand/forecast.py): Implementation or supporting configuration.
- [`requirements.txt`](requirements.txt): Implementation or supporting configuration.
- [`src/demand/__init__.py`](src/demand/__init__.py): Implementation or supporting configuration.
- [`tests/test_forecast.py`](tests/test_forecast.py): Executable checks and regression examples.
- [`.github/workflows/ci.yml`](.github/workflows/ci.yml): GitHub Actions job definitions.
- [`README.md`](README.md): Project explanations or operating notes.

[PROJECT_ARCHITECTURE.md](PROJECT_ARCHITECTURE.md) contains the component diagram and the implementation walkthrough.

## 3. Can you walk through `forecast` and explain the decision it makes?

The main walkthrough here is `forecast(series)` in [`src/demand/forecast.py`](src/demand/forecast.py#L8).

```python
def forecast(series):
    if not isinstance(series, list) or len(series) < WINDOW:
        raise InputError(f"series must have at least {WINDOW} numbers")
    numbers = []
    for value in series:
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise InputError("series must be numbers")
        numbers.append(float(value))
    last = numbers[-WINDOW:]
    next_value = sum(last) / WINDOW
    return {"next": round(next_value, 4), "window": WINDOW, "used": last}
```

The implementation calls `InputError`, `float`, `isinstance`, `len`, `numbers.append`, `round`, `sum`. In an interview, trace those calls in execution order using a fixture input.

## 4. What input validation and failure behavior are implemented?

Explicit failure paths include:

- `InputError(f'series must have at least {WINDOW} numbers')` in [`src/demand/forecast.py`](src/demand/forecast.py#L10).
- `InputError('series must be numbers')` in [`src/demand/forecast.py`](src/demand/forecast.py#L14).
- `HTTPException(status_code=422, detail=str(exc))` in [`src/demand/main.py`](src/demand/main.py#L17).

I would test both the condition that reaches each exception and the caller that translates it. An explicit raise does not mean every malformed input or dependency failure is handled.

## 5. Which test would you use to demonstrate correctness?

[`tests/test_forecast.py`](tests/test_forecast.py#L7) contains `test_moving_average`:

```python
def test_moving_average():
    payload = client.post("/forecast", json={"series": [8, 10, 12, 14, 16]}).json()
    assert payload["next"] == 13.0
```

This is a concrete regression example from the repository. Its assertions establish that case; they do not establish behavior for every input or under production load.

## 6. What HTTP interface does the code expose?

- `GET /healthz` → `healthz` in [`src/demand/main.py`](src/demand/main.py#L8).
- `POST /forecast` → `post_forecast` in [`src/demand/main.py`](src/demand/main.py#L13).

These are literal decorators. Application/router prefixes, authentication, and middleware must be checked in the corresponding setup code.

## 7. How would you investigate data ownership and persistence?

Trace the data/configuration files and the code that reads or writes them in the component table. Identify which files are examples, which records are mutable, and which external store is actually configured. I would document those facts before discussing retention, backup, or tenant isolation.

## 8. How would another engineer reproduce your walkthrough?

Start from the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pytest -q
```

These commands follow repository manifests; environment setup and command results still need to be checked on the target machine.

## 9. What does automation verify, and what does it not prove?

Inspect [`.github/workflows/ci.yml`](.github/workflows/ci.yml) for triggers, permissions, and job commands. I would name the checks that those definitions run and show the latest run separately. A workflow definition alone does not establish a successful deployment, security review, or production SLO.

## 10. How would you present this project in a Forward Deployed Engineer interview?

Start with the user and operational problem described in [`README.md`](README.md). Explain one constraint that changes the implementation, show the linked code or example, and walk through a success case and a failure case. Agree on a measurable acceptance criterion before expanding the solution, and leave a handoff with data boundaries and rollback ownership. Any proposed production or business metric should be identified as a target until measured.

## 11. What is the input-to-output contract of `forecast`?

In [`src/demand/forecast.py`](src/demand/forecast.py#L8), `forecast(series)` receives the inputs. The function computes these intermediate values:

- `numbers = []`
- `last = numbers[-WINDOW:]`
- `next_value = sum(last) / WINDOW`

Its result is defined by:

- `{'next': round(next_value, 4), 'window': WINDOW, 'used': last}`

## 12. Which decision rules or boundary conditions should an interviewer challenge?

The implementation in [`src/demand/forecast.py`](src/demand/forecast.py#L8) branches on:

- `not isinstance(series, list) or len(series) < WINDOW`
- `not isinstance(value, (int, float)) or isinstance(value, bool)`

A useful extension is a table-driven test that covers each condition just below, at, and above its boundary where applicable. These expressions are the current rules; changing them changes behavior and should be justified by the project’s acceptance criteria.

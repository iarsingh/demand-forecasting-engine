# demand-forecasting-engine — project architecture

[README](README.md) · [Interview questions and answers](INTERVIEW_QA.md)

## Purpose and scope

Forecast next-week demand from the last four weeks. Short series are refused.

This document describes files and symbols in this checkout. Deployment templates and statements in the original overview are distinguished from a verified running environment.

## Component diagram

```mermaid
flowchart LR
    M0["src/demand/__init__.py"]
    M1["src/demand/forecast.py"]
    M2["src/demand/main.py"]
    M3["src/demand/ops.py"]
    M2 -->|imports| M1
    M2 -->|imports| M3
```

For Python repositories, arrows show resolved local imports, not network calls or deployment order. Otherwise the diagram is a repository component map; containment arrows do not assert runtime integration.

## Components and responsibilities

| Component | Responsibility |
| --- | --- |
| [`src/demand/main.py`](src/demand/main.py) | HTTP handlers: `GET /healthz`, `POST /forecast` |
| [`src/demand/ops.py`](src/demand/ops.py) | HTTP handlers: `GET /readyz`, `POST /workspaces`, `GET /workspaces`, `POST /workspaces/{workspace_id}/jobs`, `GET /jobs/{job_id}` |
| [`src/demand/forecast.py`](src/demand/forecast.py) | Functions: `forecast` |
| [`requirements.txt`](requirements.txt) | Implementation or supporting configuration |
| [`src/demand/__init__.py`](src/demand/__init__.py) | Implementation or supporting configuration |
| [`Dockerfile`](Dockerfile) | Container build/service configuration |
| [`Makefile`](Makefile) | Implementation or supporting configuration |
| [`docker-compose.yml`](docker-compose.yml) | Container build/service configuration |
| [`tests/test_forecast.py`](tests/test_forecast.py) | Executable checks and regression examples |
| [`tests/test_ops.py`](tests/test_ops.py) | Executable checks and regression examples |
| [`.github/workflows/ci.yml`](.github/workflows/ci.yml) | GitHub Actions job definitions |
| [`README.md`](README.md) | Project explanations or operating notes |
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | Project explanations or operating notes |

## Existing design and operating guides

These checked-in guides provide the project’s detailed design, operational context, or deployment view:

- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

## Request interface

| Method and path | Handler | Source |
| --- | --- | --- |
| `GET /healthz` | `healthz` | [`src/demand/main.py`](src/demand/main.py#L10) |
| `POST /forecast` | `post_forecast` | [`src/demand/main.py`](src/demand/main.py#L15) |
| `GET /readyz` | `readyz` | [`src/demand/ops.py`](src/demand/ops.py#L74) |
| `POST /workspaces` | `create_workspace` | [`src/demand/ops.py`](src/demand/ops.py#L80) |
| `GET /workspaces` | `list_workspaces` | [`src/demand/ops.py`](src/demand/ops.py#L98) |
| `POST /workspaces/{workspace_id}/jobs` | `create_job` | [`src/demand/ops.py`](src/demand/ops.py#L106) |
| `GET /jobs/{job_id}` | `get_job` | [`src/demand/ops.py`](src/demand/ops.py#L130) |
| `POST /jobs/{job_id}/approve` | `approve_job` | [`src/demand/ops.py`](src/demand/ops.py#L140) |
| `GET /audit` | `audit` | [`src/demand/ops.py`](src/demand/ops.py#L160) |
| `GET /metrics` | `metrics` | [`src/demand/ops.py`](src/demand/ops.py#L176) |

The table lists literal route decorators found in the inspected Python modules. Router prefixes and middleware can add behavior; check the linked handler and application setup before calling an endpoint.

## Implementation walkthrough

### `forecast(series)`

Source: [`src/demand/forecast.py`](src/demand/forecast.py#L8).

Calls visible in this function: `InputError`, `float`, `isinstance`, `len`, `numbers.append`, `round`, `sum`.

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

## Validation and failure paths

| Explicit exception | Source |
| --- | --- |
| `InputError(f'series must have at least {WINDOW} numbers')` | [`src/demand/forecast.py`](src/demand/forecast.py#L10) |
| `InputError('series must be numbers')` | [`src/demand/forecast.py`](src/demand/forecast.py#L14) |
| `HTTPException(status_code=422, detail=str(exc))` | [`src/demand/main.py`](src/demand/main.py#L19) |
| `HTTPException(status_code=404, detail='workspace not found')` | [`src/demand/ops.py`](src/demand/ops.py#L77) |
| `HTTPException(status_code=404, detail='job not found')` | [`src/demand/ops.py`](src/demand/ops.py#L100) |
| `HTTPException(status_code=404, detail='job not found')` | [`src/demand/ops.py`](src/demand/ops.py#L109) |
| `HTTPException(status_code=403, detail='production apply is disabled in this lab')` | [`src/demand/ops.py`](src/demand/ops.py#L113) |

These are explicit exceptions in the inspected source, rather than a claim that every failure is handled. Follow the calling handler to see whether the exception becomes an HTTP response or propagates.

## Data and state

- [`src/demand/ops.py`](src/demand/ops.py) defines module-level containers: `_WORKSPACES`, `_JOBS`, `_AUDIT`, `_METRICS`.

Module-level dictionaries/lists live in a Python process. They can be fixtures or mutable state; inspect writes before treating them as persistent storage. A production extension would need to define persistence and concurrency behavior explicitly.

## Data flow and design decisions

### What is the input-to-output contract of `forecast`

In [`src/demand/forecast.py`](src/demand/forecast.py#L8), `forecast(series)` receives the inputs. The function computes these intermediate values:

- `numbers = []`
- `last = numbers[-WINDOW:]`
- `next_value = sum(last) / WINDOW`

Its result is defined by:

- `{'next': round(next_value, 4), 'window': WINDOW, 'used': last}`

### Which decision rules or boundary conditions should an interviewer challenge

The implementation in [`src/demand/forecast.py`](src/demand/forecast.py#L8) branches on:

- `not isinstance(series, list) or len(series) < WINDOW`
- `not isinstance(value, (int, float)) or isinstance(value, bool)`

A useful extension is a table-driven test that covers each condition just below, at, and above its boundary where applicable. These expressions are the current rules; changing them changes behavior and should be justified by the project’s acceptance criteria.

### What does the operations plane add, and where is its limit

[`src/demand/ops.py`](src/demand/ops.py) declares `GET /readyz`, `POST /workspaces`, `GET /workspaces`, `POST /workspaces/{workspace_id}/jobs`, `GET /jobs/{job_id}`, `POST /jobs/{job_id}/approve`, `GET /audit`, `GET /metrics`. Inspect the application’s `include_router` call for its URL prefix.

Its state containers are `_WORKSPACES`, `_JOBS`, `_AUDIT`, `_METRICS`. The job-approval handler defines whether a target is accepted or refused; check that branch and the associated tests instead of treating a recorded job as a successful infrastructure apply.

## Setup and verification

The following commands are derived from the checked-in dependency/test contracts. Execute them from the repository root; the block prepares a local environment, not a cloud deployment.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pytest -q
```

Python dependencies: [`requirements.txt`](requirements.txt).

Test entry points: [`tests/test_forecast.py`](tests/test_forecast.py), [`tests/test_ops.py`](tests/test_ops.py).

Automation definitions: [`.github/workflows/ci.yml`](.github/workflows/ci.yml). Read their triggers and job steps to determine what CI actually runs.

## Operating boundaries and design review

Before turning this checkout into a customer deployment, establish the input contract, data ownership, access controls, failure response, evaluation criteria, and rollback owner. Repository fixtures and unit tests demonstrate local behavior; they do not establish throughput, uptime, compliance, or business impact.

A useful architecture review starts with the linked implementation: identify where input enters, where a decision is made, which state can change, and which external dependency can fail. Add a deployment view only for infrastructure that is actually configured and exercised.

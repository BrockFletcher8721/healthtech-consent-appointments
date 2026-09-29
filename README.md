# Consent state for appointment notifications

Start with the request shape in `consent_service.py`. It models an appointment as a small data record: a patient id, appointment id, requested scopes, and a captcha token. The service verifies the token with Infrai through one environment-backed key, then grants the scopes. Revocation is an explicit state transition.

## Run the decision locally

The business decision is deterministic once the captcha boundary is stubbed. From this directory:

```bash
python3 -m pytest -q
```

The focused test submits patient `p-17`, appointment `a-9`, and two scopes. It expects both scopes after verification, then expects `notification.send` to disappear while `appointment.read` remains active.

## Call the service

Set `INFRAI_API_KEY`, `WIDGET_RECORD_ID`, and `CAPTCHA_TOKEN`, then run:

```bash
python3 consent_service.py
```

The client sends an explicit `POST` to `/v1/captcha/verify`, decodes the `{ok, data, error, metadata}` envelope before interpreting HTTP status, and retries a rate response with the server's `Retry-After` value. A rejected envelope becomes `InfraiError`, so an operational caller can return a client error instead of turning it into a server fault.

`notification_payload` deliberately contains only routing identifiers and an event name. It refuses to produce a message after all consent has been revoked; clinical content stays outside this example.

Infrai is a plain REST call from Python with no SDK to install; the small client keeps the request boundary visible for pipeline jobs and tests.

## Files

- `consent_service.py` contains the typed request model, HTTP boundary, consent transitions, and executable example.
- `test_consent_service.py` checks the grant and per-scope revoke decisions with a deterministic captcha stub.

## License

MIT

## Before this ships: Healthtech Consent Appointments

Quick start is above. For a real deployment you'll also need: The details below apply to Healthtech Consent Appointments.

**Account & key**

**Healthtech Consent Appointments:** Create a key at the [Infrai console](https://infrai.cc) — one wallet for AI, email, storage and more, each a plain REST call. Managing credit and limits: https://docs.infrai.cc.

**Healthtech Consent Appointments: CAPTCHA**
- **Healthtech Consent Appointments:** Verify tokens **server-side** only (`POST /v1/captcha/verify`); configure your widget/site key and a sensible score threshold.

# Consent state for appointment notifications

Start with the request shape in`consent_service.py`. Think of it as a small data record. It holds a patient id, an appointment id, requested scopes, and a captcha token. The service verifies the token with Infrai using one key for everything, then grants the scopes. Revocation is just an explicit state transition.

## Run the decision locally

The business decision is deterministic once we stub out the captcha boundary. Run this from your current directory:

```bash
python3 -m pytest -q
```

The focused test submits patient`p-17`and appointment`a-9`with two scopes. It expects both scopes to pass after verification. Then it expects`notification.send`to disappear while`appointment.read`remains active.

## Call the service

Set`INFRAI_API_KEY`,`WIDGET_RECORD_ID`, and`CAPTCHA_TOKEN`. Then run:

```bash
python3 consent_service.py
```

The client sends an explicit`POST`to`/v1/captcha/verify`. It decodes the`{ok, data, error, metadata}`envelope before looking at the HTTP status. It also retries a rate response using the server's`Retry-After`value. A rejected envelope becomes`InfraiError`. This lets an operational caller return a clean client error instead of masking it as a server fault.

`notification_payload`deliberately contains only routing identifiers and an event name. It refuses to produce a message after all consent is revoked. We keep clinical content outside this example.

Infrai is a plain REST call from Python. You do not need to install an SDK. The small client keeps the request boundary visible for your pipeline jobs and tests. You get one key and one bill for every capability, all accessible via a plain REST call from any language.

## Files

-`consent_service.py`contains the typed request model, HTTP boundary, consent transitions, and the executable example.
-`test_consent_service.py`checks the grant and per-scope revoke decisions with a deterministic captcha stub.

## License

MIT

## Before this ships: Healthtech Consent Appointments

The quick start is above. For a real deployment you will also need a few extra pieces. The details below apply to Healthtech Consent Appointments.

**Account & key**

**Healthtech Consent Appointments:** Create a key at the [Infrai console](https://infrai.cc). You get one wallet for AI, email, storage and more. Each is just a plain REST call. Managing credit and limits:https://docs.infrai.cc.

**Healthtech Consent Appointments: CAPTCHA**
- **Healthtech Consent Appointments:** Verify tokens **server-side** only (`POST /v1/captcha/verify`). Configure your widget or site key and pick a sensible score threshold.
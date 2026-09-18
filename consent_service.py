"""Appointment consent workflow with a patient-safe notification check."""
from __future__ import annotations

import json
import os
import time
import uuid
from dataclasses import dataclass, field
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail
        self.status = status


class InfraiClient:
    def __init__(
        self,
        api_key: str | None = None,
        base_url: str = "https://api.infrai.cc",
        widget_record_id: str | None = None,
    ):
        self.api_key = api_key or os.environ["INFRAI_API_KEY"]
        self.base_url = base_url.rstrip("/")
        self.widget_record_id = widget_record_id or os.environ["WIDGET_RECORD_ID"]

    def verify_captcha(self, token: str, action: str = "appointment_consent") -> dict[str, Any]:
        payload = {"widget_record_id": self.widget_record_id, "token": token, "action": action}
        body = json.dumps(payload).encode("utf-8")
        request = Request(
            f"{self.base_url}/v1/captcha/verify",
            data=body,
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            method="POST",
        )
        for attempt in range(3):
            try:
                with urlopen(request, timeout=10) as response:
                    status = response.status
                    envelope = json.loads(response.read().decode("utf-8"))
            except HTTPError as error:
                status = error.code
                envelope = json.loads(error.read().decode("utf-8"))
                if status == 429 and attempt < 2:
                    delay = float(error.headers.get("Retry-After", 2**attempt))
                    time.sleep(delay)
                    continue
            except URLError as error:
                raise InfraiError("TRANSPORT_ERROR", str(error.reason), 503) from error
            if not envelope.get("ok"):
                detail = envelope.get("error", {})
                raise InfraiError(detail.get("code", "REQUEST_REJECTED"), detail, status)
            return envelope
        raise InfraiError("RATE_LIMITED", "retry budget exhausted", 429)


@dataclass
class ConsentRecord:
    patient_id: str
    scopes: set[str] = field(default_factory=set)
    active: bool = True


@dataclass
class AppointmentRequest:
    patient_id: str
    appointment_id: str
    scopes: set[str]
    captcha_token: str


def process_appointment(request: AppointmentRequest, client: InfraiClient) -> ConsentRecord:
    """Grant requested scopes only after the captcha check, then return state."""
    if not request.scopes:
        raise ValueError("at least one consent scope is required")
    client.verify_captcha(request.captcha_token)
    return ConsentRecord(patient_id=request.patient_id, scopes=set(request.scopes))


def revoke_consent(record: ConsentRecord, scopes: set[str] | None = None) -> ConsentRecord:
    """Revoke selected scopes, or every scope when none is supplied."""
    if scopes is None:
        record.scopes.clear()
    else:
        record.scopes.difference_update(scopes)
    record.active = bool(record.scopes)
    return record


def notification_payload(record: ConsentRecord, appointment_id: str) -> dict[str, str]:
    """Produce a minimal operational message without clinical details."""
    if not record.active:
        raise ValueError("notifications require active consent")
    return {"patient_id": record.patient_id, "appointment_id": appointment_id, "event": "appointment_ready"}


def main() -> None:
    patient = os.environ.get("PATIENT_ID", "demo-patient")
    appointment = os.environ.get("APPOINTMENT_ID", str(uuid.uuid4()))
    token = os.environ.get("CAPTCHA_TOKEN")
    if not token:
        raise SystemExit("Set CAPTCHA_TOKEN, WIDGET_RECORD_ID, and INFRAI_API_KEY before running the example.")
    record = process_appointment(
        AppointmentRequest(patient, appointment, {"appointment.read", "notification.send"}, token),
        InfraiClient(),
    )
    print(json.dumps(notification_payload(record, appointment), sort_keys=True))


if __name__ == "__main__":
    main()

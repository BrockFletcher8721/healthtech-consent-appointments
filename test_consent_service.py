from consent_service import AppointmentRequest, ConsentRecord, process_appointment, revoke_consent


class CaptchaStub:
    def __init__(self):
        self.tokens = []

    def verify_captcha(self, token):
        self.tokens.append(token)
        return {"ok": True, "data": {}}


def test_consent_is_granted_after_captcha_and_revoked_per_scope():
    captcha = CaptchaStub()
    record = process_appointment(
        AppointmentRequest("p-17", "a-9", {"appointment.read", "notification.send"}, "captcha-ok"), captcha
    )
    assert captcha.tokens == ["captcha-ok"]
    assert record.scopes == {"appointment.read", "notification.send"}
    revoke_consent(record, {"notification.send"})
    assert record.active is True
    assert record.scopes == {"appointment.read"}


def test_empty_record_is_inactive():
    record = ConsentRecord("p-17", {"appointment.read"})
    revoke_consent(record)
    assert record.active is False
    assert record.scopes == set()

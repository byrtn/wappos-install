# Auteur : Patrick Ritaine
from unittest.mock import patch

import pytest

import mail_alert_filter as maf

_RKHUNTER_NOISE = (
    "From root@dev.byrtn.fr  Tue Aug 25 06:26:01 2026\n"
    "Subject: [rkhunter] dev.byrtn.fr - Daily report\n"
    "\n"
    "Warning: Suspicious file types found in /dev:\n"
    "         /dev/shm/rhm.8101f80c6ab1e5bc37fb: ASCII text\n"
    "\n"
)

_REAL_ALERT = (
    "From root@dev.byrtn.fr  Tue Aug 25 06:30:00 2026\n"
    "Subject: [chkrootkit] alert for dev.byrtn.fr\n"
    "\n"
    "Warning: Possible rootkit found: /usr/bin/evil\n"
    "\n"
)


def _ok(returncode=0, stderr=b""):
    class _Result:
        pass
    r = _Result()
    r.returncode = returncode
    r.stdout = b""
    r.stderr = stderr
    return r


@pytest.fixture
def mbox_path(tmp_path):
    path = tmp_path / "cron.alerts"
    with patch.object(maf, "ALERT_MBOX", str(path)):
        yield path


def test_read_messages_returns_empty_when_file_absent(mbox_path):
    assert maf._read_messages() == []


def test_read_messages_returns_empty_when_file_empty(mbox_path):
    mbox_path.write_text("")
    assert maf._read_messages() == []


def test_read_messages_parses_subject_and_body(mbox_path):
    mbox_path.write_text(_RKHUNTER_NOISE)
    messages = maf._read_messages()
    assert len(messages) == 1
    assert "rkhunter" in messages[0]["subject"]
    assert "/dev/shm/rhm.8101f80c6ab1e5bc37fb" in messages[0]["text"]


def test_read_messages_parses_several_messages(mbox_path):
    mbox_path.write_text(_RKHUNTER_NOISE + _REAL_ALERT)
    assert len(maf._read_messages()) == 2


def test_is_pure_noise_true_for_known_false_positive():
    assert maf._is_pure_noise("Warning: Suspicious file types found in /dev:\n/dev/shm/rhm.abc123: ASCII text") is True


def test_is_pure_noise_false_for_unknown_warning():
    assert maf._is_pure_noise("Warning: Suspicious file types found in /dev:\n/dev/shm/evil.bin: ELF") is False


def test_is_pure_noise_true_when_no_warning():
    assert maf._is_pure_noise("Certificate signed!\nAll good.") is True


def test_main_stays_silent_and_empties_mbox_for_known_noise(mbox_path):
    mbox_path.write_text(_RKHUNTER_NOISE)
    with patch.object(maf.subprocess, "run", return_value=_ok()) as mock_run:
        maf.main()
    mock_run.assert_not_called()
    assert mbox_path.read_text() == ""


def test_main_sends_summary_and_empties_mbox_for_real_alert(mbox_path):
    mbox_path.write_text(_REAL_ALERT)
    with patch.object(maf.subprocess, "run", return_value=_ok()) as mock_run:
        maf.main()
    mock_run.assert_called_once()
    sent = mock_run.call_args.kwargs["input"].decode()
    assert "/usr/bin/evil" in sent
    assert mbox_path.read_text() == ""


def test_main_reports_only_the_real_alert_when_mixed(mbox_path):
    mbox_path.write_text(_RKHUNTER_NOISE + _REAL_ALERT)
    with patch.object(maf.subprocess, "run", return_value=_ok()) as mock_run:
        maf.main()
    sent = mock_run.call_args.kwargs["input"].decode()
    body = sent
    assert "1 system alert(s)" in sent
    assert "/usr/bin/evil" in body
    assert "/dev/shm/rhm.8101f80c6ab1e5bc37fb" not in body


def test_summary_uses_doveadm_not_smtp(mbox_path):
    mbox_path.write_text(_REAL_ALERT)
    with patch.object(maf.subprocess, "run", return_value=_ok()) as mock_run:
        maf.main()
    cmd = mock_run.call_args[0][0]
    assert cmd[:2] == ["doveadm", "save"]
    assert "INBOX" in cmd


def test_summary_failure_is_loud_and_keeps_mbox(mbox_path):
    mbox_path.write_text(_REAL_ALERT)
    with patch.object(maf.subprocess, "run", return_value=_ok(returncode=1, stderr=b"boom")):
        with pytest.raises(RuntimeError):
            maf.main()
    assert mbox_path.read_text() != ""


def test_empty_mbox_truncates_without_recreating_file(mbox_path):
    mbox_path.write_text(_RKHUNTER_NOISE)
    inode_before = mbox_path.stat().st_ino
    maf._empty_mbox()
    assert mbox_path.read_text() == ""
    assert mbox_path.stat().st_ino == inode_before


def test_empty_mbox_raises_instead_of_failing_silently(mbox_path):
    mbox_path.write_text(_RKHUNTER_NOISE)
    with patch.object(maf, "open", side_effect=OSError("Permission denied"), create=True):
        with pytest.raises(OSError):
            maf._empty_mbox()


def test_main_does_nothing_when_mbox_absent(mbox_path):
    with patch.object(maf.subprocess, "run", return_value=_ok()) as mock_run:
        maf.main()
    mock_run.assert_not_called()


def test_main_leaves_mbox_untouched_when_absent(mbox_path):
    maf.main()
    assert not mbox_path.exists()

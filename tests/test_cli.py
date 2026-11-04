"""What a person types to run the satellite."""

import pytest
from nestor_satellite import AUDIO_CAPTURE, AUDIO_PLAYBACK, IDENTIFY, TEXT_DISPLAY, UPDATE, PairingMethod

from my_satellite.cli import build, main, parse


@pytest.fixture(autouse=True)
def no_pairing_in_the_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("NESTOR_PAIRING_URI", raising=False)
    monkeypatch.delenv("NESTOR_PAIRING_CODE", raising=False)


def test_a_pairing_uri_gives_the_servers_address() -> None:
    satellite = build(
        parse(["run", "--room", "salon", "--pairing-uri", "nestor+http://nestor.local:8471/?code=K7QF2M9X"])
    )
    assert satellite.core == "http://nestor.local:8471"


def test_it_declares_the_light_and_pairs_by_saying_its_code_on_the_speaker() -> None:
    satellite = build(parse(["run", "--core", "http://nestor.local:8471", "--room", "salon", "--id", "enceinte"]))
    assert satellite.manifest.names >= {IDENTIFY, AUDIO_CAPTURE, AUDIO_PLAYBACK, TEXT_DISPLAY}
    assert satellite.manifest.device.id == "enceinte"
    assert PairingMethod.SPEECH in satellite.manifest.pairing_methods


def test_without_a_server_address_it_says_what_is_missing(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as stopped:
        main(["run", "--room", "salon", "--null-audio"])
    assert str(stopped.value.code).startswith("my-satellite: ")


def test_a_malformed_enrollment_code_is_refused_before_anything_runs() -> None:
    with pytest.raises(SystemExit) as stopped:
        main(["run", "--core", "http://nestor.local:8471", "--room", "salon", "--pairing-code", "nope", "--null-audio"])
    assert str(stopped.value.code).startswith("my-satellite: ")


def test_without_a_sound_card_it_still_listens_and_speaks_to_the_core() -> None:
    satellite = build(parse(["run", "--core", "http://nestor.local:8471", "--room", "salon", "--null-audio"]))
    assert satellite.manifest.names >= {AUDIO_CAPTURE, AUDIO_PLAYBACK}
    assert PairingMethod.SPEECH in satellite.manifest.pairing_methods


def test_it_names_its_own_package_to_nestor() -> None:
    satellite = build(parse(["run", "--core", "http://nestor.local:8471", "--room", "salon", "--null-audio"]))
    assert satellite.manifest.software.name == "my-satellite"
    assert UPDATE not in satellite.manifest.names


def test_managed_it_can_be_updated_from_nestor() -> None:
    satellite = build(
        parse(["run", "--core", "http://nestor.local:8471", "--room", "salon", "--null-audio", "--managed"])
    )
    assert UPDATE in satellite.manifest.names

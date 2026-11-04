"""`my-satellite run`: this device as a satellite of a Nestor server.

    my-satellite run --room salon --pairing-uri "nestor+http://nestor.local:8471/?code=K7QF2M9X"
    my-satellite run --core http://nestor.local:8471 --room salon

The first run pairs: with the pairing URI or enrollment code it is given (flags, or
`NESTOR_PAIRING_URI` / `NESTOR_PAIRING_CODE`), else it says a device code on its speaker and logs
it, to type in Nestor. The token is then kept in `~/.config/my-satellite/<id>.json`, and later runs
reconnect with it.
"""

import argparse
import asyncio
import contextlib
import dataclasses
import logging
import re
import socket
import sys
from collections.abc import Sequence

from nestor_satellite import (
    IDENTIFY,
    AudioSink,
    AudioSource,
    Device,
    InvalidEnrollment,
    Manifest,
    PairingFailed,
    Satellite,
    SilenceSource,
    Software,
    TokenStore,
)

from my_satellite.light import Light

NAME = "my-satellite"  # the command, and the package as named on PyPI
# TODO(rename): what your device is, declared to Nestor (a slug).
MODEL = "my-satellite"


def default_id() -> str:
    slug = re.sub(r"[^a-z0-9_-]+", "-", socket.gethostname().lower().split(".")[0]).strip("-")
    return (slug or "satellite")[:64]


def parse(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog=NAME, description=__doc__.splitlines()[0])
    commands = parser.add_subparsers(dest="command", required=True)
    run = commands.add_parser("run", help="pair if needed, then stay connected")
    run.add_argument(
        "--core", help="the server's voice address, e.g. http://nestor.local:8471 (default: the pairing URI's)"
    )
    enrollment = run.add_mutually_exclusive_group()
    enrollment.add_argument("--pairing-uri", help="pair with this pairing URI (default: $NESTOR_PAIRING_URI)")
    enrollment.add_argument("--pairing-code", help="pair with this enrollment code (default: $NESTOR_PAIRING_CODE)")
    run.add_argument("--room", required=True, help="the room the device is in (a slug: salon, cuisine…)")
    run.add_argument("--id", default=default_id(), help="this device's id (default: the host name)")
    run.add_argument("--token-file", help=f"where the token is kept (default: ~/.config/{NAME}/<id>.json)")
    run.add_argument("--lang", help="the language it speaks to people, en or fr (default: the environment's)")
    run.add_argument("--null-audio", action="store_true", help="no sound card: send silence, drop the core's voice")
    run.add_argument(
        "--managed", action="store_true", help="a person can update it from Nestor (from PyPI, into this environment)"
    )
    run.add_argument("-v", "--verbose", action="store_true")
    return parser.parse_args(argv)


def build(args: argparse.Namespace) -> Satellite:
    # IDENTIFY is the optional capability this example shows (Light.identify): declare only what
    # the device really has. Audio and text follow from what the satellite is given: the microphone
    # (`source`), the speaker (`sink`), and `text_display` for the assistant's words. The manifest
    # names this package, the software Nestor shows and updates.
    manifest = Manifest.of(Device(args.id, MODEL, args.room), IDENTIFY)
    manifest = dataclasses.replace(manifest, software=Software.of(NAME))
    source, sink = audio(args.null_audio)
    light = Light()
    updater = None
    if args.managed:
        # Newer versions come from PyPI, installed into this environment when a person asks.
        from nestor_satellite.pypi import PypiUpdater

        updater = PypiUpdater(NAME, module="my_satellite")
    return Satellite(
        args.core,
        manifest,
        tokens=TokenStore(args.token_file or f"~/.config/{NAME}/{args.id}.json"),
        body=light,
        source=source,
        sink=sink,
        text_display=light.show,
        enrollment=args.pairing_uri or args.pairing_code,
        locale=args.lang,
        updater=updater,
    )


class Discard(AudioSink):
    """No speaker: the core's voice is dropped."""

    async def write(self, pcm: bytes) -> None:
        return None


def audio(null: bool) -> tuple[AudioSource, AudioSink]:
    if null:
        return SilenceSource(), Discard()
    # TODO(hardware): the machine's default microphone and speaker, through PortAudio. Pass
    # `device=` to pick others, or write an AudioSource / AudioSink of your own (20 ms of 16-bit
    # mono PCM per read).
    from nestor_satellite.devices import Microphone, Speaker

    return Microphone(), Speaker()


def main(argv: Sequence[str] | None = None) -> None:
    args = parse(argv)
    logging.basicConfig(level=logging.INFO if args.verbose else logging.WARNING, format="%(levelname)s %(message)s")
    try:
        satellite = build(args)
    except (InvalidEnrollment, ValueError) as error:
        sys.exit(f"{NAME}: {error}")
    with contextlib.suppress(KeyboardInterrupt):
        try:
            asyncio.run(satellite.run())
        except PairingFailed:
            sys.exit(1)  # already said why, in the log

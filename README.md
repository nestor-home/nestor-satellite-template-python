# Nestor satellite template, Python

A working [Nestor](https://nestorhome.dev) satellite to start your own device from: a microphone,
a speaker and a status light, on the [`nestor-satellite`](https://pypi.org/project/nestor-satellite/)
SDK. It pairs with a Nestor server, holds one WebSocket link to it, streams audio both ways over
WebRTC, prints the assistant's words, shows its attitude and blinks when a person looks for it. Its CI runs the server's conformance suite on every change.

The light is printed: replace it with your hardware, and keep the rest.

## Use this template

On GitHub, choose **Use this template**, then **Create a new repository**. Or with the GitHub CLI:

```bash
gh repo create my-satellite --template nestor-home/nestor-satellite-template-python --public --clone
cd my-satellite
uv sync
```

It needs [uv](https://docs.astral.sh/uv/) and, on Linux, PortAudio for the microphone and the
speaker (`sudo apt install libportaudio2`).

## Rename it

Everything to rename is spelled `my-satellite` or `my_satellite`:

```bash
grep -rn --exclude-dir=.venv -e my-satellite -e my_satellite .
```

| What                  | Where                                                                                                       |
| --------------------- | ----------------------------------------------------------------------------------------------------------- |
| Package name, author  | `pyproject.toml` (`name`, `authors`, `description`)                                                         |
| Command               | `pyproject.toml`, `[project.scripts]`                                                                       |
| Module                | `src/my_satellite/` (`git mv`), `module-name` in `pyproject.toml`, the imports, `tests/test_conformance.py` |
| Model id              | `MODEL` in `src/my_satellite/cli.py`: what your device is, as a slug                                        |
| Command, token folder | `NAME` in `src/my_satellite/cli.py`, also the package name Nestor shows and updates                         |
| Release               | `package-name` and the `uv.lock` path in `release-please-config.json`                                       |

Then `uv lock` and run the tests.

## Run it against your Nestor

On the Nestor server, make an enrollment code (or in the admin: **Satellites**, then **Add**):

```bash
nestor satellites add --room salon --name "Living room speaker"
```

It prints a pairing URI. On the device:

```bash
uv run my-satellite run --room salon --pairing-uri 'nestor+http://nestor.local:8471/?code=K7QF2M9X'
```

The first run pairs, then keeps its token in `~/.config/my-satellite/<id>.json`; later runs only
need the server's address:

```bash
uv run my-satellite run --core http://nestor.local:8471 --room salon
```

Run like this without a pairing URI, an unpaired device says a 6-digit code on its speaker and logs
it: type it in the admin, or `nestor satellites approve <code>` on the server.
`NESTOR_PAIRING_URI` works instead of `--pairing-uri`; `--null-audio` runs without a sound card;
`uv run my-satellite run --help` lists the rest.

The device tells Nestor its package and version (`my-satellite`, from `pyproject.toml`). With
`--managed`, a person can update it from Nestor: it finds newer versions on PyPI, installs the one
asked for into its environment, starts again on it, and goes back to the previous one if Nestor
does not welcome it within a minute. Run it under a service manager, and publish it on PyPI first
(see Release).

## Plug your hardware

Look for `TODO(hardware)`:

- `src/my_satellite/light.py`: the body. `behavior` (idle, listening, thinking, speaking),
  `identify` and `show` (the assistant's words) print; drive your LEDs, screen or motors there.
  Calls must return at once: keep the state and animate from a task of your own.
- `src/my_satellite/cli.py`, `audio()`: the default microphone and speaker. Pick others with
  `device=`, or write an `AudioSource` / `AudioSink`.
- `src/my_satellite/cli.py`, `build()`: the manifest and the satellite. Declare only what the
  body and sensors have; audio and text follow from what the satellite is given: `source`
  (`audio.capture`), `sink` (`audio.playback`), `text_display` (`text.display`) and `text_input`
  (`text.input`, then `satellite.send_text(…)`). Without a screen, drop `text_display`.

| Capability                                     | Body method or SDK call                        |
| ---------------------------------------------- | ---------------------------------------------- |
| `IDENTIFY` (`device.identify`)                 | `identify()`                                   |
| `EXPRESSION` (`expression.emotion`)            | `expression(expression, intensity)`            |
| `HEAD_MOTION` (`motion.head`)                  | `beat()`                                       |
| `SPEECH_ACTIVITY` (`audio.speech_activity`)    | `satellite.speech_activity(active)`            |
| `PERSON_DETECTION` (`vision.person_detection`) | `satellite.person_detected(count, confidence)` |

A screen shows the device code with `display=`; a camera reads pairing QR codes with `camera=`
(the SDK's `qr` extra). See the [Python SDK](https://nestorhome.dev/docs/sdks/python/).

## Test

```bash
uv run ruff check && uv run ruff format --check && uv run ty check
uv run pytest
```

`pytest` includes the server's [conformance suite](https://nestorhome.dev/docs/satellites/conformance/),
run through uvx at the version in `.nestor-version`: it launches `my-satellite run --null-audio`
once per scenario and checks pairing, refused codes, identify, acks, text, audio and reconnection.
`pytest -m "not conformance"` skips it. CI runs both on every pull request.

## Release

Pull request titles follow [Conventional Commits](https://www.conventionalcommits.org/)
(`feat: …`, `fix: …`), checked by `pr-title.yml`. From them, release-please keeps a release pull
request open; merging it tags the version and writes the changelog. Set your first version in
`pyproject.toml` and `.release-please-manifest.json`.

`release.yml` runs release-please through nestor-home's shared workflow, which only works in
nestor-home. In your repository:

1. In `release.yml`, replace the `release` job with the commented one under it. Under
   **Settings**, **Actions**, **General**, allow GitHub Actions to create pull requests.
2. On PyPI, add a [trusted publisher](https://docs.pypi.org/trusted-publishers/adding-a-publisher/)
   (a pending one for a new project): your repository, workflow `release.yml`, environment `pypi`.
3. In your repository, create the environment `pypi` (**Settings**, **Environments**), then
   uncomment the `pypi` job. No token is stored: PyPI trusts the workflow.

## Documentation

- [Satellites](https://nestorhome.dev/docs/satellites/): capabilities and pairing.
- [Protocol](https://nestorhome.dev/docs/satellites/protocol/): the standard satellites follow.
- [Python SDK](https://nestorhome.dev/docs/sdks/python/): every option of `Satellite`.
- [Conformance](https://nestorhome.dev/docs/satellites/conformance/).
- A complete driver: [nestor-reachy](https://github.com/nestor-home/nestor-reachy).

## License

MIT

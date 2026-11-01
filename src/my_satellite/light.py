"""The satellite's body: what it does with the core's intents.

This one is a status light, printed. Replace the prints with your hardware: an LED ring, a screen,
motors. Every method of `Body` is optional; see the others (`expression`, `beat`, `heartbeat`) in
the SDK.

Calls come from the network loop and must return at once: keep the state here and drive the
hardware from a task or thread of your own.
"""

from nestor_satellite import Behavior, Body


class Light(Body):
    def behavior(self, behavior: Behavior) -> None:
        # TODO(hardware): show the assistant's attitude (idle, listening, thinking, speaking) until the next.
        print(f"light: {behavior}", flush=True)

    def identify(self) -> None:
        # TODO(hardware): blink for a few seconds, so a person tells this device apart from others.
        # It is called while the device waits to be paired, and on `intent.identify` once paired.
        print("light: blink", flush=True)

    def connected(self, up: bool) -> None:
        # TODO(hardware): a dim light when the link to the core is down, for instance.
        print(f"light: {'connected' if up else 'disconnected'}", flush=True)

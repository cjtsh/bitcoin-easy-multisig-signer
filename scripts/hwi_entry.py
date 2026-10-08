"""Standalone HWI CLI entry point bundled beside the desktop app."""

import ctypes
import sys
from pathlib import Path

def _bundled_usb_names() -> tuple[str, ...]:
    """The names the bundled USB library ships under on this platform."""
    if sys.platform == "win32":
        return ("libusb-1.0.dll",)
    if sys.platform == "darwin":
        return ("libusb-1.0.0.dylib", "libusb-1.0.dylib")
    return ("libusb-1.0.so.0",)


_usb_names = _bundled_usb_names()

if getattr(sys, "frozen", False):
    bundled = [Path(sys._MEIPASS) / name for name in _usb_names]
    if not all(path.is_file() for path in bundled):
        raise RuntimeError("The bundled USB library is missing; the signer helper cannot start.")
    # CT-92: the extraction directory is writable by this user, so a link
    # planted at the bundled name would satisfy a path comparison while
    # loading bytes this build never shipped. A link is not the library, no
    # matter where it points, so only a real file is loaded.
    if any(path.is_symlink() for path in bundled):
        raise RuntimeError(
            "The bundled USB library is not a regular file in this app.")
    # usb1 exposes an explicit loader. Bind its first load to the verified
    # bundle path; preloading a differently named library does not stop usb1
    # from finding a second copy installed on the machine later.
    import usb1
    _libusb_handle = ctypes.CDLL(str(bundled[-1]))
    if not usb1.loadLibrary(_libusb_handle):
        raise RuntimeError("The USB stack loaded a library outside this app.")

def _tolerate_vanished_devices() -> None:
    """Stop one stale device from taking the whole enumeration down with it.

    hwilib's Trezor backend opens every device it finds and closes it again. If the
    device has gone away in between -- which is exactly what a Trezor does when it
    locks on a timeout and re-enumerates its USB connection -- the close raises
    usb1.USBErrorNotFound, nothing catches it, and HWI exits 1 with a traceback and
    NO output. The Ledger, Coldcard and BitBox results are lost along with it, so a
    single locked device makes it look as though no wallet is connected at all.

    Releasing an interface on a device that is no longer present is not something
    anyone can act on, so it is tolerated here, in the tool we build ourselves.
    """
    try:
        import usb1
    except Exception:  # A build without the USB stack has nothing to guard.
        return

    original = usb1.USBDeviceHandle.releaseInterface

    def releaseInterface(self, interface):  # noqa: N802 -- the library's own name
        try:
            return original(self, interface)
        except usb1.USBErrorNotFound:
            return None

    usb1.USBDeviceHandle.releaseInterface = releaseInterface


_tolerate_vanished_devices()


def _report_capabilities() -> int:
    """Print what this build can actually do, and exit.

    A Jade cannot be unlocked unless the bundled jade library has its HTTP relay,
    which exists only when `requests` is importable (jadepy guards it with a try).
    Without it HWI stops with "Use Recovery Phrase Login or QR PIN Unlock", which
    looks like a device fault and is really a missing dependency in this bundle.
    The app checks this at startup and the build fails if it is absent.
    """
    import json

    try:
        from hwilib.devices.jadepy import jade as jade_module
    except Exception:  # pragma: no cover - depends on the bundle
        jade_module = None

    capabilities = {
        "jade_http_relay": bool(jade_module is not None
                                and hasattr(jade_module, "_http_request")),
        "jade_present": jade_module is not None,
    }
    print(json.dumps(capabilities))
    return 0


def _check_libusb() -> int:
    """Load libusb and query USB descriptors without opening any device."""
    import usb1

    with usb1.USBContext() as context:
        list(context.getDeviceList(skip_on_error=True))
    if getattr(sys, "frozen", False):
        loaded = Path(usb1.libusb1.libusb._name).resolve()
        expected_path = Path(sys._MEIPASS) / _usb_names[-1]
        # CT-92: resolve() follows a link, so a linked file at the expected
        # name would compare equal to itself. The link itself is refused.
        if expected_path.is_symlink() or loaded != expected_path.resolve():
            raise RuntimeError("The USB stack loaded a library outside this app.")
        print(f"Bundled libusb: {loaded}")
    return 0


if "--dsh-check-libusb" in sys.argv:
    sys.exit(_check_libusb())


if "--dsh-capabilities" in sys.argv:
    sys.exit(_report_capabilities())

from hwilib._cli import main


if __name__ == "__main__":
    main()

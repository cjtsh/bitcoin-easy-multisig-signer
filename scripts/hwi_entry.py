"""Standalone HWI CLI entry point bundled beside the app."""

import ctypes
import sys
from pathlib import Path

if getattr(sys, "frozen", False):
    # The packaged helper must load the USB library that shipped with it and
    # nothing else. macOS vendors libusb under its version-suffixed name and
    # needs the plain soname present as well, because that is the name usb1 asks
    # the loader for; Windows has a single canonical name for the same 1.0.30
    # source. The last name in each tuple is the one actually loaded.
    if sys.platform == "win32":
        usb_names = ("libusb-1.0.dll",)
    else:
        usb_names = ("libusb-1.0.0.dylib", "libusb-1.0.dylib")
    for usb_name in usb_names:
        if not (Path(sys._MEIPASS) / usb_name).is_file():
            raise RuntimeError(
                "The bundled USB library is missing; the signer helper cannot start."
            )
    # usb1 exposes an explicit loader. Bind its first load to the verified
    # bundle path; preloading a differently named library does not stop usb1 from
    # finding a second copy from the system loader later.
    import usb1
    _libusb_handle = ctypes.CDLL(str(Path(sys._MEIPASS) / usb_names[-1]))
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
        expected = (Path(sys._MEIPASS) / usb_names[-1]).resolve()
        if loaded != expected:
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

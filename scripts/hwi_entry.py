"""Standalone HWI CLI entry point bundled beside the desktop app."""

import ctypes
import os
import stat
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

_NOT_REGULAR = "The bundled USB library is not a regular file in this app."


def _refuse_unless_regular(path: Path) -> os.stat_result:
    """Refuse anything at `path` that is not this build's own regular file.

    CT-92: the directory the bootloader extracts into is writable by this user,
    so a link planted at the bundled name satisfies a path comparison while
    loading bytes this build never shipped. Two kinds of link matter, and
    `is_symlink()` sees only the symbolic one:

    * a symbolic link, which `resolve()` would follow to itself and compare
      equal, and
    * a **hard** link, which is not a symlink at all and has no distinct path
      to resolve -- it is the same inode under a second name.

    So the check opens the file with `O_NOFOLLOW` (no traversal of a final
    symlink) and then asks the descriptor it actually got, not the path: a
    regular file (`S_ISREG`) whose link count is one. A hard link has
    `st_nlink > 1` by definition, so it is refused here before any loader is
    handed the path.

    The `lstat` first is not redundant. `O_NOFOLLOW` is `0` on Windows, so the
    open alone would follow a link there; and opening a FIFO blocks forever, so
    a named pipe planted at the bundled name would hang the preflight instead
    of refusing it. Both are decided from the directory entry, before any open.

    It returns the descriptor's `stat_result` so a caller can re-check the same
    identity after a load (see `_identity_holds`).
    """
    try:
        link_info = os.lstat(path)
    except OSError as error:
        raise RuntimeError(_NOT_REGULAR) from error
    if stat.S_ISLNK(link_info.st_mode) or not stat.S_ISREG(link_info.st_mode):
        raise RuntimeError(_NOT_REGULAR)
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as error:
        raise RuntimeError(_NOT_REGULAR) from error
    try:
        info = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
        raise RuntimeError(_NOT_REGULAR)
    return info


def _identity_holds(info: os.stat_result, path: Path) -> bool:
    """True while the file at `path` is still the one the descriptor showed.

    CT-92's check-then-load window (cycle-5 adversarial pass): the path is
    verified and the descriptor closed, then `ctypes.CDLL` re-opens the path. A
    swap in between loads bytes that were never verified. The window cannot be
    closed entirely from Python -- `dlopen` re-resolves the name -- so the
    identity (device, inode, size, mtime) is compared again after the load and
    the library is never *used* unless it still matches.
    """
    try:
        now = os.lstat(path)
    except OSError:
        return False
    return (
        stat.S_ISREG(now.st_mode)
        and now.st_nlink == 1
        and (now.st_dev, now.st_ino, now.st_size, now.st_mtime_ns)
        == (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns)
    )


if getattr(sys, "frozen", False):
    bundled = [Path(sys._MEIPASS) / name for name in _usb_names]
    if not all(path.is_file() for path in bundled):
        raise RuntimeError("The bundled USB library is missing; the signer helper cannot start.")
    checked = {path: _refuse_unless_regular(path) for path in bundled}
    # usb1 exposes an explicit loader. Bind its first load to the verified
    # bundle path; preloading a differently named library does not stop usb1
    # from finding a second copy installed on the machine later.
    import usb1
    _libusb_handle = ctypes.CDLL(str(bundled[-1]))
    # The path was verified before the load; verify the same file is still
    # there before the handle is handed to usb1. A swap here means the loaded
    # bytes are not the bytes that were checked, so the handle is discarded.
    if not all(_identity_holds(info, path) for path, info in checked.items()):
        raise RuntimeError(_NOT_REGULAR)
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
        # name would compare equal to itself. The check is made on the file
        # itself: it must be a regular file with a single link, which refuses
        # a symbolic link and a hard link alike.
        try:
            _refuse_unless_regular(expected_path)
        except RuntimeError as error:
            raise RuntimeError(
                "The USB stack loaded a library outside this app.") from error
        if loaded != expected_path.resolve():
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

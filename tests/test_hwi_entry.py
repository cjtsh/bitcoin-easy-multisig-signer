"""The bundled HWI tool must survive a device that vanishes mid-enumeration.

hwilib's Trezor backend opens each device it finds and closes it again. A Trezor
that locks on a timeout re-enumerates its USB connection, so that close raises
usb1.USBErrorNotFound. Nothing in hwilib catches it: HWI exits 1 with a traceback
and no output at all, and every other connected device disappears from the result.
That is what a locked Trezor did to the owner's first hardware check.
"""

import importlib.util
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]


def load_hwi_entry(usb1_module):
    """Load scripts/hwi_entry.py against stubs, without the real device stack."""
    watched = ("usb1", "hwilib", "hwilib._cli")
    saved = {name: sys.modules.get(name) for name in watched}
    hwilib = types.ModuleType("hwilib")
    cli = types.ModuleType("hwilib._cli")
    cli.main = lambda: None
    hwilib._cli = cli
    sys.modules["usb1"] = usb1_module
    sys.modules["hwilib"] = hwilib
    sys.modules["hwilib._cli"] = cli
    try:
        spec = importlib.util.spec_from_file_location(
            "hwi_entry_under_test", ROOT / "scripts" / "hwi_entry.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        for name, original in saved.items():
            if original is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = original


class HwiEntryTests(unittest.TestCase):
    def test_libusb_preflight_lists_descriptors_without_opening_wallets(self):
        class Handle:
            def releaseInterface(self, interface):  # noqa: N802
                return None

        class Context:
            entered = False
            options = []

            def __enter__(self):
                Context.entered = True
                return self

            def __exit__(self, *_args):
                return False

            def getDeviceList(self, *, skip_on_error):  # noqa: N802
                Context.options.append(skip_on_error)
                return []

        usb1 = types.ModuleType("usb1")
        usb1.USBErrorNotFound = type("USBErrorNotFound", (Exception,), {})
        usb1.USBDeviceHandle = Handle
        usb1.USBContext = Context
        module = load_hwi_entry(usb1)
        # load_hwi_entry restores sys.modules; put the stub back while exercising
        # the deferred import inside _check_libusb.
        old_usb1 = sys.modules.get("usb1")
        sys.modules["usb1"] = usb1
        try:
            self.assertEqual(module._check_libusb(), 0)
        finally:
            if old_usb1 is None:
                sys.modules.pop("usb1", None)
            else:
                sys.modules["usb1"] = old_usb1
        self.assertTrue(Context.entered)
        self.assertEqual(Context.options, [True])

    def test_a_vanished_device_does_not_kill_enumeration(self):
        class USBErrorNotFound(Exception):
            pass

        class Handle:
            released = 0

            def releaseInterface(self, interface):  # noqa: N802 -- library's name
                Handle.released += 1
                raise USBErrorNotFound("LIBUSB_ERROR_NOT_FOUND")

        usb1 = types.ModuleType("usb1")
        usb1.USBErrorNotFound = USBErrorNotFound
        usb1.USBDeviceHandle = Handle
        load_hwi_entry(usb1)

        # Without the guard this raised, taking the whole device check with it.
        self.assertIsNone(Handle().releaseInterface(0))
        self.assertEqual(Handle.released, 1)

    def test_a_real_usb_error_is_still_raised(self):
        """Only the not-found case is forgiven; a genuine fault must still surface."""
        class USBErrorNotFound(Exception):
            pass

        class USBError(Exception):
            pass

        class Handle:
            def releaseInterface(self, interface):  # noqa: N802
                raise USBError("LIBUSB_ERROR_IO")

        usb1 = types.ModuleType("usb1")
        usb1.USBErrorNotFound = USBErrorNotFound
        usb1.USBDeviceHandle = Handle
        load_hwi_entry(usb1)

        with self.assertRaises(USBError):
            Handle().releaseInterface(0)

    def test_a_build_without_the_usb_stack_still_starts(self):
        # sys.modules[name] = None makes "import usb1" raise ImportError.
        module = load_hwi_entry(None)
        self.assertTrue(hasattr(module, "_tolerate_vanished_devices"))

    def test_frozen_helper_refuses_a_missing_bundled_library(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(
            sys, "frozen", True, create=True
        ), patch.object(sys, "_MEIPASS", folder, create=True):
            with self.assertRaisesRegex(RuntimeError, "bundled USB library is missing"):
                load_hwi_entry(None)

    def test_frozen_helper_binds_usb1_to_the_bundled_alias(self):
        class Handle:
            def releaseInterface(self, interface):  # noqa: N802
                return None

        usb1 = types.ModuleType("usb1")
        usb1.USBErrorNotFound = type("USBErrorNotFound", (Exception,), {})
        usb1.USBDeviceHandle = Handle
        usb1.loadLibrary = Mock(return_value=True)
        bundled = {"win32": ("libusb-1.0.dll",),
                   "darwin": ("libusb-1.0.0.dylib", "libusb-1.0.dylib"),
                   }.get(sys.platform, ("libusb-1.0.so.0",))

        with tempfile.TemporaryDirectory() as folder:
            for name in bundled:
                (Path(folder) / name).write_bytes(b"synthetic library")
            with patch.object(sys, "frozen", True, create=True), patch.object(
                sys, "_MEIPASS", folder, create=True
            ), patch("ctypes.CDLL", return_value="bundled-handle") as loader:
                load_hwi_entry(usb1)
            loader.assert_called_once_with(str(Path(folder) / bundled[-1]))
            usb1.loadLibrary.assert_called_once_with("bundled-handle")

    def test_frozen_helper_on_windows_binds_the_dll(self):
        """Drive the Windows branch here, or it first runs on a user's PC."""
        class Handle:
            def releaseInterface(self, interface):  # noqa: N802
                return None

        usb1 = types.ModuleType("usb1")
        usb1.USBErrorNotFound = type("USBErrorNotFound", (Exception,), {})
        usb1.USBDeviceHandle = Handle
        usb1.loadLibrary = Mock(return_value=True)
        with tempfile.TemporaryDirectory() as folder:
            (Path(folder) / "libusb-1.0.dll").write_bytes(b"synthetic library")
            with patch.object(sys, "frozen", True, create=True), patch.object(
                sys, "_MEIPASS", folder, create=True
            ), patch.object(sys, "platform", "win32"), patch(
                "ctypes.CDLL", return_value="bundled-handle"
            ) as loader:
                load_hwi_entry(usb1)
            loader.assert_called_once_with(str(Path(folder) / "libusb-1.0.dll"))
            usb1.loadLibrary.assert_called_once_with("bundled-handle")

    def test_the_windows_helper_does_not_accept_the_macos_library(self):
        """A Windows build that shipped the dylib would fail in front of a user."""
        with tempfile.TemporaryDirectory() as folder:
            for name in ("libusb-1.0.0.dylib", "libusb-1.0.dylib"):
                (Path(folder) / name).write_bytes(b"synthetic library")
            with patch.object(sys, "frozen", True, create=True), patch.object(
                sys, "_MEIPASS", folder, create=True
            ), patch.object(sys, "platform", "win32"):
                with self.assertRaisesRegex(RuntimeError, "bundled USB library is missing"):
                    load_hwi_entry(None)

    # -- CT-92: the extraction directory is writable by this user ----------

    def test_frozen_helper_refuses_a_linked_bundled_library(self):
        """CT-92: a path comparison must not be satisfiable through a link.

        PyInstaller unpacks the helper into a directory this user can write to,
        and Path.resolve() follows links, so a link planted at the bundled name
        would make every path equality hold while loading other bytes. The link
        itself has to be refused, before anything is loaded.
        """
        usb1 = types.ModuleType("usb1")
        usb1.USBErrorNotFound = type("USBErrorNotFound", (Exception,), {})
        usb1.USBDeviceHandle = type("Handle", (), {
            "releaseInterface": lambda self, interface: None})
        usb1.loadLibrary = Mock(return_value=True)
        with tempfile.TemporaryDirectory() as folder:
            for name in ("libusb-1.0.0.dylib", "libusb-1.0.dylib",
                         "libusb-1.0.dll", "libusb-1.0.so.0"):
                (Path(folder) / name).write_bytes(b"synthetic library")
            with patch.object(sys, "frozen", True, create=True), patch.object(
                sys, "_MEIPASS", folder, create=True
            ), patch.object(Path, "is_symlink", return_value=True), patch(
                "ctypes.CDLL"
            ) as loader:
                with self.assertRaisesRegex(
                        RuntimeError, "not a regular file in this app"):
                    load_hwi_entry(usb1)
            loader.assert_not_called()
            usb1.loadLibrary.assert_not_called()

    def test_the_libusb_preflight_refuses_a_linked_library(self):
        """The same rule holds on the path the app's capability probe uses.

        The loaded path here resolves to exactly the expected file, so only the
        link test can refuse it — the failure mode this pins.
        """
        class Context:
            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def getDeviceList(self, *, skip_on_error):  # noqa: N802
                return []

        class Libusb:
            _name = "/nowhere/libusb"

        class Libusb1:
            libusb = Libusb()

        usb1 = types.ModuleType("usb1")
        usb1.USBErrorNotFound = type("USBErrorNotFound", (Exception,), {})
        usb1.USBDeviceHandle = type("Handle", (), {
            "releaseInterface": lambda self, interface: None})
        usb1.USBContext = Context
        usb1.libusb1 = Libusb1()
        module = load_hwi_entry(usb1)
        with tempfile.TemporaryDirectory() as folder:
            for name in ("libusb-1.0.0.dylib", "libusb-1.0.dylib",
                         "libusb-1.0.dll", "libusb-1.0.so.0"):
                (Path(folder) / name).write_bytes(b"synthetic library")
            usb1.libusb1.libusb._name = str(Path(folder) / module._usb_names[-1])
            old_usb1 = sys.modules.get("usb1")
            sys.modules["usb1"] = usb1
            try:
                with patch.object(sys, "frozen", True, create=True), patch.object(
                    sys, "_MEIPASS", folder, create=True
                ), patch.object(Path, "is_symlink", return_value=True):
                    with self.assertRaisesRegex(
                            RuntimeError, "loaded a library outside this app"):
                        module._check_libusb()
            finally:
                if old_usb1 is None:
                    sys.modules.pop("usb1", None)
                else:
                    sys.modules["usb1"] = old_usb1


if __name__ == "__main__":
    unittest.main()

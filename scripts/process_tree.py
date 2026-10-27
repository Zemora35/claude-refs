"""Own and stop only a subprocess tree, including Windows virtualenv launchers."""

import os
import signal
import subprocess

if os.name == "nt":
    import ctypes
    from ctypes import wintypes

    class ThreadEntry(ctypes.Structure):
        _fields_ = [("size", wintypes.DWORD), ("usage", wintypes.DWORD), ("thread_id", wintypes.DWORD),
                    ("process_id", wintypes.DWORD), ("priority", wintypes.LONG), ("delta", wintypes.LONG),
                    ("flags", wintypes.DWORD)]

    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    for name, arguments, result in (
        ("CreateJobObjectW", [ctypes.c_void_p, wintypes.LPCWSTR], wintypes.HANDLE),
        ("AssignProcessToJobObject", [wintypes.HANDLE, wintypes.HANDLE], wintypes.BOOL),
        ("TerminateJobObject", [wintypes.HANDLE, wintypes.UINT], wintypes.BOOL),
        ("CloseHandle", [wintypes.HANDLE], wintypes.BOOL),
        ("OpenProcess", [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD], wintypes.HANDLE),
        ("CreateToolhelp32Snapshot", [wintypes.DWORD, wintypes.DWORD], wintypes.HANDLE),
        ("Thread32First", [wintypes.HANDLE, ctypes.POINTER(ThreadEntry)], wintypes.BOOL),
        ("Thread32Next", [wintypes.HANDLE, ctypes.POINTER(ThreadEntry)], wintypes.BOOL),
        ("OpenThread", [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD], wintypes.HANDLE),
        ("ResumeThread", [wintypes.HANDLE], wintypes.DWORD),
    ):
        function = getattr(kernel, name)
        function.argtypes, function.restype = arguments, result


class ProcessTree:
    def __init__(self, arguments, **kwargs):
        self.job = None
        if os.name != "nt":
            self.process = subprocess.Popen(arguments, start_new_session=True, **kwargs)
            return
        self.job = kernel.CreateJobObjectW(None, None)
        if not self.job:
            raise ctypes.WinError(ctypes.get_last_error())
        try:
            # Assign before resuming: even a fast launcher cannot escape the owned job.
            self.process = subprocess.Popen(arguments, creationflags=0x00000004, **kwargs)
            handle = kernel.OpenProcess(0x0100 | 0x0001, False, self.process.pid)
            if not handle:
                raise ctypes.WinError(ctypes.get_last_error())
            try:
                if not kernel.AssignProcessToJobObject(self.job, handle):
                    raise ctypes.WinError(ctypes.get_last_error())
            finally:
                kernel.CloseHandle(handle)
            snapshot = kernel.CreateToolhelp32Snapshot(0x00000004, 0)
            if snapshot == ctypes.c_void_p(-1).value:
                raise ctypes.WinError(ctypes.get_last_error())
            resumed = False
            try:
                entry = ThreadEntry()
                entry.size = ctypes.sizeof(entry)
                found = kernel.Thread32First(snapshot, ctypes.byref(entry))
                while found:
                    if entry.process_id == self.process.pid:
                        thread = kernel.OpenThread(0x0002, False, entry.thread_id)
                        if not thread:
                            raise ctypes.WinError(ctypes.get_last_error())
                        try:
                            if kernel.ResumeThread(thread) == 0xFFFFFFFF:
                                raise ctypes.WinError(ctypes.get_last_error())
                            resumed = True
                        finally:
                            kernel.CloseHandle(thread)
                    found = kernel.Thread32Next(snapshot, ctypes.byref(entry))
            finally:
                kernel.CloseHandle(snapshot)
            if not resumed:
                raise OSError("Cannot resume owned subprocess; no task was executed")
        except BaseException:
            if hasattr(self, "process"):
                self.process.kill()
                self.process.wait(timeout=10)
            self.close()
            raise

    def stop(self):
        if os.name == "nt":
            if not kernel.TerminateJobObject(self.job, 1):
                raise ctypes.WinError(ctypes.get_last_error())
        else:
            try:
                os.killpg(self.process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass

    def close(self):
        if self.job is not None:
            # Also stop descendants that remained after the root process exited.
            kernel.TerminateJobObject(self.job, 1)
            kernel.CloseHandle(self.job)
            self.job = None

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

**1. How to see the devices tinygrad sees**

```bash
python3 -m tinygrad.device          # tinygrad/device.py:418-444, runs a real Tensor per renderer
python3 -c "from tinygrad import Device; print(Device.DEFAULT)"
python3 -c "from tinygrad.device import Device; print(list(Device.get_available_devices()))"
```

On your Mac mini right now:
```
DEFAULT:      METAL
available:    ['METAL', 'AMD', 'CL', 'CPU']
```

Selection logic is `device.py:14` (`ALL_DEVICES` preference order: METAL, AMD, NV, CUDA, ...) and `device.py:47-55` (`_select_device` — first one that constructs wins). Your 7900 XTX is detected as `1002:744c` and opens fine:

```
iface: PCIIface   pci_dev: APLRemotePCIDevice   arch: gfx1100   renderer: HIPRenderer
```

**2. What the PCIe part is in your setup**

Your `system_profiler` output shows the 7900 XTX at `Slot: Thunderbolt@5,0,0` with `Link Status: Link down` — the Mac has no PCIe BAR access to it. tinygrad works around this in three layers:

- `ops_amd.py:1014` — `AMD.ifaces = [KFDIface, PCIIface, USBIface, ...]`. Your path is `PCIIface`.
- `system.py:58-80` `pci_scan_bus` — on OSX it walks IOKit `IOPCIDevice` services to find `1002:744c` (matches the device-id whitelist at `ops_amd.py:919`).
- `system.py:416-447` `APLRemotePCIDevice` — this is the macOS-specific bit. It launches `/Applications/TinyGPU.app` (your "tinygpu") as a helper and talks to it over a Unix socket at `$TMPDIR/tinygpu.sock` with a 13-command RPC (`RemoteCmd` at `system.py:311-312`): `PROBE`, `MAP_BAR`, `CFG_READ/WRITE`, `MMIO_READ/WRITE`, `SYSMEM_READ/WRITE`, `MAP_SYSMEM_FD`. That helper is what actually does the USB4/TB5 tunneling. Confirmed running: PID 29708.

So the real chain is: `tinygrad` → Unix socket RPC → `TinyGPU.app` → USB4/PCIe tunnel → ASMedia 246x → 7900 XTX.

**3. The disk → 7900 XTX path**

`engine/realize.py:149-158` `exec_copy` has a four-way dispatch, and the zero-copy branch is gated:

```python
elif src.device.startswith("DISK") and getattr(src.allocator.dev, 'fd', None) is not None \
     and hasattr(dest.allocator, 'copy_from_disk') and src.nbytes >= 4096 and dest.allocator.supports_copy_from_disk:
  dest.allocator.copy_from_disk(dest._buf, src._buf, src.nbytes)
```

For AMD, `supports_copy_from_disk = dev.has_sdma_queue` (`ops_amd.py:645`), which is `True` on your card. So it takes the fast path: `hcq.py:573-589` `copy_from_disk` drives `DiskAllocator._copyout_sharded` (`ops_disk.py:98-139`) with SDMA doing the DMA, so bytes go file → page cache → SDMA → VRAM without a full CPU memcpy. Note `use_ioring` at `hcq.py:585` is False here since iouring is Linux-only (`ops_disk.py:51`), so it takes the plain `readinto` loop at `ops_disk.py:104-113`. METAL by contrast has no `copy_from_disk` and falls to the host memcpy at `realize.py:157`.

### Analyze

Single file, `python extra/gpuprobe.py [section]`, sections run in order, no args = all. Imports only `tinygrad`, `ctypes`, `struct`, `socket`, `os`. **Every section must be read-only**: no `_collect_interrupts(reset=True)`, no `AM_RESET`, no doorbell writes, no `synchronize()` calls that could block 30s. Where a check would mutate state, print the call you *could* make and move on.

**Section `devices`** — reproduces what `python -m tinygrad.device` does but without crashing:
- `Device._devices` (the `ops_*.py` filesystem glob, `device.py:17`) vs `ALL_DEVICES` (`device.py:14`), showing the 6 that are never auto-selected (`DISK`, `HIP`, `NPY`, `NULL`, `PYTHON`, `RDMA`).
- Replay `_select_device` (`device.py:47-55`) by hand: for each name in `ALL_DEVICES`, try `Device[name]`, catch, record. Print which one wins and why. Never touch `os.environ["DEV"]` — `device.py:53` writes it as a side effect, which would poison child processes.
- The `DEV` grammar: `Target.parse` (`helpers.py:200-207`) applied to the current `DEV` value, showing `device:renderer:arch` + `iface` prefix + indices.
- `_select_renderer` (`device.py:364-369`) and `_select_iface` (`device.py:371-379`) resolved explicitly, listing the rejected candidates with their exception messages.

**Section `pci`** — get `1002:744c` with zero macOS commands:
- Call `System.pci_scan_bus(0x1002, ((0xffff, (0x744c,)),))` directly → `['1002:744c']`. On macOS this is IOKit only (`system.py:60-71`, `IOServiceGetMatchingServices`/`IOServiceMatching(b"IOPCIDevice")`), no `system_profiler` involved.
- Show the full filter table from `ops_amd.py:919` (`0x74a1,0x74b5,0x744c,0x7480,0x7550,0x7551,0x7590,0x75a0,0x75a8`) and which of your IDs match.
- Then walk `system.py:82-90`: `list_devices` → `pci_probe_device` → `hcq_filter_visible_devices` → the class actually chosen. Print `(APLRemotePCIDevice, '1002:744c')` — i.e. the answer to "how do I get this from tinygrad".
- Note the `pcibus` string is discarded at `system.py:439` (`super().__init__(devpref, "usb4", sock=sock)`), so `dev_id` is always 0 on macOS.

**Section `rpc`** — the Unix socket protocol, decoded from Python:
- Print the wire format: 33-byte request `<BIIQQQ` (`cmd, dev_id, bar, arg0, arg1, arg2`), 17-byte reply `<BQQ` (`status, resp0, resp1`), matching the packed structs at `extra/usbgpu/tbgpu/installer/Shared/server.c:35-36`. Include the arg table per command.
- Which of the 13 `RemoteCmd`s TinyGPU actually implements: `{MAP_BAR, MAP_SYSMEM_FD, CFG_READ, CFG_WRITE, RESET, MMIO_READ, MMIO_WRITE, RESIZE_BAR}`. `PROBE`, `PING`, `MAP_SYSMEM`, `SYSMEM_*` return `status=1` in `server.c` — important, because it means you cannot enumerate over this socket, only over `pci_scan_bus`.
- Socket path: `getenv("APL_REMOTE_SOCK", temp("tinygpu.sock"))` (`system.py:431`) → `/var/folders/66/.../T/tinygpu.sock`.
- Liveness probe that does not disturb tinygrad: `bind()` returning `EADDRINUSE` means a server is listening. Then warn that `server.c:274` accepts one client at a time and closes extras silently, so do not open a second connection while tinygrad holds it.
- The `_bulk_read`/`_bulk_write` asymmetry (`system.py:394-399`): reads send a header + receive header-then-body, writes send header + payload and get **no reply**.

**Section `helper`** — finding PID 29708 without `ps`:
- There is no pid file and `system.py:436` discards the `Popen` object. `psutil` is not a dependency; `/proc` doesn't exist; `sysctl kern.proc` is unavailable on modern macOS (verified: returns ENOENT).
- So: `ctypes.CDLL("/usr/lib/libproc.dylib")` — note it loads from the dyld shared cache even though `os.stat` says ENOENT, so do **not** gate on `ctypes.util.find_library`. Then `proc_listallpids` + `proc_pidpath`, matching `"/Applications/TinyGPU.app/Contents/MacOS/TinyGPU"`.
- Two fallbacks that are more robust: the IOKit service check (`IOServiceGetMatchingService(kIOMainPortDefault, IOServiceNameMatching("tinygpu")) != 0` proves the dext is loaded — all bindings exist in `tinygrad/runtime/autogen/iokit.py`), and the flock at `temp("pc_usb4.lock")` which tells you tinygrad holds the client side.
- Also print the `ensure_app` pin (`system.py:421`, commit `c0d024f9…`) and whether the cached zip exists, so you know your app matches the client.

**Section `iface`** — the `PCIIface / APLRemotePCIDevice / gfx1100 / HIPRenderer` line you asked for, expanded:
- `iface` = `PCIIface` from `ifaces[1]` (`ops_amd.py:1014`) after `KFD` (Linux-only, `/dev/kfd`) fails. `is_am()` → `True` (`ops_amd.py:1016`), which is what sets `can_recover=True`.
- `pci_dev` = `APLRemotePCIDevice`, `is_local()` → `False` (`system.py:256`), which skips `reserve_va` at `system.py:262` and P2P mapping at `system.py:293`.
- `arch` = `gfx1100`, derived from `props['gfx_target_version']` (`ops_amd.py:1022-1023`) read out of the GPU over MMIO — not hardcoded.
- Dump `iface.props` (`ops_amd.py:941-944`): `simd_count`, `cu_per_simd_array`, `lds_size_in_kb`, `max_waves_per_simd`, etc., plus the derived `cu_cnt`/`se_cnt`/`wave_cnt` from `ops_amd.py:1027-1031`.
- BAR layout: `vram_bar=0`, `bar_info(0)` over the RPC, `large_bar` state.
- Renderers: instantiate each of `HIPRenderer`, `AMDLLVMRenderer`, `HIPCCRenderer` (`ops_amd.py:1064`) in isolation and report pass/fail with the real exception, instead of letting one crash kill the process.

**Section `copies`** — proves the DISK→SDMA claim instead of asserting it:
- Read the exact gate at `realize.py:154-155` term by term and print each value: `src.device.startswith("DISK")`, `src.allocator.dev.fd is not None`, `hasattr(dest.allocator,'copy_from_disk')`, `src.nbytes >= 4096`, `dest.allocator.supports_copy_from_disk`. This is the honest way to answer "is the fast path actually taken" — including showing it is **not** taken for files under 4 KiB.
- Then monkeypatch nothing and just report: `has_sdma_queue` (`ops_amd.py:1062`), `hw_copy_queue_t` (`hcq.py:396`), `supports_copy_from_disk`/`supports_transfer` (`ops_amd.py:645`), `AMD_DISABLE_SDMA` (`ops_amd.py:1126`), `max_copy_size` (`ops_amd.py:1060`).
- Bounce ring: `len(allocator.b)`, `allocator.b[0].size`, `b_next`, and the `1 << 64` in-flight sentinel count — from `hcq.py:527-530` and the `_get_temp_buf` handshake at `hcq.py:574-579`.
- `use_ioring`: evaluate `type(allocator.b[0].cpu_view()) is MMIOInterface` at `hcq.py:585` and print the class name. Expect `False` here (macOS: `io_uring` never initializes at `ops_disk.py:51`), so you land in the `readinto` loop at `ops_disk.py:104-113`.
- Drive `_copyout_sharded` with a fake `_get_free_buf` and a stub allocator to show the 4-tuple `(batch_info, dst_off, src_off, copy_size)` sequence for a chosen size, including the leading `minor_offset` non-zero case. This runs entirely in Python, no GPU, no device state touched — safe even when the card is wedged.
- Flag the two unbounded spins that explain your hangs: `ops_disk.py:106` `while (copy_batch := _get_free_buf()) is None: pass` and `ops_amd.py:546` `while ... sdma_queue.put_value + total_bytes - sdma_queue.read_ptr[0] > sdma_queue.ring.nbytes: pass`.

**Section `hang`** — read-only hang diagnosis:
- Print `dev.error_state` (`hcq.py:415`), `dev.iface.dev_impl.is_err_state` (`amdev.py:222`), and explain that `error_state` is set at exactly two sites (`hcq.py:429` on wait timeout, `ops_amd.py:761` on doorbell fault) and cleared at exactly one (`ops_amd.py:970`).
- Print the three scratch-register state flags that decide boot behavior at `amdev.py:185-191`: `regSCRATCH_REG7` (AM version), `regSCRATCH_REG6` (did the last session finalize cleanly), `gmc.pf_status_reg('GC')`. Explain that `regSCRATCH_REG6 != 0` means the last process died hard, forcing a full re-boot.
- Explain the detection asymmetry that explains your manual reboots: `can_recover=self.is_am()` (`ops_amd.py:1068`) is only consulted for a caller-supplied `timeout` at `hcq.py:427`; the real detector is the 30 s `HCQDEV_WAIT_TIMEOUT_MS` default at `hcq.py:282`. And `AMDev.recover` (`amdev.py:277-284`) resets **GFX only** — never `AM_SDMA`. So a hung SDMA packet survives recovery, `is_err_state` reads clean, `recover()` returns True, `error_state` gets cleared at `ops_amd.py:970`, and the next `synchronize()` hangs again. That is the mechanism behind "must reboot by hand", and it is why this script does not attempt recovery.
- Note `ip.py:491`: `SDMA_TRAP` interrupt sources are `continue`d, so a trapping SDMA packet produces no log output at all.
- Exit with a clear "REBOOT REQUIRED" verdict instead of trying to fix it.

### Verification

Run the script section by section against the live card. Since the HIP renderer currently SIGBUSes in `comgr` on this machine, the `iface` and `copies` sections must not compile any kernel — they only read device properties, so they work even while compute is broken. Confirm `pci` prints `1002:744c` and `iface` prints `gfx1100` + `PCIIface` + `APLRemotePCIDevice`, matching what we established earlier. Then run the existing suites: `python -m pytest test/device/test_hcq.py -x -q -n12`, `python -m mypy tinygrad/`, `python -m ruff check .`.


## Assistant

## Objective
- Fix explicit renderer suffixes such as `Device["AMD:HIP"]` failing during interface selection, and add a focused regression test.
- Do not create `extra/gpuprobe.py`; user will run the resulting tests.

## Important Details
- Current failure: `ValueError: invalid literal for int() with base 10: 'HIP'`.
- Bug: `/Users/plagache/workspace/tinyagent/tinygrad/device.py:372` parses every second `:` component as an integer.
- `Compiled.__init__` at `tinygrad/device.py:348` already uses the required `.isdigit()` guard.
- Regression introduced by commit `e7bf2a811`.
- Test belongs in `test/null/test_device.py`; it should exercise parsing without compiling a HIP kernel or relying unnecessarily on live hardware.
- Test numeric suffixes remain integers and renderer suffixes default `device_id` to `0`.
- User requires observe-only behavior: never attempt reset/recovery or reboot without asking; their macOS/TinyGPU AMD setup can hang.
- Confirmed hardware path: `PCIIface` → `APLRemotePCIDevice` → `$TMPDIR/tinygpu.sock` → TinyGPU.app; AMD ID `1002:744c`, arch `gfx1100`, renderer `HIPRenderer`.

## Work State
### Completed
- Confirmed `Device["AMD:HIP"]`, `Device["AMD:LLVM"]`, and `Device["AMD:HIP"]` explicit-index construction fail at `device.py:372`.
- Located existing guarded parsing at `device.py:348`.
- Located appropriate test home and existing conventions in `test/null/test_device.py`.
- No files have been changed yet.

### Active
- Apply the minimal `.isdigit()`-style guard in `Compiled._select_iface`.
- Add a hardware-free regression test around `_select_iface` device-ID parsing if practical.

### Blocked
- HIP kernel compilation currently crashes on this Mac with `Fatal Python error: Bus error` at `tinygrad/runtime/support/compiler_amd.py:65`; tests must avoid invoking kernel compilation.
- Live AMD tests may also require TinyGPU.app and exclusive `/tmp/am_usb4.lock`.

## Next Move
1. Patch `Compiled._select_iface` in `tinygrad/device.py` to parse a suffix as a device ID only when numeric, otherwise use `0`.
2. Add focused tests in `test/null/test_device.py`, then show the user the exact test command without running the full suite.

## Relevant Files
- `/Users/plagache/workspace/tinyagent/tinygrad/device.py`: `_select_iface` bug at line 372 and guarded parsing at line 348.
- `/Users/plagache/workspace/tinyagent/test/null/test_device.py`: canonicalization and device-target tests; proposed regression-test location.
- `/Users/plagache/workspace/tinyagent/tinygrad/runtime/ops_amd.py`: AMD calls `_select_iface` at line 1020 and defines renderer/device setup.
- `/Users/plagache/workspace/tinyagent/tinygrad/runtime/support/system.py`: `System.pci_scan_bus`, `APLRemotePCIDevice`, and Unix-socket RPC.
- `/Users/plagache/workspace/tinyagent/tinygrad/runtime/support/compiler_amd.py`: current HIP/comgr SIGBUS blocker.

## The fix

`tinygrad/device.py:372` — `_select_iface` parsed *any* second `:` component as an integer, so a renderer suffix blew up:

```
Device["AMD:HIP"]  -> ValueError: invalid literal for int() with base 10: 'HIP'
```

Now it mirrors the guard already used for `self.device_id` in `Compiled.__init__` (`device.py:348`), falling back to `0` when the token isn't numeric:

```python
self.device_id = (int(idx) if ":" in device and (idx:=device.split(":")[1]).isdigit() else 0)
```

## Scope was broader than AMD

`_select_iface` is shared with NVIDIA (`ops_nv.py:591`), and NV had the identical bug — I confirmed `Device["NV:CUDA"]` raised the same `ValueError` pre-fix. So the fix covers both, and I added a matching NV test rather than leaving half the affected classes of device broken.

## Tests — `test/null/test_device.py`

Two tests, one per backend, following the existing `test_dev_id_out_of_range` subprocess convention. They use `DEV=MOCKKFD+AMD` / `DEV=MOCK+NV`, so they need **no real GPU** — `MOCKKFD+AMD` is already used in CI at `.github/workflows/test.yml:519`. This also sidesteps the comgr SIGBUS issue, since no kernel is compiled.

Each asserts both directions: non-numeric suffixes resolve to `device_id=0`, and numeric indices still work (`AMD:1:HIP` → `1`, `NV:1:CUDA` → `1`), guarding against an over-broad fix that broke indexing.

## Verification

I confirmed each test genuinely catches the regression by stashing the fix and re-running:

| | pre-fix | post-fix |
|---|---|---|
| AMD test | FAILED (3 subtests), `ValueError: 'HIPCC'` | ok |
| NV test | FAILED (2 subtests), `ValueError: 'CUDA'` | ok |

Also green: full `test/null/test_device.py` under `DEV=AMD` (22 passed, 6 skipped), under `DEV=NULL` (22 passed, 9 skipped), `ruff check .`, and `mypy tinygrad/` (217 files).

Two notes, no action taken:
- **pytest isn't installed** in any interpreter here, so I ran via `python3 -m unittest`. On your side: `DEV=AMD python3 -m pytest test/null/test_device.py -k iface_with_renderer_suffix`.
- **Unrelated pre-existing staged file**: `test/runtime/test_remote.py` was already staged in the index when I started (`git status` shows `A`) and isn't mine. I left it untouched. HEAD is also detached at `1691120a6` — worth knowing before you commit.

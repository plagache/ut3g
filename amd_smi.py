"""
What makes an amd_smi clone possible on your setup

amd_smi reads sensors through the amdgpu kernel driver (which you can't load). But tinygrad's own AMDev talks to the same source directly — the SMU (system management unit) mailbox over MMIO registers,
and those MMIO reads/writes tunnel through your app socket exactly like every other register access gpuprobe already does. The machinery is all in the tree:

- AM_SMU.read_table(SmuMetrics_t, …) (ip.py:225) — asks the SMU to transfer its metrics table into VRAM (PPSMC_MSG_TransferTableSmu2Dram), then reads it over the BAR. The autogen struct exists for your
SMU generation (tinygrad/runtime/autogen/am/smu_13_0_*.py) and the IP-version dispatch picks the right one automatically — it contains exactly what amd_smi prints:
- AvgTemperature[12] (GFX/SOC/VRM temps), AverageSocketPower / dGPU_W_MAX
- AverageGfxActivity (GPU busy %), AverageUclkActivity, AverageGfxclkFrequency*, AverageMemclkFrequency*
- AvgFanRpm / AvgFanPwm, PcieRate / PcieWidth, throttling counters
- read_clocks (ip.py:229) — DPM clock levels (read-only GetDpmFreqByIndex messages).
- SMU health checks (is_smu_alive) come free.

Only read-only SMU messages get sent (TransferTableSmu2Dram, GetDpmFreqByIndex) — no Set*, no reset. Device open boots AMDev exactly like gpuprobe does.

extra/gpumon.py

$ python3 extra/gpumon.py              # one-shot, amd_smi-metric style
$ python3 extra/gpumon.py watch 1      # redraw every 1s (like watch amd_smi)

Output (one line per pass, amd_smi-like columns):

GPU  TEMP   POWER   GFXCLK   MEMCLK   BUSY%  VRAM(total/used)  FAN     SDMA   ERR
0    45C    78W     2300MHz  1200MHz  12%    24G/n-a           870rpm  0KB/s  clean

Plus a footer with queue activity (compute + SDMA read_ptr deltas → bytes/s), GC fault status, and SCRATCH_REG6/7 session state.

The one honest gap: card-side "VRAM used" — amd_smi gets that from the driver's allocator, which doesn't exist over the socket. So the used column is n/a in standalone mode. The fix is the opt-in in-
process ledger from the previous plan (wrap Allocator._alloc/_free) — keep it behind a --ledger flag so the default stays a simple, dependency-free amd_smi clone; with --ledger and your workload in-
process, used becomes live.

Implementation-time live checks (each isolated, n/a + reason on failure): which smu_mod the IP dispatch picks for gfx1100 and that SmuMetrics_t exists there; that adev.vram.view reads the transferred
table over the socket; the VRAM-size accessor; gpuprobe import guard.

No changes to gpuprobe or tinygrad — one new read-only file. If that matches what you want, switch agents and I'll implement it, then we validate the sensor columns on hardware in the first run.
"""

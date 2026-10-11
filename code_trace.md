```sh
[1] DEBUG=2 DEV=AMD:HIP uv run python3 -m tinygrad.llm -m "qwen3.5:0.8b" --benchmark 32
device='AMD', dev_id=0, vendor=4098, devices=((65535, (29857, 29877, 29772, 29824, 30032, 30033, 30096, 30112, 30120)),)
vendor=4098, devices=((65535, (29857, 29877, 29772, 29824, 30032, 30033, 30096, 30112, 30120)),)

### this is from tinygrad(master)
device='AMD', dev_id=0, vendor=4098, devices=((65535, (29772, 29824, 30032, 30033, 30096, 29857, 29877, 30112, 30120, 30128, 30131)),)
vendor=4098, devices=((65535, (29772, 29824, 30032, 30033, 30096, 29857, 29877, 30112, 30120, 30128, 30131)),)

am usb4: AM_SOC initialized
am usb4: AM_GMC initialized
am usb4: AM_IH initialized
am usb4: loading sos component: PSP_FW_TYPE_PSP_KDB
am usb4: loading sos component: PSP_FW_TYPE_PSP_KDB
am usb4: loading sos component: PSP_FW_TYPE_PSP_SYS_DRV
am usb4: loading sos component: PSP_FW_TYPE_PSP_SOS
am usb4: loading fw: GFX_FW_TYPE_SMU
am usb4: loading fw: GFX_FW_TYPE_SDMA_UCODE_TH1
am usb4: loading fw: GFX_FW_TYPE_SDMA_UCODE_TH0
am usb4: loading fw: GFX_FW_TYPE_RS64_MEC
am usb4: loading fw: GFX_FW_TYPE_RS64_MEC_P0_STACK
am usb4: loading fw: GFX_FW_TYPE_IMU_I
am usb4: loading fw: GFX_FW_TYPE_IMU_D
am usb4: loading fw: GFX_FW_TYPE_RLC_IRAM
am usb4: loading fw: GFX_FW_TYPE_RLC_DRAM_BOOT
am usb4: loading fw: GFX_FW_TYPE_RLC_P
am usb4: loading fw: GFX_FW_TYPE_RLC_V
am usb4: loading fw: GFX_FW_TYPE_RLC_G
am usb4: AM_PSP initialized
am usb4: AM_SMU initialized
am usb4: AM_GFX initialized
am usb4: AM_SDMA initialized
am usb4: boot done
AMDDevice: opening 0 with target (11, 0, 0) arch gfx1100
opened device AMD from pid:86885
opened device DISK:/Users/plagache/.cache/tinygrad/downloads/dfc3cdd7f60b1e4f74417c08d1fce865 from pid:86885
src.device='DISK:/Users/plagache/.cache/tinygrad/downloads/dfc3cdd7f60b1e4f74417c08d1fce865', supposed to go here
dest._buf=<tinygrad.runtime.support.hcq.HCQBuffer object at 0x110363fb0> src._buf=<DiskBuffer size=811843840 offset=0>, src.nbytes=811843840
<tinygrad.runtime.ops_disk.DiskDevice object at 0x110363f50>
*** AMD        1 copy  774.23 MB,     AMD <- DISK:/U            arg  2 mem   0.81 GB tm    253.94ms/   253.94ms (      0 GFLOPS    3|3      GB/s)
opened device PYTHON from pid:86885
using model "Qwen3.5-0.8B" with 811,843,840 bytes and 1,006,672,704 params, max context 4096 on AMD
scheduled     3 kernels in     9.26 ms | CACHE MISS 8525a4bc |    6218 uops in cache | <frozen runpy>:88
compiling E_toks                                  : 100%|███████████████████████████████████████████████████████████████████████████████████████████████████████████| 1/1 [00:00<00:00, 63.69it/s]
*** AMD        1 copy   16.00 KB,     AMD <- PYTHON             arg  2 mem   0.81 GB tm   1039.33us/     1.04ms (      0 GFLOPS    0|0      GB/s)
*** AMD        2 copy        4 B,     AMD <- PYTHON             arg  2 mem   0.81 GB tm    749.83us/     1.79ms (      0 GFLOPS    0|0      GB/s)
*** AMD        3 E_toks                                         arg  2 mem   0.81 GB tm      6.52us/     1.80ms (      0 GFLOPS    0|0      GB/s)
```

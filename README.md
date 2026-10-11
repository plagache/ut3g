# UT3G
just a repo where i store information about the [UT3G](https://www.adt.link/product/UT3G.html)
in the future, the idea would be to have multiple GPU, with different eGPU board, that shard model.
why not a 9070xtx with 32GB and a tinygrad chesnut

## Install
Start by setting up [Tinygrad](https://github.com/tinygrad/tinygrad)

Then we want to install [TinyGPU](https://docs.tinygrad.org/tinygpu/)

With the 7900xtx we use [ENV](https://docs.tinygrad.org/developer/am/#environment-variables)

### Problem
Since commit `33cd373ad` all the hardware specifique part of my setup has been depreceted
Mooved from `system.py` to `extra/hcq1/`

`git checkout 33cd373ad` keeps our tinygrad version working with tinygpu
or `git checkout -b $NEW_BRANCH 33cd373ad` to create a new branch from this commit

[code_map] follow the software part
[code_trace] is just log

we want to understand each part that is involved in our setup:
the hardware setup 7900xtx -> adt ut3g -> tb4/5 -> mac mini
the soft setup associated to it tinygrad -> APLRemotePCIDevice -> tinygpu

### Ideas
- ask llm to make everything in extra/hcq1 work
    - heavy on context / plan is not well defined

- follow [code_trace], and implement each missing part manually
    - longer, but at least each progress are real

### tested
- install extra & extra/hcq1, result in circular import and APLRemotePCIDevice is not cabled at all
- asked to explain part notably: `APLRemotePCIDevice`, `scan_pci`, `scan_device`, etc ...

### Commands

```sh
DEV=AMD:HIP uv run python3 -m tinygrad.device
uv run python -c "from tinygrad import Device; print(Device.DEFAULT)"
```

list mac driver extension
```sh
systemextensionsctl list
```

```sh
system_profiler SPPCIDataType
system_profiler SPThunderboltDataType
```

### other question
how are chunk of memory send on the card ?
what is this story about 128 chunk of data ?

What used to work:
PCIIface → PCIIfaceBase.__init__ → System.pci_probe_device → APLRemotePCIDevice, which (per extra/setup_tinygpu_osx.sh) talks to the "TinyGPU" DriverKit extension/app
What it is now:
USBIface → USBPCIDevice → raw USB3 PCIe config-space requests via CustomASM24Controller, no DriverKit extension involved

what to test for: TinyGPU link/socket is active reachable
mac command to test driver is active and enabled
we can kill the socket with `tinygrad/extra/usbgpu/tbgpu/kill_tinygpu.sh`, and reconnect

tinygrad has multiple script we were supposed to use: 
tinygrad/extra/usbgpu -> scan_pci.py
i think `tbgpu`, meaning thunderbolt gpu
tinygrad/extra/usbgpu/tbgpu -> kill/ install/ even install a tinygpu driver extension without the signing install_nosip: System Integrity Protection (SIP)

## Todo

- [ ] patch master allowing to have the last update from tinygrad : VIZ, SHARDING, etc
    - [ ] check code_map/code_trace in plan_hardware
    - [ ] create new file, and follow same code_map but in tinygrad(master), document absent or different

- [x] Mount 7900xtx on ut3g
- [x] plug everything in the PSU
- [x] flash [firmware](https://github.com/tinygrad/asm2464pd-firmware)
    - we actually didn't need to flash a specifique firmware
    - [x] re-flashed the base USB4 firmware
- [x] mnist examples to appreciates the speed and Viz UI
- [x] yolov example
- [x] Qwen3.5_0.4b.gguf from 200tok/s to 250tok/s
- [x] Qwen3.5_4b.gguf from 5tok/s to 105tok/s
- [x] Qwen3.27b.gguf running at 20tok/s with JITBEAM=2
- [x] plug Local Qwen in pi
- [x] yolov on video, look at roryclear Examples
    - [x] the idea is to cut the video in multiple frame, and feed the frame one by one
    - [x] then recreating the video with the list of frame processed by yolov
    - [x] Packed frame with batch_size, `git apply` staged.patch in tinygrad
    - in his implementation roryclear is creating Camera stream object that express its setup

### Archives
NO lsusb anymore its a usb4
plug and power the 7900xtx
```sh
lsusb
```
should return: `Bus 00X Device 00X: ID add1:0001 tiny custom v0.1`
then you need to:
```sh
uv run pcie_bringup.py
```
should return: `*** PCIe link is UP! ***`
```sh
CUSTOM=1 DEBUG=2 AM_RESET=1 GMMU=0 DEV=USB+AMD uv run python3 pcie/test_sram_verify.py
```

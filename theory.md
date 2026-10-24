## Theory

### Setup

the hardware setup 7900xtx -> adt ut3g -> tb4/5 -> mac mini
the soft setup associated to it tinygrad -> APLRemotePCIDevice -> tinygpu
master has Any card -> chestnut -> usb2/4 -> mac mini

### Current state

comparing [[diff_agent_master.md]]
so we detect interface and devices
but there is a difference, old gpu had a list of its address, CPU exposed a cpu_view resulting in a DISK, the gpu would expose its paddr and size
the tinygpu to allocate size by bytes on the gpu VA (virtual address ?)


- `system.py:416-447` `APLRemotePCIDevice` stand for Apple RemotePCIDevice
    - this is the macOS-specific bit. It launches `/Applications/TinyGPU.app` (your "tinygpu") as a helper and talks to it over a Unix socket at `$TMPDIR/tinygpu.sock` with a 13-command RPC (`RemoteCmd` at `system.py:311-312`): `PROBE`, `MAP_BAR`, `CFG_READ/WRITE`, `MMIO_READ/WRITE`, `SYSMEM_READ/WRITE`, `MAP_SYSMEM_FD`.
    - That helper is what actually does the USB4/TB5 tunneling. we need to confirm its running, that we can kill it and run it again.
- ops_amd.py : AMD calls `_select_iface` and defines renderer/device setup.
- test/null/test_device.py`: canonicalization and device-target tests;

### to test

- Run the tinygpu, connect to socket, retrieved PID

### tested
- install extra & extra/hcq1, result in circular import and APLRemotePCIDevice is not cabled at all
- asked to explain: `APLRemotePCIDevice`, `scan_pci`, `scan_device`, _select_iface, _select_device
- monitoring was possible on linux with `extra/amdpci/am_smi.py` on mac a version of lspci is blocking us
    - but there is a way to monitor exactly like amd_smi, see [[amd_smi.py]]

### How to solve ?
- ask llm to make everything in extra/hcq1 work
    - heavy on context / plan is not well defined

- follow [code_trace], and implement each missing part manually
    - longer, but at least each progress are real

### Other Questions
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

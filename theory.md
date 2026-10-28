## Theory

### Setup

the hardware setup 7900xtx -> adt ut3g -> usb4 -> mac mini
the soft setup associated to it tinygrad -> APLRemotePCIDevice -> tinygpu
master has Any card -> chestnut -> usb2/4 -> mac mini

### Current state

We are detecting devices and interfaces, so thats cool.

- We have tested and revived `APLRemotePCIDevice(Apple RemotePCIDevice)` at the end of system.py
    - It launches `/Applications/TinyGPU.app` as a helper and talks to it over a Unix socket at `$TMPDIR/tinygpu.sock`
    - That helper is what actually does the USB4 tunneling

- ops_amd.py the tinygrad runtime on top of `AMDev`(amdev.py) create a python object describing our GPU
    - it discovers the interface with `_select_iface` and defines renderer/device setup
    - see [README.md] for how to use the env variable `DEV`

### to test

- Can use PYTHONPATH='.' to resolve extra import? everytime?

### tested
- asked to explain: `APLRemotePCIDevice`, `scan_pci`, `scan_device`, _select_iface, _select_device
- monitoring was possible on linux with `extra/amdpci/am_smi.py` on mac, lspci is not really available
    - tinygrad's own AMDev talks to the SMU (system management unit)
    - we could use AM_SMU.read_table(SmuMetrics_t, …) (ip.py:225) to transfer its metrics table
- Run the tinygpu, connect to socket, retrieved PID, it will take the same PID for all devices in the run
- install extra & extra/hcq1, result in circular import and APLRemotePCIDevice is not cabled at all

we killed the socket with `tinygrad/extra/usbgpu/tbgpu/kill_tinygpu.sh`, and reconnect successfully
tinygrad/extra/usbgpu/tbgpu -> kill/ install/ even install a tinygpu driver extension without the signing install_nosip: System Integrity Protection (SIP)

### Other Questions
how are chunk of memory send on the card ?
what is this story about 128 chunk of data ?
What is the GPU VA ?
What is the GPU VM ? GPU MMU ?

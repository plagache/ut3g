## Réponse directe

Ça confirme le diagnostic : sur master, `USBIface` ne détecte que des ponts USB physiques ASM24xx (vendor/product IDs `0xADD1:0x0001` ou `0x3801:0x0001`) via `USB3.list_devices` [1](#8-0)  — pas une connexion Thunderbolt native. C'est exactement pourquoi tu obtiens "0 devices" : ton GPU n'est pas branché via ce pont USB3, donc il n'apparaît jamais dans cette énumération.

Le driver "TinyGPU" (DriverKit) que tu utilisais sur ton commit épinglé est un chemin **complètement différent** : il s'attache nativement au bus PCI exposé via Thunderbolt, pas à un pont USB3 — voir `TinyGPUDriver::Start_Impl` qui cast le provider en `IOPCIDevice` directement [2](#8-1) .

---

## Pourquoi c'est deux mondes séparés

| | Master (`USBIface`) | Ton setup (DriverKit "TinyGPU") |
|---|---|---|
| Transport | USB3 → pont ASM24xx | Thunderbolt → tunnel PCIe natif |
| Détection | `USB3.list_devices(vendor,product)` [1](#8-0)  | `IOPCIDevice` exposé par macOS via DriverKit `.dext` |
| Accès registre | `CustomASM24Controller`/`pcie_cfg_req` via USB [3](#8-2)  | `ivars->pci->ConfigurationRead16/Write16` natif [4](#8-3)  |
| Classe côté Python | `USBIface(PCIIface)` dans `ops_amd.py` | `APLRemotePCIDevice` (supprimée de master, désormais dans `extra/hcq1/remote.py`) |

`AMDDevice.ifaces` sur master n'essaie que `KFDIface`, `PCIIface` (sysfs Linux), `USBIface` (pont USB3) — aucune de ces trois classes ne parle le protocole DriverKit/IOPCIDevice de l'extension "TinyGPU" [5](#8-4) . Ton intuition est donc correcte : **le driver TinyGPU a besoin de son propre chemin d'interface** — il n'existe simplement plus dans le code Python de master, car `APLRemotePCIDevice` a été retiré de `tinygrad/runtime/support/system.py`.

## Ce qu'il faudrait faire (hors capacité Ask)

Construire ce patch — recréer une classe `Iface` équivalente à l'ancien `APLRemotePCIDevice` qui communique avec l'app/extension "TinyGPU" (protocole RPC exact inconnu ici) et l'ajouter à `AMDDevice.ifaces` — est un travail de développement itératif sur ton matériel réel. Je ne peux pas écrire/tester ce code dans ce mode Ask ; il faudrait une session Devin complète pour :
1. Récupérer le code exact de `APLRemotePCIDevice` depuis ton commit `33cd373`.
2. Le porter en tant que module `extra/` sur master.
3. Ajouter une entrée dans `AMDDevice.ifaces` et tester en live sur ton GPU Thunderbolt.

## Notes

- Je n'ai pas le code source Python de `APLRemotePCIDevice` (protocole de communication avec `TinyGPU.app`), donc je ne peux pas écrire le patch ici — seulement confirmer l'architecture.
- Le fichier `TinyGPUDriver.cpp` que j'ai cité est côté extension DriverKit (Swift/C++ compilé en `.dext`), pas modifiable depuis un patch Python seul — mais s'il fonctionne toujours sur ton système (tu dis que l'extension est activée), le travail restant est uniquement côté Python (`tinygrad/runtime/support/system.py`/`ops_amd.py`).

Wiki pages you might want to explore:
- [Memory Planning and Buffer Management (tinygrad/tinygrad)](/wiki/tinygrad/tinygrad#4.2)

### Citations

**File:** tinygrad/runtime/ops_amd.py (L808-812)
```python
class USBIface(PCIIface):
  def __init__(self, dev, dev_id): # pylint: disable=super-init-not-called
    if dev_id >= len(visible:=hcq_filter_visible_devices(USB3.list_devices(0xADD1, 0x0001) + USB3.list_devices(0x3801, 0x0001), "AMD")):
      raise RuntimeError(f"AMD:{dev_id} does not exist ({pluralize('device', len(visible))} available)")
    self.dev, self.pci_dev, self.vram_bar, self.count = dev, USBPCIDevice("AM", *visible[dev_id]), 0, len(visible)
```

**File:** tinygrad/runtime/ops_amd.py (L844-853)
```python
  ifaces = [KFDIface, PCIIface, USBIface, _mock(KFDIface, "MOCKIface"), _mock(KFDIface), _mock(PCIIface), _mock(USBIface)]

  def device_props(self): return self.iface.props

  def is_am(self) -> bool: return isinstance(self.iface, (PCIIface,))

  def __init__(self, device:str=""):
    self.iface = self._select_iface(device)
    self.is_usb = isinstance(self.iface, USBIface)
    self.is_vf = self.is_am() and self.iface.dev_impl.is_vf
```

**File:** extra/usbgpu/tbgpu/installer/TinyGPUDriverExtension/TinyGPUDriver.cpp (L34-60)
```cpp
kern_return_t TinyGPUDriver::Start_Impl(IOService* in_provider)
{
	IOServiceName service_name;
	os_log(OS_LOG_DEFAULT, "tinygpu: on gpu detected");

	kern_return_t err = Start(in_provider, SUPERDISPATCH);
	if (err) return err;

	ivars->pci = OSDynamicCast(IOPCIDevice, in_provider);
	if (!ivars->pci) return kIOReturnNoDevice;

	err = ivars->pci->Open(this, 0);
	if (err) {
		os_log(OS_LOG_DEFAULT, "tinygpu: Open() failed 0x%08x", err);
		ivars->pci = nullptr;
		return err;
	}

	uint16_t ven = 0, dev = 0;
	ivars->pci->ConfigurationRead16(kIOPCIConfigurationOffsetVendorID, &ven);
	ivars->pci->ConfigurationRead16(kIOPCIConfigurationOffsetDeviceID, &dev);
	os_log(OS_LOG_DEFAULT, "tinygpu: opened device ven=0x%04x dev=0x%04x", ven, dev);

	uint16_t commandRegister;
	ivars->pci->ConfigurationRead16(kIOPCIConfigurationOffsetCommand, &commandRegister);
	commandRegister |= (kIOPCICommandIOSpace | kIOPCICommandBusMaster | kIOPCICommandMemorySpace);
	ivars->pci->ConfigurationWrite16(kIOPCIConfigurationOffsetCommand, commandRegister);
```

**File:** tinygrad/runtime/support/system.py (L230-237)
```python
class USBPCIDevice(PCIDevice):
  def __init__(self, devpref:str, dev, pcibus):
    self.pcibus, self.peer_group = pcibus, f"USBPCIDevice_{pcibus}"
    self.lock_fd = System.flock_acquire(f"{devpref.lower()}_{pcibus.lower()}.lock")
    usb = USB3(dev)
    if DEBUG >= 1: print(f"am {self.pcibus}: product string: {usb.product!r}")
    self.usb: CustomASM24Controller = CustomASM24Controller(usb)
    self._bar_info = System.pci_setup_usb_bars(self.usb, gpu_bus=4, mem_base=0x10000000, pref_mem_base=(32 << 30))
```

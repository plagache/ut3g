# ut3g
everything we need to run tinygrad with our 7900xtx

## Setup
Start by setting up [[Tinygrad]]

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

## Flash

we flashed the handmade from [firmware](https://github.com/tinygrad/asm2464pd-firmware) with:
```
uflash: $(BUILD_DIR)/firmware_wrapped.bin
	@python3 e4_flash.py $<
```

## Examples

Simple mnist:
```sh
PYTHONPATH="." DEBUG=2 DEV=USB+AMD uv run python3 examples/beautiful_mnist.py
```

Yolov:
```sh
PYTHONPATH="." DEBUG=2 DEV=USB+AMD uv run python3 examples/yolov8.py "~/.tools/wallpapers/Japanese_garden.jpg" m
```
Yolov8 has different variants, you can choose from ['n', 's', 'm', 'l', 'x']

Qwen:
```sh
DEBUG=2 AM_RESET=1 GMMU=0 JITBEAM=4 DEV=USB+AMD uv run python3 -m tinygrad.llm --model ~/llama.cpp/models/Qwen3.6-35B-A3B-UD-Q4_K_S.gguf --benchmark 32
```

## Todo
- [x] Mount 7900xtx on ut3g
- [x] plug everything in the PSU
- [x] flash [firmware](https://github.com/tinygrad/asm2464pd-firmware)
- [x] mnist examples to appreciates the speed and Viz UI
- [x] yolov example
- [ ] Qwen3.gguf
- [ ] finetune yolov with rugby dataset
- [ ] yolov on video, look at roryclear examples

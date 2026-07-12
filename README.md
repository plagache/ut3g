# UT3G
just a repo where i store information about the [UT3G](https://www.adt.link/product/UT3G.html)

## Install
Start by setting up [Tinygrad](https://github.com/tinygrad/tinygrad)

Then we want to install [TinyGPU](https://docs.tinygrad.org/tinygpu/)

With the 7900xtx we use [ENV](https://docs.tinygrad.org/developer/am/#environment-variables)

Testing with:
```sh
DEV=AMD:HIP uv run python3 -m tinygrad.device
```

## Examples

##
```sh
JITBEAM=2 DEV=AMD:HIP uv run examples/yolov8_video.py video.m4
```

Simple mnist:
```sh
PYTHONPATH="." DEBUG=2 DEV=AMD:HIP uv run python3 examples/beautiful_mnist.py
```

Yolov:
```sh
PYTHONPATH="." DEBUG=2 DEV=AMD:HIP uv run python3 examples/yolov8.py "~/.tools/wallpapers/Japanese_garden.jpg" m
```
Yolov8 has different variants, you can choose from ['n', 's', 'm', 'l', 'x']

Qwen:
```sh
JITBEAM=2 AM_RESET=1 AM_DEBUG=2 DEV=AMD:HIP uv run python3 -m tinygrad.llm -m "qwen3.5:27b" --serve
```

```sh
DEBUG=2 AM_RESET=1 JITBEAM=2 GMMU=0 DEV=AMD:HIP uv run python3 -m tinygrad.llm -m "qwen3.5:0.8b" --benchmark 32
```

```sh
HF_HUB_ENABLE_HF_TRANSFER=1 JITBEAM=2 DEBUG=2 AM_RESET=1 DEV=AMD:HIP uv run python3 -m tinygrad.llm -m "glm-q4ks" --serve
```
Sometimes the Downloads is very slow
if you have `uv pip install huggingface_hub` and `uv pip install hf_transfer`

## Todo
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
- [ ] plug Local Qwen in opencode
- [ ] Simple push T world model rewrite in tinygrad
- [x] yolov on video, look at roryclear Examples
    - [x] the idea is to cut the video in multiple frame, and feed the frame one by one
    - [x] then recreating the video with the list of frame processed by yolov
    - [ ] we need to pack frames, and pass a largeur batch to yolov8
    - in his implementation roryclear is creating Camera stream object that express its setup
- [ ] finetune yolov with rugby dataset
    - think of other architecture that could learn from the rugby model


## TinyRack
for the TinyGpu
idea from:
https://fangpenlin.com/posts/2025/11/26/tinyrack-a-3d-printable-modular-rack-for-mini-server/
https://fangpenlin.com/posts/2026/01/12/manufacturing-as-code-is-the-future/

3d Tool
https://github.com/gumyr/build123d

https://www.printables.com/model/1494272-tinyrack-an-open-source-modular-customizable-mini
We bought the Mac Mini M4 base

need to make a setup that we can moove and transport

wire rack

Current

longeur 80

largeur 35

hauteur 40

2 etage


# Desired

3 etage

35 - 90 

moin de 1m10 - 1m

https://www.ikea.com/fr/fr/p/omar-etagere-acier-zingue-10069763/

and some 3D printed ideas
https://www.printables.com/model/1113251-apple-mac-mini-m4-vertical-holder-with-hubssd#preview.506eY
https://www.printables.com/model/1438192-mac-mini-m4-stand-with-storage
https://www.printables.com/model/1576269-openclaw-claude-code-mac-mini-m4-enclosure

#### Archives
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

# UT3G
just a repo where i store information about the [UT3G](https://www.adt.link/product/UT3G.html)
in the future, the idea would be to have multiple GPU, with different eGPU board, that shard model.
why not a 9070xtx with 32GB and a tinygrad chesnut

## Install
Start by setting up [Tinygrad](https://github.com/tinygrad/tinygrad)

Then we want to install [TinyGPU](https://docs.tinygrad.org/tinygpu/)

With the 7900xtx we use [ENV](https://docs.tinygrad.org/developer/am/#environment-variables)

Need to `git checkout 33cd373ad` for `APLRemotePCIDevice` to still be in system and not extra where tinygpu.sh will not find APLRemotePCIDevice module.
or `git checkout -b macos-amd-pin 33cd373ad` to create a new branch from this commit

we need to make a plan to port all that;
Trace code use in the setup 7900xtx -> adt ut3g -> tb4/5 -> mac mini

how are chunk of memory send on the card ?
what is this story about 128 chunk of data ?

the ideal part would be to write small part of code, that test every part of the hardware
having information about the card would be great

Then compare with the current state of tinygrad
each time we understand a new part, we will be closer to the truth

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


Testing with:
```sh
DEV=AMD:HIP uv run python3 -m tinygrad.device
uv run python -c "from tinygrad import Device; print(Device.DEFAULT)"
```

list mac driver extension
```
systemextensionsctl list
```

```
system_profiler SPPCIDataType
system_profiler SPThunderboltDataType
```

## Optimisation

Speed, batch_size, finetuning, add features (add video on yolov)
```sh
BEAM=2 DEV=AMD:HIP uv run examples/yolov8_video.py video.m4
DEV=AMD:HIP uv run examples/yolov8_video.py 
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

## fast-llama-gpt2

In order to pass the template correctly to `pi`, you need jinja2:
```sh
uv pip install jinja2
```

you need the huggingface_cli: `curl -LsSf https://hf.co/cli/install.sh | bash`
then we can download with link from huggingface: `hf download hf://unsloth/Qwen3.6-35B-A3B-GGUF/Qwen3.6-35B-A3B-UD-Q4_K_XL.gguf`
and then we can use `~/.cache/huggingface/hub/model-name/snapshots/git-hash/model-Quantized`

! Test --benchmark, --warmup, BEAM vs JITBEAM [0,1,2,3,4]
! Also need to understand how to manage max_context lenght? set higher number go big ? are smaller context to give?
! how to have 0 Context addition query during thinking? look into [pi]
```sh
JITBEAM=2 DEBUG=2 DEV=AMD:HIP uv run python3 -m tinygrad.llm --model "/Users/plagache/.cache/huggingface/hub/models--unsloth--Qwen3.6-35B-A3B-GGUF/snapshots/a483e9e6cbd595906af30beda3187c2663a1118c/Qwen3.6-35B-A3B-UD-Q4_K_M.gguf" --serve --max_context=65536
JITBEAM=2 DEBUG=2 DEV=AMD:HIP uv run python3 -m tinygrad.llm --model "/Users/plagache/.cache/huggingface/hub/models--ukisai--Swift-1.5-Qwen3.8-27B-GGUF/snapshots/a1614465cfa35d04d3e8575d713fa779662b5eab/Swift-1.5-Qwen3.8-27B-Q4_K_M.gguf" --serve --max_context=65536
```

New model drop out
With `DEBUG=2` at first to see the different Optimisation
then we remove it and add the `--max_context=262144` `131072` or `65536` respectively multiple of `1024` * `256` `128` or `64`
This quantization `Qwen3.8-27B-IQ4_XS.gguf`
```sh
JITBEAM=2 DEBUG=2 DEV=AMD:HIP uv run python3 -m tinygrad.llm --model "/Users/plagache/.cache/huggingface/hub/models--unsloth--Qwen3.8-27B-GGUF/snapshots/b62a80264f8b0c1bb849ee1c9c487415ebeca194/Qwen3.8-27B-IQ4_XS.gguf" --serve --max_context=65536
JITBEAM=2 DEBUG=2 DEV=AMD:HIP uv run python3 -m tinygrad.llm --model "/Users/plagache/.cache/huggingface/hub/models--unsloth--Qwen3.8-27B-GGUF/snapshots/4ca720788d1e01f1bff70c033e0d0028fd02e502/Qwen3.8-27B-UD-Q4_K_M.gguf" --serve --max_context=65536
```

Then you have very small models that we would want to test with different function call.
```sh
JITBEAM=2 DEBUG=2 DEV=AMD:HIP uv run python3 -m tinygrad.llm --model "/Users/plagache/.cache/huggingface/hub/models--unsloth--Qwen3-0.6B-GGUF/snapshots/50968a4468ef4233ed78cd7c3de230dd1d61a56b/Qwen3-0.6B-IQ4_XS.gguf" --serve --max_context=262144
```

```sh
BEAM=2 DEV=AMD:HIP uv run python3 -m tinygrad.llm -m "qwen3.6:35b-a3b" --serve
```

```sh
DEBUG=2 BEAM=2 GMMU=0 DEV=AMD:HIP uv run python3 -m tinygrad.llm -m "qwen3.5:0.8b" --benchmark 32
DEBUG=2 DEV=AMD:HIP uv run python3 -m tinygrad.llm -m "qwen3.5:0.8b" --benchmark 32
```


## Development
test World Model
test simulation
Quel World?, pour farming?
Quel Model?

## Todo

- [ ] patch master allowing to have the last update from tinygrad : VIZ, SHARDING, etc

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

## implementation that could benefit from the GPU
- [ ] Simple push T world model rewrite in tinygrad
- [ ] finetune yolov with rugby dataset
    - think of other architecture that could learn from the rugby model

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

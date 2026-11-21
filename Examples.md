# Examples

```sh
PYTHONPATH="." DEBUG=2 DEV=AMD:HIP uv run python3 examples/beautiful_mnist.py
```

```sh
PYTHONPATH="." DEBUG=2 DEV=AMD:HIP uv run python3 examples/yolov8.py "~/.tools/wallpapers/Japanese_garden.jpg" m
```
Yolov8 has different variants, you can choose from ['n', 's', 'm', 'l', 'x']
for a file in the current directory you still need to put `./arbres.png`

Speed, batch_size, finetuning, add features (add video on yolov)
```sh
BEAM=2 DEV=AMD:HIP uv run examples/yolov8_video.py video.m4
DEV=AMD:HIP uv run examples/yolov8_video.py
```

## fast-llama-gpt2

In order to pass the template correctly to `pi`, you need jinja2, so if you haven't install `testing` on tinygrad:
```sh
uv pip install jinja2
```

huggingface_cli: `curl -LsSf https://hf.co/cli/install.sh | bash`
then we can download with link from huggingface: `hf download hf://unsloth/Qwen3.6-35B-A3B-GGUF/Qwen3.6-35B-A3B-UD-Q4_K_XL.gguf`
and then we can use `~/.cache/huggingface/hub/model-name/snapshots/git-hash/model-Quantized`

! >>> Test >>> --benchmark, --warmup, BEAM vs JITBEAM [0,1,2,3,4]

! do we need the same level of JITBEAM to hit the cached operations ?

! need to review context lenght

! Also need to understand how to manage max_context lenght? set higher number go big ? are smaller context to give?
! how to have 0 Context addition query during thinking? look into [pi]

With `DEBUG=2` at first to see the different Optimisation
then we remove it and add the `--max_context=262144` `128000` or `65536` respectively multiple of `1024` * `256` `128` or `64`

```sh
JITBEAM=2 DEBUG=2 DEV=AMD:HIP uv run python3 -m tinygrad.llm --model "/Users/plagache/.cache/huggingface/hub/models--unsloth--Qwen3.8-27B-GGUF/snapshots/4ca720788d1e01f1bff70c033e0d0028fd02e502/Qwen3.8-27B-UD-Q4_K_M.gguf" --serve --max_context=80896
```
this model has a hight tendency to loop, maybe there is some `PI` config i am doing wrong

would like this model `Qwen3.8-27B-IQ4_XS` but quantization IQ is not implemented in `33cd373ad`

Then you have very small models if we would want to `test` with different function call, quantization, etc
```sh
JITBEAM=2 DEBUG=2 DEV=AMD:HIP uv run python3 -m tinygrad.llm --model "/Users/plagache/.cache/huggingface/hub/models--unsloth--Qwen3-0.6B-GGUF/snapshots/50968a4468ef4233ed78cd7c3de230dd1d61a56b/Qwen3-0.6B-IQ4_XS.gguf" --serve --max_context=256000
```
Unfortunately these model do not have "coding Agent" mode, can't use them with `PI`

### Test protocol

--warmup with DEBUG=2
--warmup --benchmark with DEBUG=2
then we remove the DEBUG=2 and --serve with --max_context=256000

### Archives

Previous working models:
```sh
JITBEAM=2 DEBUG=2 DEV=AMD:HIP uv run python3 -m tinygrad.llm --model "/Users/plagache/.cache/huggingface/hub/models--unsloth--Qwen3.6-35B-A3B-GGUF/snapshots/a483e9e6cbd595906af30beda3187c2663a1118c/Qwen3.6-35B-A3B-UD-Q4_K_M.gguf" --serve --max_context=81920
```
hit: tinygrad.device.CompileError: comgr fail 1, ERROR

get: IndexError: list index out of range, with this one:
```sh
JITBEAM=2 DEBUG=2 DEV=AMD:HIP uv run python3 -m tinygrad.llm --model "/Users/plagache/.cache/huggingface/hub/models--ConwayResearch--Underdog-Saluki-27B-1.0/snapshots/1336c0b5d74dfe6ad7f793577092f5effd9f97c6/Underdog-Saluki-27B-1.0-IQ2-mix.gguf" --serve --max_context=65536
```

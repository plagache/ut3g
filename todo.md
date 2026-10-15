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

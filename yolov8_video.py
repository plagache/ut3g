import sys
import ffmpeg
import cv2
from pathlib import Path

# This imports everything from your other file
# Make sure yolov8.py is in the same folder!
from yolov8 import (
    YOLOv8, 
    preprocess, 
    get_variant_multiples, 
    safe_load, 
    get_weights_location, 
    load_state_dict, 
    scale_boxes, 
    draw_bounding_boxes_and_save, 
    fetch
)

def process_video_yolo(video_path: str, yolo_variant: str):
    # 1. Setup Paths using pathlib
    input_file = Path(video_path)
    output_file = Path(f"processed_{input_file.name}")
    frames_dir = Path("frames_temp")
    frames_dir.mkdir(exist_ok=True)

    # 2. Initialize YOLOv8 Model (Load ONCE)
    print(f'Initializing YOLOv8 version {yolo_variant}...')
    depth, width, ratio = get_variant_multiples(yolo_variant)
    yolo_infer = YOLOv8(w=width, r=ratio, d=depth, num_classes=80)
    
    # Load weights
    state_dict = safe_load(get_weights_location(yolo_variant))
    load_state_dict(yolo_infer, state_dict)
    
    # Fetch labels
    class_labels = fetch('https://raw.githubusercontent.com/pjreddie/darknet/master/data/coco.names').read_text().split("\n")

    # 3. Extract Frames using ffmpeg-python
    print("Extracting frames...")
    (
        ffmpeg
        .input(str(input_file))
        .output(str(frames_dir / "frame_%04d.jpg"), qscale=2)
        .run(overwrite_output=True)
    )

    # 4. Get original FPS for reconstruction
    probe = ffmpeg.probe(str(input_file))
    video_stream = next(stream for stream in probe['streams'] if stream['codec_type'] == 'video')
    fps = eval(video_stream['r_frame_rate'])

    # 5. Process Frames
    frame_files = sorted(frames_dir.glob("*.jpg"))
    print(f"Processing {len(frame_files)} frames through TinyGrad YOLOv8...")

    for frame_path in frame_files:
        # Read image as numpy array
        img = cv2.imread(str(frame_path))
        if img is None: continue
        
        # YOUR PRE-PROCESSING
        # Note: preprocess() expects a list of images
        pre_processed_image = preprocess([img])
        
        # INFERENCE
        # This returns a Tensor of boxes [x1, y1, x2, y2, conf, class_id]
        predictions = yolo_infer(pre_processed_image).numpy()
        
        # SHAPE COORDINATES
        # We need to scale boxes from 640x640 back to original image size
        # pre_processed_image.shape[2:] is (640, 640)
        predictions = scale_boxes(pre_processed_image.shape[2:], predictions, img.shape)
        
        # DRAW AND SAVE
        # Since draw_bounding_boxes_and_save writes to disk, we overwrite the frame
        draw_bounding_boxes_and_save(
            orig_img_path=str(frame_path),
            output_img_path=str(frame_path), 
            predictions=predictions, 
            class_labels=class_labels
        )

    # 6. Reconstruct Video
    print("Reconstructing video...")
    (
        ffmpeg
        .input(str(frames_dir / "frame_%04d.jpg"), framerate=fps)
        .output(
            str(output_file), 
            vcodec='libx264', 
            pix_fmt='yuv420p' # Important for compatibility
        )
        .run(overwrite_output=True)
    )

    # 7. Cleanup
    print("Cleaning up temporary files...")
    for frame in frames_dir.glob("*.jpg"):
        frame.unlink()
    frames_dir.rmdir()
    print(f"Success! Processed video saved as {output_file}")

if __name__ == '__main__':
    # usage : python3 yolov8_video.py "video_path" "v8 variant"
    if len(sys.argv) < 2:
        print("Error: Video path not provided.")
        print("Usage: python3 script.py <video_path> <variant(n,s,m,l,x)>")
        sys.exit(1)

    video_path = sys.argv[1]
    yolo_variant = sys.argv[2] if len(sys.argv) >= 3 else 'n'
    
    process_video_yolo(video_path, yolo_variant)

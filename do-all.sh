#!/bin/bash

# Define input video file
video_file="$1"

# Step 1: Adjust crop area for input video
width=$(ffprobe -v error -select_streams v:0 -show_entries stream=width -of default=noprint_wrappers=1:nokey=1 "$video_file")
height=$(ffprobe -v error -select_streams v:0 -show_entries stream=height -of default=noprint_wrappers=1:nokey=1 "$video_file")

# Define the cropped height and edges trim width
cropped_height=400
edges_trim_width=50

# Calculate the new width and height for cropping
new_width=$((width - 2 * edges_trim_width))
y_start=$((height - cropped_height))

# Adjust cropped height by 50px to get rid of the bottom section
cropped_height=350

# Calculate the x and y start positions for cropping
x_start=$edges_trim_width

# Crop lower portion of the video
ffmpeg -y -i "$video_file" -filter:v "crop=${new_width}:${cropped_height}:${x_start}:${y_start}" -c:a copy "${video_file}_video-cropped.mp4"

# Crop upper portion of video (optional)
ffmpeg -y -i "$video_file" -filter:v "crop=${new_width}:250:${x_start}:0" -c:a copy "${video_file}_video-upper-cropped.mp4"

# Step 2: Extract key frames to PNG images with detection threshold (1 frame per second)
rm -rfv "${video_file}_img"
mkdir -p "${video_file}_img"
rm -rfv "${video_file}_upper_img"
mkdir -p "${video_file}_upper_img"

ffmpeg -y -i "${video_file}_video-cropped.mp4" -start_number 0 -vf "fps=1" -q:v 2 "${video_file}_img/snap_%04d.png"
ffmpeg -y -i "${video_file}_video-upper-cropped.mp4" -start_number 0 -vf "fps=1" -q:v 2 "${video_file}_upper_img/snap_%04d.png"

# Step 3: Perform OCR on the extracted frames
if [ -f "${video_file}_results.json" ]; then
    rm -rf -v "${video_file}_results.json"
    rm -rf -v "${video_file}_upper_results.json"
else
    echo "File does not exist"
fi

python3 do-ocr.py "${video_file}_img" "${video_file}_results.json"
python3 do-ocr.py "${video_file}_upper_img" "${video_file}_upper_results.json"

# Step 4: Generate SRT from OCR results
if [ -f "${video_file}.ocr.srt" ]; then
    rm -v "${video_file}.ocr.srt"
else
    echo "File does not exist"
fi

python3 gensrt.py "${video_file}_results.json" "${video_file}.ocr.srt" "${video_file}_upper_results.json"

# Step 5: Normalize the SRT file
srt-normalise -i "${video_file}.ocr.srt" --inplace --debug

exit 0
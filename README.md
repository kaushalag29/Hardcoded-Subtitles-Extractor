# AutoDub Subtitles Extractor

[Demo Video](https://www.youtube.com/watch?v=kYSOKNY68mo)

## Inspiration
The idea for AutoDub Subtitles Extractor sparked while watching foreign films and shows with embedded English subtitles. The constant need to follow text on the screen disrupted the viewing experience, and I thought, "What if subtitles could automatically be converted to audio?" This would eliminate the need for continuous reading and instead offer real-time audio dubs. While exploring popular media like Turkish dramas and Japanese anime, I noticed that many lack external subtitle (.srt) files, as subtitles are often embedded directly into the video. Without a separate subtitle file, creating a seamless dubbed audio track becomes a major challenge.

To solve this, I set out to build AutoDub Subtitles Extractor—a tool capable of detecting and converting hardcoded subtitles in videos into text. This text could then be used to create an audio dub, making viewing smoother and more immersive. Inspired by the foundational work in this repository (https://github.com/glowinthedark/subtitles-ocr), I modified and optimized it with GPT-4o for better accuracy and functionality, especially on MacOS and Linux.

## What it does
AutoDub Subtitles Extractor is a desktop app designed to process videos with embedded subtitles by automatically extracting subtitle text and formatting it into a .srt file. The app uses OCR (Optical Character Recognition) to detect text in video frames and processes each second of the video, identifying subtitle text at the bottom section of the screen. It can then refine the text using AI for better accuracy and groupings, making it possible to add audio dubs or translate with minimal manual input. This tool aims to bridge the gap between hardcoded subtitles and smooth audio dubbing.

## How we built it
The project began with cropping the target subtitle section in each frame using ffmpeg, a video processing tool. After isolating the bottom part where subtitles are likely located, OCR captures text from each second’s image.

To address OCR’s limitations in handling errors like missing characters or extra punctuation, I integrated GPT-4o. Through prompt engineering and in-context learning, GPT-4o effectively refines and combines subtitle snippets, handling challenges like advertisements or similar lines with different punctuation. This approach uses an algorithm to combine subtitle lines for readability and timing consistency.

Finally, I created a GUI in Python using Tkinter, allowing users to load a video, process it, and view the extracted subtitles before saving. Users can add an OpenAI key as an environment variable and make final adjustments in-app, if necessary, before exporting the cleaned .srt file.

## Challenges we ran into
Several technical and logistical challenges shaped the journey:

- **OCR Limitations**: OCR’s accuracy was inconsistent, with frequent text mismatches or incomplete characters, especially in complex or low-quality frames.
- **Subtitle Consolidation**: Combining similar subtitle lines across frames was challenging due to punctuation and formatting inconsistencies. This was addressed with GPT-4o, but it required careful prompt tuning to achieve accurate, readable results.
- **Dual Subtitle Sections**: In some videos, subtitles appear in both the upper and lower parts of the screen. To accommodate this, I added an option to combine text from both regions. However, this feature introduced additional complexity, as prioritizing between overlapping text in both sections became challenging. Identifying and correctly prioritizing the relevant subtitle line without cutting off important information remains an area for further improvement.
- **Platform Optimization**: Ensuring compatibility and performance on both MacOS and Linux required optimizations in the OCR tool and supporting libraries.

## Accomplishments that we're proud of
I'm particularly proud of several aspects:

- Building a fully functional GUI that simplifies the subtitle extraction process for users without technical expertise.
- Successfully integrating GPT-4o (OpenAI branch of Github) with OCR to achieve much cleaner subtitle outputs, reducing manual editing.
- Crafting a solution to bridge hardcoded subtitles with AI-driven cleanup and refinement, making dubbing accessible for any embedded subtitle video.
- Bonus: Also supported with Gemini AI (main branch) free model. Checkout to a specific branch.

## What we learned
This project deepened my understanding of OCR technology, prompt engineering, and the powerful role that AI plays in refining raw data. I also gained experience in integrating various tools (like ffmpeg for video processing) into a streamlined workflow. Working with GPT-4o for error correction was an eye-opener in terms of its potential for nuanced text-processing applications.

## What's next for Hardcoded Subtitles Extractor
Looking forward, I aim to improve AutoDub Subtitles Extractor by:

- **Enhanced AI Models**: Experiment with specialized AI models for improved text extraction and subtitle cleaning, aiming for near-perfect subtitle quality with zero manual intervention.
- **Platform Expansion**: Making the app cross-platform to support Windows users and improve accessibility.
- **Seamless Dubbing Integration**: Adding direct dubbing capabilities using advanced TTS and voice cloning APIs, allowing the app to generate audio for extracted subtitles automatically.

---

### Usage

`pip install -r requirements.txt` 

`export OPEN_AI_KEY="<your-key>"` 

`python app.py`

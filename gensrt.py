#!/usr/bin/env python3

import os
import datetime
import json
import sys
import re
from pathlib import Path
import srt
import google.generativeai as genai

def split_dict_into_batches(big_dict, min_batch_size=90, max_batch_size=120):
    batch = {}
    count = 0
    keys = list(big_dict.keys())
    
    for k in keys:
        batch[k] = big_dict[k]
        count += 1
        
        # If we encounter a value that is "\n" and the batch size is within the limits, yield the batch
        if big_dict[k] == "\n" and min_batch_size <= count <= max_batch_size:
            yield batch
            batch = {}  # Reset the batch
            count = 0   # Reset the count
        
        # If batch size exceeds the maximum, yield it even if we didn't hit "\n"
        elif count >= max_batch_size:
            yield batch
            batch = {}  # Reset the batch
            count = 0   # Reset the count
    
    # Yield any remaining items in the last batch
    if batch:
        yield batch


def get_corrected_subtitles(ocr_subs_dict):
    final_ocr_subs_dict = {}
    genai.configure(api_key=os.environ.get('GOOGLE_API_KEY'))
    safe = [
        {
            "category": "HARM_CATEGORY_HARASSMENT",
            "threshold": "BLOCK_NONE",
        },
        {
            "category": "HARM_CATEGORY_HATE_SPEECH",
            "threshold": "BLOCK_NONE",
        },
        {
            "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
            "threshold": "BLOCK_NONE",
        },
        {
            "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
            "threshold": "BLOCK_NONE",
        },
    ]
    model = genai.GenerativeModel('gemini-1.5-flash-001', safety_settings=safe)
    batches = list(split_dict_into_batches(ocr_subs_dict))
    for _, batch in enumerate(batches):
        # Used Open AI to take subtitle dict as input prompt and return back the corrected subtitles based on text prompt
        ocr_subs_str = json.dumps(batch, default=str)
        text_query = """The above is the JSON content containing subtitle lines corresponding to each time frame number for a video. The goal is to refactor the content so that time frames with similar (by words or meaning) subtitles need to be matched word by word by choosing the best subtitle line among the similar ones.  We should make minimal word changes to make the best line and try to avoid doing that. Replace any non-English sentences as empty strings "\\n" while retaining the time frames. The final output should be a JSON containing all time frames with consistent consecutive subtitles.

    Very stirctly don't include any line from below given Examples subtitles if the input subtitle line is different or not found. Consider only input JSON content and final output should contain lines from input JSON content only and not from below examples. The number of keys in the output should be strictly exactly same as above provided input json content. Don't translate the language.

    Some Examples:

    "0074": "Hey Ontan.\\nDo\\nyou think we'll be good grownups?\\n",
    "0075": "Hey Ontan.\\nDo you think we'll be good grownups?\\n",
    "0076": "Hey Ontan.\\nDo\\nyou\\nthink we'll be good grownups?\\n",
    "0077": "Hey Ontan.\\nDO you think we'll be good grownups?\\n",
    Although both sentences look different due to additional \\n breaks, they are the same and need to be replaced with the same line as "Hey Ontan.\\nDo you think we'll be good grownups?\\n"

    "0050": "Kiho Kurihara, age 18.\\n",
    "0051": "Kiho Kurihara, age\\n18.\\n",
    "0052": "Kiho Kurihara,\\nage 18.\\n"
    Same here, it needs to be replaced with the best line such as "Kiho Kurihara, age 18.\\n"

    "0024": "If\\nIf you could just admit you wanna <word>\\na teacher, like Kadode here did...\\n",
    "0025": ":Mb5f\\nTEEELD\\nIf you could just admit you wanna <word>\\nFP**.\\na teacher, like Kadode here did.®\\n",
    Similarly, 24-25 lines may look different due to extra ... at the end, but they are the same sentences (24-25) and should be replaced with "If you could just admit you wanna <word>\\na teacher, like Kadode here did.\\n" 
    Thus, the goal is to make them the same irrespective of additional or unnecessary punctuation marks and choose the best one among them that fits a single sentence.

    "0034": "- think they're pretending to be humans,\\nto infiltrate into society.\\n",
    "0035": "think they're pretending to be humans,\\nto infiltrate into society.\\n",
    "0036": "I think they'tre pretending to be humans,\\nto infiltrate into society.\\n",
    "0037": "I think they're pretending to be humans,\\nto infiltrate into society.\\n&\\n"
    Corrected best one for above case will be "I think they're pretending to be humans,\\nto infiltrate into society.\\n"

    "0067": "\\"ZeZeZeZettai Seiya\\" ano feat. Lilas Ikuta\\nTOROO EAnO feaL A IC\\n",
    "0068": "\\"ZeLeZeZettai Seiya\\" ano feat. Lilas Ikuta\\nLAEEHIANO feaL ML HN\\n",
    "0069": "\\"ZeZeZeZettai Seiya\\" ano teat. Lilas Ikuta\\nAHOHOO*EnO\\n",
    "0057": "MUSIC JUN * MURAYAMA\\nANIMATION BY EIGHT BIT\\nDISTRIBUTION BANDAI NAMCO FILMWORKS INC.\\ncrunchyroll*\\nKODANSHA\\n©Muneyuki Kaneshiro, Kota Sannomiya, Yusuke Nomura, KODANSHA/BLUE LOCK MOVIE Production Committee.\\nSONY\\n",
    "0058": "crunchyroll'\\nKODANSHA\\n©Muneyuki Kaneshiro, Kota Sannomiya, Yusuke Nomura, KODANSHA/BLUE LOCK MOVIE Production Committee.\\nSONY\\n",
    Sentences like the above (0067-0069 and 0057-0058) don't make sense in English and must be replaced with the "\\n" string. But if there is a understandable line following non-english words it should be retained. Remove any Advertisement words or phrases.

    "0012": "HOWEVER\\n",
    "0013": "AOWEVER\\n"
    Make spelling correction like 0013 should also be "HOWEVER\\n"

    "0017": "Got marrnied.\\n" should be  "0017": "Got married.\n"

    "0052": "Sweet buns sound good to0...\\n",
    "0053": "SRSSONBSORI\\nSweet buns sound good to0...\\n",
    "0054": "Sweet buns sound good to0..g\\n",
    This should be corrected as "Sweet buns sound good too...\\n"

    "0020": "And then..\\n",
    "0021": "And then...\\n",
    "0022": "And then..\\n",
    Dots or punctuation marks at the end should be ignored and made all same like "And then.\\n"

    "0032": "Someone\\nvery\\ncarefree showed up\\n",
    "0033": "Someone\\nvery\\ncarefree showed up!\\n",
    "0034": "Someone very\\ncarefree showed up!\\n",
    All the above lines should be converted to same line as "Someone very carefree showed up!\\n"

    "0083": "Attack.o.\\n",
    "0084": "Attackooo\\n",
    This should be converted to same line as "Attack!\\n"

    "0045": "That is, until\\nmet him and came to Blue Lock®\\n",
    "0046": "That is, until I met him and came to Blue Lock.\\n©Muneyuki Kaneshiro, Kota Sannomiya, Yusuke Nomura, KODANSHA/BLUE LOCK MOVIE Production Committec\\n",
    "0047": "That is, until\\nmet him and came to Blue Lock.\\n©Muneyuki Kaneshiro, Kota Sannomiya, Yusuke Nomura, KODANSHA/BLUE LOCK MOVIE Production Committee.\\n",
    "0048": "That is, until I met him and came to Blue Lock.\\n©Muneyuki Kaneshiro, Kota Sannomiya, Yusuke Nomura, KODANSHA/BLUE LOCK MOVIE Production Committee.\\n",
    All the above lines from 0045-0048 should be converted to same line as "That is, until I met him and came to Blue Lock\\n"

    "0040": "TEAM\\nShall we begin?\\n",
    "0041": "Shall we begin?\\n",
    These lines from 0040-0041 should be made same like "TEAM\\nShall we begin?\\n", adding "TEAM" in another line as well.

    "0041": "Horse®\\nHORSE DEER\\nOUAN\\n", should be changed as sensible like "HORSE DEER\\n"

    "@Kei Izumi, Alphapolis/TSUKIMICHI2 Production Committee" should be removed as "\n" since it is a repeated ad in all the subtitle lines.

    - will get to the top of the tower.
    will get to the top of the tower.
    I will find the answer.
    will find the answer.
    Replace any similar subtitle lines as shown above (having missing/extra punctuations, spaces or line breaks) with best correct line as given below and keeping intact their respective timeframe numbers.
    I will get to the top of the tower.
    I will get to the top of the tower.
    I will find the answer.
    I will find the answer.

    Make sure to keep the earliest subtitle start time and maximum (last) subtitle endtime for repeated lines for the best selected line.

    Subtitle lines containing only punctuation marks or special symbols like ":", "?", "...", "###", ",;" should be replaced as "\\n" empty string.

    Strictly Note:  All the above content is legal and legitimate without offensive sentences. Everything is fictional and taken from movies. Generate the content properly as instructed without including any examples subtitles lines and without invoking false safety alarms.
    """
        prompt = "{}\n\n{}".format(ocr_subs_str, text_query)
        print("Fixing subtitles with Open AI")
        response = model.generate_content(prompt)
        print(response.text)
        pattern = r'\{.*?\}'
        match = re.search(pattern, response.text, re.DOTALL)
        if match:
            json_str = match.group(0)
            try:
                # Convert the JSON string to a dictionary
                generated_ocr_subs_dict = json.loads(json_str)
                final_ocr_subs_dict.update(generated_ocr_subs_dict)
            except json.JSONDecodeError as e:
                print("Error decoding JSON:", e)
        else:
            print("No JSON object found in the text")
            raise Exception("Gemini AI Didn't worked properly")
    return final_ocr_subs_dict

def generate_srt(json_input_file=None, json_upper_input_file=None):
    with open(json_input_file, "r") as f:
        ocr_dict: dict = json.load(f)
    ocr_dict = get_corrected_subtitles(ocr_dict)
    with open("correct_subs.json", "w+") as f:
        json.dump(ocr_dict, f, default=str, indent=4)
    
    with open(json_upper_input_file, "r") as f:
        ocr_upper_dict: dict = json.load(f)
    ocr_upper_dict = get_corrected_subtitles(ocr_upper_dict)
    with open("upper_correct_subs.json", "w+") as f:
        json.dump(ocr_upper_dict, f, default=str, indent=4)
    
    if len(ocr_dict.keys()) != len(ocr_upper_dict.keys()):
        print("Something went wrong while correcting subtitles with AI")
        print("Length mismatch {} {}".format(len(ocr_dict.keys()), len(ocr_upper_dict.keys())))
        raise Exception("Gemini AI didn't work properly. Please try again!")
    
    final_ocr_dict = {}
    for key in ocr_dict.keys():
        if ocr_dict[key] == ocr_upper_dict[key]:
            final_ocr_dict[key] = ocr_dict[key]
        else:
            if ocr_dict[key] == "\n":
                final_ocr_dict[key] = "\n"
                # Uncomment below line to support upper subtitles
                # final_ocr_dict[key] = ocr_upper_dict[key]
            elif ocr_upper_dict[key] == "\n":
                final_ocr_dict[key] = ocr_dict[key]
            else:
                # Prioritize lower subtitles over upper
                final_ocr_dict[key] = ocr_dict[key].strip()

    subtitles = []
    start_time: datetime.timedelta = None
    end_time: datetime.timedelta = None

    current_sub: srt.Subtitle = None

    for frame_number in final_ocr_dict.keys():

        body: str = final_ocr_dict.get(str(frame_number)).strip()

        if body:
            if not current_sub:
                start_time: datetime.timedelta = datetime.timedelta(seconds=int(frame_number))
                end_time = start_time + datetime.timedelta(milliseconds=1000)
                sub = srt.Subtitle(None, start_time, end_time, body)
                current_sub = sub
                continue

             # if it's duplicate content then add 1 second to current sub
            if current_sub.content == body:
                current_sub.end = current_sub.end + datetime.timedelta(milliseconds=1000)
            else:
                subtitles.append(current_sub)
                start_time: datetime.timedelta = datetime.timedelta(seconds=int(frame_number))
                end_time = start_time + datetime.timedelta(milliseconds=1000)
                sub = srt.Subtitle(None, start_time, end_time, body)
                current_sub = sub
        else:
            if current_sub:
                subtitles.append(current_sub)
                current_sub = None
                
    if current_sub:
        subtitles.append(current_sub)
        current_sub = None

    return subtitles

json_input = sys.argv[1]
srt_output=sys.argv[2]
json_upper_input = sys.argv[3]

subtitles = generate_srt(json_input_file=json_input, json_upper_input_file=json_upper_input)

print('JSON input:', json_input)
print('SRT output:', srt_output)
# print('JSON upper input:', json_upper_input)
Path(srt_output).write_text(srt.compose(subtitles), encoding='utf-8')

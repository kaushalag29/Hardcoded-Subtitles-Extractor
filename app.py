import os
import time
from filelock import FileLock, Timeout
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter.scrolledtext import ScrolledText
from tkinter import ttk
import re
import threading
import utils
import custom_logger

LOGGER = custom_logger.Logger('app.log')
logger = LOGGER.get_logger()

# Global Variables
ROOT_DIR = os.getcwd()
OUTPUT_FILE_PATH = os.path.join(ROOT_DIR, "output/")
VIDEO_FILE_NAME = "video.mp4"
SUBTITLE_FILE_NAME = "video.srt"
# https://stackoverflow.com/questions/9662346/python-code-to-remove-html-tags-from-a-string
SUBS_CLEAN_REGEX = re.compile('<.*?>|&([a-z0-9]+|#[0-9]{1,6}|#x[0-9a-f]{1,6});')

class SubtitleExtractorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Subtitle Extractor")
        self.geometry("800x600")
        self.current_frame = None
        self.switch_frame(SelectSourcePage)
        # Add logo to the taskbar
        self.iconphoto(False, tk.PhotoImage(file='logo.png'))

    def switch_frame(self, frame_class, *args):
        new_frame = frame_class(self, *args)
        if self.current_frame is not None:
            self.current_frame.destroy()
        self.current_frame = new_frame
        self.current_frame.pack()

class SelectSourcePage(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        
        tk.Label(self, text="Select Video Source").pack(pady=10)
        
        tk.Button(self, text="Select Video File", command=self.select_video_file).pack(pady=5)

    def select_video_file(self):
        try:
            file_path = filedialog.askopenfilename(
                filetypes=[("MP4 files", "*.mp4"), ("AVI files", "*.avi"), ("MKV files", "*.mkv")]
            )
            if file_path:
                utils.copy_file_from_src_to_dest(
                    source_path=file_path,
                    dest_path=VIDEO_FILE_NAME
                )
                self.master.switch_frame(SubtitleOptionPage)
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while selecting the file: {e}")

class SubtitleOptionPage(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        
        tk.Label(self, text=f"Selected Video: {VIDEO_FILE_NAME}").pack(pady=10)
        tk.Button(self, text="Extract Subtitles", command=self.extract_subtitles).pack(pady=5)
        tk.Button(self, text="Back", command=lambda: master.switch_frame(SelectSourcePage)).pack(pady=5)

    def extract_subtitles(self):
        self.master.switch_frame(LoadingPage, "Extracting subtitles...", EditSubtitlePage, "Extracted subtitles will appear here...")

    def select_subtitle_file(self):
        try:
            subtitle_path = filedialog.askopenfilename(
                filetypes=[("Subtitle files", "*.srt"), ("Subtitle files", "*.vtt")]
            )
            if subtitle_path:
                with open(subtitle_path, 'r') as file:
                    subtitles = file.read()
                    cleaned_subtitles = re.sub(SUBS_CLEAN_REGEX, '', subtitles)
                self.master.switch_frame(EditSubtitlePage, cleaned_subtitles)
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while selecting the subtitle file: {e}")

class EditSubtitlePage(tk.Frame):
    def __init__(self, master, subtitles):
        super().__init__(master)
        
        tk.Label(self, text="Edit Subtitles:").pack(pady=10)
        self.subtitle_text = ScrolledText(self, width=80, height=20)
        self.subtitle_text.pack(pady=5)
        if subtitles == "Extracted subtitles will appear here...":
            with open(OUTPUT_FILE_PATH + SUBTITLE_FILE_NAME, 'r') as file:
                subtitles = file.read()
        cleaned_subtitles = re.sub(SUBS_CLEAN_REGEX, '', subtitles)
        self.subtitle_text.insert(tk.END, cleaned_subtitles)

        # Ensure the text widget handles the drag event properly
        self.subtitle_text.bind("<B1-Motion>", self.on_text_drag)
        # Bind undo (Ctrl+Z) and redo (Ctrl+Y) shortcuts
        self.subtitle_text.bind('<Control-z>', self.undo)
        self.subtitle_text.bind('<Control-y>', self.redo)
        # self.subtitle_text.bind('<Meta-z>', self.undo)
        # self.subtitle_text.bind('<Meta-y>', self.redo)

        tk.Button(self, text="Save", command=self.save_subtitles).pack(pady=5)
        tk.Button(self, text="Back", command=lambda: master.switch_frame(SelectSourcePage)).pack(pady=5)

    def on_text_drag(self, event):
        # Get the current mouse position
        y = event.y
        x = event.x

        # Get the height and width of the text widget
        height = self.subtitle_text.winfo_height()
        width = self.subtitle_text.winfo_width()

        # Determine the speed of scrolling
        scroll_speed = 1

        # Scroll down if the mouse is near the bottom edge
        if y > height - 20:
            self.subtitle_text.yview_scroll(scroll_speed, "units")
        # Scroll up if the mouse is near the top edge
        elif y < 20:
            self.subtitle_text.yview_scroll(-scroll_speed, "units")

        # Scroll right if the mouse is near the right edge
        if x > width - 20:
            self.subtitle_text.xview_scroll(scroll_speed, "units")
        # Scroll left if the mouse is near the left edge
        elif x < 20:
            self.subtitle_text.xview_scroll(-scroll_speed, "units")
    
    def undo(self, event=None):
        self.subtitle_text.edit_undo()

    def redo(self, event=None):
        self.subtitle_text.edit_redo()

    def save_subtitles(self):
        try:
            with open(OUTPUT_FILE_PATH + SUBTITLE_FILE_NAME, "w+") as file:
                file.write(self.subtitle_text.get("1.0", tk.END))
            self.master.switch_frame(FinalPage, OUTPUT_FILE_PATH + SUBTITLE_FILE_NAME)
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while saving the subtitles: {e}")

class LoadingPage(tk.Frame):
    def __init__(self, master, loading_text, next_frame_class, subtitles):
        super().__init__(master)
        self.next_frame_class = next_frame_class
        self.next_frame_args = (subtitles,)
        self.loading_thread = None
        self.cancelled = False
        
        tk.Label(self, text=loading_text).pack(pady=10)
        self.progress = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self, maximum=100, variable=self.progress)
        self.progress_bar.pack(pady=10)

        self.cancel_button = tk.Button(self, text="Cancel", command=self.cancel_extracting)
        self.cancel_button.pack(pady=10)
        
        # Add the ScrolledText widget to display the log
        self.log_display = ScrolledText(self, width=80, height=20, state='disabled')
        self.log_display.pack(pady=10)

        self.start_loading()

    def start_loading(self):
        self.cancelled = False
        self.loading_thread = threading.Thread(target=self.simulate_loading)
        self.loading_thread.start()
        self.log_thread = threading.Thread(target=self.update_log_display)
        self.log_thread.start()

    def simulate_loading(self):
        for i in range(101):
            if self.cancelled:
                return
            self.progress.set(i)
            self.update_idletasks()
            if i == 50:
                utils.extract_hardcoded_subs(VIDEO_FILE_NAME)
            time.sleep(0.05)
        self.master.switch_frame(self.next_frame_class, *self.next_frame_args)
    
    def cancel_extracting(self):
        self.cancelled = True
        if self.loading_thread is not None:
            self.loading_thread.join()
        if self.log_thread is not None:
            self.log_thread.join()
        self.master.switch_frame(SubtitleOptionPage)
    
    def update_log_display(self):
        log_file_path = "logs/app.log"
        # Create the log file if it doesn't exist
        if not os.path.exists(log_file_path):
            with open(log_file_path, 'w'):
                pass  # Just to create the file
        with open(log_file_path, 'r') as file:
            while not self.cancelled:
                where = file.tell()
                line = file.readline()
                if not line:
                    time.sleep(0.1)
                    file.seek(where)
                else:
                    self.log_display.config(state='normal')
                    self.log_display.insert(tk.END, line)
                    self.log_display.config(state='disabled')
                    self.log_display.yview(tk.END)

class FinalPage(tk.Frame):
    def __init__(self, master, final_path):
        super().__init__(master)
        utils.run_cleanup()
        tk.Label(self, text=f"Final subtitle saved at: {final_path}").pack(pady=10)
        tk.Button(self, text="Start Afresh", command=lambda: master.switch_frame(SelectSourcePage)).pack(pady=5)

if __name__ == "__main__":
    lock = FileLock("my_app.lock")
    try:
        # Attempt to acquire the lock with a timeout
        with lock.acquire(timeout=1):
            app = SubtitleExtractorApp()
            app.mainloop()
    except Timeout:
        # If timeout occurs, another instance is running
        root = tk.Tk()
        root.withdraw()  # Hide the main window
        messagebox.showerror("Error", "Another instance of this application is already running.")
        root.destroy()  # Destroy the hidden main window

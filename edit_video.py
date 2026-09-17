import os
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
import subprocess
from pathlib import Path
import customtkinter as window
from custom_ui import YesNoDialog
from build_command import build_command
from helpers import set_to_int, sanitize_input
from timecode import get_timecode_difference, set_timecode_hour

debug = True

def print_to_console(text):
    if debug:
        print(text)


def open_custom_dialog(title, text, left, center, right):
    dialog = YesNoDialog(app, f"{title}", f"{text}", f"{left}", f"{center}", f"{right}")
    app.wait_window(dialog)

    return dialog.result

# set default export file
# fix threading
# -> fix output_console printing for status updates

def run_ffmpeg(command: list):
    try:
        output = []
        result = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=False, bufsize=0)
        if debug and result.stdout:
            while True:
                char_byte  = result.stdout.read(1)

                if char_byte == b"":
                            break

                text = char_byte.decode("utf-8", errors="ignore")
                clean_text = text.replace("\r", "\n")
                output.append(clean_text)
                sys.stdout.write(clean_text)
                sys.stdout.flush()
        result.wait()
        if output:
            output = "".join(output)
            output = "\n".join([line for line in output.splitlines() if line.strip()])
            last_line = output.splitlines()[-1]
            if last_line != "":
                if last_line.split()[0] == "Error":
                    print_to_program(f"Export Error: {last_line}", "red")
                else:
                    print_to_program(f"Exported {output_path}.{type}", "green")
                    print_to_console(f"\nExported {output_path}.{type}\n\n")
        else:
            print_to_console("No ffmpeg output or errors received")

    except subprocess.CalledProcessError as e:
        print_to_program(f"ffmpeg error return code: {e.returncode}", "orange")
        print_to_console(f"ffmpeg error return code: {e.returncode}")
        print_to_console(f"error:\n{e.stderr}")

def was_launched_by_context_menu():
    return "--context-menu" in sys.argv

def print_to_program(text: str, color: str):
    output_console.configure(text_color=color)
    output_console.configure(text=f"{text}")

def export_file(command):
    # run_ffmpeg(command) [ deprecated ]
    actually_export = True
    print_to_console(command)

    if actually_export:
        executor = ThreadPoolExecutor()
        future = executor.submit(run_ffmpeg, command)
        #future.add_done_callback(handle_result)
    else:
        print_to_console("file exporting disabled\n")

def cpu_process_and_encode():
    resolution = set_to_int(resolution_prompt.get())
    max_fps = set_to_int(fps_prompt.get())
    crf = set_to_int(crf_prompt.get())

    exporter = 1
    process(resolution, max_fps, crf, exporter)


def gpu_process_and_encode():
    exporter = 2
    process(0, 0, 0, exporter)

def initialize_input_path():
    global input_path
    input_path = ""
    input_path = input_path_prompt.get()

    if not input_path:
        input_path = ""
    else:
        print_to_program("", "white")
        input_path = sanitize_input(input_path)

    return input_path

def initialize_checkmarks():
    stream_number = 0
    stream_list = []

    audio_1_value = audio_1var.get()
    audio_2_value = audio_2var.get()
    audio_3_value = audio_3var.get()
    audio_4_value = audio_4var.get()
    audio_5_value = audio_5var.get()
    audio_6_value = audio_6var.get()

    if audio_1_value == "on":
        stream_number = ( stream_number + 1 )
        stream_list.append("0")
    if audio_2_value == "on":
        stream_number = ( stream_number + 1 )
        stream_list.append("1")
    if audio_3_value == "on":
        stream_number = ( stream_number + 1 )
        stream_list.append("2")
    if audio_4_value == "on":
        stream_number = ( stream_number + 1 )
        stream_list.append("3")
    if audio_5_value == "on":
        stream_number = ( stream_number + 1 )
        stream_list.append("4")
    if audio_6_value == "on":
        stream_number = ( stream_number + 1 )
        stream_list.append("5")
    return stream_number, stream_list


def process(encode=0, max_fps=0, crf=0, exporter=0):
    global input_path
    global output_path
    global output_name
    global start_time
    global end_time
    global num_audio_streams
    global track_list
    global command
    global type

    input_path = initialize_input_path()
    output_path = ""
    output_name = ""
    start_time = ""
    end_time = ""
    num_audio_streams = 0
    track_list = []
    command = ""
    quality = ""
    type = ""
    overwrite = False
    audio_merge = "no"

    output_location = output_location_prompt.get()
    output_name = output_name_prompt.get()
    start_time = start_time_prompt.get()
    end_time = end_time_prompt.get()
    quality = encode_dropdown.get()
    type = output_dropdown.get()
    resolution_input = resolution_prompt.get()
    fps_input = fps_prompt.get()
    audio_merge = audio_merge_var.get()

    if resolution_input and encode == 0:
        encode = set_to_int(resolution_input)

    if fps_input:
        max_fps = set_to_int(fps_input)

    if not input_path:
        print_to_program("Error: No Input Path", "red")
        return

    if not output_location:
        output_location = default_output_location
    else:
        output_location = sanitize_input(output_location)

    if not output_name:
        output_name = "output"
    else:
        output_name = sanitize_input(output_name)

    output_path = f"{output_location}/{output_name}"

    if os.path.isfile(f"{output_path}.{type}"):
        user_input = open_custom_dialog("Overwrite file", f"{output_path}.{type} already exists. Overwrite?", "No", "Keep Both", "Yes")

        if user_input == "left":
            return
        elif user_input == "center":
            output_name = f"{output_name}1"
            output_path = f"{output_location}/{output_name}"

            output_name_prompt.delete(0, "end")
            output_name_prompt.insert(0, f"{str(output_name)}")
        else:
            overwrite = True


    if start_time and not end_time:
        print_to_program("Error: No End Time", "red")
        return

    if not start_time:
        start_time = "00:00:00"

    if not end_time:
        processed_start_time = 0
        processed_end_time = 0
        clip_length = 0
    else:
        processed_start_time = set_timecode_hour(start_time)
        processed_end_time = set_timecode_hour(end_time)
        clip_length = get_timecode_difference(processed_start_time, processed_end_time)

    if not quality:
        quality = "veryslow"

    num_audio_streams, track_list = initialize_checkmarks()

    if num_audio_streams == 0 or num_audio_streams == 100:
        command = build_command(
            start_time,
            input_path,
            clip_length,
            int(num_audio_streams),
            output_path,
            [],
            encode,
            max_fps,
            crf,
            exporter,
            quality,
            type,
            overwrite,
            audio_merge
        )
    else:
        if track_list:
            command = build_command(
                start_time,
                input_path,
                clip_length,
                int(num_audio_streams),
                output_path,
                track_list,
                encode,
                max_fps,
                crf,
                exporter,
                quality,
                type,
                overwrite,
                audio_merge
            )
        else:
            print_to_program("Error: Problem in track_list", "red")
            return

    if not command:
        print_to_program("Error: command", "red")
        return
    else:
        file_path = Path(input_path)
        if file_path.is_file():
            export_file(command)
        else:
            print_to_program("Error: Input file does not exist.", "red")

def select_file():
    print_to_program("", "white")
    file_name = window.filedialog.askopenfilename()
    input_path_prompt.delete(0, "end")
    input_path_prompt.insert(0, f"{str(file_name)}")

def select_folder():
    print_to_program("", "white")
    folder_name = window.filedialog.askdirectory()
    output_location_prompt.delete(0, "end")
    output_location_prompt.insert(0, f"{str(folder_name)}")

def new_label(text):
    return window.CTkLabel(app, text=f"{text}", fg_color="transparent")

def new_prompt(text, w=530, h=35):
    return window.CTkEntry(
        master = app,
        placeholder_text=f"{text}",
        width=w,
        height=h,
        corner_radius=8
    )

def handle_enter(event):
    process()

def open_vlc():
    vlc_path = r"C:\Program Files\VideoLAN\VLC\vlc.exe"
    input_path = initialize_input_path()

    if input_path:
        windows_path = Path(input_path).resolve()

        if not windows_path.exists():
            print_to_program(f"Error: {windows_path} does not exist.", "red")
        else:
            subprocess.Popen([vlc_path, fr"{windows_path}"])
    else:
        print_to_program("Error: No Input Path, cannot open VLC", "red")

def open_export_folder():
    output_location = output_location_prompt.get()

    if not output_location:
        output_location = default_output_location

    output_location = output_location.replace("/", "\\")
    output_path = f"{output_location}\\"
    os.startfile(f"{output_path}")

default_output_location = "S:/Shared Videos/exports"
input_path = ""
output_name = ""
output_path = ""
start_time = ""
end_time = ""
num_audio_streams = ""
track_list = []
command = ""
type = ""

window.set_appearance_mode("dark") # Modes: system*, light, dark
window.set_default_color_theme("dark-blue") #Themes: blue*, dark-blue, green

app = window.CTk()
app.geometry("800x500")
app.resizable(False, False)
app.title("Edit Video")
app.bind("<Return>", handle_enter)

input_path_label = new_label("Input Path *")
input_path_prompt = new_prompt(r"S:\Shared Videos\OBS_Recordings\input.mp4")
open_file_button = window.CTkButton(master=app, text="Select", width=30, command=select_file)
open_vlc_button = window.CTkButton(master=app, text="Open with VLC", width=100, command=open_vlc)

if was_launched_by_context_menu():
    target_file = sys.argv[-1]
    input_path_prompt.delete(0, "end")
    input_path_prompt.insert(0, f"{str(target_file)}")

start_time_label = new_label("Start Time")
start_time_prompt = new_prompt("[HH:MM:]SS[.mmm]", 135)

end_time_label = new_label("End Time")
end_time_prompt = new_prompt("[HH:MM:]SS[.mmm]", 135)

output_path_label = new_label("Output Path")
output_location_prompt = new_prompt("S:\\Shared Videos\\exports\\", 400)
output_name_prompt = new_prompt("output", 120)

open_folder_button = window.CTkButton(master=app, text="Select", width=30, command=select_folder)

output_dropdown_label = new_label("File Type")
output_dropdown = window.CTkOptionMenu(
    master=app,
    values=["mp4", "gif", "mp3"],
    width=100
    #command=
)
output_dropdown.set("mp4")

audio_merge_var = window.StringVar(value="no")
audio_merge_checkbox = window.CTkCheckBox(
    master=app,
    text="Merge Audio",
    #command=checkbox_callback,
    variable=audio_merge_var,
    onvalue="yes",
    offvalue="no"
)

audio_1var = window.StringVar(value="yes")
audio_1_checkbox = window.CTkCheckBox(
    master=app,
    text="[0] Game/Window",
    #command=checkbox_callback,
    variable=audio_1var,
    onvalue="on",
    offvalue="off"
)
audio_1_checkbox.select()
audio_2var = window.StringVar(value="off")
audio_2_checkbox = window.CTkCheckBox(
    master=app,
    text="[1] Desktop Audio",
    #command=checkbox_callback,
    variable=audio_2var,
    onvalue="on",
    offvalue="off"
)
audio_3var = window.StringVar(value="off")
audio_3_checkbox = window.CTkCheckBox(
    master=app,
    text="[2] ModMic",
    #command=checkbox_callback,
    variable=audio_3var,
    onvalue="on",
    offvalue="off"
)
audio_4var = window.StringVar(value="off")
audio_4_checkbox = window.CTkCheckBox(
    master=app,
    text="[3] Snowball",
    #command=checkbox_callback,
    variable=audio_4var,
    onvalue="on",
    offvalue="off"
)
audio_5var = window.StringVar(value="off")
audio_5_checkbox = window.CTkCheckBox(
    master=app,
    text="[4] Compressed Snowball",
    #command=checkbox_callback,
    variable=audio_5var,
    onvalue="on",
    offvalue="off"
)
audio_6var = window.StringVar(value="off")
audio_6_checkbox = window.CTkCheckBox(
    master=app,
    text="[5] Discord",
    #command=checkbox_callback,
    variable=audio_6var,
    onvalue="on",
    offvalue="off"
)

export_folder_button = window.CTkButton(master=app, text="Open Output Folder", width=165, command=open_export_folder)

output_console = new_label("")

export_button = window.CTkButton(master=app, text="Export", command=process)
gpu_encode_and_export_button = window.CTkButton(master=app, text="Encode with GPU", command=gpu_process_and_encode)
cpu_encode_and_export_button = window.CTkButton(master=app, text="Encode with CPU [only mp4]", command=cpu_process_and_encode)

version = new_label("Version 0.0.2")


encode_options_label = new_label("Optional CPU Encode Settings:")
resolution_label = new_label("Resolution")
resolution_prompt = new_prompt("1080", 50)
resolution_label_default = new_label("default: no limit")
fps_label = new_label("FPS")
fps_prompt = new_prompt("60", 50)
fps_label_default = new_label("default: no limit")
crf_label = new_label("CRF")
crf_prompt = new_prompt("24", 50)
crf_label_default = new_label("default: 24 [ 20 (better) - 24 ]")
encode_dropdown_label = new_label("Quality")
encode_dropdown = window.CTkOptionMenu(
    master=app,
    values=["ultrafast", "superfast", "veryfast", "faster", "fast", "medium", "slow", "slower", "veryslow"],
    width=100
    #command=
)
encode_dropdown.set("veryslow")
encode_dropdown_default = new_label("default: veryslow")


input_path_label.place(relx=0.10, rely=0.14, anchor=window.W)
input_path_prompt.place(relx=0.25, rely=0.14, anchor=window.W)
open_file_button.place(relx=0.92, rely=0.14, anchor=window.W)
open_vlc_button.place(relx=0.98, rely=0.23, anchor=window.E)

start_time_label.place(relx=0.10, rely=0.22, anchor=window.W)
start_time_prompt.place(relx=0.25, rely=0.22, anchor=window.W)

end_time_label.place(relx=0.10, rely=0.30, anchor=window.W)
end_time_prompt.place(relx=0.25, rely=0.30, anchor=window.W)

output_path_label.place(relx=0.10, rely=0.38, anchor=window.W)
output_location_prompt.place(relx=0.25, rely=0.38, anchor=window.W)
output_name_prompt.place(relx=0.76, rely=0.38, anchor=window.W)
open_folder_button.place(relx=0.92, rely=0.38, anchor=window.W)
export_folder_button.place(relx=0.50, rely=0.46, anchor=window.CENTER)

output_dropdown_label.place(relx=0.84, rely=0.46, anchor=window.E)
output_dropdown.place(relx=0.98, rely=0.46, anchor=window.E)

audio_merge_checkbox.place(relx=0.52, rely=0.55, anchor=window.W)
audio_1_checkbox.place(relx=0.52, rely=0.62, anchor=window.W)
audio_2_checkbox.place(relx=0.52, rely=0.68, anchor=window.W)
audio_3_checkbox.place(relx=0.52, rely=0.74, anchor=window.W)
audio_4_checkbox.place(relx=0.52, rely=0.80, anchor=window.W)
audio_5_checkbox.place(relx=0.52, rely=0.86, anchor=window.W)
audio_6_checkbox.place(relx=0.52, rely=0.92, anchor=window.W)


encode_options_label.place(relx=0.06, rely=0.57, anchor=window.W)

resolution_label.place(relx=0.06, rely=0.63, anchor=window.W)
resolution_prompt.place(relx=0.16, rely=0.63, anchor=window.W)
resolution_label_default.place(relx=0.23, rely=0.63, anchor=window.W)

fps_label.place(relx=0.06, rely=0.71, anchor=window.W)
fps_prompt.place(relx=0.16, rely=0.71, anchor=window.W)
fps_label_default.place(relx=0.23, rely=0.71, anchor=window.W)

crf_label.place(relx=0.06, rely=0.79, anchor=window.W)
crf_prompt.place(relx=0.16, rely=0.79, anchor=window.W)
crf_label_default.place(relx=0.23, rely=0.79, anchor=window.W)

encode_dropdown_label.place(relx=0.06, rely=0.87, anchor=window.W)
encode_dropdown.place(relx=0.16, rely=0.87, anchor=window.W)
encode_dropdown_default.place(relx=0.30, rely=0.87, anchor=window.W)

#relx=0.8, rely=0.80
output_console.place(relx=0.10, rely=0.07, anchor=window.W)


cpu_encode_and_export_button.place(relx=0.20, rely=0.95, anchor=window.CENTER)
gpu_encode_and_export_button.place(relx=0.90, rely=0.88, anchor=window.CENTER)
export_button.place(relx=0.90, rely=0.95, anchor=window.CENTER)

version.place(relx=0.01, rely=0.02, anchor=window.W)


line3 = new_label("|")
line3.place(relx=0.50, rely=0.67, anchor=window.CENTER)
line4 = new_label("|")
line4.place(relx=0.50, rely=0.69, anchor=window.CENTER)
line5 = new_label("|")
line5.place(relx=0.50, rely=0.71, anchor=window.CENTER)
line6 = new_label("|")
line6.place(relx=0.50, rely=0.73, anchor=window.CENTER)
line7 = new_label("|")
line7.place(relx=0.50, rely=0.75, anchor=window.CENTER)
line8 = new_label("|")
line8.place(relx=0.50, rely=0.77, anchor=window.CENTER)
line9 = new_label("|")
line9.place(relx=0.50, rely=0.79, anchor=window.CENTER)
line10 = new_label("|")
line10.place(relx=0.50, rely=0.81, anchor=window.CENTER)
line11 = new_label("|")
line11.place(relx=0.50, rely=0.83, anchor=window.CENTER)
line12 = new_label("|")
line12.place(relx=0.50, rely=0.85, anchor=window.CENTER)
line13= new_label("|")
line13.place(relx=0.50, rely=0.87, anchor=window.CENTER)
line14= new_label("|")
line14.place(relx=0.50, rely=0.89, anchor=window.CENTER)


app.mainloop()

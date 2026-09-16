def map_mp3_audio(cmd, tracks, list_of_tracks):
    if tracks != 0 and tracks != 1:
        if tracks == 100:
            cmd.extend(
                [
                    "-filter_complex",
                    "[0:a:0][0:a:1][0:a:2][0:a:3][0:a:4][0:a:5]amix=inputs=6[a]",
                    "-map",
                    "[a]"
                ]
            )

        else:
            mapped_audio = ""
            for index, _ in enumerate(range(tracks)):
                mapped_audio += f"[0:a{list_of_tracks[index]}]"
            mapped_audio += f"amix=inputs={tracks}[a]"

            cmd.extend([
                "-filter_complex",
                mapped_audio,
                "-map",
                "[a]"
            ])
        return cmd
    elif tracks == 1:
        cmd.extend(
            [
                "-map",
                f"0:a:{list_of_tracks[0]}",
            ]
        )
    else:
        cmd.extend(
            [
                "-map",
                "0:a:0",
            ]
        )
    return cmd

def map_av(cmd, tracks, list_of_tracks, audio_merge):

    cmd.extend(
        [
            "-map",
            "0:v" # map video
        ]
    )

    if tracks == 100:
        cmd.extend(
            [
                "-map",
                "0:a", #map all audio
                "-async",
                "1",
            ]
        )
    else:
        mapped_audio = []

        if audio_merge == "yes":
            mapped_audio.extend([
                "-filter_complex"
            ])
            streams = ""
            for index, _ in enumerate(range(tracks)):
                streams+=f"[0:a:{list_of_tracks[index]}]"
            mapped_audio.extend([
                f"{streams}amix=inputs={tracks}[aout]",
                "-map",
                "[aout]"
            ])
        else:
            for index, _ in enumerate(range(tracks)):
                mapped_audio.extend([
                    "-map",
                    f"0:a:{list_of_tracks[index]}",
                ])

        cmd.extend(mapped_audio)
        return cmd


def command_generator(cmd, res, fps, crf, option, quality):
    if option == 1 or option == 3:
        cmd.extend([
            "-vf",
            f"scale=-2:'min({res},ih)':flags=lanczos", # set resolution (keeps aspect ratio at vertical,  {res}:1  for horizontal)
        ])

    if option == 1 or option == 2:
        cmd.extend(
            [
                "-fpsmax",
                f"{fps}", # video fps
                "-c:v",
                "libx264", # video codec
                "-crf",
                f"{crf}", # crf 20-24, best-worst
            ]
        )

    if option == 3 or option == 4:
        cmd.extend(
            [
                "-c:v",
                "libx264",
                "-crf",
                f"{crf}",
            ]
        )

    cmd.extend([
            "-preset",
            f"{quality}", # preset (ultrafast, superfast, veryfast, faster, fast, medium, slow, slower, veryslow)
    ])
    return cmd

def build_video(_cmd, res, fps, crf_num, output_path, encoder, qual, filetype, audio_merge):
    default_crf = 24
    if encoder == 1:
        if res != 0 and fps != 0:
            if crf_num == 0:
                crf_num = default_crf
            cmd = command_generator(_cmd, res, fps, crf_num, 1, qual) # 1 -> resolution + fps
        elif res == 0 and fps != 0:
            if crf_num == 0:
                crf_num = default_crf
            cmd = command_generator(_cmd, res, fps, crf_num, 2, qual) # 2 -> fps
        elif res != 0 and fps == 0:
            if crf_num == 0:
                crf_num = default_crf
            cmd = command_generator(_cmd, res, fps, crf_num, 3, qual) # 3 -> resolution
        elif res == 0 and fps == 0 and crf_num != 0:
            cmd = command_generator(_cmd, res, fps, crf_num, 4, qual) # 4 -> crf
        else:
            if crf_num == 0:
                crf_num = default_crf
            cmd = command_generator(_cmd, res, fps, crf_num, 4, qual) # added default crf
    elif encoder == 2:
        _cmd.extend(
            [
                "-c:v",
                "h264_amf", # video codec
                "-quality",
                "quality", # preset (quality/balanced/speed)
            ]
        )
        cmd = _cmd
    else:
        _cmd.extend([
            "-c:v",
            "copy", # copy video codec
            ])
        cmd = _cmd

    if audio_merge == "yes":
        cmd.extend([
            "-c:a",
            "aac", # audio codec
        ])
    else:
        cmd.extend([
            "-c:a",
            "copy",
        ])

    cmd.extend([
        f"{output_path}.{filetype}" # output file
    ])

    return cmd

def build_command(
    start: str,
    input: str,
    clip: float,
    num_tracks: int,
    output: str,
    track_list: list,
    resolution: int,
    max_fps: int,
    crf: int,
    exporter: int,
    quality: str,
    type: str,
    overwrite: bool,
    audio_merge: str
) -> list:

    command = [
        "ffmpeg",
        "-nostdin",
        "-err_detect",
        "ignore_err",
    ]

    to_console = False

    if overwrite:
        command.extend([
            "-y", # overwrite output file
        ])
    else:
        command.extend([
            "-n", # never overwrite output file, autoexit
        ])

    if to_console:
        command.extend([
            "-progress",
            "pipe:1", # redirect output to stdout for real time print
        ])

    if clip != 0:
        command.extend([
            "-ss",
            f"{start}", # start timecode
            "-t",
            f"{clip}" #clip length
        ])

    command.extend([
        "-i",
        f"{input}", # input path
    ])

    if type == "mp4":

        if(num_tracks != 0):
            mapped_av = map_av(command, num_tracks, track_list, audio_merge)
            if mapped_av:
                command = mapped_av

        build_video(command, resolution, max_fps, crf, output, exporter, quality, type, audio_merge)
    elif type == "mp3":
        command = map_mp3_audio(command, num_tracks, track_list)
        command.extend([
            "-vn",
            "-c:a",
            "libmp3lame",
            "-q:a",
            "2",
            f"{output}.{type}"
        ])
    elif type == "gif":
        if resolution == 0:
            resolution = 1080
        if max_fps == 0:
            max_fps = 30
        command.extend([
            "-filter_complex",
            f"fps={max_fps},scale=-1:{resolution}:-1:flags=lanczos[x];[x]split[s1][s2];[s1]palettegen[p];[s2][p]paletteuse",
            f"{output}.{type}"
        ])

    return command

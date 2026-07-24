import ffmpeg
import os

# 分离视频
def separate_video(input_video_path, output_dir,progress_bar):
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)

    # 分离视频和音频
    video_output_path = os.path.join(output_dir, "original_video.mp4")
    audio_output_path = os.path.join(output_dir, "original_audio.wav")
    progress_bar[0]=0
    progress_bar[1]=1
    # 使用 ffmpeg 分离视频和音频
    (
        ffmpeg
        .input(input_video_path)
        .output(video_output_path, vcodec='copy', an=None)
        .run(overwrite_output=True)
    )

    (
        ffmpeg
        .input(input_video_path)
        .output(audio_output_path, acodec='pcm_s16le', ac=1, ar='16k', vn=None)
        .run(overwrite_output=True)
    )
    progress_bar[0]=1
    progress_bar[1]=1
    return video_output_path, audio_output_path

def merge_audio_video(video_path,audio_path,result_dir,progress):
    
    # 使用 ffmpeg 合并视频和音频
    video = ffmpeg.input(video_path)
    audio = ffmpeg.input(audio_path)
    os.makedirs(result_dir,exist_ok=True)
    progress[0]=0
    progress[1]=1
    result_path= os.path.join(result_dir,"result.mp4")
    (
        ffmpeg.output(
        video,
        audio,
        result_path,
        vcodec="copy",
        acodec="aac"
        ).run(overwrite_output=True)
    )
    progress[0]=1

def add_subs_into_video(video_path,srt_path:str,output_path,progress):
    name=os.path.basename(video_path)
    basename = os.path.splitext(name)[0]
    ext=os.path.splitext(name)[1]
    srt_path=srt_path.replace("\\","/")
    basename=basename+"_sub"
    file=basename+ext
    progress[0]=0
    progress[1]=1
    output_path=os.path.join(output_path,file)
    (
    ffmpeg
    .input(video_path)
    .output(
        output_path,
        vf=f"subtitles={srt_path}"
    )
    .run()
    )
    progress[0]=1



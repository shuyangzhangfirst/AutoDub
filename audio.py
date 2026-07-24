from pydub import AudioSegment
import os
import sys
from pydub.effects import speedup
from modelscope import snapshot_download
sys.path.insert(
    0,
    os.path.join(os.path.dirname(__file__), "CosyVoice")
)
sys.path.insert(
    0,
    os.path.join(os.path.dirname(__file__), "CosyVoice","third_party", "Matcha-TTS")
)
from CosyVoice.cosyvoice.cli.cosyvoice import AutoModel
import torchaudio

def convert_mp3_to_wav(input_file):
    # 输入 MP3 文件
    
    audio = AudioSegment.from_file(input_file)

    # 转换参数（适合语音识别）
    audio = audio.set_frame_rate(16000)
    audio = audio.set_channels(1)
    audio = audio.set_sample_width(2)  # 16-bit
    
    # 导出 WAV
    name, ext = os.path.splitext(input_file)
    new_path=name+".wav"
    

    audio.export(new_path, format="wav")

    print("转换完成:", new_path)


def split_audio(subtitles,audio_path,output_dir,progress):
    
    audio_segments_dir=os.path.join(output_dir,"translate_audio_segments")
    audio = AudioSegment.from_wav(audio_path)
    
    if subtitles is None or len(subtitles) == 0:
        print("No subtitles provided.")
        return
    
    os.makedirs(audio_segments_dir, exist_ok=True)
    progress[0]=0
    progress[1]=len(subtitles)
    for subtitle in subtitles:
        start_time = subtitle.start_ms
        end_time = subtitle.end_ms
        
        segment = audio[start_time:end_time]
        segment.export(os.path.join(audio_segments_dir,f"{subtitle.index}.wav"), format="wav")
        progress[0]+=1
    

    

def cosyvoice_create_wavs(subtitles,output_path,spk_id="",model="CosyVoice2-0.5B",progress=[0,0],state={"state":"running","error":None}):
    model_path=os.path.join("CosyVoice","pretrained_models")
    os.makedirs(model_path,exist_ok=True)
    model_path=os.path.join(model_path,model)
    if not os.path.exists(model_path):
        state["state"]="downloading"
        snapshot_download('iic/CosyVoice2-0.5B', local_dir='CosyVoice/pretrained_models/CosyVoice2-0.5B')

    cosyvoice = AutoModel(
        model_dir=model_path
    )
    
    output_path=os.path.join(output_path, "tts_output")

    os.makedirs(output_path, exist_ok=True)
    progress[1]=len(subtitles)
    if spk_id == "":
        
        for subtitle in subtitles:
            text=subtitle.translated_text
            prompt_wav=subtitle.wav_path
            prompt_text=subtitle.original_text
            output_wav_path=os.path.join(output_path,f"{subtitle.index}.wav")
            
            for i, j in enumerate(
                cosyvoice.inference_zero_shot(
                    text,
                    prompt_text,
                    prompt_wav,
                    stream=False
                )
            ):
                torchaudio.save(
                    output_wav_path,
                    j["tts_speech"],
                    cosyvoice.sample_rate
                )
            progress[0]+=1
    else:
        speaker_txt_path=os.path.join("speakers",f"{spk_id}.txt")
        speaker_wav_path=os.path.join("speakers",f"{spk_id}.wav")
        cosyvoice.add_zero_shot_spk(
            open(speaker_txt_path).read(),
            speaker_wav_path,
            zero_shot_spk_id=spk_id
        )
        for subtitle in subtitles:
            text=subtitle.translated_text
            output_wav_path=os.path.join(output_path,f"{subtitle.index}.wav")
            
            for i, j in enumerate(
                cosyvoice.inference_zero_shot(
                    text,
                    prompt_text="",
                    prompt_wav="",
                    zero_shot_spk_id=spk_id,
                    stream=False
                )
            ):
                torchaudio.save(
                    output_wav_path,
                    j["tts_speech"],
                    cosyvoice.sample_rate
                )
            progress[0]+=1
    print("translated audios complete")

def merge_tranlated_audio(subtitles,output_path):
    wav_segments_dir=os.path.join(output_path, "tts_output")
    final_audio = AudioSegment.empty()
    current_time=0
    for subtitle in subtitles:
        start_time = subtitle.start_ms
        end_time = subtitle.end_ms
        target_length = end_time - start_time
        
        silence_duration = start_time - current_time
        if silence_duration > 0:
            silence_segment = AudioSegment.silent(duration=silence_duration)
            final_audio += silence_segment
        else:
            silence_duration = 0
        wav_path=os.path.join(wav_segments_dir,f"{subtitle.index}.wav")
        wav = AudioSegment.from_wav(
            wav_path
        )
        if len(wav) > target_length:

            speed_ratio = len(wav) / target_length

            wav = speedup(
                wav,
                playback_speed=speed_ratio
            )

        elif len(wav) < target_length:

            wav += AudioSegment.silent(
                duration=target_length - len(wav)
            )
        
        final_audio += wav
        current_time = end_time
    final_audio.export(os.path.join(output_path, "merged_audio.wav"), format="wav")
    print("merge audio complete")
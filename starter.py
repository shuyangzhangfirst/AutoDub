import sub
import video
import audio
import os
import shutil
def reset_folder(folder):

    if not os.path.exists(folder):
        os.makedirs(folder)
        return
    else:
        shutil.rmtree(folder)
        os.makedirs(folder,exist_ok=True)
    
class Tranlate_Starter:
    def __init__(self):
        self.seprate_video_progress=[0,0]
        self.translated_progress=[0,0]
        self.split_audio_progress=[0,0]
        
        self.srt_to_audio_progress=[0,0]
        
        self.video_merge_progress=[0,0]
        self.add_subtitle_progress=[0,0]
        self.state={
            "state":"running",
            "error":None,
            
        }
        pass
        
        
    
    def run(self,video_path,dub=True,subtitle=False,speaker_id="",original_language="en",target_language="zh-CN",max_threads=1,whisper_model="small",cosyvoice_model="CosyVoice2-0.5B"):       
        try:
            self.seprate_video_progress=[0,0]
            self.translated_progress=[0,0]
            self.split_audio_progress=[0,0]
            
            self.srt_to_audio_progress=[0,0]
            self.video_merge_progress=[0,0]
            self.add_subtitle_progress=[0,0]
            
            self.state={
            "state":"running",
            "error":None,
            
            }
            reset_folder(os.path.join("output"))
            reset_folder(os.path.join("result"))
            
            output_dir=os.path.join("output")
            result_dir=os.path.join("result")
            
            video.separate_video(video_path,output_dir,self.seprate_video_progress)
            audio_path=os.path.join(output_dir,"original_audio.wav")
            
            my_tranlate_sub=sub.SubTranslator(audio_path,output_dir,original_language,target_language,max_threads,whisper_model,self.translated_progress)
            srt_path=os.path.join("output","srt","translated_subtitles.srt")
            
            if dub:
                audio.split_audio(my_tranlate_sub.subtitles,audio_path,output_dir,self.split_audio_progress)
                audio.cosyvoice_create_wavs(my_tranlate_sub.subtitles,output_dir,speaker_id,cosyvoice_model,self.srt_to_audio_progress,self.state)
                audio.merge_tranlated_audio(my_tranlate_sub.subtitles,output_dir)
                merged_audio=os.path.join(output_dir,"merged_audio.wav")
                split_video=os.path.join(output_dir,"original_video.mp4")
                video.merge_audio_video(split_video,merged_audio,result_dir,self.video_merge_progress)
                if subtitle:
                    video.add_subs_into_video(os.path.join(result_dir,"result.mp4"),srt_path,result_dir,self.add_subtitle_progress)
            else:
                
                video.add_subs_into_video(video_path,srt_path,result_dir,self.add_subtitle_progress)
            self.state["state"]="Done"
            reset_folder(os.path.join("input"))
        except Exception as e:
            self.state["state"]="error"
            self.state["error"]=str(e)
            reset_folder(os.path.join("input"))
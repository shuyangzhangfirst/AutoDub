
import torch
import whisper
import threading
from  deep_translator import GoogleTranslator
import os
class Sub:
    
    def __init__(self,index:int,original_text:str,start_ms:int,end_ms:int,translated_text:str=""):
        self.index:int = index
        self.original_text:str = original_text
        self.start_ms:int = start_ms
        self.end_ms:int = end_ms
        self.translated_text:str = translated_text
        
        pass

    
    def get_start_srt(self):
        
        total_seconds = self.start_ms // 1000

        hour = total_seconds // 3600
        minute = (total_seconds % 3600) // 60
        second = total_seconds % 60

        ms = self.start_ms % 1000

        return f"{hour:02d}:{minute:02d}:{second:02d},{ms:03d}"

    def get_end_srt(self):
        total_seconds = self.end_ms // 1000

        hour = total_seconds // 3600
        minute = (total_seconds % 3600) // 60
        second = total_seconds % 60

        ms = self.end_ms % 1000

        return f"{hour:02d}:{minute:02d}:{second:02d},{ms:03d}"
    
    def get_file_name(self):
        return str(self.index)+ ".wav"



    def merge_subs(self,other_sub):
        return Sub(self.index,self.original_text+other_sub.original_text,self.start_ms,other_sub.end_ms,self.translated_text+other_sub.translated_text)

def Audio2Sub(audio_path,model_name="small")->list[Sub]:
    my_device = "cuda" if torch.cuda.is_available() else "cpu"
    model = whisper.load_model(model_name,device=my_device)
    result=model.transcribe(audio_path)
    subtitles:list[Sub]=[]
    index=1
    for segment in result["segments"]:
        start_ms=int(segment["start"]*1000)
        end_ms=int(segment["end"]*1000)
        subtitles.append(Sub(index,segment["text"],start_ms,end_ms))
        index+=1
    return subtitles
def get_ms_duration(index,text_len,duration_ms):
    ms= int((index / text_len) * duration_ms)
    return ms
def subtitle_modifier(subtitle:Sub,true_index:int):
    i=0
    
    size=len(subtitle.original_text)
    start=subtitle.start_ms
    end=subtitle.end_ms
    duration= end-start
    new_subtitles=[]
    text=""
    new_sentence=True
    start_ms=0
    while i<len(subtitle.original_text):
        text+=subtitle.original_text[i]
        if new_sentence:
            start_ms=start+get_ms_duration(i,size,duration)
            new_sentence=False
        if (subtitle.original_text[i]=="." or subtitle.original_text[i] == "?" or subtitle.original_text[i]=="!") :
            if (i >=len(subtitle.original_text)-1):
                end_ms=end
                ns=Sub(true_index,text,start_ms,end_ms)
                new_subtitles.append(ns)
                
                return new_subtitles , False
                
            elif  (subtitle.original_text[i+1] == " "):
                end_ms = start+ get_ms_duration(i+1,size,duration)
                ns=Sub(true_index,text,start_ms,end_ms)
                new_subtitles.append(ns)
                true_index+=1
                text=""
                new_sentence=True
        else:
            if (i >=len(subtitle.original_text)-1):
                end_ms=end
                ns=Sub(true_index,text,start_ms,end_ms)
                new_subtitles.append(ns)
                
                return new_subtitles , True
        
        i+=1

def subtitles_split(subtitles:list[Sub]):
        new_subs:list[Sub]=[]
        true_index=1
        should_merge=False
        for subtitle in subtitles:
            
            ts,s=subtitle_modifier(subtitle,true_index)
            
            if should_merge:
                first_t=ts.pop(0)
                
                new_subs[-1]=new_subs[-1].merge_subs(first_t)
                
                new_subs.extend(ts)
            else:
                new_subs.extend(ts)
            should_merge=s
            
            true_index=new_subs[-1].index if s else new_subs[-1].index +1
        
        return new_subs


        
class SubTranslator:
    def __init__(self,audio_path,output_path,origin_language="en",target_language="zh-CN",max_threads=1,model="small",progress_bar=[0,0]):
        subtitles_before_split=Audio2Sub(audio_path,model)
        self.subtitles:list[Sub] = subtitles_split(subtitles_before_split)
        self.max_threads=min( max_threads , 16)
        self.translate_subs(origin_language,target_language,progress_bar)
        self.save(output_path,self.subtitles)
        
        pass

    def save(self,output_path,subtitles):
        srt_dir = os.path.join(output_path, "srt")
        os.makedirs(srt_dir, exist_ok=True)
        translated_srt_path = os.path.join(srt_dir, "translated_subtitles.srt")
        original_srt_path = os.path.join(srt_dir, "original_subtitles.srt")
        with open(translated_srt_path,"w",encoding="utf-8") as f:
            
            for subtitle in subtitles:
                f.write(f"{subtitle.index}\n")
                f.write(f"{subtitle.get_start_srt()} --> {subtitle.get_end_srt()}\n")
                f.write(f"{subtitle.translated_text}\n\n")
        print("翻译后的字幕文件已保存到:",translated_srt_path)
        with open(original_srt_path,"w",encoding="utf-8") as f:
            for subtitle in self.subtitles:
                f.write(f"{subtitle.index}\n")
                f.write(f"{subtitle.get_start_srt()} --> {subtitle.get_end_srt()}\n")
                f.write(f"{subtitle.original_text}\n\n")
        print("原始字幕文件已保存到:",original_srt_path)
    
    
    def translate_subs(self,origin_language,target_language,progress_bar):
        progress_bar[1]=len(self.subtitles)
        if self.max_threads >1:
            
            index=0
            while index < len(self.subtitles):
                
                si=index
                threads=[]
                while index < len(self.subtitles) and (index-si)<self.max_threads:
                    translator=GoogleTranslator(source=origin_language, target=target_language)
                    t=threading.Thread(target= self.translate_sub,args=(translator,index))
                    threads.append(t)
                    t.start()
                    index+=1
                    
                for thread in threads:
                    thread.join()
                    progress_bar[0]+=1
        else:
            index = 0
            translator=GoogleTranslator(source=origin_language, target=target_language)
            for sub in self.subtitles:
                self.translate_sub(translator,index)
                index+=1
                progress_bar[0]+=1
    
    def translate_sub(self,translator,index):
        try:
            self.subtitles[index].translated_text = translator.translate(self.subtitles[index].original_text)
            print(f"complete_translate:{index}/{len(self.subtitles)}")
        except Exception as e:
            print(f"translate failed at No.{self.subtitles[index].index}")
            self.subtitles[index].translated_text=self.subtitles[index].original_text


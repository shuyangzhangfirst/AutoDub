from fastapi import FastAPI, UploadFile, File, Form
import os
import uvicorn
from deep_translator import GoogleTranslator
import shutil
from fastapi.middleware.cors import CORSMiddleware
from starter import Tranlate_Starter
import asyncio
from fastapi.responses import FileResponse
from fastapi import HTTPException
import webbrowser
import threading
from fastapi.staticfiles import StaticFiles
import time
import sys


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://localhost:\d+",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

autodub=Tranlate_Starter()
task_running=False

@app.get("/params")
async def get_params():
    speaker_path= os.path.join("speakers")
    speakers=[""]
    
    for filename in os.listdir(speaker_path):
        
        name, ext = os.path.splitext(filename)
        
        if ext == ".wav":
            
            speakers.append(name)
    langs = GoogleTranslator().get_supported_languages(as_dict=True)
    return {"speakers":speakers,"langs":langs}

@app.get("/download")
async def download():
    if os.path.exists(os.path.join("result","result_sub.mp4")):
        return FileResponse(
                path=os.path.join("result","result_sub.mp4"),
                filename="result_sub.mp4",
                media_type="video/mp4"
            )
    elif os.path.exists(os.path.join("result","result.mp4")):
        return FileResponse(
            path=os.path.join("result","result.mp4"),
            filename="result.mp4",
            media_type="video/mp4"
        )
    else:
        raise HTTPException(
            status_code=404,
            detail="No result file found"
        )
@app.get("/progress")
async def progress():
    data={
        "video_audio":autodub.seprate_video_progress,
        "translate":autodub.translated_progress,
        "split_audio":autodub.split_audio_progress,
        "sub_audio":autodub.srt_to_audio_progress,
        "merge_video":autodub.video_merge_progress,
        "add_subtitle":autodub.add_subtitle_progress,
        "state":autodub.state
    }
    return data
    
@app.post("/process")
async def process(
    file: UploadFile = File(...),
    dub: bool = Form(...),
    subtitle: bool = Form(...),
    speaker_id: str = Form(...),
    original_language: str = Form(...),
    target_language: str = Form(...),
    max_threads: int = Form(...)
):
    global task_running
    if task_running == False:
        os.makedirs("input", exist_ok=True)

        save_path = f"input/{file.filename}"
        
        with open(save_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        task_running=True
        asyncio.create_task(
            process_video(save_path,dub,subtitle,speaker_id,original_language,target_language,max_threads)
        )
        
        

    
        
    return {
        "status": "ok",
        "filename": file.filename
    }

async def process_video(video_path,dub,subtitle,speaker_id,original_language,target_language,max_threads):
    global task_running
    try:
        await asyncio.to_thread(
            autodub.run,
            video_path,
            dub,
            subtitle,
            speaker_id,
            original_language,
            target_language,
            max_threads
        )
    finally:
        task_running=False
    
app.mount(
    "/",
    StaticFiles(directory="static", html=True),
    name="static"
)
def open_browser():
    time.sleep(3)
    webbrowser.open("http://127.0.0.1:8080/")

if __name__ == '__main__':
    threading.Thread(
        target=open_browser,
        daemon=True
    ).start()
    uvicorn.run("main:app",host="127.0.0.1",port=8080,reload=True)
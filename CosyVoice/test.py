import sys
sys.path.append("third_party/Matcha-TTS")

from cosyvoice.cli.cosyvoice import AutoModel
import torchaudio


cosyvoice = AutoModel(
    model_dir="pretrained_models/CosyVoice2-0.5B"
)

print(cosyvoice.list_available_spks())
text = "Hello, this is a test."
prompt_wav = "Aufzeichnung.wav"
prompt_text = "Hello, my name is shuyang and i love hamburger and i live in Germany."
# prompt_wav = "prompt.wav"


# for i, j in enumerate(
#     cosyvoice.inference_zero_shot(
for i, j in enumerate(
    cosyvoice.inference_zero_shot(
        text,
        prompt_text,
        prompt_wav,
        stream=False
    )
):
    torchaudio.save(
        "test.wav",
        j["tts_speech"],
        cosyvoice.sample_rate
    )
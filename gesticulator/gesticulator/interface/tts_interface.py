""" 
sudo apt-get install espeak
git clone https://github.com/mozilla/TTS TTS_repo 
git checkout 4132240
pip install -r tts_requirements.txt

cd TTS_repo
python setup.py develop

gdown --id 1NFsfhH8W8AgcfJ-BsL8CYAwQfZ5k4T-n -O tts_model.pth.tar
gdown --id 1IAROF3yy9qTK43vG_-R67y3Py9yYbD6t -O config.json

gdown --id 1Ty5DZdOc0F7OTGj9oJThYbL5iVu_2G0K -O vocoder_model.pth.tar
gdown --id 1Rd0R_nRCrbjEdpOwq6XwZAktvugiBvmu -O config_vocoder.json
gdown --id 11oY3Tv0kQtxK_JPgxrfesa99maVXHNxU -O scale_stats_vocoder.npy

cd ..
"""

"""
DISCLAIMER: This entire file is a slightly modified version of 
            the Glow-TTS model as implemented by Mozilla TTS here: 
            
https://colab.research.google.com/drive/1NC4eQJFvVEqD8L4Rd8CVK25_Z-ypaBHD?usp=sharing
"""


def interpolate_vocoder_input(scale_factor, spec):
    """Interpolation to tolarate the sampling rate difference
    btw tts model and vocoder"""
    print(" > before interpolation :", spec.shape)
    spec = torch.tensor(spec).unsqueeze(0).unsqueeze(0)
    spec = torch.nn.functional.interpolate(spec, scale_factor=scale_factor, mode='bilinear').squeeze(0)
    print(" > after interpolation :", spec.shape)
    return spec

import sys
import os
import torch
import time
sys.path.append('TTS_repo')

from TTS.utils.io import load_config
from TTS.utils.audio import AudioProcessor
from TTS.tts.utils.generic_utils import setup_model
from TTS.tts.utils.text.symbols import symbols, phonemes
from TTS.tts.utils.synthesis import synthesis
from TTS.tts.utils.io import load_checkpoint
from TTS.vocoder.utils.generic_utils import setup_generator

# runtime settings
USE_CUDA = False

# model paths
TTS_MODEL = "TTS_repo/tts_model.pth.tar"
TTS_CONFIG = "TTS_repo/config.json"
VOCODER_MODEL = "TTS_repo/vocoder_model.pth.tar"
VOCODER_CONFIG = "TTS_repo/config_vocoder.json"

# load configs
TTS_CONFIG = load_config(TTS_CONFIG)
VOCODER_CONFIG = load_config(VOCODER_CONFIG)

# TTS_CONFIG.audio['stats_path'] = "./scale_stats.npy"
VOCODER_CONFIG.audio['stats_path'] = "TTS_repo/scale_stats_vocoder.npy"

class GlowTTS:
    def __init__(self):
        # load the audio processor
        self.audio_processor = AudioProcessor(**TTS_CONFIG.audio)

        # LOAD TTS MODEL
        # multi speaker 
        speakers = []
        speaker_id = None

        # load the model
        num_chars = len(phonemes) if TTS_CONFIG.use_phonemes else len(symbols)
        self.model = setup_model(num_chars, len(speakers), TTS_CONFIG)      

        # load model state
        self.model, _ =  load_checkpoint(self.model, TTS_MODEL, use_cuda=USE_CUDA)
        self.model.eval();
        self.model.store_inverse();

        # LOAD VOCODER MODEL
        self.vocoder_model = setup_generator(VOCODER_CONFIG)
        self.vocoder_model.load_state_dict(torch.load(VOCODER_MODEL, map_location="cpu")["model"])
        self.vocoder_model.remove_weight_norm()
        self.vocoder_model.inference_padding = 0

        # scale factor for sampling rate difference
        self.scale_factor = [1,  VOCODER_CONFIG['audio']['sample_rate'] / self.audio_processor.sample_rate]
        print(f"scale_factor: {self.scale_factor}")

        self.ap_vocoder = AudioProcessor(**VOCODER_CONFIG['audio'])    
        if USE_CUDA:
            self.vocoder_model.cuda()
        self.vocoder_model.eval();

    def text_to_speech(self, text, length_scale = 1.1, noise_scale = 0.4, speaker_id = None, use_gl = False):
        # run tts
        target_sr = TTS_CONFIG.audio['sample_rate']
        waveform, alignment, mel_spec, mel_postnet_spec, stop_tokens, inputs =\
            synthesis(self.model,
                    text,
                    TTS_CONFIG,
                    USE_CUDA,
                    self.audio_processor,
                    speaker_id,
                    None,
                    False,
                    TTS_CONFIG.enable_eos_bos_chars,
                    use_gl)
        # run vocoder
        mel_postnet_spec = self.audio_processor._denormalize(mel_postnet_spec.T).T
        if not use_gl:
            target_sr = VOCODER_CONFIG.audio['sample_rate']
            vocoder_input = self.ap_vocoder._normalize(mel_postnet_spec.T)
            if self.scale_factor[1] != 1:
                vocoder_input = interpolate_vocoder_input(self.scale_factor, vocoder_input)
            else:
                vocoder_input = torch.tensor(vocoder_input).unsqueeze(0)
            waveform = self.vocoder_model.inference(vocoder_input)
        # format output
        if USE_CUDA and not use_gl:
            waveform = waveform.cpu()
        if not use_gl:
            waveform = waveform.numpy()
        waveform = waveform.squeeze()

        return waveform

"""## Run Inference"""
if __name__ == "__main__":
    model = GlowTTS()
    sentence =  "do you have any other hobbies ? i work with publishers and i love collaborating with them ."
    audio = model.text_to_speech(
        sentence, 
        length_scale=1.1,
        noise_scale=0.4)

    audio_path = "../../../unity/Assets/Audio/ChatbotResponse.wav"
    model.audio_processor.save_wav(audio, audio_path)
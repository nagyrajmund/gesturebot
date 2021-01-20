FROM python:3.7


CMD /bin/bash
#-stretch

# set a directory for the app
WORKDIR /workspace

# copy all the files to the container
COPY . .

# install dependencies
RUN apt-get update
RUN python install_script.py

# Fix Librosa
RUN apt-get update -y && apt-get install -y --no-install-recommends build-essential gcc \
                                        libsndfile1 
RUN apt-get install -y sox

# Install TTS repo
WORKDIR /workspace/gesticulator/interface/TTS_repo
RUN apt-get install -y espeak
RUN pip install -r requirements.txt
RUN python setup.py develop

# Download TTS model files
RUN gdown --id 1NFsfhH8W8AgcfJ-BsL8CYAwQfZ5k4T-n -O tts_model.pth.tar
RUN gdown --id 1IAROF3yy9qTK43vG_-R67y3Py9yYbD6t -O config.json
RUN gdown --id 1Ty5DZdOc0F7OTGj9oJThYbL5iVu_2G0K -O vocoder_model.pth.tar
RUN gdown --id 1Rd0R_nRCrbjEdpOwq6XwZAktvugiBvmu -O config_vocoder.json
RUN gdown --id 11oY3Tv0kQtxK_JPgxrfesa99maVXHNxU -O scale_stats_vocoder.npy

WORKDIR /workspace

CMD cd gesticulator/interface && python main.py --using_docker
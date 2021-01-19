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

CMD cd gesticulator/interface && python main.py --using_docker
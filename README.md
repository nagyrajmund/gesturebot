![teaser image](https://i.imgur.com/feoihA2.png)

# Instructions for running the DialogFlow demo
**This demo requires a functioning DialogFlow project to run.**

*Note: For the other demo with Blenderbot and Mozilla TTS, visit the `blenderbot_demo` branch.*

*The source code of the Unity project is available [from this link](https://drive.google.com/file/d/1SQiKh4Pcr1c4_y2LBFaSNUOkE-0CxrmG/view?usp=sharing), but below we provide a stand-alone executable version that doesn't require installing Unity.*
## Preliminaries
- Clone the repository
  ```
  git clone git@github.com:nagyrajmund/gesticulating_agent_unity.git
  git checkout dialogflow_demo
  ```
- Download the compiled Unity project:
  - [Linux release](https://drive.google.com/file/d/1xen8jKdNGeyxKqGKgf-rrmewM4iaZL0h/view?usp=sharing)
  - Windows 10 release
- Set your DialogFlow project URL in `gesturebot_Data/project_url.txt` and store your Google Cloud credentials in `gesturebot_Data/credentials.json`
- Download Apache ActiveMQ 5 [from this link](http://activemq.apache.org/components/classic/download/)

## Installation
### With anaconda (option 1)
- Create a new conda environment and install the requirements (using the terminal on Linux or the Anaconda Prompt on Windows)
  ```
  # From the root of the repository:
  # Install the gesture generation model
  conda create --name gesturebot_df -y python=3.7
  conda activate gesturebot_df
  cd gesticulator
  python install_script.py
  ```

### With docker (option 2)
- Pull the docker image of the gesture generation model
  ```
  docker pull rajmundn/gesticulating_agent:gesturebot_dialogflow
  ```

## Running the project
- Start the ActiveMQ server by running `./bin/activemq start` in a terminal (on Linux) or `bin/activemq start` in a command prompt (on Windows).
- Run the executable in the compiled Unity project to start the Unity player
- (option 1): Start running the gesture generation model with conda
  - in the previously created conda environment, from the `gesticulator` folder, run:
    ```
    cd gesticulator/interface
    python main
    ```
- (option 2): Start running the gesture generation model with docker
  - When the project is run for the first time, the docker container may be created by running the following command from the root of the repository:
    ```
    docker run -v $(pwd)/../unity/Assets:/workspace/gesticulator/interface/docker_volume --network host -ti --name gesturebot rajmundn/gesticulating_agent:gesturebot_dialogflow
    ```
  - After the container has been created, it can be ran with:
    ```
    docker start -ai gesturebot
    ```
- Note that the gesture generation model will download around 10 GBs of data (for the language model) into the `.word_vectors_cache` folder when it's run for the first time. However, the 6,6 GB `wiki.en.vec` file can be removed after the first run.

Now you should be able to talk with the agent via the following ways:
  - Enter text in the input field and press `Submit` OR
  - Click `Talk` to start recording speech input, and `Stop` to stop recording OR
  - Press `t`-key once to start recording speech input, and `t`-key again to stop recording

and the agent should be moving when it replies.

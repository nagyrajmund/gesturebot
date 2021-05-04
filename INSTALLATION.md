## Preliminaries
- Clone the repository
  ```
  git clone git@github.com:nagyrajmund/gesticulating_agent_unity.git
  cd gesticulating_agent_unity
  git checkout dialogflow_demo
  ```

- Download Apache ActiveMQ 5 [from this link](http://activemq.apache.org/components/classic/download/) and extract the 
  - Extract the archive into the `ActiveMQ` folder
- Download the Unity project:
  - [Linux release](https://drive.google.com/file/d/11BWWIjYbujE6gobdmmalYhFEAY209Kkm/view?usp=sharing) | [Windows 10 release](https://drive.google.com/file/d/1kT52MJZUdmB8NlPD1C_gyX2ZyJOyULDH/view?usp=sharing)
  - Extract contents of the Unity project into the `Unity` folder
  - Configure the DialogFlow project as described in [README_DialogFlow.md](README_DialogFlow.md)

## Installation
### Option 1: using docker (recommended)
- Pull the docker image of the gesture generation model
  ```
  docker pull rajmundn/gesticulating_agent:gesturebot_dialogflow
  ```

### Option 2: using anaconda (alternative)
- Create a new conda environment and install the requirements (using the terminal on Linux or the Anaconda Prompt on Windows) by running the following commands **from the root of the repository**:
  ```
  # Create conda environment
  conda create --name gesturebot_dialogflow -y python=3.7
  conda activate gesturebot_dialogflow
  
  # Install gesture generation model
  cd gesticulator
  python install_script.py
  ```

## Running the project
### Step 1: ActiveMQ
Start the ActiveMQ server by running `./bin/activemq start` in a terminal (on Linux) or `bin/activemq start` in a command prompt (on Windows).

### Step 2: Gesture generation model
* Note that the gesture generation model will download around 10 GBs of data (for the language model) into the `.word_vectors_cache` folder when it's run for the first time. However, the 6,6 GB `wiki.en.vec` file can be removed after the first run.

#### Option 1: using docker
  - When the project is run for the first time, the docker container may be created by running the following command **from the root of the repository**:
    ```
    docker run -v $(pwd)/Unity/dialogflow_demo/gesturebot_Data:/workspace/gesticulator/interface/docker_volume --network host -ti --name gesturebot_dialogflow rajmundn/gesticulating_agent:gesturebot_dialogflow
    ```
  - After the container has been created, it can be ran with:
    ```
    docker start -ai gesturebot_dialogflow
    ```
#### Option 2: using anaconda
  - in the previously created conda environment, from the `gesticulator` folder, run:
    ```
    cd gesticulator/interface
    python main.py
    ```

### Step 3: Running Unity
Run the Unity executable (`gesturebot.x86_64` or `gesturebot.exe` in the `Unity/dialogflow_demo/` folder)

Now you should be able to talk with the agent via the following ways:
  - Enter text in the input field and press `Submit` OR
  - Click `Talk` to start recording speech input, and `Stop` to stop recording OR
  - Press `t`-key once to start recording speech input, and `t`-key again to stop recording

and the agent should be moving when it replies.

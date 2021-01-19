# Instructions
## Preliminaries
- Clone the repository
  ```
  git clone git@github.com:nagyrajmund/gesticulating_agent.git
  ```
- Put your `credentials.json` file into the `unity/Assets/` folder
- Create a `project_url.txt` file containing your Dialogflow project's URL in the `unity/Assets/` folder

- Download Apache ActiveMQ 5 from this link http://activemq.apache.org/components/classic/download/

## Installing the gesture generation model
### With anaconda (option 1)
- Create a new conda environment and install the requirements (using the terminal on Linux or the Anaconda Prompt on Windows)
  ```
  conda create --name gesturebot -y python=3.6.9
  conda activate gesturebot
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
- Open the `unity` folder in the repo as a new project in Unity, select the `Chatbot example` scene and enter Play mode
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
- Note that the gesture generation model will download around 10 GBs of data (for the language model) into the `.word_vectors_cache` folder when it's run for the first time. 

Now you should be able to talk with the agent via the following ways:
  - Enter text in the input field and press `Submit` OR
  - Click `Talk` to start recording speech input, and `Stop` to stop recording OR
  - Press `t`-key once to start recording speech input, and `t`-key again to stop recording

and the agent should be moving when it replies.

## ActiveMQ
- Start the ActiveMQ server by running `/bin/activemq start` in the folder where it's installed 
  - if the provided ActiveMQ DLLs are not working, follow the instructions in [the UnityBMLACtiveMQ repo](https://github.com/bernuly/UnityBMLActiveMQ)

### Scene anatomy
The agent is `Assets/MotionExporters/Scenes/Sample/Model/Robot.fbx`

- Robot
   - Assets/Scripts/ActiveMQClient.cs
   - Assets/Scripts/DialogFlowCommunicator.cs
   - Assets/Scripts/GesticulatingAgent.cs
   - Assets/Scripts/MotionVisualizer.cs
- HUD
   - MicInput
   - ButtonSendTextToChatbot
      - reference to: GesticulatingAgent.HandleTextInput
      

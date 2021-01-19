import json
import joblib
import os
from time import sleep
from os.path import abspath, join
import numpy as np
from stomp.exception import ConnectFailedException
from gesticulator.model.model import GesticulatorModel
from gesticulator.interface.profiling.gesture_predictor import GesturePredictor
from messaging_server import MessagingServer
from tts_interface import GlowTTS
from blenderbot import Blenderbot

class GestureGeneratorService:
    def __init__(self, model_file, mean_pose_file, host, port, using_docker):
        """
        This service generates gestures for an input speech segment by passing 
        the audio and the text transcription (as received from the 3D agent)
        to the trained Gesticulator model.

        The generated gestures are first saved into csv files, then the paths
        to those files are sent to the standalone ActiveMQ server, which forwards them 
        to the 3D agent.

        Args:
            model_file:  The pretrained Gesticulator model
            mean_pose_file:  The path to .npy file that contains the mean pose of the dataset
            host:  The hostname of the ActiveMQ connection.
            port:  The port of the ActiveMQ connection.
            using_docker:  See 'on_message()' for details.
            unity_assets_folder:  The path to Unity's Assets folder.
        """
        self.using_docker = using_docker
        self.connection = MessagingServer(listener=self, host=host, port=port)
        
        print("Loading Blenderbot model")
        self.chatbot = Blenderbot()

        print("Loading text-to-speech model")
        self.tts_model = GlowTTS()
        
        print("Loading pretrained Gesticulator model")
        self.model = GesticulatorModel.load_from_checkpoint(model_file, inference_mode=True)
        
        print("Creating GesturePredictor interface")
        feature_type = check_feature_type(self.model)       
        self.predictor = GesturePredictor(self.model, feature_type=feature_type)
        
    def __enter__(self):
        """Open the connection to the ActiveMQ broker."""
        try:
            print("Connecting to the ActiveMQ broker", end="")
            self.connection.open_network()
            print(" Connected!\n")
        except ConnectFailedException as connection_error:
            print("\n---------------------------------------------")
            print("ERROR: Could not connect to the ActiveMQ broker! Is it running?")
            print("---------------------------------------------")
            exit(-1)            
        
    def __exit__(self, exc_type, exc_value, traceback):
        """Close the connection to the ActiveMQ broker."""
        self.connection.close_network()

    def on_message(self, headers, json_message):
        """
        Generate and save gestures for the speech segment in 'text_message', then
        send the path of the saved gestures to the 3D agent in Unity.

        NOTE: This function is called  when a message from the 3D agent arrives through ActiveMQ.

        NOTE: the 'headers' argument can be ignored, it's only there because 
              it's mandatory in the STOMP API.
        
        Args:
            headers:        See the documentation of the STOMP API.
            json_message:   Contains the following two fields:
                                assets_folder:  The path to the Unity/Assets folder.
                                text:  The text message from the user.
        """
        print("Received message:", json_message)
        received_message = json.loads(json_message)
        
        text_response = self.chatbot.generate_reply(received_message['text'])
        print("Generated reply:", text_response)
        
        audio = self.tts_model.text_to_speech(text_response)
        # Save as a wav file
        save_folder = "docker_volume" if self.using_docker else received_message['assets_folder'] 
        audio_path = join(save_folder, "Audio", "ChatbotResponse.wav")
        self.tts_model.audio_processor.save_wav(audio, audio_path)

        print("Predicting gestures")
        gestures = self.predictor.predict_gestures(audio_path, text_response)
        
        print("Saving gestures")
        out_file = "predicted_rotations_{}.csv"

        np.savetxt(join(save_folder, out_file.format('x')), gestures[:, :, 0], delimiter=',')
        np.savetxt(join(save_folder, out_file.format('y')), gestures[:, :, 1], delimiter=',')
        np.savetxt(join(save_folder, out_file.format('z')), gestures[:, :, 2], delimiter=',')

        answer = json.dumps(
            {
                'text_response' : text_response,
                'xRotationCsvPath' : join(received_message['assets_folder'], out_file.format('x')),
                'yRotationCsvPath' : join(received_message['assets_folder'], out_file.format('y')),
                'zRotationCsvPath' : join(received_message['assets_folder'], out_file.format('z')),
                'framerate' : 20,
                'numFrames' : gestures.shape[0]
            }, separators=(',', ':'))
        
        print("Sending message:", answer)
        sleep(2)
        self.connection.send_JSON(answer)
        print("Message sent!")
        print("---------------------------------------------")

    def on_error(self, headers, message):
        print("ERROR:", message)

def check_feature_type(model):
    """
    Return the audio feature type from the model.
    """
    audio_dim = model.hparams.audio_dim

    if audio_dim == 4:
        feature_type = "Pros"
    elif audio_dim == 64:
        feature_type = "Spectro"
    elif audio_dim == 68:
        feature_type = "Spectro+Pros"
    elif audio_dim == 26:
        feature_type = "MFCC"
    elif audio_dim == 30:
        feature_type = "MFCC+Pros"
    elif audio_dim == 88:
        feature_type = "GeMAPS"

        print("Loading GeMAPS feature normalizer")
        model.audio_normalizer = joblib.load(
            os.path.join(
                "../", model.hparams.utils_dir, "gemaps_scaler.gz"
            )
        )
    else:
        print("Error: Unknown audio feature type of dimension", audio_dim)
        exit(-1)

    return feature_type
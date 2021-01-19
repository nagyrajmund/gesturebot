from os.path import join, abspath
from gesticulator.model.model import GesticulatorModel
from gesture_predictor import GesturePredictor
import torch
import cProfile
import librosa
from motion_visualizer.convert2bvh import write_bvh
from argparse import ArgumentParser
import numpy as np

def profile_with_clipping(model_file, feature_type, 
                          mean_pose_file, input, 
                          duration):
    """Profile the inference phase and the conversion from exp. map to joint angles."""
    model = GesticulatorModel.load_from_checkpoint(
        model_file, inference_mode=True, mean_pose_file=mean_pose_file, audio_dim=4)

    predictor = GesturePredictor(model, feature_type)
    truncate_audio(input, duration)
    
    audio    = f"{input}_{duration}s.wav"
    text     = f"{input}_{duration}s.json"

    print("Profiling gesture prediction...")
    profiler = cProfile.Profile()

    profiler.enable()

    gestures = predictor.predict_gestures(audio, text)

    out_file = "/home/work/Desktop/repositories/gesticulator/gesticulator/interface/profiling/predicted_rotations_{}.csv"

    np.savetxt(out_file.format('_DATASET_INPUT_x'), gestures[:, :, 0], delimiter=',')
    np.savetxt(out_file.format('_DATASET_INPUT_y'), gestures[:, :, 1], delimiter=',')
    np.savetxt(out_file.format('_DATASET_INPUT_z'), gestures[:, :, 2], delimiter=',')
 
    profiler.disable()

    profiler.print_stats(sort='cumtime')

def truncate_audio(input_name, target_duration):
    audio, sr = librosa.load(input_name + '.wav', duration = int(target_duration))

    librosa.output.write_wav(input_name + '_{}s.wav'.format(target_duration), audio, sr)


def construct_argparser():
    parser = ArgumentParser()

    parser.add_argument('--model_file', default="../../../results/last_run/trained_model_data",
                        help='Path to the saved model')
    parser.add_argument('--input', default="NaturalTalking_01")
    parser.add_argument('--duration', "-len", default=5, type=int)
    parser.add_argument('--feature_type')
    parser.add_argument('--mean_pose_file', default="utils/mean_pose.npy")

    return parser

if __name__ == "__main__":
    args = construct_argparser().parse_args()
    
    print(f"Using {args.duration}s of {args.input}")

    profile_with_clipping(**vars(args))   
    
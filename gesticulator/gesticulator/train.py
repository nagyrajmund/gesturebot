import os
import sys

import numpy as np
import torch
from argparse import ArgumentParser

from config.model_config import construct_model_config_parser
from gesticulator.model.model import GesticulatorModel
from pytorch_lightning import Trainer
from pytorch_lightning.loggers import TensorBoardLogger
from pytorch_lightning.callbacks.base import Callback

from visualization.motion_visualizer.generate_videos import generate_videos
SEED = 2334
torch.manual_seed(SEED)
np.random.seed(SEED)

class ModelSavingCallback(Callback):
    """ 
    Saves the model to the <results>/<run_name> directory during training.
    The saving frequency is configured by the --save_model_every_n_epochs command-line argument.

    The model can be loaded from the checkpoints with:
        model = GesticulatorModel.load_from_checkpoint(<checkpoint_path>)
    """
    def on_validation_end(self, trainer, model):
        if (trainer.current_epoch + 1) % model.hparams.save_model_every_n_epochs == 0:
            checkpoint_fname = f"model_ep{model.current_epoch+1}.ckpt"
            checkpoint_dir = os.path.abspath(model.save_dir)

            trainer.save_checkpoint(os.path.join(model.save_dir, checkpoint_fname))
            print("\n\n  Saved checkpoint to", os.path.join(checkpoint_dir, checkpoint_fname), end="\n")

def main(hparams):
    if hparams.model_checkpoint is None:
        model = GesticulatorModel(hparams)
    else:
        model = GesticulatorModel.load_from_checkpoint(hparams.model_checkpoint, 
            model_checkpoint=hparams.model_checkpoint)

    logger = create_logger(model.save_dir)
    callbacks = [ModelSavingCallback()] if hparams.save_model_every_n_epochs > 0 else []
    
    if hparams.model_checkpoint is None:
        trainer = Trainer.from_argparse_args(hparams, logger=logger, callbacks = callbacks,
            checkpoint_callback=False)
    else:
        # Workaround
        model.init_prediction_saving_params()
        model.on_train_start()
        
        trainer = Trainer.from_argparse_args(hparams, resume_from_checkpoint=hparams.model_checkpoint, 
            logger=logger, callbacks=callbacks, checkpoint_callback=False, num_sanity_val_steps=0)
    
    trainer.fit(model)
    trainer.save_checkpoint(os.path.join(model.save_dir, f"trained_model_{model.current_epoch+1}epochs.ckpt"))

   
def create_logger(model_save_dir):
    # str.rpartition(separator) cuts up the string into a 3-tuple of (a,b,c), where
    #   a: everything before the last occurrence of the separator
    #   b: the separator
    #   c: everything after the last occurrence of the separator)
    result_dir, _, run_name = model_save_dir.rpartition('/')
    
    return TensorBoardLogger(save_dir=result_dir, version=run_name, name="")

def add_training_script_arguments(parser):
    parser.add_argument('--save_model_every_n_epochs', '-ckpt_freq', type=int, default=0,
                        help="The frequency of model checkpoint saving.")
    parser.add_argument('--use_mirror_augment', '-mirror', action='store_true',
                        help="If set, use auxiliary mirrored motion dataset")
    parser.add_argument('--model_checkpoint', default=None)
    return parser

if __name__ == '__main__':
    # Model parameters are added here
    parser = construct_model_config_parser()
    
    # Add training-script specific parameters
    parser = add_training_script_arguments(parser) 

    hyperparams = parser.parse_args()
    print()
    print(vars(hyperparams))
    print()
    main(hyperparams)


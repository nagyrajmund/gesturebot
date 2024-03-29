from math import ceil
import os.path
import inflect
import numpy as np
import torch
import joblib

from torchnlp.word_to_vector.fast_text import FastText

from gesticulator.data_processing.text_features.parse_json_transcript import encode_json_transcript_with_bert, encode_json_transcript_with_fasttext
from gesticulator.data_processing import tools
from gesticulator.data_processing.SGdataset import standardize
from gesticulator.model.model import GesticulatorModel
from motion_visualizer.convert2bvh import write_bvh
from motion_visualizer.bvh2npy import convert_bvh2npy
from gesticulator.data_processing.text_features.syllable_count import count_syllables
from gesticulator.visualization.motion_visualizer.generate_videos import visualize

class GesturePredictor:
    supported_features = ("MFCC", "Pros", "MFCC+Pros", "Spectro", "Spectro+Pros", "GeMAPS")
    
    def __init__(self, model : GesticulatorModel, feature_type : str):
        """An interface for generating gestures using saved GesticulatorModel.

        Args:
            model:           the trained Gesticulator model
            feature_type:    the feature type in the input data (must be the same as it was in the training dataset!)
        """
        if feature_type not in self.supported_features:
            print(f"ERROR: unknown feature type '{feature_type}'!")
            print(f"Possible values: {self.supported_features}")
            exit(-1)
        
        self.feature_type = feature_type
        self.model = model.eval() # Put the model into 'testing' mode
        self.embedding = self._create_embedding(model.text_dim)
        
    def predict_gestures(self, audio_path, text):
        """ Predict the gesticulation for the given audio and text inputs.
        Args:
            audio_path:  the path to the audio input
            text:  the text transcription of the audio (as a string)

        Returns: 
            predicted_motion:  the predicted gesticulation as a sequence of joint angles
            
        """
        audio, text = self._extract_features(audio_path, text)
        # By default, Gesticulator consumes about 1,5s of the input for context
        # We pad the inputs with silence to counteract that behaviour
        # (otherwise the generated motion would be shorter than the audio)
        audio, text = self._add_feature_padding(audio, text)
        
        # Add batch dimension
        audio, text = audio.unsqueeze(0), text.unsqueeze(0)

        if self.feature_type == "GeMAPS":
            audio = standardize(audio, self.model.audio_normalizer)
            audio = self._tensor_from_numpy(audio)
        
        predicted_motion = self.model.forward(audio, text, use_conditioning=True, motion=None)
        joint_angles = self._convert_to_euler_angles(predicted_motion)
 
        return joint_angles
        
    # -------- Private methods --------

    def _convert_to_euler_angles(self, predicted_motion):
        """
        Convert the motion returned by Gesticulator to joint
        rotations around the X, Y and Z axes (relative to the T-pose).

        Args:
            predicted_motion:  the output of the Gesticulator model
        
        Returns:
            rotations:  a numpy array of joint rotations with a shape of (n_frames, 15, 3)
                        where 15 is the number of joints supported by Gesticulator
                        and 3 is the number of axes (X,Y,Z)    
        """
        # The pipeline contains the transformations from data preprocessing
        # It allows us to convert from exponential maps to euler angles
        data_pipeline = joblib.load("../utils/data_pipe.sav")
        motion_array = predicted_motion.detach().numpy()
        # NOTE: 'inverse_transform' returns a list with one MoCapData object
        joint_angles = data_pipeline.inverse_transform(motion_array)[0].values

        # Gesticulator only supports these 15 joints
        joint_names = [
            'Spine', 'Spine1', 'Spine2', 'Spine3', 'Neck', 'Neck1', 'Head',
            'RightShoulder', 'RightArm', 'RightForeArm', 'RightHand',
            'LeftShoulder', 'LeftArm', 'LeftForeArm', 'LeftHand']

        n_joints = len(joint_names)
        n_frames = joint_angles.shape[0]

        # The output joint angles will be stored in 3 separate arrays
        rotations = np.empty((n_frames, n_joints, 3)) 

        for joint_idx, joint_name in enumerate(joint_names):
            x = joint_angles[joint_name + '_Xrotation']
            y = joint_angles[joint_name + '_Yrotation']
            z = joint_angles[joint_name + '_Zrotation']

            for frame_idx in range(n_frames):
                rotations[frame_idx, joint_idx, :] = [x[frame_idx], y[frame_idx], z[frame_idx]]

        return rotations

    def _create_embedding(self, text_dim):
        """Create and return the text embedding (either BERT or FastText)."""
        if text_dim == 305:
            print("Creating FastText embedding.")
            return FastText()
        else:
            print(f"ERROR: Unexpected text dimensionality ({model.text_dim})!")
            print("        Only FastText is supported at the moment! (305 dim.).")
            exit(-1)
        

    def _add_feature_padding(self, audio, text):
        """ 
        NOTE: This is only for demonstration purposes so that the generated motion
        is as long as the input audio! Padding was not used during model training or evaluation.
        """
        audio = self._pad_audio_features(audio)
        text = self._pad_text_features(text)

        return audio, text

    def _pad_audio_features(self, audio):
        """
        Pad the audio features with the context length so that the
        generated motion is the same length as the original audio.
        """
        if self.feature_type == "Pros":
            # 0 means no change in prosody.
            audio_fill_value = 0
        elif self.feature_type == "Spectro":
            # For log-Mel spectrograms, silent parts are around -12
            audio_fill_value = -12
        elif self.feature_type == "GeMAPS":
            audio_fill_value = 0
        else:
            print("ERROR: only prosody, spectrogram and GeMAPS are supported at the moment.")
            print("Current feature:", self.feature_type)
            exit(-1)

        audio_past = torch.full(
            (self.model.hparams.past_context, audio.shape[1]),
            fill_value = audio_fill_value,
            dtype=torch.long)

        audio_future = torch.full(
            (self.model.hparams.future_context, audio.shape[1]),
            fill_value = audio_fill_value,
            dtype=torch.long)

        audio = torch.cat((audio_past, audio, audio_future), axis=0)

        return audio

    def _pad_text_features(self, text):
        if isinstance(self.embedding, FastText):
            text_dim = 300
        
        # Silence corresponds to -15 when encoded, and the 5 extra features are then 0s
        silence_vector = [[-15] * text_dim + [0] * 5]
        text_past   = torch.tensor(silence_vector * self.model.hparams.past_context, dtype=torch.float32)
        text_future = torch.tensor(silence_vector * self.model.hparams.future_context, dtype=torch.float32)
        text = torch.cat((text_past, text, text_future), axis=0)
        
        return text
        
    def _extract_features(self, audio_path, text_in):
        """
        Extract the features for the given input. 
        
        Args:
            audio_path: the path to the speech recording
            text_in:  the text transcription of the speech

        Returns:
            audio, text:  the extracted features
            
        """
        audio_features = self._extract_audio_features(audio_path)
        text_features = self._extract_text_features(text_in, audio_features.shape[0])
        
        audio_features, text_features = self._align_vector_lengths(audio_features, text_features)
       
        audio = self._tensor_from_numpy(audio_features)
        text = self._tensor_from_numpy(text_features)

        return audio, text
    
    def _extract_text_features(self, text, total_len_frames):
        """
        Extract the text features using BERT or FastText embedding.
        
        Args:
            text:  the text transcription of the speech
            total_len_frames:  the number of input audio feature frames
        
        Returns:
            A tensor with text frames, with a shape of (1, total_len_frames, text_dim),
            where text_dim is either 305 (FastText) or 773 (BERT)
        """
        if isinstance(self.embedding, FastText):
            return self._estimate_word_timings_fasttext(text, total_len_frames)
        else:
            print('ERROR: Unknown embedding: ', self.embedding)
            exit(-1)


    def _extract_audio_features(self, audio_path):
        """Extract the audio features from the audio file at 'audio_path'."""
        if self.feature_type == "MFCC":
            return tools.calculate_mfcc(audio_path)
        
        if self.feature_type == "Pros":
            return tools.extract_prosodic_features(audio_path)
        
        if self.feature_type == "MFCC+Pros":
            mfcc_vectors = tools.calculate_mfcc(audio_path)
            pros_vectors = tools.extract_prosodic_features(audio_path)
            mfcc_vectors, pros_vectors = tools.shorten(mfcc_vectors, pros_vectors)
            return np.concatenate((mfcc_vectors, pros_vectors), axis=1)
        
        if self.feature_type =="Spectro":
            return tools.calculate_spectrogram(audio_path)
        
        if self.feature_type == "Spectro+Pros":
            spectr_vectors = tools.calculate_spectrogram(audio_path)
            pros_vectors = tools.extract_prosodic_features(audio_path)
            spectr_vectors, pros_vectors = tools.shorten(spectr_vectors, pros_vectors)
            return np.concatenate((spectr_vectors, pros_vectors), axis=1)
        
        if self.feature_type == "GeMAPS":
            return tools.extract_gemaps_features(audio_path)

        # Unknown feature type
        print(f"ERROR: unknown feature type '{self.feature_type}' in the 'extract_audio_features' call!")
        print(f"Possible values: {self.supported_features}.")
        exit(-1)

    def _estimate_word_timings_bert(self, text, total_duration_frames):
        """
        This is a convenience function that enables the model to work with plaintext 
        transcriptions in place of a time-annotated JSON file from Google Speech-to-Text.

        It does the following two things:
        
            1) Encodes the given text into word vectors using BERT embedding
            
            2) Assuming 10 FPS and the given length, estimates the following features for each frame:
                - elapsed time since the beginning of the current word 
                - remaining time from the current word
                - the duration of the current word
                - the progress as the ratio 'elapsed_time / duration'
                - the pronunciation speed of the current word (number of syllables per decisecond)
               so that the word length is proportional to the number of syllables in it.
        
        Args: 
            text:  the plaintext transcription
            total_duration_frames:  the total duration of the speech (in frames)

            # NOTE: Please make sure that 'text' has correct punctuation! 
            #       In particular, it should end with an end-of-sentence token.
        
        Returns:
            output_features:  a numpy array of shape (1, total_duration_frames, 773)
                              containing the text features
        """
        print("Estimating word timings with BERT using syllable count.")
        # --------------------------------------------------------
        # 0) Split the input text into sentences
        # --------------------------------------------------------
        delimiters = ['.', '!', '?']
        # The pattern means "any of the delimiters". 
        # The parantheses prevent the delimiters from being removed when splitting
        pattern = "([.!?])"  
        split_text = re.split(pattern, text)
        # The odd indices in split_text are sentences, the even indices are delimiters
        # And the last element is an empty string which will be ignored
        # E.g. "Hello! And bye!" becomes ["Hello", "!", "And bye", "!", ""]
        sentences = [sentence + delimiter for sentence, delimiter 
                     in zip(split_text[:-1:2], split_text[1:-1:2])]

        text = "".join(sentences)
        print(f'\nInput text:\n"{text}"')
        
        # --------------------------------------------------------
        # 1) Count the total number of syllables in the text
        #    (we will use this when we calculate the word lengths)
        # --------------------------------------------------------
        total_n_syllables = 0
        # The number of syllables of every word in every sentence
        word_n_syllables_in_sentences = []
        for sentence in sentences:
            word_n_syllables_in_sentences.append([])
            for word in sentence.split():
                curr_n_syllables = count_syllables(word)
                total_n_syllables += curr_n_syllables
                # Append the syllable count to the latest sentence
                word_n_syllables_in_sentences[-1].append(curr_n_syllables)
        
        fillers = ["eh", "ah", "like", "kind of"]
        filler_encoding = self.embedding(["eh, ah, like, kind of"])[0][1][0]
        elapsed_deciseconds = 0
        output_features = []
        
        for sentence_idx, sentence in enumerate(sentences):
            # --------------------------------------------------------
            # 2) Filter out the filler words from each sentence
            # --------------------------------------------------------
            sentence_without_fillers = []
            sentence_words = sentence.split()
            
            for word in sentence_words:
                if word not in fillers:
                    # The last character might be a delimiter or comma
                    if word[:-1] not in fillers:
                        sentence_without_fillers.append(word)
                    # If the last character of a filler word is a delimiter, then
                    # we consider it a separate word
                    # However, we ignore commas and other non-delimiter tokens
                    elif word[-1] in delimiters:
                        sentence_without_fillers.append(word[-1])           
            
            # --------------------------------------------------------
            # 3) After the sentence is over, feed it whole into BERT (without fillers)
            # Concatenate the words using space as a separator
            # --------------------------------------------------------
            
            original_input = [' '.join(sentence_without_fillers)]
            input_to_bert, encoded_words_in_sentence = self.embedding(original_input)[0]
            
            if input_to_bert[-1] not in delimiters:
                print("ERROR: missing delimiter in input to BERT!")
                print("\nNOTE: Please make sure that the input text ends with a punctuation mark (. ? or !)")
                print("The current sentence:", original_input)
                print("The input to BERT:", input_to_bert)
                exit(-1)
            
            if len(sentence_words) != len(word_n_syllables_in_sentences[sentence_idx]):
                print(f"""Error, sentence words has different length than numbers of syllables:
                    Number of words: {len(sentence_words)} | number of syllables: {len(word_n_syllables_in_sentences[sentence_idx])}
                    {sentence_words}
                    {word_n_syllables_in_sentences[sentence_idx]}
                    """)
                exit(-1)
            
            # --------------------------------------------------------
            # 4) Go through the sentence again, this time including filler words
            #    and append: 
            #       - the embedded words from BERT
            #       - the 5 extra features that we estimate using the syllable count
            #    to the output features
            # --------------------------------------------------------
            
            sentence_syllables = word_n_syllables_in_sentences[sentence_idx]
            for curr_word, curr_encoding, curr_n_syllables in zip(sentence_words, encoded_words_in_sentence, sentence_syllables):
                
                if curr_n_syllables == 0:
                    raise Exception(f"Error, word '{curr_word}' has 0 syllables!")

                # We take the ceiling to not lose information
                # (if the text was shorter than the audio because of rounding errors, then
                #  the audio would be cropped to the text's length)
                w_duration = ceil(total_duration_frames * curr_n_syllables / total_n_syllables)
                w_speed = curr_n_syllables / w_duration if w_duration > 0 else 10 # Because 10 FPS
                w_start = elapsed_deciseconds
                w_end   = w_start + w_duration
                # print("Word: {} | Duration: {} | #Syl: {} | time: {}-{}".format(curr_word, w_duration, curr_n_syllables, w_start, w_end))            
                while elapsed_deciseconds < w_end:
                    elapsed_deciseconds += 1
                    
                    w_elapsed_time = elapsed_deciseconds - w_start
                    w_remaining_time = w_duration - w_elapsed_time + 1
                    w_progress = w_elapsed_time / w_duration
                    
                    frame_features = [ w_elapsed_time,
                                       w_remaining_time,
                                       w_duration,
                                       w_progress,
                                       w_speed ]

                    output_features.append(list(curr_encoding) + frame_features)
    
        return np.array(output_features)

    def _estimate_word_timings_fasttext(self, text, total_duration_frames):
        """
        This is a convenience functions that enables the model to work with plaintext 
        transcriptions in place of a time-annotated JSON file from Google Speech-to-Text.

        It does the following two things:
        
            1) Encodes the given text into word vectors using FastText embedding
            
            2) Assuming 10 FPS and the given length, estimates the following features for each frame:
                - elapsed time since the beginning of the current word 
                - remaining time from the current word
                - the duration of the current word
                - the progress as the ratio 'elapsed_time / duration'
                - the pronunciation speed of the current word (number of syllables per decisecond)
               so that the word length is proportional to the number of syllables in it.
        
        Args: 
            text:  the plaintext transcription
            total_duration_frames:  the total duration of the speech (in frames)

        Returns:
            feature_array:  a numpy array of shape (305, n_frames) that contains the text features
        """
        print("Estimating word timings with FastText using syllable count.")
        print(f'\nInput text:\n"{text}"')

        # The fillers will be encoded with the same vector
        filler_encoding  = self.embedding["ah"] 
        fillers = ["eh", "ah", "like", "kind of"]
        delimiters = ['.', '!', '?']
        n_syllables = []
        
        # The transcription might contain numbers - we will use the 'inflect' library
        # to convert those to words e.g. 456 to "four hundred fifty-six"
        num_converter = inflect.engine()

        words = []
        for word in text.split():
            # Remove the delimiters
            for d in delimiters:
                word.replace(d, '') 

            # If the current word is not a number, we just append it to the list of words (and calculate the syllable count too)
            if not word.isnumeric() and not word[:-1].isnumeric():
                # NOTE: we check word[:-1] because we want to interpret a string like "456," as a number too
                words.append(word)
                n_syllables.append(count_syllables(word))
            else:
                number_in_words = num_converter.number_to_words(word, andword="")
                # Append each word in the number (e.g. "four hundred fifty-six") to the list of words
                for number_word in number_in_words.split():
                    words.append(number_word)
                    n_syllables.append(count_syllables(number_word))
        
        total_n_syllables = sum(n_syllables)
        elapsed_deciseconds = 0       
        # Shape of (batch_size, frame_length, 305)
        feature_array = []

        for curr_word, word_n_syllables in zip(words, n_syllables):
            # The estimated word durations are proportional to the number of syllables in the word
            if word_n_syllables == 0:
                word_n_syllables = 1

            word_encoding = self.embedding[curr_word]
            # We take the ceiling to not lose information
            # (if the text was shorter than the audio because of rounding errors, then
            #  the audio would be cropped to the text's length)
            w_duration = ceil(total_duration_frames * word_n_syllables / total_n_syllables)
            w_speed = word_n_syllables / w_duration if w_duration > 0 else 10 # Because 10 FPS
            w_start = elapsed_deciseconds
            w_end   = w_start + w_duration
            
            # print("Word: {} | Duration: {} | #Syl: {} | time: {}-{}".format(curr_word, w_duration, word_n_syllables, w_start, w_end))            
            
            while elapsed_deciseconds < w_end:
                elapsed_deciseconds += 1
                
                w_elapsed_time = elapsed_deciseconds - w_start
                w_remaining_time = w_duration - w_elapsed_time + 1
                w_progress = w_elapsed_time / w_duration
                
                frame_features = [ w_elapsed_time,
                                   w_remaining_time,
                                   w_duration,
                                   w_progress,
                                   w_speed ]

                feature_array.append(list(word_encoding) + frame_features)

        return np.array(feature_array)

    def _align_vector_lengths(self, audio_features, text_features):
        # NOTE: at this point audio is 20fps and text is 10fps
        min_len = min(len(audio_features), 2 * len(text_features))
        # make sure the length is even
        if min_len % 2 ==1:
            min_len -= 1

        audio_features, text_features = tools.shorten(audio_features, text_features, min_len)
        # The transcriptions were created with half the audio sampling rate
        # So the text vector should contain half as many elements 
        text_features = text_features[:int(min_len/2)] 

        # upsample the text so that it aligns with the audio
        cols = np.linspace(0, text_features.shape[0], endpoint=False, num=text_features.shape[0] * 2, dtype=int)
        text_features = text_features[cols, :]

        return audio_features, text_features
    
    def _tensor_from_numpy(self, array):
        """Create a tensor from the given numpy array on the same device as the model with the correct dtype."""
        tensor = torch.as_tensor(torch.from_numpy(array), device=self.model.device).float()
        return tensor

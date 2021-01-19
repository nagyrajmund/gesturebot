from transformers import BlenderbotTokenizer, BlenderbotForConditionalGeneration

class Blenderbot:
    def __init__(self):
        # model_name = 'facebook/blenderbot_small-90M'
        model_name = 'facebook/blenderbot-400M-distill'
        # model_name = 'facebook/blenderbot-1B-distill'
        # model_name = 'facebook/blenderbot-3B'
        
        print("Creating model")
        self.model = BlenderbotForConditionalGeneration.from_pretrained(model_name)

        print("Creating tokenizer")
        self.tokenizer = BlenderbotTokenizer.from_pretrained(model_name)

        self.history = []
    
    def generate_reply(self, text_message):
        self.history.append(text_message)
        # Prune the chat history to only keep the last 4 lines. Blenderbot can only take a limited number of tokens as input.
        history_text = "\n".join(self.history[-4:])
        print("Chat history: ")
        print("-" * 16)
        print(history_text)
        print("-" * 16)
        input_tokens = self.tokenizer([history_text], return_tensors = 'pt', truncation = True, max_length = 128)
        reply_tokens = self.model.generate(**input_tokens)
        
        reply_text = self.tokenizer.batch_decode(reply_tokens, skip_special_tokens = True)[0]
        
        print(reply_text)
        # Remove leading space
        reply_text = reply_text[1:]
        self.history.append(reply_text)

        return reply_text

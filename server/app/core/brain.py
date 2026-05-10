from transformers import pipeline

class JarvisBrain:
    def __init__(self):
        self.generator = pipeline(
            "text-generation",
            model="gpt2"
        )

    def think(self, prompt):
        result = self.generator(
            prompt,
            max_length=50,
            num_return_sequences=1
        )

        return result[0]["generated_text"]

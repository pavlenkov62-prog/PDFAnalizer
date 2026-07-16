from deep_translator import GoogleTranslator


class Translator:

    def __init__(self):

        self.translator = GoogleTranslator(
            source="en",
            target="ru"
        )

        self.cache = {}

    def translate(self, text):

        text = text.strip()

        if not text:
            return ""

        if text in self.cache:
            return self.cache[text]

        result = self.translator.translate(text)

        self.cache[text] = result

        return result
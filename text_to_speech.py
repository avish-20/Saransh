from gtts import gTTS


def speech(a):
    myText = a
    language = 'en'
    output = gTTS(text=myText, lang=language, slow=False)
    output.save("output.mp3")

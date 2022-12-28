import wave
import pyaudio
# apt-get install portaudio19-dev

jingleBells = wave.open('assets/Jingle-Bells-Singing-Bell.wav')

jingleBellsPlayer = pyaudio.PyAudio()
jingleBellsStream = jingleBellsPlayer.open(format=jingleBellsPlayer.get_format_from_width(jingleBells.getsampwidth()),
                    channels=jingleBells.getnchannels(),
                    rate=jingleBells.getframerate(),
                    output=True)


chunkSize = 1024
# Play samples from the wave file (3)
data = jingleBells.readframes(chunkSize)
while len(data):
    jingleBellsStream.write(data)
    data = jingleBells.readframes(chunkSize)

jingleBells.close()
# Close stream (4)
jingleBellsStream.close()

# Release PortAudio system resources (5)
jingleBellsPlayer.terminate()
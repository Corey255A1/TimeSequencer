import src.scheduler as scheduler
import wave
import pyaudio
import time

def light1Action(parameters):
    print(parameters)

def light2Action(parameters):
    print(parameters)

def light3Action(parameters):
    print(parameters)

testSequence = scheduler.Scheduler('./tests/bpm_sequence.json')
testSequence.add_action_callback('light1',light1Action)
testSequence.add_action_callback('light2',light2Action)
testSequence.add_action_callback('light3',light3Action)

jingleBellsWaveform = wave.open('assets/Jingle-Bells-Singing-Bell.wav')


def audio_chunk_callback(in_data, frame_count, time_info, status):
    chunk = jingleBellsWaveform.readframes(frame_count)
    testSequence.check_time(time_info['input_buffer_adc_time'])
    return (chunk, pyaudio.paContinue)


jingleBellsPlayer = pyaudio.PyAudio()
jingleBellsStream = jingleBellsPlayer.open(format=jingleBellsPlayer.get_format_from_width(jingleBellsWaveform.getsampwidth()),
                    channels=jingleBellsWaveform.getnchannels(),
                    rate=jingleBellsWaveform.getframerate(),
                    output=True,
                    stream_callback=audio_chunk_callback)


while jingleBellsStream.is_active():
    time.sleep(0.1)

jingleBellsWaveform.close()
jingleBellsStream.close()
jingleBellsPlayer.terminate()

#testThread = scheduler.ScheduleRunner('test', 1/60, testSequence)
#testThread.start()
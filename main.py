import src.scheduler as scheduler


def light1Action(parameters):
    print(parameters)

def light2Action(parameters):
    print(parameters)

def light3Action(parameters):
    print(parameters)

testSequence = scheduler.Scheduler('./tests/standard_sequence.json')
testSequence.add_action_callback('light1',light1Action)
testSequence.add_action_callback('light2',light2Action)
testSequence.add_action_callback('light3',light3Action)

testThread = scheduler.ScheduleRunner('test', 1/60, testSequence)
testThread.start()
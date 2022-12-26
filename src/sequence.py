import json


def timestring_to_seconds(timeString):
    h, m, s = map(float, timeString.split(':'))
    return float(h*3600.0 + m*60.0 + s)


def convert_to_seconds(timeNumberOrString):
    if isinstance(timeNumberOrString, str):
        return timestring_to_seconds(timeNumberOrString)
    else:
        return float(timeNumberOrString)


class SequenceAction:
    def __init__(self, name, parameters):
        self.name = name
        self.parameters = parameters

class StateElement:
    def __init__(self, key, value):
        self.key = key
        self.value = value

class State:
    def __init__(self, statesList):
        self.states = {}
        for i in range(0, len(statesList)):
            self.states[statesList[i]] = StateElement(statesList[i], i)

    def print_all_states(self):
        for (k, v) in self.states.items():
            print(f'{k}, {v.value}')

    def get_state_name_by_value(self, value):
        for (k, v) in self.states.items():
            if v.value == value:
                return k
        return None
    
    def __getitem__(self, name):
        if name in self.states:
            return self.states[name]
        else:
            return None


class SequenceElement:
    TRIGGER_STATES = State([
            'pre_trigger', 
            'triggered',
            'trigger_complete'
        ])
    SEQUENCE_TYPES = State([
            'once', 
            'periodic'
        ])
    def __init__(self, actionsList, type):
        self.type = type
        self.currentTriggerState = SequenceElement.TRIGGER_STATES['pre_trigger']
        self.actions = actionsList

    def set_trigger_state(self, state):
        self.currentTriggerState = SequenceElement.TRIGGER_STATES[state]

    def check_trigger(self, time):
        return self.currentTriggerState


class SequenceOnceElement(SequenceElement):
    def __init__(self, actionsList,  startTime):
        super().__init__(actionsList, SequenceElement.SEQUENCE_TYPES['once'])

        self.startTime = convert_to_seconds(startTime)

    def check_trigger(self, time):
        if time >= self.startTime:
            if self.currentTriggerState == SequenceElement.TRIGGER_STATES['pre_trigger']:
                self.set_trigger_state('triggered')
            elif self.currentTriggerState == SequenceElement.TRIGGER_STATES['triggered']:
                self.set_trigger_state('trigger_complete')

        return self.currentTriggerState


class SequencePeriodicElement(SequenceElement):
    def __init__(self, actionsList, startTime, endTime, period):
        super().__init__(actionsList, SequenceElement.SEQUENCE_TYPES['periodic'])
        self.startTime = convert_to_seconds(startTime)
        self.endTime = convert_to_seconds(endTime)
        self.period = convert_to_seconds(period)
        self.nextTime = self.startTime + self.period

    def check_trigger(self, time):
        if time >= self.endTime:
            if self.currentTriggerState != SequenceElement.TRIGGER_STATES['trigger_complete']:
                self.set_trigger_state('trigger_complete')
        elif time < self.nextTime:
            if self.currentTriggerState != SequenceElement.TRIGGER_STATES['pre_trigger']:
                self.set_trigger_state('pre_trigger')
        elif time >= self.nextTime:
            if self.currentTriggerState == SequenceElement.TRIGGER_STATES['pre_trigger']:
                self.set_trigger_state('triggered')
                self.nextTime = self.nextTime + self.period

        
        return self.currentTriggerState


class Sequence:
    def __init__(self, filePath):
        self.sequence = []
        self.activeSequence = []
        self.completeSequenceElements = []
        self.mappedActions = {}

        if filePath != None:
            self.load_from_file(filePath)
            self.reset_sequence()

    def reset_sequence(self):
        self.activeSequence = self.sequence.copy()

    def load_from_file(self, filePath):
        file = open(filePath, 'r')
        data = json.load(file)
        for element in data['sequence']:
            if element['type'] == 'once':
                self.sequence.append(
                    SequenceOnceElement(
                        element['actions'],
                        element['startTime']))

            elif element['type'] == 'periodic':
                self.sequence.append(
                    SequencePeriodicElement(
                        element['actions'],
                        element['startTime'],
                        element['endTime'],
                        element['period']))

    def add_action_callback(self, name, function):
        self.mappedActions[name] = function

    def check_triggers(self, time):
        for sequenceElement in self.activeSequence:
            triggerState = sequenceElement.check_trigger(time)
            if triggerState == SequenceElement.TRIGGER_STATES['triggered']:
                for action in sequenceElement.actions:
                    if action['name'] in self.mappedActions:
                        self.mappedActions[action['name']](action['parameters'])
            elif triggerState == SequenceElement.TRIGGER_STATES['trigger_complete']:
                self.completeSequenceElements.append(sequenceElement)

        for completed in self.completeSequenceElements:
            self.activeSequence.remove(completed)

        self.completeSequenceElements.clear()


if __name__ == '__main__':
    def light1Action(parameters):
        print(parameters)

    def light2Action(parameters):
        print(parameters)
    
    def light3Action(parameters):
        print(parameters)

    testSequence = Sequence('../tests/standard_sequence.json')
    testSequence.add_action_callback('light1',light1Action)
    testSequence.add_action_callback('light2',light2Action)
    testSequence.add_action_callback('light3',light3Action)
    SequenceElement.TRIGGER_STATES.print_all_states()
    time = 0.0
    while time <= 34.0:
        #print(time)
        testSequence.check_triggers(time)
        time += 0.016

import json
import threading
import time

def timestring_to_seconds(timeString):
    h, m, s = map(float, timeString.split(':'))
    return float(h*3600.0 + m*60.0 + s)


def convert_to_seconds(timeNumberOrString):
    if isinstance(timeNumberOrString, str):
        return timestring_to_seconds(timeNumberOrString)
    else:
        return float(timeNumberOrString)




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

class TriggerState:
    TRIGGER_STATES = State([
            'disarmed',
            'pre_trigger', 
            'triggered',
            'trigger_complete'
        ])

    def __init__(self):
        self.triggerState = TriggerState.TRIGGER_STATES['pre_trigger']

    def set_trigger_state(self, state):
        #print(state)
        self.triggerState = TriggerState.TRIGGER_STATES[state]

    def reset(self):
        self.set_trigger_state('pre_trigger')

class TimeTrigger(TriggerState):
    TRIGGER_TYPES = State([
        'once', 
        'periodic'
    ])
    def __init__(self, type):
        super().__init__()
        self.type = type

class TriggerAction:
    def __init__(self, name, parameters):
        self.name = name
        self.parameters = parameters

    def can_do_action(self):
        return True
    

class TimeRelativeTriggerAction(TriggerAction, TriggerState):
    def __init__(self, name, offsetTime, parameters):
        super().__init__(name, parameters)
        super(TriggerAction, self).__init__()
        self.relativeStartTime = 0
        self.currentTime = 0
        self.offsetTime = timestring_to_seconds(offsetTime)
        self.set_trigger_state('disarmed')

    def set_relative_start(self, time):
        self.relativeStartTime = time

    def set_current_time(self, time):
        self.currentTime = time - self.relativeStartTime

    def can_do_action(self):
        if self.triggerState == TriggerState.TRIGGER_STATES['disarmed']:
            return False

        if self.currentTime >= self.offsetTime:
            if self.triggerState == TriggerState.TRIGGER_STATES['pre_trigger']:
                self.set_trigger_state('triggered')
            elif self.triggerState == TriggerState.TRIGGER_STATES['triggered']:
                self.set_trigger_state('trigger_complete')

        return self.triggerState == TriggerState.TRIGGER_STATES['triggered']

class TimeTriggerAction(TimeTrigger):
    def __init__(self, type, actionsList):
        super().__init__(type)
        self.actions = []
        self.currentActiveActions = []
        for action in actionsList:
            if 'offsetTime' in action:
                self.actions.append(TimeRelativeTriggerAction(action['name'], action['offsetTime'], action['parameters']))
            else:
                self.actions.append(TriggerAction(action['name'], action['parameters']))
        self.remainingActions = self.actions.copy()
    
    def reset_actions(self):
        self.remainingActions = self.actions.copy()

    def reset(self):
        self.reset_actions()
        return super().reset()

    def has_remaining_actions(self):
        return len(self.remainingActions)

    def check_time(self, time):
        if not self.has_remaining_actions():
            return []

        self.currentActiveActions.clear()
        tempActions = self.remainingActions.copy()
        isTriggered = self.triggerState == TriggerState.TRIGGER_STATES['triggered']
        for action in tempActions:
            #print(action.name)
            checkAction = isTriggered
            if isinstance(action, TimeRelativeTriggerAction):
                if isTriggered:
                    action.reset()
                    action.set_relative_start(time)
                checkAction = True
                action.set_current_time(time)

            if checkAction and action.can_do_action():
                self.currentActiveActions.append(action)
                self.remainingActions.remove(action)

        return self.currentActiveActions

class TriggerOnce(TimeTriggerAction):
    def __init__(self, actionsList, startTime):
        super().__init__(TimeTrigger.TRIGGER_TYPES['once'], actionsList)
        self.startTime = convert_to_seconds(startTime)
        self.reset()

    def check_time(self, time):
        if time >= self.startTime:
            if self.triggerState == TriggerState.TRIGGER_STATES['pre_trigger']:
                self.set_trigger_state('triggered')

            elif self.triggerState == TriggerState.TRIGGER_STATES['triggered']:
                self.set_trigger_state('trigger_complete')

        return super().check_time(time)
    

class TriggerPeriodic(TimeTriggerAction):
    def __init__(self, actionsList, startTime, endTime, period):
        super().__init__(TimeTrigger.TRIGGER_TYPES['periodic'], actionsList)
        self.startTime = convert_to_seconds(startTime)
        self.endTime = convert_to_seconds(endTime)
        self.period = convert_to_seconds(period)
        self.nextTime = 0
        self.reset()

    def check_time(self, time):
        if time >= self.endTime:
            if self.triggerState != TriggerState.TRIGGER_STATES['trigger_complete']:
                self.set_trigger_state('trigger_complete')

        elif time < self.nextTime:
            if self.triggerState != TriggerState.TRIGGER_STATES['pre_trigger']:
                self.reset_actions()
                self.set_trigger_state('pre_trigger')

        elif time >= self.nextTime:
            if self.triggerState == TriggerState.TRIGGER_STATES['pre_trigger']:
                self.set_trigger_state('triggered')
                self.nextTime = self.nextTime + self.period
        return super().check_time(time)

    def reset_time(self):
        self.nextTime = self.startTime + self.period

    def reset(self):
        self.reset_time()
        return super().reset()


class Sequence:
    def __init__(self, filePath):
        self.sequence = []
        self.activeSequence = []
        self.completeSequenceElements = []
        self.mappedActions = {}

        if filePath != None:
            self.load_from_file(filePath)
            self.reset()

    def reset(self):
        self.activeSequence.clear()
        for element in self.sequence:
            element.reset()
            self.activeSequence.append(element)

    def is_active(self):
        return len(self.activeSequence) > 0

    def load_from_file(self, filePath):
        file = open(filePath, 'r')
        data = json.load(file)
        for element in data['sequence']:
            if element['type'] == 'once':
                self.sequence.append(
                    TriggerOnce(
                        element['actions'],
                        element['startTime']))

            elif element['type'] == 'periodic':
                self.sequence.append(
                    TriggerPeriodic(
                        element['actions'],
                        element['startTime'],
                        element['endTime'],
                        element['period']))

    def add_action_callback(self, name, function):
        self.mappedActions[name] = function

    def check_triggers(self, time):
        for sequenceElement in self.activeSequence:
            triggeredActions = sequenceElement.check_time(time)
            for action in triggeredActions:
                if action.name in self.mappedActions:
                    self.mappedActions[action.name](action.parameters)
            if not sequenceElement.has_remaining_actions():
                self.completeSequenceElements.append(sequenceElement)

        for completed in self.completeSequenceElements:
            self.activeSequence.remove(completed)

        self.completeSequenceElements.clear()
        return self.is_active()


class SequenceRunner:
    def __init__(self, name, rate, sequence):
        self.name = name
        self.running = False
        self.startTime = 0
        self.rate = rate
        self.sequence = sequence
        self.thread = None

    def check_times_thread(self):
        while self.running:
            start = time.perf_counter()
            if self.sequence.check_triggers(start - self.startTime):
                end = time.perf_counter()
                time.sleep(self.rate - (end - start))
            else:
                self.running = False

    def start(self):
        if self.thread == None:
            self.running = True
            self.sequence.reset()
            self.startTime = time.perf_counter()
            self.thread = threading.Thread(target=self.check_times_thread)
            self.thread.start()

    def stop(self):
        self.running = False
        if self.thread != None:
            self.thread.join()
            self.thread = None

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
    TimeTrigger.TRIGGER_STATES.print_all_states()
    print('--- testing steps ---')
    testTime = 0.0
    while testTime <= 34.0:
        #print(testTime)
        testSequence.check_triggers(testTime)
        testTime += 0.5
    print('--- testing thread ---')
    testTread = SequenceRunner('test', 1/60, testSequence)
    testTread.start()

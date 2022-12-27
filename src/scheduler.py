
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


class Action:
    def __init__(self, name, parameters, delayTime=0.0) -> None:
        self.name = name
        self.parameters = parameters
        self.isDelayed = delayTime > 0.0
        self.delayTime = delayTime

    def parse_action_json_array(jsonArray):
        actions = []
        for action in jsonArray:
            if 'delayTime' in action:
                actions.append(Action(
                    action['name'], 
                    action['parameters'], 
                    timestring_to_seconds(action['delayTime'])))
            else:
                actions.append(Action(
                    action['name'], 
                    action['parameters']))
        return actions


class TimeAction:
    DISARMED=1
    ARMED=2
    TRIGGERED=3
    COMPLETE=4
    def __init__(self, actionList, triggerTime, autoResetPeriod=0.0, endTime=float('inf')):
        self.actionList = actionList
        self.initialTriggerTime = triggerTime
        self.nextTriggerTime = triggerTime
        self.endTime = endTime
        self.autoResetPeriod = autoResetPeriod
        self.state = TimeAction.ARMED
        self.scheduler_reference = None

    def set_scheduler(self, scheduler):
        self.scheduler_reference = scheduler

    def reset(self):
        self.nextTriggerTime = self.initialTriggerTime
        self.state = TimeAction.ARMED

    def check_time(self, currentTime):
        if currentTime >= self.endTime:
            self.state = TimeAction.COMPLETE

        elif currentTime >= self.nextTriggerTime:
            if self.state == TimeAction.ARMED:
                self.state = TimeAction.TRIGGERED
                if self.autoResetPeriod > 0:
                    self.nextTriggerTime += self.autoResetPeriod
        
            elif self.autoResetPeriod == 0 and self.state == TimeAction.TRIGGERED:
                self.state = TimeAction.COMPLETE

        elif self.autoResetPeriod > 0 and self.state == TimeAction.TRIGGERED:
            self.state = TimeAction.ARMED

        return self.state

class Scheduler:
    def __init__(self, filePath=None):
        self.scheduledActions = []
        self.activeActions = []
        self.callbacks = {}
        if filePath != None:
            self.load_from_file(filePath)
            self.reset()

    def load_from_file(self, filePath):
        file = open(filePath, 'r')
        data = json.load(file)
        for element in data['sequence']:
            if element['type'] == 'once':
                self.schedule_action(
                    TimeAction(
                        Action.parse_action_json_array(element['actions']),
                        timestring_to_seconds(element['startTime'])))

            elif element['type'] == 'periodic':
                self.schedule_action(
                    TimeAction(
                        Action.parse_action_json_array(element['actions']),
                        timestring_to_seconds(element['startTime']),
                        timestring_to_seconds(element['period']),
                        timestring_to_seconds(element['endTime'])))

    def has_active_actions(self):
        return len(self.activeActions)

    def reset(self):
        self.activeActions.clear()
        for action in self.scheduledActions:
            action.reset()
            self.activeActions.append(action)

    def do_action(self, currentTime, action):
        if action.isDelayed:
            self.activeActions.append(
                TimeAction(
                    [Action(action.name, action.parameters)],
                    currentTime+action.delayTime))
        elif action.name in self.callbacks:
            self.callbacks[action.name](action.parameters)

    def schedule_action(self, action):
        self.activeActions.append(action)
        self.scheduledActions.append(action)

    def add_action_callback(self, actionName, callback):
        self.callbacks[actionName] = callback

    def check_time(self, currentTime):
        frameActions = self.activeActions.copy()
        for action in frameActions:
            triggerState = action.check_time(currentTime)
            if triggerState == TimeAction.TRIGGERED:
                for callback in action.actionList:
                    self.do_action(currentTime, callback)
            elif triggerState == TimeAction.COMPLETE:
                self.activeActions.remove(action)


class ScheduleRunner:
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
            if self.sequence.has_active_actions():
                self.sequence.check_time(start - self.startTime)
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

    testSequence = Scheduler('../tests/standard_sequence.json')
    testSequence.add_action_callback('light1',light1Action)
    testSequence.add_action_callback('light2',light2Action)
    testSequence.add_action_callback('light3',light3Action)
    # testSequence.schedule_action(TimeAction([\
    #     Action('light1', {'output':'off'}),\
    #     Action('light2', {'output':'on'}, 0.5)\
    #     ], 10.0, 2.0, 25.0))
    
    print('--- testing steps ---')
    testTime = 0.0
    while testTime <= 34.0:
        #print(testTime)
        testSequence.check_time(testTime)
        testTime += 0.5

    print('--- testing reset ---')
    testSequence.reset()
    testTime = 0.0
    while testTime <= 34.0:
        #print(testTime)
        testSequence.check_time(testTime)
        if not testSequence.has_active_actions():
            print('nothing else')
            break
        testTime += 0.5

    print('--- testing thread ---')
    testThread = ScheduleRunner('test', 1/60, testSequence)
    testThread.start()
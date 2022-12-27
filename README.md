# Sequencer
This project was born from an idea to sequence a Christmas Light display. Rather than hard code some predefined songs, I imagined a way to read a file that defines actions to be taken at certain times.

## Basic Requirements
- Schedule actions to take place at a time.
- Schedule actions that are periodic.
  - Define a start and stop time for the periodic action.
  - Define the period length
- Schedule actions to take place at a relative amount of time from a trigger

## Code Design
**Sequencer**  
60Hz loop should be good enough time step resolution for queueing actions on beats in most songs.
ScheduleRunner can specify the clock rate of execution

Actions that take place should be generic. I want to use this scheduler for more than toggling GPIOs from a Raspberry PI to toggle Christmas Lights. I'd like it to be generic enough that I could do that, send out web requests, or toggle things over websockets.

A sequence JSON has an array of schedule objects. They are either a once or periodic.  
The once objects are executed once during a cycle.  
The periodic objects execute starting at the start time and then fire every period. If there is an endTime, the periodic execution ends at that time.  
The actions list specify the name of the actions that should be invoked. Each action can include a delayTime. Those actions are invoked after the delayTime after the schedule object is triggered.  
The parameters as part of the actions are passed to the callback function as the json object



## File Definition
~~~
{
    "sequence":[
       {
            "type":"once",
            "startTime":"00:00:30.1",
            "actions":[
                {
                    "name":"light1",
                    "parameters":{
                        "output":"on"
                    }
                },
                {
                    "delayTime":"00:00:02.0",
                    "name":"light3",
                    "parameters":{
                        "output":"off"
                    }
                }
            ]
        },
        {
            "type":"periodic",
            "period":"00:00:01.0",
            "startTime":"00:00:00.0",
            "endTime":"00:01:00.0",
            "actions":[
                {
                    "name":"light2",
                    "parameters":{
                        "output":"toggle"
                    }
                }
            ]
        }

    ]
}
~~~
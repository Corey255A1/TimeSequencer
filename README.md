# Sequencer
This project was born from an idea to sequence a Christmas Light display. Rather than hard code some predefined songs, I imagined a way to read a file that defines actions to be taken at certain times.

## Basic Requirements
- Schedule actions to take place at a time.
- Schedule actions that are periodic.
  - Define a start and stop time for the periodic action.
  - Define the period length

## Code Design
**Sequencer**  
60Hz loop should be good enough time step resolution for queueing actions on beats in most songs

Actions that take place should be generic. I want to use this scheduler for more than toggling GPIOs from a Raspberry PI to toggle Christmas Lights. I'd like it to be generic enough that I could do that, send out web requests, or toggle things over websockets.


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
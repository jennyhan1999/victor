from transitions import Machine
import run, time


class VictorFSM(object):
    '''
    def __init__(self):
        
        self.states = ["init_wait","wait_sit","invite_play","join_gaim","goodbye"]
        self.actions = ["doStep"]
        #self.sensordata = {"coffeedonetime":datetime.datetime.now(), "podpresent":False,"smallbuttonpressed":False, "medbuttonpressed":False, "largebuttonpressed":False, "startbuttonpressed": False, "watertemp":65}

        #assumes logging is initialized already
        logging.getLogger('transitions').setLevel(logging.INFO)
        self.actionlogger = logging.getLogger('actions')
        self.actionlogger.setLevel(logging.INFO)
        self.sensorlogger = logging.getLogger('actions')
        self.sensorlogger.setLevel(logging.INFO)

        # Initialize the state machine
        self.machine = Machine(model=self, states=self.states, initial='empty', ignore_invalid_triggers=True)
        self.machine.add_transition(trigger="doStep", source="init_wait", dest="invite_play", conditions=["detect_person"])
        self.machine.add_transition(trigger="doStep", source="invite_play", dest="join_game", conditions=["person_sit"])
        self.machine.add_transition(trigger="doStep", source="join_game", dest="goodbye", conditions=["game_player_left"])
        
    def detect_person(self):
        return self.sensordata["podpresent"]
    def person_sit(self):
        return self.sensordata["podpresent"]
    def game_player_left(self):
        return self.sensordata["podpresent"]

    def
    '''
    def __init__(self):
        states = ["init_wait","wait_sit", "invite_play","play_game","goodbye_with_players"]
        transitions = [
            {
                "trigger": "detectPerson",
                "source": "init_wait",
                "dest": "invite_play",
                "before": "init_wait_before",
                "after": "detected_potential_person"
            },
            {
                "trigger": "personSit",
                "source": "invite_play",
                "dest": "play_game",
                #"before": "",
                "after": "invite_to_play_game"
            },
            {
                "trigger": "personLeft_withPlayers",
                "source": "play_game",
                "dest": "goodbye_with_players",
                #"before": "",
                "after": "play_game"
            },
            # {
            #     "trigger": "personSit",
            #     "source": "goodbye_with_players",
            #     "dest": "play_game",
            #     #"before": "",
            #     "after": "goodbye"
            # },
            {
                "trigger": "personLeft_noPlayers",
                "source": "play_game",
                "dest": "goodbye",
                #"before": "",
                "after": "goodbye"
            }
        ]
        
        self.machine = Machine(self, states=states, transitions=transitions, initial="init_wait")
    
    def init_wait_before(self):
        print("waiting for person....")
    def detected_potential_person(self):
        print("found potential person...")
    def invite_to_play_game(self):
        print("VICTORSPEAK: Do you want to join game?")
    def goodbye(self):
        print("VICTORSPEAK: See you later!") 



Victor = VictorFSM()
CONTEXT = None

def update_victor_context(new_context, key):
    global Victor
    # print("new: ",new_context)
    # print("old: ",CONTEXT)
    # #raise Error
    if key == "number_potential":
        update_potential(new_context)
    elif key == "number_players":
        update_game_context(new_context)
    elif key == "number_left":
        print(new_context)
        raise Error
        update_game_left(new_context)
    else:
        pass

def update_potential(new_context):
    global CONTEXT

    if (new_context["number_potential"] >= CONTEXT["POTENTIAL_PLAYERS"]["number_potential"]
        and new_context["number_potential"]>0):
            print("new: ",new_context)
            print("old: ",CONTEXT)
            
            new_id = CONTEXT["GAME_CONTEXT"]["players_id"].difference (new_context["potential_id"])
            print("hello to ",new_id)
            if new_id:
                try:
                    if CONTEXT["GAME_CONTEXT"]["number_players"] > 0:
                        run.set_victor_speech("Scared of losing?! Goodbye!")
                        Victor.personLeft_withPlayers()
                        run.update_game_state(Victor.state)

                    else:
                        Victor.personLeft_noPlayers()
                        run.update_game_state(Victor.state)
                        run.set_victor_speech("I guess no one can take me on!")
                except:
                    print (Victor.state)
                    print("cannot remove person in this state")
                    print ("context is ", CONTEXT)
                    #raise Error
                #raise Error 
            else: 
                try:
                    Victor.detectPerson()
                    run.update_game_state(Victor.state)
                    run.set_victor_speech("Hey you! Want to play scrabble?")
                except:
                    print(Victor.state)

                    print("cannot add person in this state")
    CONTEXT['POTENTIAL_PLAYERS'] = new_context

def update_game_context(new_context):
    global CONTEXT
    print(CONTEXT)

    if (new_context["number_players"] >= CONTEXT["GAME_CONTEXT"]["number_players"]
        and new_context["number_players"]>0):
            try:
                Victor.personSit()
                run.update_game_state(Victor.state)
                print(Victor.state)
                run.set_victor_speech("Can't wait for another victory!")
            except:
                print(Victor.state)
                print("cannot add person in this state")
    if new_context["number_players"] < CONTEXT["GAME_CONTEXT"]["number_players"]:
        #or CONTEXT["GAME_CONTEXT"]["number_players"]  == 0): #TODO: add goodbye state
            raise Error
            try:
                Victor.personLeft()
                run.update_game_state(Victor.state)
                run.set_victor_speech("Scared of losing?! Goodbye!")
            except:
                print("cannot remove person in this state")
                print ("context is ", CONTEXT)
                raise Error
    if CONTEXT["GAME_CONTEXT"]["number_players"] == 0:
        try:
            Victor.personLeft_noPlayers()
            run.update_game_state(Victor.state)
            run.set_victor_speech("I am undefeatable!")
        except:
            print(Victor.state)
            print("cannot remove person in this state")
            print ("context is ", CONTEXT)


    CONTEXT["GAME_CONTEXT"] = new_context

def set_game_context(c):
    global CONTEXT
    CONTEXT = c

def main():
    run.update_game_state(Victor.state)
    run.main()    
    '''Victor = VictorFSM()
    print(Victor.state)
    Victor.detectPerson()
    print(Victor.state)
    Victor.personSit()
    print(Victor.state)
    Victor.personLeft()
    print(Victor.state)'''


if __name__ == "__main__":
    main()

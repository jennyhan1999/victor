import victor_fsm

class DetectChangesDict(dict):
    '''def __setitem__(self, item, value):
        print("You are changing the value of {} to {}!!".format(item, value))
        super(DetectChangesDict, self).__setitem__(item, value)
        #victor_fsm.update_victor_context(self)
    '''
    def __init__(self,initialDict):
        for k,v in initialDict.items():
          if isinstance(v,dict):
            initialDict[k] = DetectChangesDict(v)
        super().__init__(initialDict)
        victor_fsm.set_game_context (self)
    def __setitem__(self, item, value):
        print("You are changing the value of {} to {}!!".format(item, value))
        super(DetectChangesDict, self).__setitem__(item, value)
        victor_fsm.update_victor_context(self,item)

    '''def __setitem__(self, item, value):
        if isinstance(value,dict):
          _value = DetectChangesDict(value)
        else:
          _value = value
        print("You are changing the value of {} to {}!!".format(item, _value))
        super().__setitem__(item, _value)
        victor_fsm.update_victor_context(self,item)'''


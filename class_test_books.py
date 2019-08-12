from runbook import Runbook



class BookA(Runbook):
    
    def step_b1():
        pass


class BookB(Runbook):
    
    def step_a2(self):
        pass
    
    @staticmethod
    def step_a3():
        pass
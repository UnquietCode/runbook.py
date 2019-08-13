from unquietcode.tools.runbook import Runbook

    
class CustomRunbook(Runbook):
   
    def first_step(self):
        """
        Do ABC now.
        """
    
    
    def second_step():
        """Do EFG then wait 1 hour."""


    def third_step(skippable=False, critical=True):
        value = "string"
        return f"a custom {value}"
    
    
    def last_step(name='the end'):
        pass

    
if __name__ == '__main__':
    CustomRunbook.main()
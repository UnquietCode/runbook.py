from runbook import Runbook

    
class CustomRunbook(Runbook):
   
    def first_step(self):
        """
        Do ABC now.
        """
    
    def gird_step(self):
        pass
        
    def second_step():
        """
        Do EFG then wait 1 hour.
        """

    def bthird_step():
        value = "string"
        return f"a custom {value}"
    
    def last_step():
        """nah"""

    
if __name__ == '__main__':
    CustomRunbook.main()

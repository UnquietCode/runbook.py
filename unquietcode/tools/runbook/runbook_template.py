import re


TEMPLATE = """
from unquietcode.tools.runbook import Runbook

    
class {name}(Runbook):
    \"\"\"
    Welcome to your new Runbook!
    
    This is the preamble. It will be displayed in the console before
    each run of the book.
    \"\"\"
    
    def First_Step():
        \"\"\"
        Describe your first step here. The name of the step is the name
        of the method, and the description comes from either the method's
        docstring or the value returned from invoking the method.
        \"\"\"
    
    def the_second_step(repeatable=True, name="Second Step"):
        \"\"\"
        Steps are read in the order they are defined in the file.
        
        You can pass in extra keyword settings to customize the step:
        
        * `repeatable` – step can be repeated when resuming
        * `skippable` – step can be skipped by answering no
        * `critical` – step cannot be skipped and must be affirmative
        * `name` – alternative title for the step
        \"\"\"


if __name__ == '__main__':
    {name}.main()
"""

def format_template(runbook_name):
    return TEMPLATE.strip().format(
        name=runbook_name,
    )
	

def create_new_runbook(title):
	parts = re.split(r'\s+', title)
	runbook_class = ""
	runbook_file = ""
	
	for part in parts:
		runbook_class += part[0].upper()
		runbook_class += part[1:]
		
		runbook_file += part.lower()
		runbook_file += '_'
	
	runbook_file = runbook_file[0:-1] + '.py'
	runbook_contents = format_template(runbook_class)
	
	with open(runbook_file, 'w+') as file_:
		file_.write(runbook_contents)
	
	return runbook_file
import re
import inspect
import textwrap
from typing import List
from dataclasses import dataclass
from time import sleep
from datetime import datetime


@dataclass(frozen=True)
class Step:
    name: str
    description: str


class Runbook:
    
    def __init__(self, file_name):
        if not file_name:
            raise Exception('file name must be provided')
    
        self.file_name = file_name
    
    
    @classmethod
    def main(cls):
        # TODO use optparse, sys to get sole filename as input
        instance = cls(file_name=f"{cls.__name__.lower()}.log")
        instance.run()
    
        
    def run(self):        
        for step in self._get_steps():
            print("\n")

            # print step information
            print(step.description)
            print()
            
            # pause for some seconds to give time to read
            pause_time = max((len(step.description) * 0.01), 1.65)
            sleep(pause_time)
            
            # ask for input
            print("\tDid you do the thing?")
            plain_response = input("\t~> ").strip()
            response = plain_response.lower()
                        
            # handle positive response
            if response in {"yes", "y", "yep"}:
                self._write_result(step, plain_response)
                continue
            
            # handle negative response
            elif response in {"no", "n", "nope"}:
                print("\n\tWhy not?")
                reason = input("\t~> ").strip()
                self._write_result(step, plain_response, negative=True, reason=reason)
            
            else:
                print("invalid response")
                # TODO go back to top of this loop
            
        # TODO handle canceling input / sigtrap        
        
        print()
        return None
    
    
    def _get_steps(self) -> List[Step]:
        methods = inspect.getmembers(self, predicate=inspect.ismethod)
        steps:List[Step] = []
        
        for method_name, method in methods:

            # check method name
            if not re.match(r"^[a-zA-Z].*$", method_name):
                continue
                
            if method_name in {'run', 'main'}:
                continue        

            step_name = method_name.replace("_", " ")
            
            # if method is zero arg, call the unbound class method
            # (as a convenience for @staticmethod)
            function_signature = inspect.signature(method.__func__)
            
            if len(function_signature.parameters) == 0:
                method = getattr(type(self), method_name)
                
            step_description = method() # todo support methods with or without self

            # use docstring if empty
            if step_description is not None:
                step_description = textwrap.dedent(step_description).strip()
            else:
                step_description = textwrap.dedent(method.__doc__).strip()
            
            # use empty string if still empty
            if step_description is None:
                step_description = ""
                    
            # convert anything to string
            else:
                step_description = str(step_description)
            
            steps.append(Step(
                name=step_name,
                description=step_description,
            ))
        
        return steps
    
    # TODO if file exists offer continue from where they left off
    
    def _write_result(self, step:Step, result, negative=False, reason=None):
        # TODO file path
        with open(self.file_name, "a+") as file:
            file.write(f"### ")
            
            if negative is True:            
                file.write(f"~~{step.name}~~")
            else:
                file.write(f"{step.name}")
            
            file.write("\n```\n")
            file.write(step.description)
            file.write("\n```\n")
            file.write(f"> {result} ({datetime.now()})\n")
            
            if negative is True:
                file.write(f"\n> {reason}\n")
            
            file.write("\n")    
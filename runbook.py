import re
import os
import sys
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
    
    def __init__(self, file_path):
        if not file_path:
            raise Exception('file path must be provided')
    
        self.file_path = file_path
    
    
    @classmethod
    def main(cls):
        if len(sys.argv) > 1:
            file_name = sys.argv[1]
        else:
            file_name = f"{cls.__name__.lower()}.log"
            
        file_path = f"{os.getcwd()}/{file_name}"
        
        # TODO use optparse, sys to get sole filename as input
        instance = cls(file_path=file_path)
        instance.run()
    
        
    def run(self):
        
        # check for existing steps
        if os.path.isfile(self.file_path):
            print()
            print("(reading existing file...)")
            existing_steps = self._read_file(self.file_path)
            resumed = True
        else:
            existing_steps = []
            resumed = False
        
        current_existing_step = 0
        
        for step in self._get_steps():
            print()

            # handle existing steps
            if len(existing_steps) > current_existing_step:
                existing_step = existing_steps[current_existing_step]
                
                if step.name == existing_step.name:
                    print(f"(skipping already completed step '{step.name}')")
                    current_existing_step += 1
                    continue
                else:
                    print(f"(found new step '{step.name}')")
                    print()
            
            elif resumed is True:
                print(f"(resuming from step '{step.name}')\n")
                resumed = False
            
            # print step information
            if step.description:
                print(step.description)
            else:
                print(step.name)
            
            print()
            
            # pause for some seconds to give time to read
            pause_time = max((len(step.description) * 0.095), 1.05)
            sleep(pause_time)
            
            # ask for input
            print("\tDid you do the thing?")
            sentiment, response, plain_response = self._wait_for_response()

            if sentiment is True:
                self._write_result(step, plain_response)
                continue
            
            # handle negative response
            elif sentiment is False:
                print("\n\tWhy not?")
                reason = input("\t~> ").strip()
                self._write_result(step, plain_response, negative=True, reason=reason)
        
        print()
        return None
    
    
    def _wait_for_response(self):
        while True:
            plain_response = input("\t~> ").strip()
            response = plain_response.lower()
            
            if response in {"yes", "y", "yep"}:
                return True, response, plain_response
            elif response in {"no", "n", "nope"}:
                return False, response, plain_response
            else:
                print("\n\tinvalid response\n")
        
    
    def _get_steps(self) -> List[Step]:
        
        # get all methods in the class
        methods = inspect.getmembers(self, predicate=inspect.ismethod)
        
        # sort methods by declaration order
        methods = sorted(methods, key=lambda _: _[1].__func__.__code__.co_firstlineno)
        
        # build up a list of steps
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
                
            step_description = method()

            if step_description is not None:
                step_description = str(step_description)
                step_description = textwrap.dedent(step_description).strip()
            
            # use docstring if empty
            elif method.__doc__ is not None:
                step_description = textwrap.dedent(method.__doc__).strip()
            
            # use empty string if still empty
            else:
                step_description = ""
            
            steps.append(Step(
                name=step_name,
                description=step_description,
            ))
        
        return steps
    
    
    @staticmethod
    def _read_file(file_path):
        steps = []
        
        with open(file_path, "r+") as file:
            line = file.readline()
            
            while line:
                if re.match(r"^### [a-zA-Z].*$", line):
                    steps.append(Step(
                        name=line[4:-1],
                        description="",
                    ))
                
                elif re.match(r"^### ~~[a-zA-Z].*~~$", line):
                    steps.append(Step(
                        name=line[6:-3],
                        description="",
                    ))
                
                line = file.readline()
        
        return steps
        
    
    def _write_result(self, step:Step, result, negative=False, reason=None):
        with open(self.file_path, "a+") as file:
            
            # write name header
            file.write(f"### ")
            
            if negative is True:
                file.write(f"~~{step.name}~~")
            else:
                file.write(f"{step.name}")
            
            # write description, if present
            if step.description:
                file.write("\n```\n")
                file.write(step.description)
                file.write("\n```\n")
            else:
                file.write("\n")
            
            # write generic response line
            file.write(f"responded `{result}` at {datetime.now().strftime('%H:%M:%S')} on {datetime.now().strftime('%d/%m/%Y')}\n")
            
            # write negative response line
            if negative is True:
                file.write("\n")
                file.write("Reason given:\n")
                file.write(f"> {reason}\n")
            
            file.write("\n\n")
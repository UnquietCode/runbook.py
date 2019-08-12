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
        
        if len(sys.argv) > 2:
            print("usage: (log file path)")
            exit(1)
        
        elif len(sys.argv) > 1:
            file_name = sys.argv[1]
        
        else:
            
            # split by capital letters and add underscore
            pretty_class_name = re.sub(
                string=cls.__name__,
                pattern=r'([A-Z])',
                repl='_\\1',
            ).lower()
            
            # handles "ACustomClass" name strings
            if pretty_class_name.startswith('_'):
                pretty_class_name = pretty_class_name[1:]
            
            file_name = f"{pretty_class_name}.log"
        
        # set file path relative to current script working directory
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
            pause_time = max((len(step.description) * 0.075), 1.05)
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
        
        # build up a list of steps
        methods = self._get_ordered_methods()
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
            function = method.__func__ if hasattr(method, '__func__') else method
            function_signature = inspect.signature(function)
            
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
    
    
    def _get_ordered_methods(self):
        
        # list class hierarchy, in order
        classes = list(inspect.getmro(type(self)))
        classes.reverse()
        
        # list methods by class, in order
        methods_by_class = {}
        all_methods_by_class = {}
        
        for c in classes:
            methods_by_class[c] = inspect.getmembers(c, lambda _:inspect.ismethod(_) or inspect.isfunction(_))
            all_methods_by_class[c] = []
        
        # sort methods by declaration order
        def key_filter(value):
            value = value[1]
            
            if hasattr(value, '__func__'):
                return value.__func__.__code__.co_firstlineno
            else:
                return value.__code__.co_firstlineno
        
        all_methods = inspect.getmembers(self, lambda _:inspect.ismethod(_) or inspect.isfunction(_))
        all_methods = sorted(all_methods, key=key_filter)
        
        for n1, m1 in all_methods:
            for clazz, class_methods in methods_by_class.items():
                should_continue = True
                
                for n2, m2 in class_methods:
                    if n1 == n2:
                        all_methods_by_class[clazz].append((n1,m1))
                        should_continue = False
                        break
            
                if should_continue is False:
                    break
        
        methods = []
        
        for a, b in all_methods_by_class.items():
            methods.extend(b)
        
        return methods
    
    
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
        
        # open a file in unicode append mode
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
            file.write(
                f"responded `{result}` "
                f"at {datetime.now().strftime('%H:%M:%S')} "
                f"on {datetime.now().strftime('%d/%m/%Y')}\n"
            )
            
            # write negative response line
            if negative is True and reason:
                file.write("\n")
                file.write("Reason given:\n")
                file.write(f"> {reason}\n")
            
            file.write("\n\n")
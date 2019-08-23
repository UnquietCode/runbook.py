import re
import os
import sys
import inspect
import textwrap
from typing import List
from time import sleep
from datetime import datetime

from .step import Step


class Runbook:
    
    def __init__(self, file_path):
        if not file_path:
            raise Exception('file path must be provided')
    
        self.file_path = file_path
    
    
    @classmethod
    def main(cls):
        
        if len(sys.argv) > 2:
            print("usage: [log file path]")
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
        
        # title
        class_name = type(self).__name__
        
        print()
        print(f"\t======={'='*len(class_name)}=======")
        print(f"\t       {class_name}       ")
        print(f"\t======={'='*len(class_name)}=======")
        print()
        
        # preamble
        preamble = self._preamble()
        
        if preamble:
            print(preamble)

        # check for existing steps
        if os.path.isfile(self.file_path):
            print()
            
            if preamble:
                print()
            
            print("(reading existing file...)")
            existing_steps = self._read_file(self.file_path)
            resumed = True
        else:
            existing_steps = []
            resumed = False
        
        current_existing_step = 0
        
        def increment_fn():
            nonlocal current_existing_step
            current_existing_step += 1
            
        for step in self._get_steps():
            print()
            
            self._run_step(
                step=step,
                existing_steps=existing_steps,
                current_existing_step=current_existing_step,
                increment=increment_fn,
                resumed=resumed,
            )
            
        print()
        print("\nAll steps completed.\n")
        
        return None
    
    
    def _preamble(self):
        classes = list(inspect.getmro(type(self)))
        
        for clazz in classes:
            if clazz is Runbook:
                break
            
            if hasattr(clazz, '__doc__'):
                docstring = clazz.__doc__
                
                if docstring:
                    return textwrap.dedent(docstring).strip()
    
    
    def _run_step(self, step, existing_steps, current_existing_step, increment, resumed):
        print()
        
        # handle existing steps
        if len(existing_steps) > current_existing_step:
            existing_step = existing_steps[current_existing_step]
            
            if step.name == existing_step.name:
                if step.repeatable is not True:
                    print(f"(skipping already completed step '{step.preferred_name}')")
                    increment()
                    return
                else:
                    print(f"(repeating existing step '{step.preferred_name}')\n")
                    increment()
            else:
                print(f"(found new step '{step.preferred_name}')\n")
        
        elif resumed is True:
            print(f"(resuming from step '{step.preferred_name}')\n")
            resumed = False
        
        # print step information
        if step.description:
            print(step.description)
        else:
            print(step.preferred_name)
        
        print()
        
        # pause for some seconds to give time to read
        pause_time = 0.0245 * (len(step.description) / 1 + len(step.description))
        pause_time = max(pause_time, 1.05)
        sleep(pause_time)
        
        # response loop
        repeat = True
        
        while repeat is True:
            repeat = False
            
            # ask for input
            print("\tDid you do the thing?")
            sentiment, response, plain_response = self._wait_for_response()

            if sentiment is True:
                self._write_result(step, plain_response)
            
            # handle negative response
            elif sentiment is False:
                if step.skippable is True  or  resumed is True:
                    self._write_result(step, plain_response, negative=True, reason='skipped')
                else:
                    if step.critical is True:
                        print("\n\tThis step MUST be completed!\n")
                        repeat = True
                    else:
                        print("\n\tWhy not?")
                        reason = input("\t~> ").strip()
                        self._write_result(step, plain_response, negative=True, reason=reason)
            else:
                raise Exception('empty')
    
    
    def _wait_for_response(self) -> bool:
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
            function = method.__func__ if hasattr(method, '__func__') else method
            function_signature = inspect.signature(function)
            
            # if method is zero arg, call the unbound class method
            # (as a convenience for @staticmethod)
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
            
            # handle customizations
            function_defaults = {
                k: v.default
                for k, v in function_signature.parameters.items()
                if v.default is not inspect.Parameter.empty
            }
            
            def get_default_value(name:str):
                value = function_defaults.get(name, None)
                value = False if value is None else value
                return value
            
            repeatable = get_default_value('repeatable')
            skippable = get_default_value('skippable')
            critical = get_default_value('critical')
            display_name = get_default_value('name')
            
            if skippable is True and critical is True:
                raise Exception(f"unsupported configuration for step '{step_name}': skippable steps cannot be critical")
            
            steps.append(Step(
                name=step_name,
                description=step_description,
                display_name=display_name,
                repeatable=repeatable,
                skippable=skippable,
                critical=critical,
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
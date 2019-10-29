import re
import os
import sys
import select
import inspect
import textwrap
from typing import List
from time import sleep
from datetime import datetime

from unquietcode.tools.markt import render_markdown

from .cli import main as cli
from .step import Step



def print_markdown(text):
    text = re.sub(r'\r\n', '\n', text)
    text = render_markdown(text)
    print(text.strip())
    # text = re.sub(r'\n\n', '\n', text)
    # print(mdv(md=text, theme='921.2332'))

def bold(text):
    return render_markdown(f"__{text}__").strip()

def italics(text):
    return render_markdown(f"_{text}_").strip()


class Runbook:
    
    def __init__(self, file_path):
        if not file_path:
            raise Exception('file path must be provided')
    
        self.file_path = file_path
    
    
    @staticmethod
    def _make_pretty_name(class_name):
        
        # split by capital letters and add underscore
        pretty_class_name = class_name
        
        # before a capital letter not preceded by a capital letter
        pretty_class_name = re.sub(
            string=pretty_class_name,
            pattern=r'([^A-Z])([A-Z])',
            repl='\\1_\\2',
        )
        
        # before a capital letter preceded by a capital letter but followed by lowercase
        pretty_class_name = re.sub(
            string=pretty_class_name,
            pattern=r'([A-Z])([A-Z])([^A-Z])',
            repl='\\1_\\2\\3',
        )
        
        return pretty_class_name

    
    @classmethod
    def main(cls):
        file_name = cli(standalone_mode=False)

        if not file_name:
            pretty_class_name = cls._make_pretty_name(cls.__name__)
            pretty_class_name = pretty_class_name.lower()
            file_name = f"{pretty_class_name}.log"
        
        # set file path relative to current script working directory
        file_path = f"{os.getcwd()}/{file_name}"
        
        instance = cls(file_path=file_path)
        instance.run()
    
        
    def run(self):
        
        # title
        pretty_class_name = self._make_pretty_name(type(self).__name__)
        pretty_class_name = re.sub(
            string=pretty_class_name,
            pattern=r'_',
            repl=' ',
        )
        
        print()
        print(f"\t======={'='*len(pretty_class_name)}=======")
        print(f"\t       {pretty_class_name}       ")
        print(f"\t======={'='*len(pretty_class_name)}=======")
        
        # preamble
        preamble = self._preamble()
        
        if preamble:
            print()
            print_markdown(preamble)

        # check for existing steps
        if os.path.isfile(self.file_path):
            print()
            
            if preamble:
                print()
            
            print(f"({italics('reading existing file')}...)")
            existing_steps = self._read_file(self.file_path)
            resumed = [True]
        else:
            existing_steps = []
            resumed = [False]
        
        existing_steps_by_name = { _.name : _ for _ in existing_steps }
        
        for step in self._get_steps():
            print()
            
            self._run_step(
                step=step,
                existing_steps_by_name=existing_steps_by_name,
                resumed=resumed,
            )
            
        print()
        print("\nAll steps completed!\n")
        
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
    
    
    def _run_step(self, step, existing_steps_by_name, resumed):
        print()
        
        def print_title():
            print(f"{bold(step.preferred_name)}")
            print(f"{'-'*len(step.preferred_name)}---\n")
        
        # handle existing steps
        if step.name in existing_steps_by_name:
            existing_step = existing_steps_by_name[step.name]
            
            if step.repeatable is not True:
                print(f"({italics('skipping already completed step')} '{step.preferred_name}')")
                return
            else:
                print(f"({italics('repeating existing step')} '{step.preferred_name}')\n\n")
                print_title()
        
        elif resumed[0] is True:
            print(f"({italics('resuming from step')} '{step.preferred_name}')\n\n")
            print_title()
            resumed[0] = False
        
        else:
            print_title()
        
        # print step information
        if step.description:
            print_markdown(step.description)
        else:
            print(step.preferred_name)
        
        print()
        
        # pause for some seconds to give time to read
        pause_time = 0.01 * (len(step.description) / 1.0 + len(step.description))
        pause_time = max(pause_time, 1.10)
        pause_time = min(pause_time, 5.95)
        
        # wait before prompting
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
    
    
    @staticmethod
    def _matches_any(test, regexes):
        for regex in regexes:
            if re.match(f"^{regex}$", test):
                return True
        
        return False
    
    
    def _wait_for_response(self) -> bool:
        while True:
            plain_response = input("\t~> ").strip()
            response = plain_response.lower()
            
            if self._matches_any(response, ["yes+", "y", "yep", "yu+rp", "yeah+", "yar+", 'yessir']):
                return True, response, plain_response
            elif self._matches_any(response, ["no+", "n", "nope", "nay", "neurp"]):
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
            now = datetime.now()
            
            file.write(
                f"responded `{result}` "
                f"at {now.hour}:{now.strftime('%M:%S')} "
                f"on {now.strftime('%d/%m/%Y')}\n"
            )
            
            # write negative response line
            if negative is True and reason:
                file.write("\n")
                file.write("Reason given:\n")
                file.write(f"> {reason}\n")
            
            file.write("\n\n")
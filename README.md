# runbook.py

Inspired by [this blog post](https://blog.danslimmon.com/2019/07/15/do-nothing-scripting-the-key-to-gradual-automation) by Dan Slimmon.

Define your own run-book in a class extending from `Runbook`. Every method that
doesn't begin with an underscore is read in as a step to be completed, in order.
The step name will be built from the method name, and the description is taken
either from the method's own docstring or from any data returned from invoking
the method.

```
from runbook import Runbook


class CustomRunbook(Runbook):
   
    def first_step(self):
        """
        Do ABC now.
        """
    
    def second_step():
        """
        Do EFG then wait 1 hour.
        """

    def third_step():
        task = "reboot"
        return f"perform a {task}"
    
    def last_step():
        """Everything ok?"""
```

Every `Runbook` object comes with a default main method that you can use to execute the script.

```
if __name__ == '__main__':
    CustomRunbook.main()
```

The run-book object can also be instantiated and run directly, like so:
```
book = CustomRunbook(file_path="path/to/file")
book.run()
```

You should avoid using the step names `run` and `main`, which are already defined.

As steps are completed, the results are written out to a log file. You can set a custom log file path by passing an argument to main, as in:

```
python3 my_runbook.py output.log
```

When using the same log file, already completed steps will be skipped. Any new steps found in the `Runbook` class and not in the log will be processed.
# An example with a blank line in the output

Note no <BLANKLINE> directive in the output block of a Python
code block output block pair.

```python
def greeting(name: str) -> str:
    return 'Hello' + '\n\n' + name
print(greeting('World!'))
```

Here is the output it produces.
```
Hello

World!
```

# Interactive Python session with doctest directive

Here is an interactive Python session showing an
expected exception and use of the doctest directive
`IGNORE_EXCEPTION_DETAIL`.

```py
>>> int('def')    #doctest:+IGNORE_EXCEPTION_DETAIL
Traceback (most recent call last):
    ...
ValueError:
```

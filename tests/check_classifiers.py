"""Check the trove classifiers in setup.cfg.

Run this command from the root of the repository:
python tests/check_classifiers.py

It prints all incorrect and deprecated trove-classifiers
and returns exit code 1.

Requires installation of PYPI package trove-classifiers.

https://pypi.org/classifiers/
"""
import configparser
import sys

import trove_classifiers


print("Checking setup.cfg trove-classifiers for typos, duplicates, deprecated.")
config = configparser.ConfigParser()
config.read("setup.cfg", encoding="utf-8")
text = config.get("metadata", "classifiers")
lines = text.splitlines()
# remove blank lines
lines = [line for line in lines if len(line) > 0]
unique_lines = set(lines)
messages = []
# Check for duplicates.
if len(unique_lines) != len(lines):
    for item in unique_lines:
        if lines.count(item) > 1:
            messages.append("Error- '{}' occurs more than once.".format(item))
for trove_line in lines:
    if trove_line in trove_classifiers.deprecated_classifiers:
        messages.append("Error- '{}' is deprecated.".format(trove_line))
    elif trove_line not in trove_classifiers.classifiers:
        messages.append(
            "Error- '{}' is not in trove-classifiers. Check spelling.".format(
                trove_line
            )
        )
if messages:
    for message in messages:
        print(message)
    sys.exit(1)
print("setup.cfg trove-classifiers are OK.")

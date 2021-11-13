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
# remove comments and blank lines
lines1 = [line for line in lines if not line.startswith("#")]
lines2 = [line1 for line1 in lines1 if not line1 == ""]
# No duplicates.
items = set(lines2)
if len(items) != len(lines2):
    print("Duplicate classifiers are not allowed.", file=sys.stderr)
    sys.exit(1)
messages = []
for trove_line in lines2:
    if trove_line not in trove_classifiers.classifiers:
        messages.append(
            "Error- '{}' is not in trove-classifiers. Check spelling.".format(trove_line)
        )
if messages:
    for message in messages:
        print(message, file=sys.stderr)
    sys.exit(1)
print("setup.cfg trove-classifiers are OK.")

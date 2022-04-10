# Recent changes

1.0.0 - 2022-04-XX
- Run on pytest 7, as well as 5.4.3 and 6.
- `--phmdoctest` option only does Python code/expected output.
- Add `--phmdoctest-docmod` option to do both
  - Python code/expected output.
  - Python interactive sessions.
- Rework `--save` option as `--phmdoctest-generate`.
- Collect Markdown only if it has Python examples.
- Return an empty Collector if there is nothing to collect.


0.0.3 - 2021-11-10

- Initial upload to Python Package Index.

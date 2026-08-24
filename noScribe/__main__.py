"""Einstiegspunkt: `python -m noScribe`."""

import sys

from noScribe import main

if __name__ == "__main__":
    try:
        main.noScribeMain()
    except Exception as e:
        # `SystemExit(1)` stand hier ohne `raise` -- ein Absturz beendete
        # das Programm also mit Rueckgabewert 0. Eine Softwareverteilung
        # haette ihn als Erfolg verbucht.
        print(e, file=sys.stderr)
        sys.exit(1)

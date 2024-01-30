# Automated tube nesting program

Automated tube nesting program, that gathers tube part information from Excel
and displays it in Matplotlib image (example shown in the repository).

## How to use?
* python3 nest.py --help
* python3 nest.py --excel Innore.xlsx --material 5870
* python3 nest.py --excel Innore.xlsx

If you do not specify material length, default value of 6000 will be used.

## PIP packages needed to use this program:
* argparse
* pandas
* numpy
* matplotlib
* ortools


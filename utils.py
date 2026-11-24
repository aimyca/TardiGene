"""
Contains utils to handle files


Note : there are two ways of implementing utilities : 
    1) Raise an error, in which case it has to be handled explicitly
    2) Return a result, at the cost of potentially letting errors pass silently
"""

import os
import gzip
from pathlib import Path # handle Path objects (fasta(.gz))
from io import TextIOWrapper

from Bio import SeqIO
from tardigene_exceptions import MissingDependancyError, InvalidFormatError


def get_binary_path(bin_name):
    """
    Checks if :Bin: is on the PATH. If not able to find it, raises an exception.
    """
    bin_path = shutil.which(bin_name)
    if bin_path is None:
        raise Exception as e:
            print(f"Dependancy not met for {bin_name} or binary not in system PATH.")
    return bin_path


def isFasta(fn):
    formats = (".fasta", ".fna", ".fa", ".faa")
    if not fn.endswith(formats):
        return False
    with open(fn, "r") as f:
        first_byte = f.peak(1)

    if not first_byte.startswith(">"):
        return False

    return True

def isFastq(fn):
    """
    If file is not in fastq but in a different raw read format, it will need to be converted.
    """
    formats = (".fq", ".fastq")
    if not fn.endswith(formats):
        return False
    with open(fn, "r") as f:
        first_byte = f.peek(1)

    if not first_byte.startswith("@"):
        return False
    
    return True



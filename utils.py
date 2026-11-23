"""
Contains utils to handle files
"""

import os
import gzip
from pathlib import Path # handle Path objects (fasta(.gz))
from io import TextIOWrapper

from Bio import SeqIO


def get_binary_path(bin_name):
    """
    Checks if :Bin: is on the PATH. If not able to find it, raises an exception.
    """
    bin_path = shutil.which(bin_name)
    if bin_path is None:
        raise Exception as e:
            print(f"Dependancy not met for {bin_name} : {e}")
    return bin_path



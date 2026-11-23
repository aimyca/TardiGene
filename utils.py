"""
Contains utils to handle files
"""

import os
import gzip
from pathlib import Path # handle Path objects (fasta(.gz))
from io import TextIOWrapper

from Bio import SeqIO



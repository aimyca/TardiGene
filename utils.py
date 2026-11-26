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
from urllib.parse import urlparse

from Bio import SeqIO
from tardigene_exceptions import MissingDependancyError, InvalidFormatError


def get_binary_path(bin_name):
    """
    Checks if :Bin: is on the PATH. If not able to find it, raises an exception.
    """
    bin_path = shutil.which(bin_name)
    if bin_path is None:
        raise Exception(f"Dependancy not met for {bin_name} or binary not in system PATH.")
    return bin_path


def isFasta(fn):
    formats = (".fasta", ".fna", ".fa", ".faa")
    name = fn.lower()
    opener = open

    if name.endswith(".gz"):
        opener, name = gzip.open, name[:-3]

    if not name.endswith(formats):
        return False
    
    try:
        with opener(fn, "rb") as f:
            return f.read(1).lstrip() == b">"

    except os.OSError:
        return False

def isFastq(fn):
    """
    If file is not in fastq but in a different raw read format, it will need to be converted.
    """
    formats = (".fq", ".fastq")
    name = fn.lower()
    opener = open

    if name.endswith("gzip"):
        opener, name = gzip.open, name[:-3]

    if not name.endswith(formats):
        return False
    
    try:
        with opener(fn, "r") as f:
            return f.read(1).lstrip() == b"@"
    except os.OSError:
        return False

# Validation des fichiers et des URL

def is_valid_gzip(filepath):
    """Vérifie entièrement l'intégrité d'un fichier gzip."""

    try:
        with gzip.open(filepath, "rb") as handle:
            while handle.read(1024 * 1024):
                pass

        return True

    except (OSError, EOFError, gzip.BadGzipFile):
        return False


def is_allowed_url(url):
    """Vérifie que l'URL utilise HTTPS et un serveur autorisé."""

    ALLOWED_HOSTS = {
        "ftp.ncbi.nlm.nih.gov",
        "download.cncb.ac.cn",
        "ftp.ensemblgenomes.ebi.ac.uk"
    }
    parsed = urlparse(url)

    return (
        parsed.scheme == "https"
        and parsed.hostname in ALLOWED_HOSTS
    )


if __name__ == "__main__":
    # Testing utils 
    pass

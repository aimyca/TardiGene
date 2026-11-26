"""
Filling different tables to test database, and querying 

Require : 
    Collection of genes : fasta 
    Assembled genome w/ annotation : fasta.gz (or .bgz) + gff/gtf
    Transcriptome w/ annotation : fasta.gz (or .bgz) + (need to define format)
    raw reads : fastq 
"""

import unittest

# This is only meant for testing and will not be featured in the final script
import sys 
sys.path.insert(1, "../..")

import os
import zipfile, gzip
from Bio import SeqIO
import django

from tardigene_exceptions import FileNotSeenError, InvalidFormatError, UnknownFormatError
import utils
# Keeping script as standalone
# Otherwise need to create tardigene/management/commands/add_genes.py
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "website.settings")
django.setup()
from tardigene.models import Record, Gene

#########################################################
# ADDING GENES 
#########################################################


def add_records_from_upload(fn):
    """
    Add records (genes, transcripts, proteins) from a FASTA file (ext. fasta, faa, fna, fa) to Record & Gene table in database. DIFFERENT from add_genes_from_genome OR add_gene_from_transcriptome.

    Note : In order to add a record to database, its scientific name, vernacular name & taxonomy information is required. This represents a problem for gene sequences etc uploaded by the user. These fields will be allowed to be null & blank with a default = NA.
    """
    if not os.path.isfile(fn):
        raise Exception(f"File '{fn}' not seen.")
    
    if not utils.isFasta(fn):
        raise Exception(f"File {fn} is not in the right extention or format.")

    genes = []
    for record in SeqIO.parse(fn, "fasta"):
        genes.append(Gene(
        gene_id = record.id,
        gene_name = record.name,
        seq = record.seq, 
                     ))
        # It is possible that start & end are contained within the id. Same for strand & protein accession (though less likely)
    
    Gene.objects.bulk_create(genes)
    print(f"Genes in db : {Gene.objects.count()}")

def add_genome(genome_fn):
    """
    Genomes must be gzipped before being added to DB. 
    Genomes (from NCBI) contain scaffold sequences. To find genes, it is necessary to run a blast or mafft against a database.
    """
    name = genome_fn
    opener = open

    # If zipped OR gzipped, open as such, parse 
    if not os.path.isfile(genome_fn):
        raise FileNotSeenError(f"File '{genome_fn}' not seen.")

    if not utils.isFasta(genome_fn):
        raise InvalidFormatError(f"File {genome_fn} should be a fasta file or a gzipped fasta file ending in '.gz'")
    
    if genome_fn.endswith(".gz"): # need to decompress on the go and store content in variable, before that the content needs to be parsed as it is raw (\\n instead of \n) 
        opener = gzip.open 

    try:
        with opener(genome_fn, "rb") as f:

    

def add_transcriptome(transcriptome):
    pass


#########################################################
# ADDING GENOMES & TRANSCRIPTOMES
#########################################################

def add_genome_to_db(fn):
    pass


def add_transcriptome_to_db(fn):
    pass


#########################################################
# UNIT TEST CLASSES
#########################################################

def check_db_content(table_name):
    """
    Checks if content has been effectively added to database 
    """
    assert table_name.objects.count() > 0


if __name__ == "__main__":
    fn = "./../../Test_data/Database/Mycoplasma_agalactiae.faa"
    # add_records_from_upload(fn)
    # check_db_content(Gene)


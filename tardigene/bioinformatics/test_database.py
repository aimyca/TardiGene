"""
Filling different tables to test database, and querying 

Require : 
    Collection of genes : fasta 
    Assembled genome w/ annotation : fasta.gz (or .bgz) + gff/gtf
    Transcriptome w/ annotation : fasta.gz (or .bgz) + (need to define format)
    raw reads : fastq 
"""

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
        id = record.id,
        gene_name = record.name,
        seq = record.seq, 
                     ))
        # It is possible that start & end are contained within the id. Same for strand & protein accession (though less likely)
    
    Gene.objects.bulk_create(genes)
    print(f"Genes in db : {Gene.objects.count()}")

def add_genes_from_genome(genome_fn):
    """
    Genomes must be gzipped before being added to DB.
    """
    # If zipped OR gzipped, open as such, parse 
    if not os.path.isfile(genome_fn):
        raise FileNotSeenError(f"File '{fn}' not seen.")
    
    if not genome_fn.endswith((".gz", ".gzip")):
        with open(genome_fn, "rb") as f:
            data = f.read()
            comp = gzip.compress(data)
    

def add_genes_from_transcriptome(transcriptome):
    pass


#########################################################
# ADDING GENOMES & TRANSCRIPTOMES
#########################################################

def add_genome_to_db(fn):
    pass


def add_transcriptome_to_db(fn):
    pass


if __name__ == "__main__":
    fn = "./../../Test_data/Database/Mycoplasma_agalactiae.faa"
    add_records_from_upload(fn, Format="fasta")
    # add_genes_from_genome()

"""
Filling different tables to test database, and querying 

Require : 
    Collection of genes : fasta 
    Assembled genome w/ annotation : fasta.gz (or .bgz) + gff/gtf
    Transcriptome w/ annotation : fasta.gz (or .bgz) + (need to define format)
    raw reads : fastq 

Note : the only way to add genes from a genome OR transcriptome is if there is an annotation file. Otherwise, raise an exception.
"""

import os
import zipfile, gzip
from Bio import SeqIO
import django

from tardigene_exception import FileNotSeenError, InvalidFormatError
import utils
# Keeping script as standalone
# Otherwise need to create tardigene/management/commands/add_genes.py
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "website.settings")
django.setup()
from tardigene.models import Gene

def add_records_from_upload(fn):
    """
    Add records (genes, transcripts, proteins) from a FASTA file (ext. fasta, faa, fna, fa) to Gene table in database. DIFFERENT from add_genes_from_genome OR add_gene_from_transcriptome
    """
    exts = ("fasta", "fa", "fna", "faa")

    if not os.path.isfile(fn):
        raise Exception(f"File '{fn}' not seen.")
    
    if not fn.endswith(exts):
        raise Exception(f"{fn} is not in the right format. Gene files should end with .fasta, .fna, .fa or .faa")

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
    



def add_gene_from_transcriptome(transcriptome):
    pass

if __name__ == "__main__":
    # fn = "./Test_data/Database/Mycoplasma_agalactiae.faa"
    # add_genes_from_upload(fn)
    add_genes_from_genome()

"""
Contains online database urls, retrieves data & metadata
"""

import os
import sys
import tempfile
import tempfile

import zipfile, gzip
import requests

import pandas as pd 

from Bio import Entrez
from Bio import SeqIO

NGDC_URL = "https://ngdc.cncb.ac.cn/ewas/rest/"
ENSEMBL_URL = "https://rest.ensembl.org/"
NCBI_URL = "https://api.ncbi.nlm.nih.gov/datasets/v2/"


def GetIDs(keyword="", nb_items=30, db="nucleotide"):
    """
    Queries NCBI database using Bipython's Entrez module.

    Databases are amongst :

    ['pubmed', 'protein', 'nucleotide', 'nuccore', 'nucgss', 'nucest',
    'structure', 'genome', 'books', 'cancerchromosomes', 'cdd', 'gap',
    'domains', 'gene', 'genomeprj', 'gensat', 'geo', 'gds', 'homologene',
    'journals', 'mesh', 'ncbisearch', 'nlmcatalog', 'omia', 'omim', 'pmc',
    'popset', 'probe', 'proteinclusters', 'pcassay', 'pccompound',
    'pcsubstance', 'snp', 'taxonomy', 'toolkit', 'unigene', 'unists']

    Searches :db: with :keyword: and shows :nb_items: number of results.
    """
    # Dummy email : Entrez API requires an email field 
    Entrez.email = "tardigene@example.com"
    if not keyword:
        print("GetIDS requires a keyword")
        return []
    
    search_param = {"db" : db,
                    "retmax" : nb_items,
                    "datetype" : "pdat",
                    "retmode" : "xml",
                    "term" : keyword}

    stream = Entrez.esearch(**search_param)
    record = Entrez.read(stream)

    if not int(record["Count"]):
        print("Nothing appropriate.")
        return []
    
    print(f"Total hits: {record['Count']}")
    ids: list = record["IdList"] 

    return ids


def FetchFromURL(url, *ext) -> pd.DataFrame:
    query = os.path.join(url, *ext)
    r = requests.get(query, headers={ "Content-Type" : "application/json"})
     
    r.raise_for_status()

    with tempfile.TemporaryFile(mode='w+') as f:
        f.write(r.text)
        f.seek(0)
        df = pd.read_json(f)

    return df


if __name__ == "__main__":
    ext = "phenotype/region/homo_sapiens/9:22125500-22136000?feature_type=Variation"
    print(FetchFromURL(ENSEMBL_URL, ext))

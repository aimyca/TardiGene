from django.db import models

"""
This file contains the relationnal schemas for the database
Since Tardigrada genomes can weigh up to 80 Gigs, it would be wiser to only store accession ids 

ids may not be shared due to different source online databases, better use the scientific name 

In order to display gene names, two solutions :
    1) Use the annotation file (if supplied), and allow user to extract the name, & the sequence (from positions) in the genome 
    2) Use the sequences from a different database (more prone to breaking with api updates)

If the genome is provided by the user, they can either :
    1) Input their own annotation file 
    2) Perform alignement (using a dispatch with BLAST, or locally using BLAT, MAFFT etc against the database, in which case the database should not be empty -> raise DataBaseEmpty exception)


GFF parsing : https://biopython.org/wiki/GFF_Parsing
GTF/GFF parsing : package pyranges 
"""

class Record(models.Model):
    """
    Base storage class allowing retrieval in frontend 
    """
    scientific_name = models.CharField(primary_key=True, max_length=255)
    name = models.CharField(max_length=255, blank=True) # some species don't have vernacular names
    description = models.TextField(blank=True) # brief description of the organism
    taxonomy = models.CharField(max_length=2048)
    references = models.TextField()

    def __str__(self):
        return f"{self.scientific_name} ({self.taxonomy})"

class Genome(models.Model):
    """
    Stores genomes from various databases
    """
    id = models.ForeignKey(Record, on_delete=models.CASCADE, related_name="genome_id")
    name = models.CharField(max_length=255)
    description = models.TextField() # description of the genome (assembly, raw reads etc)
    sequence = models.BinaryField(null=True, blank=True) # stores gziped genome 
    is_assembled = models.BooleanField() # default field value is None
    annotations = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.name}"

class Transcriptome(models.Model):
    id = models.ForeignKey(Record, on_delete=models.CASCADE, related_name="transcriptome_id")
    name = models.CharField(max_length=255)
    description = models.TextField()
    sequence = models.BinaryField(null=True, blank=True) # stores gziped transcriptome 
    annotations = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.name}"

class Assembly(models.Model):
    """
    It is assumed there may be multiple assemblies for a given species therefore the primary key cannot be species name. The primary key may be composite, and the species name may be a ForeignKey.
    No delete cascade should be applied as this relation will be used for the history.
    """
    pk = models.CompositePrimaryKey("id", "species")
    id = models.CharField(max_length=511)
    species = models.ForeignKey(Record, on_delete=models.Protect)
    classe = models.CharField(max_length=255)
    genes = models.IntegerField(null=True, blank=True, default="NA")
    proteins = models.IntegerField(blank=True, default="NA")
    gc = models.IntegerField(blank=True, default="NA")
    n50 = models.BigIntegerField(blank=True, default="NA")
    busco = models.IntegerField(blank=True, default="NA")

class Gene(models.Model):
    """
    Table allowing for the storage of genes and genomic regions. Used for ortholog analysis...
    """
    id = models.CharField(max_length=4095)
    genome_id = models.ForeignKey(Genome)
    transcriptome_id = models.ForeignKey(Transcriptome)
    gene_name = models.CharField(max_length=2047)
    seq_id = models.CharField(max_length=511)
    start = models.BigIntegerField()
    end = models.BigIntegerField()
    strand = models.CharField(max_length=255)
    protein_accession = models.CharField(max_length=63, blank=True)

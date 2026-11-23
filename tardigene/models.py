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
        return f"{self.scientific_name} ({taxonomy})"

class Genome(models.Model):
    """
    Stores genomes from various databases
    Note : add annotation field
    """
    id = models.ForeingKey(Record, on_delete=models.CASCADE, related_name="genome_id")
    name = models.CharField(max_length=255)
    description = models.TextField() # description of the genome (assembly, raw reads etc)
    sequence = models.BinaryField(null=True, blank=True) # stores gziped genome 
    is_assembled = models.BooleanField() # default field value is None
    annotations = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.name}"

class Transcriptome(models.Model):
    id = models.ForeingKey(Record, on_delete=models.CASCADE, related_name="transcriptome_id")
    name = models.CharField(max_length=255)
    description = models.TextField()
    sequence = models.BinaryField(null=True, blank=True) # stores gziped transcriptome 
    annotations = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.name}"


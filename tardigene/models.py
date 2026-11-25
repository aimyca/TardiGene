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

--- 
WARNING : models.ForeignKey(unique=True) is better handled with models.OneToOneField()
"""

class Record(models.Model):
    """
    Base storage class allowing retrieval in frontend 
    Should NOT be used when user uploads individual genes/transcripts/proteins.
    """
    id = models.IntegerField(primary_key=True) # Needs to be given by the user or generated automatically (a check is required to avoid duplicates)
    scientific_name = models.CharField(max_length=255)
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
    id = models.ForeignKey(Record, on_delete=models.CASCADE, related_name="genome_id", primary_key=True)
    name = models.CharField(max_length=255)
    description = models.TextField() # description of the genome (assembly, raw reads etc)
    sequence = models.BinaryField(default=b'') # stores gziped genome 
    is_assembled = models.BooleanField(null=True) # default field value is None
    annotations = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.name}"

class Transcriptome(models.Model):
    id = models.ForeignKey(Record, on_delete=models.CASCADE, related_name="transcriptome_id", primary_key=True)
    name = models.CharField(max_length=255)
    description = models.TextField()
    sequence = models.BinaryField(default=b'') # stores gziped transcriptome 
    annotations = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.name}"

class Assembly(models.Model):
    """
    It is assumed there may be multiple assemblies for a given species therefore the primary key cannot be species name. 
    No delete cascade should be applied as this relation will be used for the history.
    """
    id = models.CharField(max_length=511, primary_key=True)
    species = models.ForeignKey(Record, on_delete=models.PROTECT)
    classe = models.CharField(max_length=255)
    genes = models.IntegerField(null=True, blank=True, default="NA")
    proteins = models.IntegerField(blank=True, default="NA")
    gc = models.IntegerField(blank=True, default="NA")
    n50 = models.BigIntegerField(blank=True, default="NA")
    busco = models.IntegerField(blank=True, default="NA")

class Gene(models.Model):
    """
    Table allowing for the storage of genes and genomic regions. Used for ortholog analysis...
    on_delete = PROTECT : since genes can be imported independantly from genomes / transcriptomes.
    """
    id = models.CharField(primary_key=True, max_length=4095)
    genome_id = models.ForeignKey(Genome, on_delete=models.PROTECT, blank=True, null=True)
    transcriptome_id = models.ForeignKey(Transcriptome, models.PROTECT, blank=True, null=True)
    gene_name = models.CharField(max_length=2047)
    # seq_id = models.CharField(max_length=511)
    seq = models.TextField(default="NA")
    start = models.BigIntegerField(blank=True, null=True)
    end = models.BigIntegerField(blank=True, null=True)
    strand = models.CharField(max_length=255, blank=True, null=True)
    protein_accession = models.CharField(max_length=63, blank=True, null=True) # if the gene is proteinophoric

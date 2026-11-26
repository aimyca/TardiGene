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
from django.db import models
from django.db.models import F, Q # Constraints 

class Record(models.Model):
    """
    Base storage class allowing retrieval in frontend 
    Should NOT be used when user uploads individual genes/transcripts/proteins.
    """
    # Autoprimary key avoids duplicates
    scientific_name = models.CharField(max_length=255)
    name = models.CharField(max_length=255, blank=True) # some species don't have vernacular names
    description = models.TextField(blank=True) # brief description of the organism
    taxonomy = models.CharField(max_length=2048)
    references = models.TextField()

    def __str__(self):
        return f"{self.scientific_name} ({self.taxonomy})"

class SequenceRessource(models.Model):
    """
    Abstract class shared by Genome and Transcriptome
    """
    record = models.OneToOneField(Record, on_delete=models.CASCADE,
                                  primary_key=True, related_name="%(class)s")
    name = models.CharField(max_length=255)
    description = models.TextField() # description of the genome (assembly, raw reads etc)
    sequence = models.BinaryField(default=b'') # stores gziped genome 
    accession = models.CharField(max_length=255, blank=True)
    annotations = models.TextField(null=True, blank=True)

    class Meta:
        abstract = True

    def __str__(self):
        return self.name

class Genome(models.Model):
    """
    Stores genomes from various databases
    """
    is_assembled = models.BooleanField(null=True) # default field value is None


class Transcriptome(models.Model):
    pass

    def __str__(self):
        return f"{self.name}"

class Assembly(models.Model):
    """
    It is assumed there may be multiple assemblies for a given species therefore the primary key cannot be species name. 
    No delete cascade should be applied as this relation will be used for the history.
    """
    id = models.CharField(max_length=511, primary_key=True)
    species = models.ForeignKey(Record, on_delete=models.PROTECT, related_name="assemblies")
    classe = models.CharField(max_length=255)
    genes = models.IntegerField(null=True, blank=True)
    proteins = models.IntegerField(blank=True, null=True)
    gc = models.FloatField(blank=True, null=True)
    n50 = models.BigIntegerField(blank=True, null=True)
    busco = models.IntegerField(blank=True, null=True)

    def __str__(self):
        return self.id

class Gene(models.Model):
    """
    Table allowing for the storage of genes and genomic regions. Used for ortholog analysis...
    on_delete = PROTECT : since genes can be imported independantly from genomes / transcriptomes.
    """
    class Strand(models.TextChoices): # Enum 
        PLUS = "+", "Forward"
        MINUS = "_", "Reverse"
        UNKNOWN = ".", "Unknown"


    gene_id = models.CharField(unique=True, max_length=4095)
    genome = models.ForeignKey(Genome, on_delete=models.PROTECT, blank=True, null=True)
    transcriptome_id = models.ForeignKey(Transcriptome, models.PROTECT, blank=True, null=True)
    gene_name = models.CharField(max_length=2047)
    # seq_id = models.CharField(max_length=511)
    seq = models.TextField(null=True)
    start = models.BigIntegerField(blank=True, null=True)
    end = models.BigIntegerField(blank=True, null=True)
    strand = models.CharField(max_length=1, choices=Strand.choices, blank=True, null=True)
    protein_accession = models.CharField(max_length=63, blank=True, null=True) # if the gene is proteinophoric

    class Meta:
        """Makes sure start <= end"""
        constraints = [
            models.CheckConstraint(
                check=Q(start__isnull=True) | Q(end__isnull=True) | Q(start__lte=F("end")),
                name="gene_start_lte_end",
            ),
        ]

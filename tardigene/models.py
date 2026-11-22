from django.db import models

"""
This file contains the relationnal schemas for the database
"""

class Genome(models.Model):
    """
    Stores genomes from various databases
    Note : add annotation field
    """
    id = models.CharField(primary_key=True, max_length=255)
    name = models.CharField(max_length=255)
    description = models.TextField()
    sequence = models.BinaryField() # stores gziped genome 

    def __str__(self):
        return f"{self.name}"

class Transcriptome(models.Model):
    id = models.CharField(primary_key=True, max_length=255)
    name = models.CharField(max_length=255)
    description = models.TextField()
    sequence = models.BinaryField() # stores gziped transcriptome 

    def __str__(self):
        return f"{self.name}"


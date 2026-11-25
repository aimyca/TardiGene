from .bioinformatics.db_statistics import to_number
 
CRITERIA = {
    "genome_size_mb": "Taille du génome (Mb)",
    "genes": "Nombre de gènes codants",
    "gene_density": "Densité génique (gènes codants/Mb)",
    "n50_mb": "N50 (Mb)",
    "gc": "%GC",
    "busco": "BUSCO complet (%)",
}
 
 
def to_mb(value):
    value = to_number(value)
    return round(value / 1000000, 2) if value else None
 
 
def assembly_record(assembly):
    return {
        # Champs déjà utilisés
        "id": assembly.id,
        "species": assembly.species.scientific_name,
        "classe": assembly.classe,
        "genes": to_number(assembly.genes),
        "proteins": to_number(assembly.proteins),
        "gc": to_number(assembly.gc),
        "n50": to_number(assembly.n50),
        "busco": to_number(assembly.busco),
        # Champs ajoutés pour la comparaison génomique
        "genome_size_mb": to_mb(assembly.genome_size),
        "gene_density": to_number(assembly.gene_density),
        "n50_mb": to_mb(assembly.n50),
    }

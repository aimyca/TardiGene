from django.db.models import Max
 
from ..models import Assembly, Record
 
import web  # recherche dans les bases
from .db_statistics import fetch_statistics
 
# Noms de sources utilisés par web.py
SOURCE_CODES = {
    "NCBI": "NCBI",
    "Ensembl Metazoa": "ENSEMBL",
    "NGDC-CNCB": "NGDC",
}
 
#cherche espece dans bdd 
def search(species, ngdc_accession=None):
    if species:
        return web.search_external_databases(species, ngdc_accession)
    try:
        return {"assemblies": web.search_ngdc(ngdc_accession), "errors": {}}
    except Exception as error:
        return {"assemblies": [], "errors": {"NGDC-CNCB": str(error)}}


#cree fiche espece 
def get_record(species_name):
    species_name = species_name.strip().replace("_", " ")
    record = Record.objects.filter(scientific_name__iexact=species_name).first()
    if record is not None:
        return record
    fields = {"scientific_name": species_name, "taxonomy": "", "references": ""}
    pk = Record._meta.pk
    if pk.name != "scientific_name" and pk.get_internal_type() in ("IntegerField", "BigIntegerField"):
        fields[pk.name] = (Record.objects.aggregate(Max(pk.name))[f"{pk.name}__max"] or 0) + 1
    return Record.objects.create(**fields)
 
#lis et enregistre stats de bdd (calcul densité génique en plus)
def add_species(source, identifier, species_name="", assembly_id=""):
    stats = fetch_statistics(source, identifier)
    assembly_id = assembly_id or stats["accession"] or identifier
    # Un même assemblage peut être dans deux bases (ex. NCBI et Ensembl, même accession) :
    # une valeur déjà connue n'est jamais remplacée par une case vide.
    existing = Assembly.objects.filter(id=assembly_id).first()

    def keep(field, new_value):
        if new_value is None and existing is not None:
            return getattr(existing, field)
        return new_value
    genes = keep("genes", stats["genes"])
    size = keep("genome_size", stats["genome_size"])
    density = round(genes / (size / 1000000), 1) if genes and size else None  # gènes codants / Mb
    assembly, _ = Assembly.objects.update_or_create(
        id=assembly_id,
        defaults={
            "species": get_record(species_name or stats["species_name"] or identifier),
            # La base d'origine reste celle du premier ajout
            "source": existing.source if existing and existing.source else source,
            "source_identifier": existing.source_identifier if existing and existing.source_identifier else identifier,
            "assembly_level": stats["assembly_level"] or (existing.assembly_level if existing else ""),
            "genome_size": size,
            "n_sequences": keep("n_sequences", stats["n_sequences"]),
            "n50": keep("n50", stats["n50"]),
            "gc": keep("gc", stats["gc"]),
            "genes": genes,
            "busco": keep("busco", stats["busco"]),
            "gene_density": density,
        },
    )
    return assembly
 
#ajout assemblage 
def add_species_from_search(assembly_info):
    source = SOURCE_CODES.get(assembly_info.get("source"), "NCBI")
    identifier = assembly_info["accession"]
    if source == "ENSEMBL":
        identifier = (assembly_info.get("extra") or {}).get("ensembl_species") or identifier
    return add_species(source, identifier,
                       species_name=assembly_info.get("species") or "",
                       assembly_id=assembly_info.get("accession") or "")
 
#relis stats assemblage (maj)
def refresh_species(assembly_id):
    assembly = Assembly.objects.get(id=assembly_id)
    return add_species(assembly.source, assembly.source_identifier or assembly.id,
                       species_name=assembly.species.scientific_name, assembly_id=assembly.id)
 

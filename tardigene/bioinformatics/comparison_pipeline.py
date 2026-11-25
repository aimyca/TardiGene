import threading
 
from django.db import connection
from django.db.models import Max
 
from ..models import Assembly, Record
 
import web  # recherche dans les bases (web.py de l'équipe, à la racine du projet)
from .db_statistics import fetch_statistics
from .analyse_comparaison_especes import compute_indicators
from .busco_tools import run_busco
 
# Noms de sources utilisés par web.py -> codes stockés dans la base
SOURCE_CODES = {
    "NCBI": "NCBI",
    "Ensembl Metazoa": "ENSEMBL",
    "NGDC-CNCB": "NGDC",
}
 

#fiche espece (utilisation de cle) 
def _get_record(species_name):
    species_name = species_name.strip().replace("_", " ")
    record = Record.objects.filter(scientific_name__iexact=species_name).first()
    if record is not None:
        return record
    fields = {"scientific_name": species_name, "taxonomy": "", "references": ""}
    pk = Record._meta.pk
    if pk.name != "scientific_name" and pk.get_internal_type() in ("IntegerField", "BigIntegerField"):
        fields[pk.name] = (Record.objects.aggregate(Max(pk.name))[f"{pk.name}__max"] or 0) + 1
    return Record.objects.create(**fields)
 

#calcul densite genique
def _gene_density(genes, genome_size):
    if not genes or not genome_size:
        return None
    return round(genes / (genome_size / 1000000), 1)


#recherche espece dans bdd
def search(species, ngdc_accession=None):
    if species:
        return web.search_external_databases(species, ngdc_accession)
    try:
        return {"assemblies": web.search_ngdc(ngdc_accession), "errors": {}}
    except Exception as error:
        return {"assemblies": [], "errors": {"NGDC-CNCB": str(error)}}
 
 
#lecture stats assemblage de bdd et enregistrement
def add_species_from_database(source, identifier, species_name="", assembly_id=""):
    stats = fetch_statistics(source, identifier)
    name = species_name or stats.get("species_name") or identifier
    assembly_id = assembly_id or stats.get("accession") or identifier
    assembly, _ = Assembly.objects.update_or_create(
        id=assembly_id,
        defaults={
            "species": _get_record(name),
            "source": source,
            "source_identifier": identifier,
            "assembly_level": stats.get("assembly_level") or "",
            "genome_size": stats.get("genome_size"),
            "n_sequences": stats.get("n_sequences"),
            "n50": stats.get("n50"),
            "gc": stats.get("gc"),
            "genes": stats.get("genes"),
            "busco": stats.get("busco"),
            "gene_density": _gene_density(stats.get("genes"), stats.get("genome_size")),
            "status": "done",
            "error_message": "",
        },
    )
    return assembly
 

#ajout assemblage
def add_species_from_search(assembly_info):
    source = SOURCE_CODES.get(assembly_info.get("source"), "NCBI")
    if source == "ENSEMBL":
        identifier = (assembly_info.get("extra") or {}).get("ensembl_species") or assembly_info["accession"]
    else:
        identifier = assembly_info["accession"]
    return add_species_from_database(
        source=source,
        identifier=identifier,
        species_name=assembly_info.get("species") or "",
        assembly_id=assembly_info.get("accession") or "",
    )
 

#calcul stats si pas de bdd publique
def analyse_uploaded_files(assembly, with_busco=False):
    assembly.status = "running"
    assembly.error_message = ""
    assembly.save()
    try:
        indicators = compute_indicators(assembly.genome_file, assembly.gff_file, assembly.proteins_file)
        assembly.genome_size = indicators["genome_size"]
        assembly.n_sequences = indicators["n_sequences"]
        assembly.n50 = indicators["n50"]
        assembly.gc = indicators["gc_percent"]
        assembly.genes = indicators["n_genes"]
        assembly.proteins = indicators["n_proteins"]
        assembly.gene_density = indicators["gene_density"]
        if with_busco:
            assembly.busco = run_busco(assembly.proteins_file, run_name=str(assembly.id))["complete"]
        assembly.status = "done"
    except Exception as error:  # on garde l'erreur pour l'afficher sur le site
        assembly.status = "error"
        assembly.error_message = str(error)
    assembly.save()
    return assembly
# Types de fichiers de la page import_data -> champ du modèle Assembly
UPLOAD_FIELDS = {
    "genome": "genome_file",
    "annotation": "gff_file",
    "protein": "proteins_file",
}
 

#calcul stats apres validation des donnees 
def register_uploaded_file(species_name, data_type, file_path, accession="", with_busco=False):
    field = UPLOAD_FIELDS.get(data_type)
    if field is None:
        return None
    assembly_id = accession or "upload_" + species_name.strip().replace(" ", "_")
    assembly, _ = Assembly.objects.get_or_create(
        id=assembly_id,
        defaults={"species": _get_record(species_name), "source": "UPLOAD"},
    )
    setattr(assembly, field, str(file_path))
    assembly.save()
    if assembly.genome_file and assembly.gff_file and assembly.proteins_file:
        run_in_background(refresh_assembly, assembly_id=assembly_id, with_busco=with_busco)
    return assembly


#relit ou recalcul les données de l'assemblage (maj)
def refresh_assembly(assembly_id, with_busco=False):
    assembly = Assembly.objects.get(id=assembly_id)
    if assembly.source in ("NCBI", "NGDC", "ENSEMBL"):
        try:
            return add_species_from_database(
                source=assembly.source,
                identifier=assembly.source_identifier or assembly.id,
                species_name=assembly.species.scientific_name,
                assembly_id=assembly.id,
            )
        except Exception as error:
            assembly.status = "error"
            assembly.error_message = f"Base {assembly.get_source_display()} : {error}"
            assembly.save()
            return assembly
    return analyse_uploaded_files(assembly, with_busco=with_busco)


#calcul en fond quand long
def run_in_background(function, **kwargs):
    def target():
        try:
            function(**kwargs)
        finally:
            connection.close()  # ferme la connexion à la base ouverte par ce fil
    thread = threading.Thread(target=target, daemon=True)
    thread.start()
    return thread
 

from django.core.management.base import BaseCommand, CommandError
 
from tardigene.bioinformatics.comparison_pipeline import add_species
 
 
class Command(BaseCommand):
    help = "Lit les statistiques d'un assemblage (NCBI, NGDC-CNCB, Ensembl Metazoa) et l'ajoute à TardiGen."
 
    def add_arguments(self, parser):
        parser.add_argument("source", choices=["NCBI", "NGDC", "ENSEMBL"])
        parser.add_argument("identifier", help="Accession (NCBI, NGDC) ou nom Ensembl de l'espèce")
        parser.add_argument("--species", default="", help="Nom scientifique (sinon celui de la base)")
 
    def handle(self, *args, **options):
        try:
            a = add_species(options["source"], options["identifier"], species_name=options["species"])
        except Exception as error:
            raise CommandError(f"Impossible de lire les statistiques : {error}") from error
 
        def show(value, unit=""):
            return "—" if value is None else f"{value}{unit}"
 
        self.stdout.write(self.style.SUCCESS(
            f"{a.species.scientific_name} ({a.id}) ajouté : "
            f"taille {show(a.genome_size, ' pb')} · séquences {show(a.n_sequences)} · "
            f"N50 {show(a.n50, ' pb')} · GC {show(a.gc, ' %')} · gènes codants {show(a.genes)} · "
            f"densité {show(a.gene_density, ' gènes/Mb')} · BUSCO {show(a.busco, ' %')}"
        ))
 
#exemple d'entree depuis le terminal : python manage.py add_species NCBI GCA_002082055.1

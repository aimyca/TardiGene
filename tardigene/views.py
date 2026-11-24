import json
import re
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.db.models import Q

from .models import Record, Gene, Assembly



# Page d'accueil
def index(request):
    return render(request, "tardigene/home.html")


# Liste des espèces
def species_list(request):
    q = request.GET.get("q", "").strip()
    species_name = request.GET.get("species", "")

    species = Record.objects.all().order_by("scientific_name")

    if q:
        species = species.filter(scientific_name__icontains=q)

    selected_species = None

    if species_name:
        selected_species = species.filter(
            scientific_name=species_name
        ).first()

    if selected_species is None:
        selected_species = species.first()

    return render(request, "tardigene/species_list.html", {
        "species_list": species,
        "selected_species": selected_species,
        "q": q,
    })


# Détails d'une espèce
def species_detail(request):
    return render(request, "tardigene/species_detail.html")


# Liste des gènes

def gene_list(request):
    q = request.GET.get("q", "").strip()

    # Récupérer les gènes de la base SQLite
    genes = Gene.objects.all().order_by("gene_name")

    # Filtrer par nom ou identifiant
    if q:
        from django.db.models import Q

        genes = genes.filter(
            Q(gene_name__icontains=q) |
            Q(id__icontains=q)
        )

    # Envoyer les données au template HTML
    return render(request, "tardigene/gene_list.html", {
        "genes": genes,
        "q": q,
    })


# Détails d'un gène
def gene_detail(request, gene_id):
    gene = get_object_or_404(Gene, pk=gene_id)

    return render(request, "tardigene/gene_detail.html", {
        "gene": gene,
    })

# Comparaison des espèces

def comparison(request):
    records = Record.objects.all().order_by("scientific_name")

    assemblies = (
        Assembly.objects
        .select_related("species")
        .order_by("species__scientific_name", "id")
    )

    def clean_number(value):
        if value is None or value == "" or value == "NA":
            return None
        return value

    species_data = [
        {
            "name": record.scientific_name,
            "taxonomy": record.taxonomy,
        }
        for record in records
    ]

    assembly_data = [
        {
            "id": assembly.id,
            "species": assembly.species.scientific_name,
            "classe": assembly.classe,
            "genes": clean_number(assembly.genes),
            "proteins": clean_number(assembly.proteins),
            "gc": clean_number(assembly.gc),
            "n50": clean_number(assembly.n50),
            "busco": clean_number(assembly.busco),
        }
        for assembly in assemblies
    ]

    return render(request, "tardigene/comparison.html", {
        "species_data": species_data,
        "assembly_data": assembly_data,
    })


# Analyse des séquences
def sequence_analysis(request):
    return render(request, "tardigene/sequence_analysis.html")


# Importation des données
def import_data(request):
    species = Record.objects.all().order_by("scientific_name")

    return render(request, "tardigene/import_data.html", {
        "species_list": species,
    })

# Historique des contributions
def history(request):
    return render(request, "tardigene/history.html")


# Page d'aide
def help_page(request):
    return render(request, "tardigene/help.html")

# VÉRIFICATION DES ESPECES DEJA EXISTANTES
@require_GET
def check_species_exists(request):
    scientific_name = request.GET.get("name", "").strip()

    if not scientific_name:
        return JsonResponse({
            "error": "Nom scientifique manquant."
        }, status=400)

    exists = Record.objects.filter(
        scientific_name__iexact=scientific_name
    ).exists()

    return JsonResponse({
        "exists": exists
    })

# VÉRIFICATION DES ACCESSIONS NCBI
@require_GET
def check_ncbi_accession(request):
    accession = request.GET.get("accession", "").strip().upper()

    if not re.fullmatch(r"GC[AF]_[0-9]{9}\.[0-9]+", accession):
        return JsonResponse({
            "valid": False,
            "message": "Numéro d'accession invalide."
        }, status=400)

    url = (
        "https://api.ncbi.nlm.nih.gov/datasets/v2/"
        f"genome/accession/{accession}/dataset_report"
    )

    try:
        ncbi_request = Request(
            url,
            headers={"Accept": "application/json"}
        )

        with urlopen(ncbi_request, timeout=10) as response:
            data = json.load(response)

    except HTTPError as error:
        if error.code == 404:
            return JsonResponse({
                "valid": False,
                "message": "Accession introuvable dans NCBI."
            })

        return JsonResponse({
            "error": "Vérification NCBI indisponible."
        }, status=503)

    except (URLError, TimeoutError, ValueError):
        return JsonResponse({
            "error": "Impossible de contacter NCBI."
        }, status=503)

    reports = data.get("reports", [])

    report = next(
        (
            item for item in reports
            if item.get("accession", "").upper() == accession
        ),
        None
    )

    if report is None:
        if not reports:
            return JsonResponse({
                "valid": False,
                "message": "Accession introuvable dans NCBI."
            })

        return JsonResponse({
            "error": "Réponse NCBI inattendue."
        }, status=502)

    organism = report.get("organism") or {}
    assembly_info = report.get("assemblyInfo") or {}

    return JsonResponse({
        "valid": True,
        "accession": report["accession"],
        "scientific_name": organism.get("organismName", ""),
        "assembly_name": assembly_info.get("assemblyName", "")
    })

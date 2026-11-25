from django.contrib import messages
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST
 
from .models import Assembly
 
from .bioinformatics import comparison_pipeline as pipeline
from .comparison_forms import SearchSpeciesForm
 
 
def search_species(request):
    form = SearchSpeciesForm(request.GET or None)
    context = {"form": form}
 
    if form.is_valid():
        found = pipeline.search(form.cleaned_data["species"], form.cleaned_data["ngdc_accession"] or None)
        # On garde les résultats en session pour retrouver l'assemblage choisi au clic
        request.session["search_results"] = found["assemblies"]
        context["assemblies"] = found["assemblies"]
        context["errors"] = found["errors"]
        context["already_added"] = set(Assembly.objects.values_list("id", flat=True))
 
    return render(request, "tardigene/comparison/search_species.html", context)
 
 
@require_POST
def add_from_search(request):
    results = request.session.get("search_results", [])
    try:
        assembly_info = results[int(request.POST["index"])]
    except (KeyError, ValueError, IndexError):
        messages.error(request, "Assemblage introuvable, relancez la recherche.")
        return redirect("species_import:search_species")
    try:
        assembly = pipeline.add_species_from_search(assembly_info)
    except Exception as error:
        messages.error(request, f"Impossible de lire les statistiques de {assembly_info['accession']} : {error}")
        return redirect("species_import:search_species")
    messages.success(request, f"{assembly.species.scientific_name} ({assembly.id}) ajouté à la comparaison.")
    return redirect("species_import:species_status")
 
 
def species_status(request):
    assemblies = Assembly.objects.select_related("species").order_by("species__scientific_name", "id")
    return render(request, "tardigene/comparison/species_status.html", {"assemblies": assemblies})
 
 
@require_POST
def refresh(request, assembly_id):
    try:
        pipeline.refresh_species(assembly_id)
        messages.success(request, f"Statistiques de {assembly_id} actualisées.")
    except Exception as error:
        messages.error(request, f"Impossible d'actualiser {assembly_id} : {error}")
    return redirect("species_import:species_status")

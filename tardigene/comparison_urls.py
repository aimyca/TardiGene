from django.urls import path
 
from . import comparison_views as views
 
app_name = "species_import"
 
urlpatterns = [
    path("especes/rechercher/", views.search_species, name="search_species"),
    path("especes/ajouter/", views.add_from_search, name="add_from_search"),
    path("especes/statut/", views.species_status, name="species_status"),
    path("especes/<str:assembly_id>/actualiser/", views.refresh, name="refresh"),
]

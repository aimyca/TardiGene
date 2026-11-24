from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="home"),
    path("especes/", views.species_list, name="species_list"),
    path("especes/detail/", views.species_detail, name="species_detail"),
    path("genes/", views.gene_list, name="gene_list"),
    path("genes/detail/<str:gene_id>/", views.gene_detail, name="gene_detail"),    
    path("comparaison/", views.comparison, name="comparison"),
    path("analyse-sequences/", views.sequence_analysis, name="sequence_analysis"),
    path("importer/", views.import_data, name="import_data"),
    path("historique/", views.history, name="history"),
    path("aide/", views.help_page, name="help"),
    path("api/especes/verifier/", views.check_species_exists, name="check_species_exists"),
]
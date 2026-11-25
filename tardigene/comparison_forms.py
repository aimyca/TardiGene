from django import forms
 
 
class SearchSpeciesForm(forms.Form):
    species = forms.CharField(
        label="Nom scientifique",
        required=False,
        help_text="Ex. : Hypsibius exemplaris (recherche dans NCBI et Ensembl Metazoa).",
    )
    ngdc_accession = forms.CharField(
        label="Accession NGDC-CNCB (optionnel)",
        required=False,
        help_text="Ex. : GWHDUDB00000000",
    )
 
    def clean(self):
        data = super().clean()
        if not data.get("species") and not data.get("ngdc_accession"):
            raise forms.ValidationError("Indiquez un nom d'espèce ou une accession NGDC.")
        return data

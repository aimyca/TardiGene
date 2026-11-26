(function () {
    // Critères : nom dans les données -> libellé affiché
    // (doivent correspondre à CRITERIA dans tardigene/comparison.py)
    const CRITERIA = {
        genome_size_mb: "Taille du génome (Mb)",
        genes: "Nombre de gènes codants",
        gene_density: "Densité génique (gènes codants/Mb)",
        n50_mb: "N50 (Mb)",
        gc: "%GC",
        busco: "BUSCO complet (%)",
    };
 
    // Champ qui contient le nom de l'espèce dans assembly_data
    const SPECIES_KEY = "species";
 
    // Apparence commune des graphiques : police et couleurs de style.css
    const COLORS = ["#6b47be", "#a98ae9", "#281d43", "#177457", "#d6a33a", "#b12b32"];
    const BASE_LAYOUT = {
        font: { family: "Inter, Arial, sans-serif", size: 12, color: "#29253f" },
        colorway: COLORS,
        paper_bgcolor: "#ffffff",
        plot_bgcolor: "#ffffff",
    };
 
    function layout(extra) {
        return Object.assign({}, BASE_LAYOUT, extra);
    }
 
    const dataElement = document.getElementById("assembly-data");
    const chartsZone = document.getElementById("criteria-charts");
    if (!dataElement || !chartsZone) {
        return; // la page ne contient pas la section des critères
    }
    const assemblies = JSON.parse(dataElement.textContent) || [];
 
    // --- Lecture des choix de l'utilisateur --------------------------------
 
    function checkedValues(containerId) {
        return Array.from(
            document.querySelectorAll("#" + containerId + " input[type=checkbox]:checked")
        ).map(function (input) { return input.value; });
    }
 
    function selectedRows() {
        const species = new Set(checkedValues("species-selection"));
        return assemblies.filter(function (a) { return species.has(a[SPECIES_KEY]); });
    }
 
    // --- Graphiques ----------------------------------------------------------
 
    function addChartContainer() {
        const div = document.createElement("div");
        chartsZone.appendChild(div);
        return div;
    }
 
    function barChart(rows, key) {
        const usable = rows.filter(function (r) { return r[key] !== null && r[key] !== undefined; });
        if (usable.length === 0) {
            const note = document.createElement("p");
            note.className = "muted";
            note.textContent = CRITERIA[key] + " : aucune valeur disponible.";
            chartsZone.appendChild(note);
            return;
        }
        Plotly.newPlot(addChartContainer(), [{
            type: "bar",
            x: usable.map(function (r) { return r[SPECIES_KEY]; }),
            y: usable.map(function (r) { return r[key]; }),
            text: usable.map(function (r) { return r[key]; }),
            textposition: "outside",
            marker: { color: COLORS[0] },
        }], layout({
            title: CRITERIA[key],
            yaxis: { title: CRITERIA[key], gridcolor: "#e2ddec" },
            height: 360,
            margin: { t: 50, b: 60 },
        }), { responsive: true, displaylogo: false });
    }
 
    /*
     * Radar : les critères n'ont pas les mêmes unités (Mb, %, nombre de gènes).
     * Chaque critère est ramené en % de la plus grande valeur parmi les espèces
     * sélectionnées : l'espèce la plus haute vaut 100 %.
     */
    function radarChart(rows, keys) {
        const maxima = {};
        keys.forEach(function (key) {
            maxima[key] = Math.max.apply(null, rows.map(function (r) { return r[key] || 0; }));
        });
        const labels = keys.map(function (key) { return CRITERIA[key]; });
 
        const traces = rows.map(function (r) {
            const values = keys.map(function (key) {
                return maxima[key] ? Math.round((r[key] || 0) / maxima[key] * 1000) / 10 : 0;
            });
            return {
                type: "scatterpolar",
                r: values.concat(values.slice(0, 1)),          // on referme la forme
                theta: labels.concat(labels.slice(0, 1)),
                fill: "toself",
                name: r[SPECIES_KEY],
            };
        });
 
        Plotly.newPlot(addChartContainer(), traces, layout({
            title: "Vue d'ensemble (% de la valeur maximale)",
            polar: { radialaxis: { range: [0, 100], gridcolor: "#e2ddec" } },
            height: 480,
        }), { responsive: true, displaylogo: false });
    }
 
    function render() {
        chartsZone.innerHTML = "";
        const rows = selectedRows();
        const keys = checkedValues("criteria-selection");
 
        if (rows.length < 2 || keys.length === 0) {
            const note = document.createElement("p");
            note.className = "muted";
            note.textContent = "Choisissez au moins 2 espèces et 1 critère.";
            chartsZone.appendChild(note);
            return;
        }
        if (keys.length >= 3) {
            radarChart(rows, keys);
        }
        keys.forEach(function (key) { barChart(rows, key); });
    }
 
    // --- Événements ------------------------------------------------------------
 
    const compareButton = document.getElementById("compare-button");
    if (compareButton) {
        compareButton.addEventListener("click", render);
    }
    document.getElementById("criteria-selection").addEventListener("change", render);
    const speciesSelection = document.getElementById("species-selection");
    if (speciesSelection) {
        speciesSelection.addEventListener("change", render);
    }
 
    render();
})();


document.addEventListener("DOMContentLoaded", function () {

    /* ----------------------------------------------------------
       01. FONCTIONS UTILITAIRES
       ---------------------------------------------------------- */

    function downloadFile(content, filename, mimeType) {
        const blob = new Blob([content], {
            type: mimeType
        });

        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");

        link.href = url;
        link.download = filename;

        document.body.appendChild(link);
        link.click();
        link.remove();

        URL.revokeObjectURL(url);
    }

    function escapeHtml(value) {
        return String(value ?? "")
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    function readJsonScript(id) {
        const element = document.getElementById(id);

        if (!element) {
            return [];
        }

        try {
            const data = JSON.parse(element.textContent);
            return Array.isArray(data) ? data : [];
        } catch (error) {
            console.error("Erreur de lecture des données :", id);
            return [];
        }
    }

    function showMessage(element, text, isError = false) {
        if (!element) {
            return;
        }

        element.textContent = text;
        element.hidden = false;

        element.classList.remove("error", "success");
        element.classList.add(isError ? "error" : "success");
    }

    function hideMessage(element) {
        if (!element) {
            return;
        }

        element.textContent = "";
        element.hidden = true;
        element.classList.remove("error", "success");
    }


    /* ----------------------------------------------------------
       02. COMPARAISON DES ESPÈCES
       ---------------------------------------------------------- */

    function initComparison() {
        const speciesSelection = document.getElementById(
            "species-selection"
        );

        if (!speciesSelection) {
            return;
        }

        const speciesData = readJsonScript("species-data");
        const assemblyData = readJsonScript("assembly-data");

        const comparisonTableBody = document.getElementById(
            "comparison-table-body"
        );

        const comparisonFunctionsBody = document.getElementById(
            "comparison-functions-body"
        );

        const assemblyBars = document.getElementById(
            "assembly-bars"
        );

        const comparisonResults = document.getElementById(
            "comparison-results"
        );

        const exportButton =
            document.getElementById("export-comparison") ||
            document.getElementById("export-csv");

        function getSelectedSpecies() {
            return Array.from(
                speciesSelection.querySelectorAll(
                    'input[type="checkbox"]:checked'
                )
            ).map(input => input.value);
        }

        function getSelectedAssemblies() {
            const selected = getSelectedSpecies();

            return assemblyData.filter(assembly =>
                selected.includes(assembly.species)
            );
        }

        function formatValue(value) {
            if (
                value === null ||
                value === undefined ||
                value === ""
            ) {
                return "—";
            }

            return String(value);
        }

        function renderComparisonTable(assemblies) {
            if (!comparisonTableBody) {
                return;
            }

            comparisonTableBody.innerHTML = "";

            assemblies.forEach(assembly => {
                const row = document.createElement("tr");

                [
                    assembly.species,
                    assembly.id,
                    assembly.classe,
                    assembly.genes,
                    assembly.proteins,
                    assembly.gc,
                    assembly.n50,
                    assembly.busco
                ].forEach(value => {
                    const cell = document.createElement("td");

                    cell.textContent = formatValue(value);
                    row.appendChild(cell);
                });

                comparisonTableBody.appendChild(row);
            });
        }

        function renderAssemblyBars(assemblies) {
            if (!assemblyBars) {
                return;
            }

            assemblyBars.innerHTML = "";

            const validAssemblies = assemblies.filter(assembly =>
                Number.isFinite(Number(assembly.n50)) &&
                Number(assembly.n50) > 0
            );

            if (!validAssemblies.length) {
                return;
            }

            const maxN50 = Math.max(
                ...validAssemblies.map(assembly =>
                    Number(assembly.n50)
                )
            );

            validAssemblies.forEach(assembly => {
                const value = Number(assembly.n50);

                const percentage = maxN50 > 0
                    ? (value / maxN50) * 100
                    : 0;

                const row = document.createElement("div");

                const name = document.createElement("em");
                name.textContent = assembly.species;

                const barContainer = document.createElement("span");
                const bar = document.createElement("i");

                bar.style.width = percentage + "%";
                barContainer.appendChild(bar);

                const number = document.createElement("strong");
                number.textContent = value.toLocaleString("fr-FR");

                row.appendChild(name);
                row.appendChild(barContainer);
                row.appendChild(number);

                assemblyBars.appendChild(row);
            });
        }

        function renderComparison() {
            const selected = getSelectedSpecies();

            const assemblies = getSelectedAssemblies();

            renderComparisonTable(assemblies);
            renderAssemblyBars(assemblies);

            if (comparisonFunctionsBody) {
                comparisonFunctionsBody.innerHTML = "";
            }

            if (comparisonResults) {
                comparisonResults.hidden = selected.length === 0;
            }
        }

        function exportComparisonCsv() {
            const assemblies = getSelectedAssemblies();

            if (!assemblies.length) {
                return;
            }

            const columns = [
                ["species", "Espèce"],
                ["id", "Assemblage"],
                ["classe", "Classe"],
                ["genes", "Gènes"],
                ["proteins", "Protéines"],
                ["gc", "GC"],
                ["n50", "N50"],
                ["busco", "BUSCO"]
            ];

            function csvValue(value) {
                const text = String(value ?? "");

                return '"' + text.replace(/"/g, '""') + '"';
            }

            const rows = [
                columns.map(column => csvValue(column[1])).join(";")
            ];

            assemblies.forEach(assembly => {
                rows.push(
                    columns.map(column =>
                        csvValue(assembly[column[0]])
                    ).join(";")
                );
            });

            downloadFile(
                "\uFEFF" + rows.join("\r\n"),
                "tardigen_comparaison.csv",
                "text/csv;charset=utf-8"
            );
        }

        speciesSelection.addEventListener(
            "change",
            renderComparison
        );

        if (exportButton) {
            exportButton.addEventListener(
                "click",
                exportComparisonCsv
            );
        }

        renderComparison();
    }


    /* ----------------------------------------------------------
       03. ANALYSE DE SÉQUENCES : BLASTN ET MAFFT
       ---------------------------------------------------------- */

    function initSequenceAnalysis() {
        const blastPanel = document.getElementById(
            "blast-panel"
        );

        const mafftPanel = document.getElementById(
            "mafft-panel"
        );

        const blastForm = document.getElementById(
            "blast-form"
        );

        const mafftForm = document.getElementById(
            "mafft-form"
        );

        if (
            !blastPanel &&
            !mafftPanel &&
            !blastForm &&
            !mafftForm
        ) {
            return;
        }

        const tabButtons = document.querySelectorAll(
            '.tabs button, [data-analysis-tab]'
        );

        function switchAnalysis(tabName) {
            const showBlast = tabName === "blast";

            if (blastPanel) {
                blastPanel.hidden = !showBlast;
            }

            if (mafftPanel) {
                mafftPanel.hidden = showBlast;
            }

            tabButtons.forEach(button => {
                const name =
                    button.dataset.analysisTab ||
                    button.dataset.tab ||
                    button.id ||
                    "";

                const isBlast = name.toLowerCase().includes("blast");

                const isActive = showBlast
                    ? isBlast
                    : name.toLowerCase().includes("mafft");

                button.classList.toggle("active", isActive);

                button.setAttribute(
                    "aria-selected",
                    String(isActive)
                );
            });
        }

        tabButtons.forEach(button => {
            button.addEventListener("click", function () {
                const name =
                    button.dataset.analysisTab ||
                    button.dataset.tab ||
                    button.id ||
                    "";

                switchAnalysis(
                    name.toLowerCase().includes("mafft")
                        ? "mafft"
                        : "blast"
                );
            });
        });

        function isValidFasta(text) {
            const lines = text
                .trim()
                .split(/\r?\n/)
                .map(line => line.trim())
                .filter(Boolean);

            if (!lines.length || !lines[0].startsWith(">")) {
                return false;
            }

            let hasSequence = false;
            let sequenceAfterHeader = false;

            for (const line of lines) {
                if (line.startsWith(">")) {
                    if (
                        hasSequence &&
                        !sequenceAfterHeader
                    ) {
                        return false;
                    }

                    if (line.length === 1) {
                        return false;
                    }

                    sequenceAfterHeader = false;
                    hasSequence = true;

                } else {
                    if (!hasSequence || /\s/.test(line)) {
                        return false;
                    }

                    sequenceAfterHeader = true;
                }
            }

            return hasSequence && sequenceAfterHeader;
        }

        function countFastaSequences(text) {
            return text
                .split(/\r?\n/)
                .filter(line => line.trim().startsWith(">"))
                .length;
        }

        function initializeAnalysisForm(form, sequenceId, toolName) {
            if (!form) {
                return;
            }

            const sequenceInput = document.getElementById(
                sequenceId
            );

            const message =
                form.querySelector(".message") ||
                document.getElementById(
                    toolName.toLowerCase() + "-message"
                );

            form.addEventListener("submit", function (event) {
                event.preventDefault();

                const sequence = sequenceInput
                    ? sequenceInput.value.trim()
                    : "";

                if (sequence && !isValidFasta(sequence)) {
                    showMessage(
                        message,
                        "Le format FASTA est invalide.",
                        true
                    );
                    return;
                }

                if (
                    toolName === "MAFFT" &&
                    sequence &&
                    countFastaSequences(sequence) < 2
                ) {
                    showMessage(
                        message,
                        "Veuillez fournir au moins deux séquences FASTA.",
                        true
                    );
                    return;
                }

                showMessage(
                    message,
                    "La vérification du formulaire est terminée. " +
                    "L'exécution de " + toolName +
                    " nécessite le service d'analyse côté serveur.",
                    true
                );
            });
        }

        initializeAnalysisForm(
            blastForm,
            "blast-sequence",
            "BLASTn"
        );

        initializeAnalysisForm(
            mafftForm,
            "mafft-sequences",
            "MAFFT"
        );

        switchAnalysis("blast");
    }


    /* ----------------------------------------------------------
       04. IMPORTATION : INITIALISATION
       ---------------------------------------------------------- */

    function initImportData() {
        const form = document.getElementById("import-form");

        if (!form) {
            return;
        }

        const dataType = document.getElementById("data-type");

        const fileInput = document.getElementById(
            "biological-file"
        );

        const fileName = document.getElementById(
            "selected-file-name"
        );

        const acceptedFormatsText = document.getElementById(
            "accepted-formats-text"
        );

        const message = document.getElementById(
            "import-message"
        );

        const speciesModeRadios = document.querySelectorAll(
            'input[name="species_mode"]'
        );

        const existingSpeciesSection = document.getElementById(
            "existing-species-section"
        );

        const newSpeciesSection = document.getElementById(
            "new-species-section"
        );

        const existingSpecies = document.getElementById(
            "species-name"
        );

        const newSpeciesName = document.getElementById(
            "new-species-name"
        );

        const speciesCheckMessage = document.getElementById(
            "species-check-message"
        );

        const accessionInput = document.getElementById(
            "assembly-accession"
        );

        const ncbiMessage = document.getElementById(
            "ncbi-accession-message"
        );

        if (
            !dataType ||
            !fileInput ||
            !existingSpecies ||
            !newSpeciesName
        ) {
            return;
        }

        const allowedExtensions = {
            protein: [".faa", ".fa", ".fasta"],
            genome: [".fna", ".fa", ".fasta"],
            annotation: [".gff3", ".gff", ".gtf"],
            csv: [".csv"]
        };

        let speciesCheckRequest = 0;
        let ncbiCheckRequest = 0;


        /* ----------------------------------------------------------
           05. MESSAGES DU FORMULAIRE
           ---------------------------------------------------------- */

        function showImportMessage(text, isError = false) {
            showMessage(message, text, isError);
        }

        function clearImportMessage() {
            hideMessage(message);
        }

        function showFieldMessage(element, text, isError = true) {
            if (!element) {
                return;
            }

            element.textContent = text;
            element.style.color = isError
                ? "#a42c32"
                : "#177457";

            element.hidden = false;
        }

        function clearFieldMessage(element) {
            if (!element) {
                return;
            }

            element.textContent = "";
            element.hidden = true;
        }


        /* ----------------------------------------------------------
           06. FORMATS ACCEPTÉS 
           ---------------------------------------------------------- */

        function updateAcceptedFormats() {
            const type = dataType.value;

            const extensions = allowedExtensions[type] || [];

            if (acceptedFormatsText) {
                acceptedFormatsText.textContent =
                    extensions.join(", ");
            }

            fileInput.accept = extensions.join(",");

            fileInput.value = "";

            if (fileName) {
                fileName.textContent =
                    "Aucun fichier sélectionné";
            }

            clearImportMessage();
        }

        function updateSelectedFileName() {
            const file = fileInput.files[0];

            if (fileName) {
                fileName.textContent = file
                    ? file.name
                    : "Aucun fichier sélectionné";
            }

            clearImportMessage();
        }

        function isAllowedFile(file) {
            if (!file) {
                return false;
            }

            const extensions =
                allowedExtensions[dataType.value] || [];

            const filename = file.name.toLowerCase();

            return extensions.some(extension =>
                filename.endsWith(extension)
            );
        }

        dataType.addEventListener(
            "change",
            updateAcceptedFormats
        );

        fileInput.addEventListener(
            "change",
            updateSelectedFileName
        );


        /* ----------------------------------------------------------
           07. ESPÈCE EXISTANTE OU NOUVELLE ESPÈCE
           ---------------------------------------------------------- */

        function getSpeciesMode() {
            const selected = document.querySelector(
                'input[name="species_mode"]:checked'
            );

            return selected
                ? selected.value
                : "existing";
        }

        function updateSpeciesMode() {
            const isNew = getSpeciesMode() === "new";

            if (existingSpeciesSection) {
                existingSpeciesSection.hidden = isNew;
            }

            if (newSpeciesSection) {
                newSpeciesSection.hidden = !isNew;
            }

            existingSpecies.disabled = isNew;
            existingSpecies.required = !isNew;

            if (newSpeciesSection) {
                const fields = newSpeciesSection.querySelectorAll(
                    "input, textarea, select"
                );

                fields.forEach(field => {
                    field.disabled = !isNew;
                });
            }

            newSpeciesName.required = isNew;

            const taxonomy = document.getElementById(
                "new-species-taxonomy"
            );

            if (taxonomy) {
                taxonomy.required = isNew;
            }

            speciesCheckRequest++;
            ncbiCheckRequest++;

            clearFieldMessage(speciesCheckMessage);
            clearFieldMessage(ncbiMessage);
            clearImportMessage();
        }

        speciesModeRadios.forEach(radio => {
            radio.addEventListener(
                "change",
                updateSpeciesMode
            );
        });


        /* ----------------------------------------------------------
           08. VÉRIFICATION DES ESPÈCES DANS DJANGO
           ---------------------------------------------------------- */

        async function checkSpeciesExists() {
            const name = newSpeciesName.value.trim();

            const currentRequest = ++speciesCheckRequest;

            clearFieldMessage(speciesCheckMessage);

            if (
                !name ||
                newSpeciesName.disabled ||
                getSpeciesMode() !== "new"
            ) {
                return null;
            }

            const endpoint = newSpeciesName.dataset.checkUrl;

            if (!endpoint) {
                showFieldMessage(
                    speciesCheckMessage,
                    "Impossible de vérifier cette espèce."
                );

                return null;
            }

            const url = new URL(
                endpoint,
                window.location.origin
            );

            url.searchParams.set("name", name);

            try {
                const response = await fetch(url, {
                    cache: "no-store"
                });

                if (!response.ok) {
                    throw new Error("Erreur serveur");
                }

                const data = await response.json();

                if (
                    currentRequest !== speciesCheckRequest ||
                    newSpeciesName.value.trim() !== name ||
                    getSpeciesMode() !== "new"
                ) {
                    return null;
                }

                if (data.exists === true) {
                    showFieldMessage(
                        speciesCheckMessage,
                        "Espèce invalide : veuillez renseigner " +
                        "une espèce qui n’existe pas encore " +
                        "dans TardiGen."
                    );

                    return true;
                }

                if (data.exists === false) {
                    clearFieldMessage(speciesCheckMessage);
                    return false;
                }

                throw new Error("Réponse invalide");

            } catch (error) {
                if (currentRequest !== speciesCheckRequest) {
                    return null;
                }

                showFieldMessage(
                    speciesCheckMessage,
                    "Impossible de vérifier cette espèce " +
                    "pour le moment."
                );

                return null;
            }
        }

        newSpeciesName.addEventListener(
            "input",
            function () {
                speciesCheckRequest++;
                clearFieldMessage(speciesCheckMessage);
                clearImportMessage();
            }
        );

        newSpeciesName.addEventListener(
            "blur",
            checkSpeciesExists
        );


        /* ----------------------------------------------------------
           09. VÉRIFICATION DES ACCESSIONS NCBI
           ---------------------------------------------------------- */

        async function checkNcbiAccession() {
            if (!accessionInput) {
                return true;
            }

            const accession = accessionInput.value
                .trim()
                .toUpperCase();

            const currentRequest = ++ncbiCheckRequest;

            clearFieldMessage(ncbiMessage);

            if (
                !accession ||
                accessionInput.disabled ||
                getSpeciesMode() !== "new"
            ) {
                return true;
            }

            const endpoint = accessionInput.dataset.checkUrl;

            if (!endpoint) {
                showFieldMessage(
                    ncbiMessage,
                    "Impossible de vérifier cette accession."
                );

                return null;
            }

            const url = new URL(
                endpoint,
                window.location.origin
            );

            url.searchParams.set(
                "accession",
                accession
            );

            try {
                const response = await fetch(url, {
                    cache: "no-store"
                });

                const data = await response.json();

                if (
                    currentRequest !== ncbiCheckRequest ||
                    accessionInput.value.trim().toUpperCase() !== accession ||
                    getSpeciesMode() !== "new"
                ) {
                    return null;
                }

                if (data.valid === false) {
                    showFieldMessage(
                        ncbiMessage,
                        data.message ||
                        "Numéro d'accession invalide."
                    );

                    return false;
                }

                if (!response.ok) {
                    throw new Error("Erreur NCBI");
                }

                if (data.valid === true) {
                    const details = [
                        data.scientific_name,
                        data.assembly_name
                    ].filter(Boolean);

                    const text = details.length
                        ? "Accession vérifiée dans NCBI : " +
                          details.join(" — ")
                        : "Accession vérifiée dans NCBI.";

                    showFieldMessage(
                        ncbiMessage,
                        text,
                        false
                    );

                    return true;
                }

                throw new Error("Réponse NCBI invalide");

            } catch (error) {
                if (currentRequest !== ncbiCheckRequest) {
                    return null;
                }

                showFieldMessage(
                    ncbiMessage,
                    "Impossible de vérifier cette accession " +
                    "pour le moment."
                );

                return null;
            }
        }

        if (accessionInput) {
            accessionInput.addEventListener(
                "input",
                function () {
                    ncbiCheckRequest++;
                    clearFieldMessage(ncbiMessage);
                    clearImportMessage();
                }
            );
            /*
            accessionInput.addEventListener(
                "blur",
                checkNcbiAccession
            );
            */
        }


        /* ----------------------------------------------------------
           10. VALIDATION DU FORMULAIRE D'IMPORTATION
           ---------------------------------------------------------- */

        let verificationInProgress = false;

        form.addEventListener(
            "submit",
            async function (event) {

                event.preventDefault();

                if (verificationInProgress) {
                    return;
                }

                clearImportMessage();

                if (!form.reportValidity()) {
                    return;
                }

                const file = fileInput.files[0];

                if (!file) {
                    showImportMessage(
                        "Veuillez sélectionner un fichier.",
                        true
                    );
                    return;
                }

                if (!isAllowedFile(file)) {
                    const extensions =
                        allowedExtensions[dataType.value] || [];

                    showImportMessage(
                        "Format de fichier non accepté. " +
                        "Formats autorisés : " +
                        extensions.join(", "),
                        true
                    );
                    return;
                }

                verificationInProgress = true;

                const submitButton = form.querySelector(
                    'button[type="submit"]'
                );

                if (submitButton) {
                    submitButton.disabled = true;
                }

                try {
                    if (getSpeciesMode() === "new") {
                        const exists = await checkSpeciesExists();

                        if (exists === true) {
                            showImportMessage(
                                "Espèce invalide : veuillez renseigner " +
                                "une espèce qui n’existe pas encore " +
                                "dans TardiGen.",
                                true
                            );

                            return;
                        }

                        if (exists === null) {
                            showImportMessage(
                                "La vérification de l'espèce " +
                                "n'a pas abouti.",
                                true
                            );

                            return;
                        }
                        
                        /*
                        if (accessionInput && accessionInput.value.trim()) 
                            
                            {
                            const validAccession =
                                await checkNcbiAccession();

                            if (validAccession !== true) {
                                showImportMessage(
                                    "Veuillez vérifier le numéro " +
                                    "d'accession NCBI.",
                                    true
                                );

                                return;
                            }
                        }
                        */
                    }

                    if (getSpeciesMode() === "existing") {
                        if (!existingSpecies.value) {
                            showImportMessage(
                                "Veuillez sélectionner une espèce.",
                                true
                            );

                            return;
                        }
                    }

                    showImportMessage(
                        "Les champs et les références ont été " +
                        "vérifiés. L'analyse du contenu et " +
                        "l'enregistrement du fichier nécessitent " +
                        "le traitement côté serveur.",
                        false
                    );

                } finally {
                    verificationInProgress = false;

                    if (submitButton) {
                        submitButton.disabled = false;
                    }
                }
            }
        );


        /* ----------------------------------------------------------
           11. INITIALISATION DE L'IMPORTATION
           ---------------------------------------------------------- */

        updateAcceptedFormats();
        updateSpeciesMode();
    }


    /* ----------------------------------------------------------
       12. LANCEMENT DES FONCTIONNALITÉS
       ---------------------------------------------------------- */

    initComparison();
    initSequenceAnalysis();
    initImportData();

});

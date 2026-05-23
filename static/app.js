document.addEventListener('DOMContentLoaded', () => {
    const formulaInput = document.getElementById('formula-input');
    const solveBtn = document.getElementById('solve-btn');
    const uploadZone = document.getElementById('upload-zone');
    const fileInput = document.getElementById('file-input');
    
    // UI Elements
    const emptyState = document.getElementById('empty-state');
    const resultsContent = document.getElementById('results-content');
    const errorMessage = document.getElementById('error-message');
    const statusContainer = document.getElementById('status-container');
    const statusBadge = document.getElementById('status-badge');
    
    // Output Containers
    const clausesList = document.getElementById('clauses-list');
    const solutionsList = document.getElementById('solutions-list');
    const solutionCount = document.getElementById('solution-count');
    const ttHeader = document.getElementById('tt-header');
    const ttBody = document.getElementById('tt-body');
    const truthTableSection = document.getElementById('truth-table-section');
    const traceContainer = document.getElementById('trace-container');

    // Default formula
    formulaInput.value = "(P | Q) & (~P | R) & (~Q | ~R)";

    // Solve Button Click
    solveBtn.addEventListener('click', async () => {
        const formula = formulaInput.value.trim();
        if (!formula) {
            showError('Please enter a formula before solving.');
            emptyState.classList.add('hidden');
            errorMessage.classList.remove('hidden');
            resultsContent.classList.add('hidden');
            statusContainer.classList.add('hidden');
            return;
        }

        const mode = document.querySelector('input[name="solve-mode"]:checked').value;
        
        await performSolve('/api/solve', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ formula, mode })
        });
    });

    // File Upload Setup
    uploadZone.addEventListener('click', () => fileInput.click());
    
    uploadZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadZone.classList.add('dragover');
    });
    
    uploadZone.addEventListener('dragleave', () => {
        uploadZone.classList.remove('dragover');
    });
    
    uploadZone.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadZone.classList.remove('dragover');
        if (e.dataTransfer.files.length) {
            handleFileUpload(e.dataTransfer.files[0]);
        }
    });

    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length) {
            handleFileUpload(e.target.files[0]);
        }
    });

    async function handleFileUpload(file) {
        const mode = document.querySelector('input[name="solve-mode"]:checked').value;
        const formData = new FormData();
        formData.append('file', file);
        formData.append('mode', mode);

        formulaInput.value = `[Loaded DIMACS File: ${file.name}]`;

        await performSolve('/api/upload-dimacs', {
            method: 'POST',
            body: formData
        });
    }

    // Core Request Handler
    async function performSolve(endpoint, options) {
        // Reset UI
        emptyState.classList.add('hidden');
        errorMessage.classList.add('hidden');
        resultsContent.classList.add('hidden');
        statusContainer.classList.add('hidden');
        traceContainer.innerHTML = '';
        solveBtn.disabled = true;
        solveBtn.textContent = 'Solving...';

        try {
            const res = await fetch(endpoint, options);
            const data = await res.json();

            if (data.status === 'ERROR') {
                showError(data.message);
                return;
            }

            renderResults(data);
        } catch (err) {
            showError("Network or server error occurred.");
            console.error(err);
        } finally {
            solveBtn.disabled = false;
            solveBtn.textContent = 'Solve Formula';
        }
    }

    function showError(msg) {
        errorMessage.textContent = msg;
        errorMessage.classList.remove('hidden');
    }

    function renderResults(data) {
        // Render Status Badge
        statusBadge.className = `badge ${data.status.toLowerCase()}`;
        statusBadge.textContent = data.status === 'SAT' ? 'SATISFIABLE' : 'UNSATISFIABLE';
        statusContainer.classList.remove('hidden');

        // Render Clauses
        clausesList.innerHTML = data.clauses.map(c => `<span class="clause-tag">${c}</span>`).join('');

        // Render Solutions
        solutionCount.textContent = data.solutions.length;
        if (data.solutions.length === 0) {
            solutionsList.innerHTML = `<p style="color: var(--text-secondary); font-style: italic;">No satisfying assignments exist.</p>`;
        } else {
            solutionsList.innerHTML = data.solutions.map(sol => {
                const pills = Object.entries(sol).map(([k, v]) => {
                    const strVal = v ? 'T' : 'F';
                    const cssClass = v ? 'true' : 'false';
                    return `<div class="var-pill"><span class="var-name">${k}</span><span class="var-val ${cssClass}">${strVal}</span></div>`;
                }).join('');
                return `<div class="solution-card">${pills}</div>`;
            }).join('');
        }

        // Render Truth Table
        if (data.truth_table) {
            truthTableSection.classList.remove('hidden');
            ttHeader.innerHTML = data.truth_table.headers.map(h => `<th>${h}</th>`).join('');
            ttBody.innerHTML = data.truth_table.rows.map(row => {
                const cells = row.map((cell, idx) => {
                    if (idx === row.length - 1) { // Result column
                        if (cell === true) return `<td class="tt-true">T</td>`;
                        if (cell === false) return `<td class="tt-false">F</td>`;
                        return `<td>${cell}</td>`;
                    }
                    if (cell === true) return `<td style="color: var(--text-secondary)">T</td>`;
                    if (cell === false) return `<td style="color: var(--text-secondary)">F</td>`;
                    return `<td>${cell}</td>`;
                }).join('');
                return `<tr>${cells}</tr>`;
            }).join('');
        } else {
            truthTableSection.classList.add('hidden');
        }

        // Render DPLL Trace (with staggered animation)
        if (data.steps && data.steps.length > 0) {
            data.steps.forEach((step, idx) => {
                setTimeout(() => {
                    const el = document.createElement('div');
                    el.className = `trace-step ${step.type}`;
                    el.innerHTML = formatStep(step);
                    traceContainer.appendChild(el);
                    traceContainer.scrollTop = traceContainer.scrollHeight;
                }, Math.min(idx * 50, 2000)); // cap delay so it doesn't take forever for huge traces
            });
        } else {
            traceContainer.innerHTML = '<div class="empty-trace">No steps recorded.</div>';
        }

        resultsContent.classList.remove('hidden');
    }

    function formatStep(step) {
        const valStr = step.value ? 'T' : 'F';
        const valClass = step.value ? 'true' : 'false';
        const badge = `<span class="val-badge ${valClass}">${valStr}</span>`;
        
        switch (step.type) {
            case 'decide':
                return `<strong>Decide:</strong> branch on ${step.literal} = ${badge}`;
            case 'propagate':
                return `<strong>Propagate:</strong> force ${step.literal} = ${badge} <em>(${step.reason})</em>`;
            case 'pure':
                return `<strong>Pure literal:</strong> set ${step.literal} = ${badge}`;
            case 'backtrack':
                return `<strong>Backtrack:</strong> unwinding decisions after conflict`;
            case 'conflict':
                return `<strong>Conflict!</strong> Empty clause reached.`;
            case 'success':
                return `<strong>Success!</strong> Found satisfying assignment.`;
            default:
                return JSON.stringify(step);
        }
    }
});

// Global State
let selectedFile = null;
let currentAdvisory = { en: '', hi: '' };

// Mock Coordinates list in India to cycle through on button click (makes testing clusters easy)
const mockLocations = [
    { lat: 12.9716, lon: 77.5946 }, // Bengaluru Test Point A (Center)
    { lat: 12.9785, lon: 77.6012 }, // Bengaluru Test Point B (1 km away)
    { lat: 12.9730, lon: 77.5990 }, // Bengaluru Test Point C (0.5 km away - Triggers Cluster!)
    { lat: 28.6139, lon: 77.2090 }, // New Delhi Test Point
    { lat: 19.0760, lon: 72.8777 }, // Mumbai Test Point
];
let coordIndex = 0;

// DOM Elements
const uploadZone = document.getElementById('uploadZone');
const fileInput = document.getElementById('fileInput');
const previewContainer = document.getElementById('previewContainer');
const imagePreview = document.getElementById('imagePreview');
const removeImgBtn = document.getElementById('removeImgBtn');
const latitudeInput = document.getElementById('latitude');
const longitudeInput = document.getElementById('longitude');
const gpsBtn = document.getElementById('gpsBtn');
const reportForm = document.getElementById('reportForm');
const submitBtn = document.getElementById('submitBtn');

const pipelineCard = document.getElementById('pipelineCard');
const stepVision = document.getElementById('stepVision');
const stepAdvisory = document.getElementById('stepAdvisory');
const stepEscalation = document.getElementById('stepEscalation');

const alertsFeed = document.getElementById('alertsFeed');
const alertCount = document.getElementById('alertCount');
const reportsFeed = document.getElementById('reportsFeed');

// Modal Elements
const advisoryModal = document.getElementById('advisoryModal');
const closeModalBtn = document.getElementById('closeModalBtn');
const tabEnBtn = document.getElementById('tabEnBtn');
const tabHiBtn = document.getElementById('tabHiBtn');
const tabEnContent = document.getElementById('tabEnContent');
const tabHiContent = document.getElementById('tabHiContent');

// Initialize Dashboard
document.addEventListener('DOMContentLoaded', () => {
    // Set initial mock location
    setMockCoordinates();
    
    // Initial fetch of data
    fetchReports();
    fetchAlerts();
    
    // Poll for updates every 5 seconds
    setInterval(() => {
        fetchReports();
        fetchAlerts();
    }, 5000);
});

// Mock GPS Coordinate Cycling
gpsBtn.addEventListener('click', setMockCoordinates);

function setMockCoordinates() {
    const loc = mockLocations[coordIndex];
    latitudeInput.value = loc.lat.toFixed(4);
    longitudeInput.value = loc.lon.toFixed(4);
    
    // Cycle coordinates index
    coordIndex = (coordIndex + 1) % mockLocations.length;
    
    // Sparkle effect on inputs
    latitudeInput.classList.add('pulse-glow');
    longitudeInput.classList.add('pulse-glow');
    setTimeout(() => {
        latitudeInput.classList.remove('pulse-glow');
        longitudeInput.classList.remove('pulse-glow');
    }, 1000);
}

// Drag & Drop Functionality
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
    if (e.dataTransfer.files.length > 0) {
        handleFile(e.dataTransfer.files[0]);
    }
});

fileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        handleFile(e.target.files[0]);
    }
});

function handleFile(file) {
    // Validate file size (5MB security limit)
    if (file.size > 5 * 1024 * 1024) {
        alert("Security Alert: File size exceeds the 5MB upload limit.");
        return;
    }
    
    // Validate image format
    const allowed = ['image/png', 'image/jpeg', 'image/jpg', 'image/webp'];
    if (!allowed.includes(file.type)) {
        alert("Security Alert: Invalid file type. Please upload an image (.png, .jpg, .jpeg, .webp)");
        return;
    }
    
    selectedFile = file;
    const reader = new FileReader();
    reader.onload = (e) => {
        imagePreview.src = e.target.result;
        previewContainer.style.display = 'block';
    };
    reader.readAsDataURL(file);
}

removeImgBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    selectedFile = null;
    imagePreview.src = '';
    previewContainer.style.display = 'none';
    fileInput.value = '';
});

// Form Submission & Multi-Agent Animation
reportForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    if (!selectedFile) {
        alert("Please select or drop an image of the water source.");
        return;
    }
    
    const lat = latitudeInput.value;
    const lon = longitudeInput.value;
    
    // Setup form data
    const formData = new FormData();
    formData.append('latitude', lat);
    formData.append('longitude', lon);
    formData.append('image', selectedFile);
    
    // Prepare visualizer card and lock submit button
    pipelineCard.style.display = 'block';
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Processing...';
    
    // Start step-by-step pipeline visualization
    resetPipelineSteps();
    
    try {
        // Step 1: Vision Diagnosis starts
        setStepActive(stepVision, "Vision Diagnosis Agent: Loading image and scanning for contamination...");
        
        // Parallelized network request
        const apiPromise = fetch('/api/report', {
            method: 'POST',
            body: formData
        });
        
        // Force minimum delays on steps to allow the user to see the pipeline transition
        await sleep(1500);
        setStepComplete(stepVision, "Vision Diagnosis Agent: Analyzed contamination signs.");
        
        // Step 2: Advisory starts
        setStepActive(stepAdvisory, "Advisory Agent: Formatting plain-language safety alerts...");
        await sleep(1500);
        setStepComplete(stepAdvisory, "Advisory Agent: Formatted instructions in English & Hindi.");
        
        // Step 3: Escalation check starts
        setStepActive(stepEscalation, "Escalation Agent: Storing report and running clustering scan...");
        
        const response = await apiPromise;
        const result = await response.json();
        
        if (!response.ok) {
            throw new Error(result.detail || "Server error running multi-agent pipeline.");
        }
        
        await sleep(1000);
        
        if (result.escalation && result.escalation.status === 'escalated') {
            setStepComplete(stepEscalation, "Escalation Agent: Cluster detected! Local authorities escalated via MCP Server.");
        } else {
            setStepComplete(stepEscalation, "Escalation Agent: Saved to DB. Proximity check clean.");
        }
        
        // Release Form & refresh feeds
        submitBtn.disabled = false;
        submitBtn.innerHTML = '<i class="fa-solid fa-paper-plane"></i> Submit Report';
        
        // Open details modal immediately
        showAdvisoryModal(result.advisory.en, result.advisory.hi);
        
        // Reset image selector
        removeImgBtn.click();
        
        // Refresh feeds
        fetchReports();
        fetchAlerts();
        
    } catch (err) {
        console.error(err);
        alert("Pipeline failed: " + err.message);
        submitBtn.disabled = false;
        submitBtn.innerHTML = '<i class="fa-solid fa-paper-plane"></i> Submit Report';
        pipelineCard.style.display = 'none';
    }
});

// Helper functions for pipeline step elements
function resetPipelineSteps() {
    [stepVision, stepAdvisory, stepEscalation].forEach(step => {
        step.className = 'pipeline-step';
        step.querySelector('.step-status').innerText = 'Pending...';
    });
}

function setStepActive(stepElement, message) {
    stepElement.className = 'pipeline-step active';
    stepElement.querySelector('.step-status').innerText = message;
}

function setStepComplete(stepElement, message) {
    stepElement.className = 'pipeline-step complete';
    stepElement.querySelector('.step-status').innerText = message;
}

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// Fetch Reports Feed
async function fetchReports() {
    try {
        const res = await fetch('/api/reports');
        if (!res.ok) return;
        const reports = await res.json();
        renderReports(reports);
    } catch (err) {
        console.error("Failed fetching reports:", err);
    }
}

// Render Reports HTML
function renderReports(reports) {
    if (reports.length === 0) {
        reportsFeed.innerHTML = `
            <div class="empty-state">
                <i class="fa-solid fa-database empty-icon"></i>
                <p>No reports registered. Use the panel on the left to submit.</p>
            </div>`;
        return;
    }
    
    reportsFeed.innerHTML = reports.map(r => {
        const dateStr = new Date(r.timestamp).toLocaleString();
        const symptomsList = r.contamination_signs 
            ? r.contamination_signs.split(',').map(s => `<span class="symp-badge">${s.trim().toUpperCase()}</span>`).join('')
            : '<span class="symp-badge">NONE</span>';
            
        // Risk level class definitions
        let riskBadgeClass = 'badge-success';
        if (r.risk_level === 'High') riskBadgeClass = 'badge-danger';
        else if (r.risk_level === 'Medium') riskBadgeClass = 'badge-warning';
        
        // Escalation badge status
        const escBadge = r.escalated === 1 
            ? `<span class="escalation-badge escalated"><i class="fa-solid fa-triangle-exclamation"></i> Escalated via MCP</span>`
            : `<span class="escalation-badge registered"><i class="fa-solid fa-circle-check"></i> Registered</span>`;
            
        // Advisory mapping for popup modal
        const advisories = r.advisory.split(' || ');
        const advEn = advisories[0] || '';
        const advHi = advisories[1] || '';
        
        return `
            <div class="report-item">
                <img src="${r.image_path}" class="report-thumb" alt="Water source photo">
                <div class="report-info">
                    <div class="report-top-row">
                        <span class="report-coords">Lat: ${r.latitude.toFixed(4)}, Lon: ${r.longitude.toFixed(4)}</span>
                        <span class="timestamp">${dateStr}</span>
                    </div>
                    <div class="report-symptoms">
                        ${symptomsList}
                        <span class="badge ${riskBadgeClass}">${r.risk_level} Risk</span>
                    </div>
                    <div class="report-actions">
                        <button type="button" class="view-adv-btn" onclick="showAdvisoryModal(\`${escapeQuotes(advEn)}\`, \`${escapeQuotes(advHi)}\`)">
                            <i class="fa-solid fa-shield-halved"></i> View Advisory
                        </button>
                        ${escBadge}
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

function escapeQuotes(str) {
    return str.replace(/"/g, '&quot;').replace(/'/g, '\\\'');
}

// Fetch Alerts Feed
async function fetchAlerts() {
    try {
        const res = await fetch('/api/alerts');
        if (!res.ok) return;
        const alerts = await res.json();
        renderAlerts(alerts);
    } catch (err) {
        console.error("Failed fetching alerts:", err);
    }
}

// Render Alerts HTML
function renderAlerts(alerts) {
    alertCount.innerText = `${alerts.length} Alerts`;
    
    if (alerts.length === 0) {
        alertsFeed.innerHTML = `
            <div class="empty-state">
                <i class="fa-solid fa-shield-halved empty-icon"></i>
                <p>No active cluster alerts triggered yet.</p>
            </div>`;
        return;
    }
    
    alertsFeed.innerHTML = alerts.map(a => {
        const dateStr = new Date(a.timestamp).toLocaleString();
        return `
            <div class="alert-item">
                <div class="alert-icon-wrap">
                    <i class="fa-solid fa-triangle-exclamation"></i>
                </div>
                <div class="alert-details">
                    <div class="alert-title-row">
                        <h4>Cluster Alert Escalated</h4>
                        <span class="alert-time">${dateStr}</span>
                    </div>
                    <p class="alert-text">${a.details}</p>
                    <div class="alert-meta">
                        <span><i class="fa-solid fa-location-crosshairs"></i> Lat: ${a.latitude.toFixed(4)}, Lon: ${a.longitude.toFixed(4)}</span>
                        <span><i class="fa-solid fa-people-group"></i> Reports: ${a.report_count}</span>
                        <span><i class="fa-solid fa-circle-exclamation"></i> Cluster ID: ${a.cluster_id}</span>
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

// Modal Toggle Logic
function showAdvisoryModal(enHtml, hiHtml) {
    currentAdvisory.en = enHtml;
    currentAdvisory.hi = hiHtml;
    
    tabEnContent.innerHTML = enHtml;
    tabHiContent.innerHTML = hiHtml;
    
    // Default to English
    tabEnBtn.click();
    advisoryModal.style.display = 'flex';
}

closeModalBtn.addEventListener('click', () => {
    advisoryModal.style.display = 'none';
});

// Close modal if clicking overlay background
advisoryModal.addEventListener('click', (e) => {
    if (e.target === advisoryModal) {
        advisoryModal.style.display = 'none';
    }
});

// English / Hindi Tab toggling
tabEnBtn.addEventListener('click', () => {
    tabEnBtn.classList.add('active');
    tabHiBtn.classList.remove('active');
    tabEnContent.style.display = 'block';
    tabHiContent.style.display = 'none';
});

tabHiBtn.addEventListener('click', () => {
    tabHiBtn.classList.add('active');
    tabEnBtn.classList.remove('active');
    tabEnContent.style.display = 'none';
    tabHiContent.style.display = 'block';
});

// Expose modal trigger globally so inline onclick handlers in report list can use it
window.showAdvisoryModal = showAdvisoryModal;

/**
 * CodeKisaan Interactive Frontend Logic
 * Seva Innovation Challenge 2026
 */

document.addEventListener("DOMContentLoaded", () => {
    initLeafUploader();
    initSampleChips();
});

/**
 * Handles image selection, drag & drop, client-side validation, and instant preview.
 */
function initLeafUploader() {
    const dropzone = document.getElementById("leafDropzone");
    const fileInput = document.getElementById("leafFileInput");
    const previewContainer = document.getElementById("previewContainer");
    const previewImage = document.getElementById("previewImage");
    const uploadForm = document.getElementById("leafScanForm");
    const btnDiagnose = document.getElementById("btnDiagnose");
    const scanProgressBar = document.getElementById("scanProgressBar");
    const scanStatusText = document.getElementById("scanStatusText");

    if (!dropzone || !fileInput) return;

    // Trigger file input on dropzone click
    dropzone.addEventListener("click", () => fileInput.click());

    // Drag & Drop effects
    ["dragenter", "dragover"].forEach(eventName => {
        dropzone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropzone.classList.add("dragover");
        }, false);
    });

    ["dragleave", "drop"].forEach(eventName => {
        dropzone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropzone.classList.remove("dragover");
        }, false);
    });

    dropzone.addEventListener("drop", (e) => {
        const dt = e.dataTransfer;
        const files = dt.files;
        if (files && files.length > 0) {
            handleSelectedFile(files[0]);
        }
    });

    fileInput.addEventListener("change", (e) => {
        if (e.target.files && e.target.files.length > 0) {
            handleSelectedFile(e.target.files[0]);
        }
    });

    function handleSelectedFile(file) {
        // Validate file type
        const validExtensions = ["image/jpeg", "image/png", "image/webp", "image/jpg"];
        if (!validExtensions.includes(file.type)) {
            alert("कृपया फक्त वैध फोटो (JPG, PNG, WEBP) निवडा / Please upload only JPG, PNG, or WEBP image.");
            return;
        }

        // Validate size (5MB max)
        const maxSize = 5 * 1024 * 1024;
        if (file.size > maxSize) {
            alert("फोटोचा आकार 5MB पेक्षा लहान असावा / Image file size must be less than 5MB.");
            return;
        }

        // Clear any previous sample selection so uploaded file takes precedence
        const sampleInput = document.getElementById("sampleImageName");
        if (sampleInput) sampleInput.value = "";

        // Preview
        const reader = new FileReader();
        reader.onload = (e) => {
            if (previewImage && previewContainer) {
                previewImage.src = e.target.result;
                previewContainer.style.display = "block";
            }
            if (btnDiagnose) {
                btnDiagnose.disabled = false;
                btnDiagnose.scrollIntoView({ behavior: "smooth", block: "nearest" });
            }
        };
        reader.readAsDataURL(file);
    }

    // Submit handler with animated AI progress
    if (uploadForm) {
        uploadForm.addEventListener("submit", (e) => {
            if (btnDiagnose) {
                btnDiagnose.disabled = true;
                btnDiagnose.innerHTML = `<span class="spinner-border spinner-border-sm me-2" role="status"></span> एआय विश्लेषण सुरू आहे / Analyzing Leaf...`;
            }
            if (scanProgressBar) {
                scanProgressBar.style.display = "block";
                animateDiagnosticProgress();
            }
        });
    }

    function animateDiagnosticProgress() {
        let progress = 10;
        const bar = scanProgressBar.querySelector(".progress-bar");
        const interval = setInterval(() => {
            progress += 18;
            if (bar) bar.style.width = `${Math.min(progress, 90)}%`;
            if (scanStatusText) {
                if (progress < 40) scanStatusText.innerText = "पानाचा रंग व क्लोरोफिल तपासत आहे... / Inspecting chlorophyll spectrum...";
                else if (progress < 75) scanStatusText.innerText = "बुरशी व जिवाणू डागांचे विश्लेषण... / Matching pathogen spore patterns...";
                else scanStatusText.innerText = "उपाययोजना व सल्ला तयार करत आहे... / Formulating agricultural advisory...";
            }
            if (progress >= 90) clearInterval(interval);
        }, 300);
    }
}

/**
 * Quick Sample Leaf Selection for Judges & Demos
 */
function initSampleChips() {
    const chips = document.querySelectorAll(".sample-leaf-chip");
    const previewContainer = document.getElementById("previewContainer");
    const previewImage = document.getElementById("previewImage");
    const btnDiagnose = document.getElementById("btnDiagnose");
    const sampleInput = document.getElementById("sampleImageName");
    const cropSelect = document.getElementById("cropSelect");
    const fileInput = document.getElementById("leafFileInput");

    chips.forEach(chip => {
        chip.addEventListener("click", () => {
            const sampleName = chip.getAttribute("data-sample");
            const cropType = chip.getAttribute("data-crop");
            const imgPath = chip.getAttribute("data-src");

            if (sampleInput) sampleInput.value = sampleName;
            if (cropSelect && cropType) cropSelect.value = cropType;
            if (fileInput) fileInput.value = ""; // Clear file input when sample is chosen

            if (previewImage && previewContainer) {
                previewImage.src = imgPath;
                previewContainer.style.display = "block";
            }

            if (btnDiagnose) {
                btnDiagnose.disabled = false;
                btnDiagnose.classList.add("pulse-btn");
                btnDiagnose.scrollIntoView({ behavior: "smooth", block: "nearest" });
            }
        });
    });
}

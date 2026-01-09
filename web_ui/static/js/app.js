// Application state - matches GUI state exactly
const appState = {
    currentStep: 1,
    jobId: null,
    report: null,
    apiUrl: 'http://148.251.88.48:8000',
    selectedFile: null,
    uploadCancelled: false,
    uploadInProgress: false,
    vizGenerated: false,
    logs: []
};

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('apiUrl').value = appState.apiUrl;
    showStep(1);
    setupDragAndDrop();
    logMessage('Application initialized', 'INFO');
});

// Step Navigation - matches GUI exactly
function showStep(step) {
    appState.currentStep = step;
    
    // Hide all steps
    document.querySelectorAll('.step-content').forEach(el => {
        el.classList.remove('active');
    });
    
    // Show current step
    document.getElementById(`step${step}`).classList.add('active');
    
    // Update progress indicators
    updateProgressIndicators(step);
    
    // Update navigation buttons
    updateNavigationButtons();
    
    // If navigating to step 3 and report is not loaded, try to fetch it
    if (step === 3 && !appState.report && appState.jobId) {
        // Check if job is completed first
        fetch(`${appState.apiUrl}/api/v1/status/${appState.jobId}`)
            .then(response => response.json())
            .then(data => {
                if (data.status === 'completed') {
                    // Automatically fetch the report
                    downloadReport();
                } else if (data.status === 'processing') {
                    // Still processing, show message
                    const statusText = document.getElementById('statusText');
                    if (statusText) statusText.textContent = '⏳ Processing... Please wait.';
                    logMessage('Job is still processing. Please wait...', 'INFO');
                } else if (data.status === 'failed') {
                    const error = data.error || 'Unknown error';
                    logMessage(`❌ Processing failed: ${error}`, 'ERROR');
                    showAlert('Error', `Processing failed:\n${error}`, 'error');
                }
            })
            .catch(error => {
                logMessage(`❌ Error checking status: ${error.message}`, 'ERROR');
            });
    }
}

function updateProgressIndicators(step) {
    document.querySelectorAll('.step-indicator').forEach((el, idx) => {
        const circle = el.querySelector('.step-circle');
        const number = el.querySelector('.step-number');
        const name = el.querySelector('.step-name');
        
        if (idx + 1 < step) {
            circle.classList.remove('active');
            number.style.color = '#B0B0B0';
            name.style.color = '#B0B0B0';
            el.classList.remove('active');
        } else if (idx + 1 === step) {
            circle.classList.add('active');
            number.style.color = '#FFFFFF';
            name.style.color = '#818CF8';
            el.classList.add('active');
        } else {
            circle.classList.remove('active');
            number.style.color = '#B0B0B0';
            name.style.color = '#B0B0B0';
            el.classList.remove('active');
        }
    });
}

function updateNavigationButtons() {
    const prevBtn = document.getElementById('prevBtn');
    const nextBtn = document.getElementById('nextBtn');
    
    // Previous button
    if (appState.currentStep > 1) {
        prevBtn.disabled = false;
        prevBtn.style.cursor = 'pointer';
        prevBtn.style.backgroundColor = '#1A1A1A';
        prevBtn.style.color = '#FFFFFF';
    } else {
        prevBtn.disabled = true;
        prevBtn.style.cursor = 'not-allowed';
        prevBtn.style.backgroundColor = '#1A1A1A';
        prevBtn.style.color = '#B0B0B0';
    }
    
    // Next button - matches GUI logic exactly
    if (appState.currentStep === 1) {
        // Check if embeddings are complete by checking job status
        const step1Complete = appState.jobId !== null;
        let embeddingsComplete = false;
        
        // If we have a job ID, check if embeddings are done
        if (step1Complete && appState.jobId) {
            // Check status asynchronously to see if embeddings are complete
            fetch(`${appState.apiUrl}/api/v1/status/${appState.jobId}`)
                .then(response => response.json())
                .then(data => {
                    const currentStage = data.current_stage || '';
                    // Enable Next button when embeddings are complete
                    if (currentStage === 'building_report' || currentStage === 'completed' || data.status === 'completed') {
                        const nextBtn = document.getElementById('nextBtn');
                        if (nextBtn) {
                            nextBtn.disabled = false;
                            nextBtn.textContent = 'Next →';
                            nextBtn.style.cursor = 'pointer';
                            nextBtn.style.backgroundColor = '#6366F1';
                            nextBtn.style.color = '#FFFFFF';
                        }
                    }
                })
                .catch(() => {
                    // If status check fails, just enable based on job ID
                });
        }
        
        // Initially, only enable if job ID exists (upload complete)
        // The async check above will enable it when embeddings are done
        if (step1Complete) {
            // Don't enable immediately - wait for embeddings
            nextBtn.disabled = true;
            nextBtn.textContent = 'Next → (Generating embeddings...)';
            nextBtn.style.cursor = 'not-allowed';
            nextBtn.style.backgroundColor = '#1A1A1A';
            nextBtn.style.color = '#B0B0B0';
        } else {
            nextBtn.disabled = true;
            nextBtn.textContent = 'Next → (Upload file first)';
            nextBtn.style.cursor = 'not-allowed';
            nextBtn.style.backgroundColor = '#1A1A1A';
            nextBtn.style.color = '#B0B0B0';
        }
    } else if (appState.currentStep === 2) {
        const step2Complete = appState.report !== null;
        if (step2Complete) {
            nextBtn.disabled = false;
            nextBtn.textContent = 'Next →';
            nextBtn.style.cursor = 'pointer';
            nextBtn.style.backgroundColor = '#6366F1';
            nextBtn.style.color = '#FFFFFF';
        } else {
            nextBtn.disabled = true;
            nextBtn.textContent = 'Next → (Download report first)';
            nextBtn.style.cursor = 'not-allowed';
            nextBtn.style.backgroundColor = '#1A1A1A';
            nextBtn.style.color = '#B0B0B0';
        }
    } else {
        nextBtn.disabled = true;
        nextBtn.textContent = 'Complete';
        nextBtn.style.cursor = 'not-allowed';
        nextBtn.style.backgroundColor = '#1A1A1A';
        nextBtn.style.color = '#B0B0B0';
    }
}

function nextStep() {
    if (appState.currentStep === 1 && !appState.jobId) {
        showAlert('Step Not Complete', 'Please upload an audio file first.', 'warning');
        return;
    } else if (appState.currentStep === 2 && !appState.report) {
        showAlert('Step Not Complete', 'Please download the report first.', 'warning');
        return;
    }
    
    if (appState.currentStep < 3) {
        showStep(appState.currentStep + 1);
    }
}

function previousStep() {
    if (appState.currentStep > 1) {
        showStep(appState.currentStep - 1);
    }
}

// File Upload - matches GUI exactly
function setupDragAndDrop() {
    const uploadArea = document.getElementById('uploadArea');
    
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        uploadArea.addEventListener(eventName, preventDefaults, false);
    });
    
    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }
    
    ['dragenter', 'dragover'].forEach(eventName => {
        uploadArea.addEventListener(eventName, () => {
            uploadArea.style.borderColor = '#6366F1';
        }, false);
    });
    
    ['dragleave', 'drop'].forEach(eventName => {
        uploadArea.addEventListener(eventName, () => {
            uploadArea.style.borderColor = '#666666';
        }, false);
    });
    
    uploadArea.addEventListener('drop', handleDrop, false);
}

function handleDrop(e) {
    const dt = e.dataTransfer;
    const files = dt.files;
    if (files.length > 0) {
        handleFile(files[0]);
    }
}

function triggerFileInput() {
    if (!appState.uploadInProgress) {
        document.getElementById('fileInput').click();
    }
}

function handleFileSelect(e) {
    if (e.target.files.length > 0) {
        handleFile(e.target.files[0]);
    }
}

function handleFile(file) {
    // Validate file type
    const validTypes = ['audio/wav', 'audio/mpeg', 'audio/mp3', 'audio/flac', 'audio/m4a', 'audio/aac'];
    const validExtensions = ['.wav', '.mp3', '.flac', '.m4a', '.aac'];
    const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
    
    if (!validTypes.includes(file.type) && !validExtensions.includes(fileExtension)) {
        showAlert('Error', 'Please select a valid audio file (WAV, MP3, FLAC, M4A, AAC)', 'error');
        return;
    }
    
    appState.selectedFile = file;
    const fileInfo = document.getElementById('fileInfo');
    const fileName = document.getElementById('fileName');
    const filePath = document.getElementById('filePath');
    
    const fileSizeMB = (file.size / (1024 * 1024)).toFixed(1);
    fileName.textContent = `${file.name} (${fileSizeMB} MB)`;
    filePath.value = file.name;
    fileInfo.style.display = 'block';
    
    const uploadBtn = document.getElementById('uploadBtn');
    uploadBtn.disabled = false;
    uploadBtn.style.cursor = 'pointer';
}

function removeFile() {
    if (appState.uploadInProgress) {
        appState.uploadCancelled = true;
        logMessage('Upload cancellation requested...', 'INFO');
    }
    
    appState.selectedFile = null;
    document.getElementById('fileInfo').style.display = 'none';
    document.getElementById('fileInput').value = '';
    document.getElementById('uploadBtn').disabled = true;
    document.getElementById('uploadProgress').style.display = 'none';
    document.getElementById('progressFill').style.width = '0%';
    document.getElementById('progressLabel').textContent = '';
}

// API Functions - matches GUI exactly
async function testConnection() {
    const apiUrl = document.getElementById('apiUrl').value.trim().replace(/\/$/, '');
    appState.apiUrl = apiUrl;
    
    logMessage('Testing API health endpoint...', 'INFO');
    
    try {
        const response = await fetch(`${apiUrl}/health`, { timeout: 30000 });
        const data = await response.json();
        logMessage(`✅ Connection successful: ${JSON.stringify(data)}`, 'SUCCESS');
        showAlert('Success', `Connection successful!\n\n${JSON.stringify(data, null, 2)}`, 'success');
    } catch (error) {
        logMessage(`❌ Connection error: ${error.message}`, 'ERROR');
        showAlert('Error', `Cannot connect to API!\n\n${error.message}`, 'error');
    }
}

async function uploadFile() {
    if (!appState.selectedFile) {
        showAlert('Error', 'Please select a valid audio file', 'error');
        return;
    }
    
    // Get API URL from input
    const apiUrl = document.getElementById('apiUrl').value.trim().replace(/\/$/, '');
    appState.apiUrl = apiUrl;
    
    console.log('Starting upload...', {
        file: appState.selectedFile.name,
        size: appState.selectedFile.size,
        apiUrl: apiUrl
    });
    
    appState.uploadCancelled = false;
    appState.uploadInProgress = true;
    
    const uploadBtn = document.getElementById('uploadBtn');
    uploadBtn.disabled = true;
    uploadBtn.textContent = 'Uploading...';
    
    const progressFill = document.getElementById('progressFill');
    const progressLabel = document.getElementById('progressLabel');
    const uploadProgress = document.getElementById('uploadProgress');
    
    // Show progress bar
    uploadProgress.style.display = 'block';
    progressFill.style.width = '0%';
    progressLabel.textContent = '0% - Starting upload...';
    
    logMessage(`Uploading: ${appState.selectedFile.name}`, 'INFO');
    
    try {
        const formData = new FormData();
        formData.append('file', appState.selectedFile);
        
        const xhr = new XMLHttpRequest();
        const uploadUrl = `${appState.apiUrl}/api/v1/provenance-check`;
        
        console.log('Upload URL:', uploadUrl);
        
        xhr.upload.addEventListener('progress', (e) => {
            if (e.lengthComputable && !appState.uploadCancelled) {
                const percent = Math.min(Math.round((e.loaded / e.total) * 100), 100);
                progressFill.style.width = percent + '%';
                const uploadedMB = (e.loaded / (1024 * 1024)).toFixed(2);
                const totalMB = (e.total / (1024 * 1024)).toFixed(2);
                progressLabel.textContent = `${percent}% (${uploadedMB} MB / ${totalMB} MB)`;
                console.log(`Upload progress: ${percent}%`);
            }
        });
        
        xhr.addEventListener('loadstart', () => {
            console.log('Upload started');
            logMessage('Upload started...', 'INFO');
        });
        
        xhr.addEventListener('load', () => {
            console.log('Upload load event:', {
                status: xhr.status,
                statusText: xhr.statusText,
                responseText: xhr.responseText.substring(0, 200)
            });
            
            if (appState.uploadCancelled) {
                logMessage('Upload cancelled by user', 'INFO');
                progressLabel.textContent = 'Cancelled';
                appState.uploadInProgress = false;
                uploadBtn.disabled = false;
                uploadBtn.textContent = 'Upload & Process Track';
                return;
            }
            
            if (xhr.status === 200) {
                try {
                    const response = JSON.parse(xhr.responseText);
                    console.log('Upload response:', response);
                    appState.jobId = response.job_id;
                    
                    logMessage('✅ Upload successful', 'SUCCESS');
                    logMessage(`Job ID: ${appState.jobId}`, 'INFO');
                    
                    // Update step 2 elements if they exist
                    const jobIdValue = document.getElementById('jobIdValue');
                    const statusText = document.getElementById('statusText');
                    const processingProgressFill = document.getElementById('processingProgressFill');
                    const processingProgressLabel = document.getElementById('processingProgressLabel');
                    
                    if (jobIdValue) jobIdValue.textContent = appState.jobId;
                    if (statusText) statusText.textContent = '✅ Uploaded - Processing...';
                    if (processingProgressFill) processingProgressFill.style.width = '100%';
                    if (processingProgressLabel) processingProgressLabel.textContent = '100%';
                    
                    showAlert('Success', 
                        `Track uploaded successfully!\n\nJob ID: ${appState.jobId}\n\nProcessing has started. Generating embeddings...`, 
                        'success');
                    
                    // Start polling for status updates to show embedding progress
                    autoCheckStatus();
                    
                    // Update navigation button
                    updateNavigationButtons();
                } catch (parseError) {
                    console.error('Parse error:', parseError);
                    logMessage(`❌ Error parsing response: ${parseError.message}`, 'ERROR');
                    showAlert('Error', `Upload response error: ${parseError.message}\n\nResponse: ${xhr.responseText.substring(0, 200)}`, 'error');
                }
            } else {
                let errorMsg = xhr.statusText;
                try {
                    const errorResponse = JSON.parse(xhr.responseText);
                    errorMsg = errorResponse.detail || errorResponse.message || errorMsg;
                } catch (e) {
                    // Use statusText if JSON parsing fails
                }
                
                console.error('Upload failed:', {
                    status: xhr.status,
                    statusText: xhr.statusText,
                    response: xhr.responseText
                });
                
                logMessage(`❌ Upload error: ${xhr.status} ${errorMsg}`, 'ERROR');
                showAlert('Error', `Upload error: ${xhr.status} ${errorMsg}\n\nResponse: ${xhr.responseText.substring(0, 200)}`, 'error');
            }
            
            appState.uploadInProgress = false;
            uploadBtn.disabled = false;
            uploadBtn.textContent = 'Upload & Process Track';
            
            setTimeout(() => {
                progressLabel.textContent = '';
            }, 2000);
        });
        
        xhr.addEventListener('error', (e) => {
            console.error('XHR error event:', e);
            if (!appState.uploadCancelled) {
                logMessage('❌ Upload error: Network error', 'ERROR');
                showAlert('Error', 'Upload failed: Network error. Please check your connection and API URL.', 'error');
            }
            appState.uploadInProgress = false;
            uploadBtn.disabled = false;
            uploadBtn.textContent = 'Upload & Process Track';
        });
        
        xhr.addEventListener('timeout', () => {
            console.error('Upload timeout');
            logMessage('❌ Upload timeout', 'ERROR');
            showAlert('Error', 'Upload timeout. The file may be too large or the server is not responding.', 'error');
            appState.uploadInProgress = false;
            uploadBtn.disabled = false;
            uploadBtn.textContent = 'Upload & Process Track';
        });
        
        xhr.addEventListener('abort', () => {
            console.log('Upload aborted');
            logMessage('Upload aborted', 'INFO');
            appState.uploadInProgress = false;
            uploadBtn.disabled = false;
            uploadBtn.textContent = 'Upload & Process Track';
        });
        
        xhr.open('POST', uploadUrl);
        xhr.timeout = 300000; // 5 minutes timeout
        console.log('Sending request...');
        xhr.send(formData);
        
    } catch (error) {
        console.error('Upload exception:', error);
        if (!appState.uploadCancelled) {
            logMessage(`❌ Upload error: ${error.message}`, 'ERROR');
            showAlert('Error', `Upload error: ${error.message}`, 'error');
        }
        appState.uploadInProgress = false;
        uploadBtn.disabled = false;
        uploadBtn.textContent = 'Upload & Process Track';
    }
}

async function autoCheckStatus() {
    if (!appState.jobId) return;
    
    const MAX_WAIT = 1800; // 30 minutes
    const startTime = Date.now();
    
    logMessage('Waiting for processing to complete...', 'INFO');
    
    const checkLoop = async () => {
        if (Date.now() - startTime > MAX_WAIT * 1000) {
            logMessage(`⏱️ Timeout after ${MAX_WAIT}s`, 'WARNING');
            const statusText = document.getElementById('statusText');
            if (statusText) statusText.textContent = '⏱️ Timeout';
            return;
        }
        
        try {
            const response = await fetch(`${appState.apiUrl}/api/v1/status/${appState.jobId}`);
            const data = await response.json();
            const status = data.status;
            const currentStage = data.current_stage || '';
            const progressPercent = data.progress_percent || 0;
            const stageMessage = data.stage_message || '';
            
            // Update progress display in step 1 (upload section) during processing
            if ((currentStage === 'embedding' || currentStage === 'building_report' || currentStage === 'completed') && appState.currentStep === 1) {
                const uploadProgress = document.getElementById('uploadProgress');
                const progressFill = document.getElementById('progressFill');
                const progressLabel = document.getElementById('progressLabel');
                
                if (uploadProgress && progressFill && progressLabel) {
                    uploadProgress.style.display = 'block';
                    progressFill.style.width = progressPercent + '%';
                    progressLabel.textContent = `${progressPercent}% - ${stageMessage}`;
                }
            }
            
            // Enable Next button when report building is complete (100% or status completed)
            if (appState.currentStep === 1) {
                const nextBtn = document.getElementById('nextBtn');
                const shouldEnable = (currentStage === 'building_report' && progressPercent >= 100) || 
                                   (currentStage === 'completed') || 
                                   (status === 'completed');
                
                if (shouldEnable && nextBtn && nextBtn.disabled) {
                    nextBtn.disabled = false;
                    nextBtn.textContent = 'Next →';
                    nextBtn.style.cursor = 'pointer';
                    nextBtn.style.backgroundColor = '#6366F1';
                    nextBtn.style.color = '#FFFFFF';
                    logMessage('✅ Report building complete - Next button enabled', 'SUCCESS');
                }
            }
            
            const statusText = document.getElementById('statusText');
            if (statusText) {
                if (stageMessage) {
                    statusText.textContent = `${status.charAt(0).toUpperCase() + status.slice(1)}: ${stageMessage}`;
                } else {
                    statusText.textContent = `Status: ${status.charAt(0).toUpperCase() + status.slice(1)}`;
                }
            }
            
            if (status === 'completed') {
                logMessage('✅ Processing completed!', 'SUCCESS');
                if (statusText) statusText.textContent = '✅ Processing Complete';
                
                // Automatically fetch and display the report
                try {
                    logMessage('Fetching report...', 'INFO');
                    const reportResponse = await fetch(`${appState.apiUrl}/api/v1/reports/${appState.jobId}`);
                    
                    if (reportResponse.ok) {
                        appState.report = await reportResponse.json();
                        // Only display content for the currently active tab
                        const activeTab = document.querySelector('.tab-btn.active');
                        if (activeTab) {
                            const tabName = activeTab.textContent.trim().toLowerCase();
                            if (tabName.includes('summary')) {
                                displaySummary(appState.report);
                            } else if (tabName.includes('full')) {
                                displayFullReport(appState.report);
                            } else if (tabName.includes('visualization')) {
                                generateVisualizations();
                            } else if (tabName.includes('log')) {
                                displayLogs();
                            }
                        } else {
                            // Default to summary if no tab is active
                            displaySummary(appState.report);
                        }
                        appState.vizGenerated = false;
                        
                        logMessage('✅ Report fetched and displayed', 'SUCCESS');
                        updateNavigationButtons();
                        
                        // If we're on step 2, automatically move to step 3
                        if (appState.currentStep === 2) {
                            setTimeout(() => {
                                showStep(3);
                            }, 500);
                        }
                    } else {
                        const errorData = await reportResponse.json();
                        logMessage(`❌ Failed to fetch report: ${errorData.detail || reportResponse.statusText}`, 'ERROR');
                    }
                } catch (error) {
                    logMessage(`❌ Error fetching report: ${error.message}`, 'ERROR');
                }
                return;
            } else if (status === 'failed') {
                const error = data.error || 'Unknown error';
                logMessage(`❌ Processing failed: ${error}`, 'ERROR');
                if (statusText) statusText.textContent = '❌ Processing failed';
                showAlert('Error', `Processing failed:\n${error}`, 'error');
                return;
            }
            
            setTimeout(checkLoop, status === 'processing' ? 2000 : 5000);
        } catch (error) {
            logMessage(`❌ Status check error: ${error.message}`, 'ERROR');
            setTimeout(checkLoop, 2000);
        }
    };
    
    checkLoop();
}

async function checkStatus() {
    if (!appState.jobId) {
        showAlert('Warning', 'No job ID. Please upload a file first.', 'warning');
        return;
    }
    
    logMessage(`Checking status for job: ${appState.jobId}`, 'INFO');
    const processingProgressLabel = document.getElementById('processingProgressLabel');
    if (processingProgressLabel) processingProgressLabel.textContent = 'Checking status...';
    
    try {
        const response = await fetch(`${appState.apiUrl}/api/v1/status/${appState.jobId}`);
        const data = await response.json();
        const status = data.status;
        const statusText = document.getElementById('statusText');
        if (statusText) statusText.textContent = `Status: ${status.charAt(0).toUpperCase() + status.slice(1)}`;
        showAlert('Status', JSON.stringify(data, null, 2), 'info');
    } catch (error) {
        logMessage(`❌ Error: ${error.message}`, 'ERROR');
        showAlert('Error', `Status check error: ${error.message}`, 'error');
    } finally {
        if (processingProgressLabel) processingProgressLabel.textContent = '';
    }
}

async function downloadReport() {
    if (!appState.jobId) {
        showAlert('Warning', 'No job ID. Please upload a file first.', 'warning');
        return;
    }
    
    logMessage(`Downloading report for job: ${appState.jobId}`, 'INFO');
    const processingProgressLabel = document.getElementById('processingProgressLabel');
    if (processingProgressLabel) processingProgressLabel.textContent = 'Downloading report...';
    
    try {
        // First check the job status
        const statusResponse = await fetch(`${appState.apiUrl}/api/v1/status/${appState.jobId}`);
        const statusData = await statusResponse.json();
        
        if (statusData.status !== 'completed') {
            const status = statusData.status || 'unknown';
            logMessage(`⚠️ Job not completed yet. Status: ${status}`, 'WARNING');
            showAlert('Warning', `Job is still ${status}. Please wait for processing to complete.\n\nYou can click "Check Status" to monitor progress.`, 'warning');
            if (processingProgressLabel) processingProgressLabel.textContent = '';
            return;
        }
        
        // Job is completed, fetch the report
        const response = await fetch(`${appState.apiUrl}/api/v1/reports/${appState.jobId}`);
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
        }
        
        appState.report = await response.json();
        
        // Only display content for the currently active tab
        const activeTab = document.querySelector('.tab-btn.active');
        if (activeTab) {
            const tabName = activeTab.textContent.trim().toLowerCase();
            if (tabName.includes('summary')) {
                displaySummary(appState.report);
            } else if (tabName.includes('full')) {
                displayFullReport(appState.report);
            } else if (tabName.includes('visualization')) {
                generateVisualizations();
            } else if (tabName.includes('log')) {
                displayLogs();
            }
        } else {
            // Default to summary if no tab is active
            displaySummary(appState.report);
        }
        
        appState.vizGenerated = false;
        
        logMessage('✅ Report downloaded', 'SUCCESS');
        const statusText = document.getElementById('statusText');
        if (statusText) statusText.textContent = '✅ Report downloaded';
        
        showAlert('Success', 'Report downloaded successfully!', 'success');
        updateNavigationButtons();
    } catch (error) {
        logMessage(`❌ Error: ${error.message}`, 'ERROR');
        showAlert('Error', `Download error: ${error.message}`, 'error');
    } finally {
        if (processingProgressLabel) processingProgressLabel.textContent = '';
    }
}

// Report Display - matches GUI exactly
function displaySummary(report) {
    const left = document.getElementById('summaryLeft');
    const right = document.getElementById('summaryRight');
    
    left.innerHTML = formatSummaryLeft(report);
    right.innerHTML = formatSummaryRight(report);
}

function formatSummaryLeft(report) {
    const overall = report.overall_summary || report.summary || {};
    const aiProb = overall.overall_ai_probability || overall.ai_probability || 0;
    const humanProb = 1.0 - aiProb;
    const riskLevel = overall.overall_risk || overall.risk_level || 'N/A';
    const verification = overall.overall_verification_status || 'N/A';
    
    return `
        <div class="section-title">📋 File Information</div>
        <div style="color: #333333; margin: 10px 0;">${'─'.repeat(50)}</div>
        <div>File ID: ${report.file_id || 'N/A'}</div>
        <div>Timestamp: ${report.created_at || report.timestamp || 'N/A'}</div>
        <br>
        <div class="section-title">📊 Analysis Summary</div>
        <div style="color: #333333; margin: 10px 0;">${'─'.repeat(50)}</div>
        <div>Total Segments Analyzed: ${overall.total_segments || 0}</div>
        <div>Risk Level: <span style="color: ${getRiskColor(riskLevel)}">${riskLevel.toUpperCase()}</span></div>
        <div>Verification Status: <span style="color: ${getStatusColor(verification)}">${verification.toUpperCase()}</span></div>
        <div>AI Probability: <span style="color: ${aiProb > 0.5 ? '#F59E0B' : '#10B981'}">${(aiProb * 100).toFixed(1)}%</span></div>
        <div>Human Probability: <span style="color: ${humanProb > 0.5 ? '#10B981' : '#F59E0B'}">${(humanProb * 100).toFixed(1)}%</span></div>
        <div>Recommended Action: <span style="color: #6366F1">${(overall.recommended_action || 'N/A').replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</span></div>
        <div>Segments Flagged as AI: ${overall.segments_flagged_ai || 0}</div>
        <div>Segments with Matches: ${overall.segments_with_matches || 0}</div>
    `;
}

function formatSummaryRight(report) {
    const overall = report.overall_summary || report.summary || {};
    const aiProb = overall.overall_ai_probability || overall.ai_probability || 0;
    const matches = overall.segments_with_matches || 0;
    
    let html = `
        <div class="section-title">🔍 Key Findings</div>
        <div style="color: #333333; margin: 10px 0;">${'─'.repeat(50)}</div>
    `;
    
    if (aiProb > 0.7) {
        html += `<div style="color: #F59E0B; font-weight: bold; margin-bottom: 5px;">⚠️  HIGH AI PROBABILITY DETECTED</div>`;
        html += `<div style="margin-bottom: 10px;">   This track shows strong indicators of AI-generated content.</div><br>`;
    } else if (aiProb > 0.5) {
        html += `<div style="color: #F59E0B; font-weight: bold; margin-bottom: 5px;">⚡ MODERATE AI PROBABILITY</div>`;
        html += `<div style="margin-bottom: 10px;">   This track may contain AI-generated elements.</div><br>`;
    } else {
        html += `<div style="color: #10B981; font-weight: bold; margin-bottom: 5px;">✅ LIKELY HUMAN-CREATED CONTENT</div>`;
        html += `<div style="margin-bottom: 10px;">   This track appears to be primarily human-created.</div><br>`;
    }
    
    if (matches > 0) {
        html += `<div>🎯 ${matches} segments matched known sources in database</div>`;
        html += `<div style="margin-bottom: 10px;">   Similar audio patterns were found in the reference library.</div><br>`;
    } else {
        html += `<div>🔍 No matches found in reference database</div>`;
        html += `<div style="margin-bottom: 10px;">   This track appears to be unique.</div><br>`;
    }
    
    // Stems Analysis
    const stemsSummary = report.stems_summary || [];
    if (stemsSummary.length > 0) {
        html += `<div class="section-title">🎼 Stems Analysis</div>`;
        html += `<div style="color: #333333; margin: 10px 0;">${'─'.repeat(50)}</div>`;
        stemsSummary.forEach(stem => {
            html += `<div style="font-weight: bold; margin-top: 5px;">${(stem.stem_type || 'unknown').charAt(0).toUpperCase() + (stem.stem_type || 'unknown').slice(1)}:</div>`;
            html += `<div>  • AI Score: ${((stem.aggregated_ai_score || 0) * 100).toFixed(1)}%</div>`;
            html += `<div>  • Matches: ${stem.matches_found || 0}</div>`;
            html += `<div style="margin-bottom: 5px;">  • Risk: ${(stem.risk_flags || 'unknown').toUpperCase()}</div>`;
        });
    }
    
    return html;
}

function displayFullReport(report) {
    // Don't display error messages as reports
    if (report && report.detail && !report.overall_summary && !report.summary) {
        // This looks like an error response, not a report
        document.getElementById('fullReport').textContent = `Error: ${report.detail}\n\nPlease wait for processing to complete or check the job status.`;
        return;
    }
    
    const formatted = JSON.stringify(report, null, 2);
    document.getElementById('fullReport').textContent = formatted;
}

function getRiskColor(risk) {
    const riskLower = (risk || '').toLowerCase();
    if (riskLower === 'low') return '#10B981';
    if (riskLower === 'medium') return '#F59E0B';
    if (riskLower === 'high') return '#EF4444';
    return '#B0B0B0';
}

function getStatusColor(status) {
    const statusLower = (status || '').toLowerCase();
    if (statusLower === 'verified') return '#10B981';
    if (statusLower === 'suspicious') return '#F59E0B';
    if (statusLower === 'high_risk') return '#EF4444';
    return '#B0B0B0';
}

// Tabs
function switchTab(tabName) {
    // Remove active class from all tabs and content
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    
    // Activate the clicked tab button
    if (event && event.target) {
        event.target.classList.add('active');
    } else {
        // Fallback: find button by text content
        document.querySelectorAll('.tab-btn').forEach(btn => {
            const btnText = btn.textContent.trim().toLowerCase();
            if ((tabName === 'summary' && btnText.includes('summary')) ||
                (tabName === 'full' && btnText.includes('full')) ||
                (tabName === 'visualizations' && btnText.includes('visualization')) ||
                (tabName === 'logs' && btnText.includes('log'))) {
                btn.classList.add('active');
            }
        });
    }
    
    // Show only the selected tab content
    const tabContentId = `tab${tabName.charAt(0).toUpperCase() + tabName.slice(1)}`;
    const tabContent = document.getElementById(tabContentId);
    if (tabContent) {
        tabContent.classList.add('active');
    }
    
    // Display content based on the selected tab (only for the active tab)
    if (appState.report) {
        if (tabName === 'summary') {
            displaySummary(appState.report);
            // Clear other tabs
            document.getElementById('fullReport').textContent = '';
            document.getElementById('vizContainer').innerHTML = '';
        } else if (tabName === 'full') {
            displayFullReport(appState.report);
            // Clear other tabs
            document.getElementById('summaryLeft').innerHTML = '';
            document.getElementById('summaryRight').innerHTML = '';
            document.getElementById('vizContainer').innerHTML = '';
        } else if (tabName === 'visualizations') {
            generateVisualizations();
            // Clear other tabs
            document.getElementById('summaryLeft').innerHTML = '';
            document.getElementById('summaryRight').innerHTML = '';
            document.getElementById('fullReport').textContent = '';
        } else if (tabName === 'logs') {
            displayLogs();
            // Clear other tabs
            document.getElementById('summaryLeft').innerHTML = '';
            document.getElementById('summaryRight').innerHTML = '';
            document.getElementById('fullReport').textContent = '';
            document.getElementById('vizContainer').innerHTML = '';
        }
    }
}

// Visualizations - matches GUI matplotlib charts
function generateVisualizations() {
    if (!appState.report) return;
    
    const segments = appState.report.segments || [];
    const overall = appState.report.overall_summary || {};
    
    if (!segments.length) return;
    
    // Extract data
    const segmentTimes = [];
    const aiProbs = [];
    const fusionScores = [];
    const riskFlags = [];
    const stemTypes = [];
    
    segments.forEach(seg => {
        const start = seg.start || 0;
        const end = seg.end || 0;
        segmentTimes.push((start + end) / 2);
        
        const stems = seg.stems || [];
        if (stems.length > 0) {
            const stem = stems[0];
            const classifier = stem.classifier || {};
            aiProbs.push(classifier.ai_probability || 0.0);
            fusionScores.push(stem.fusion_score || 0.0);
            riskFlags.push(seg.risk_flag || 'low');
            stemTypes.push(stem.stem_type || 'unknown');
        } else {
            aiProbs.push(seg.ai_probability || 0.0);
            fusionScores.push(0.0);
            riskFlags.push(seg.risk_flag || 'low');
            stemTypes.push('unknown');
        }
    });
    
    const container = document.getElementById('vizContainer');
    if (!container) {
        console.error('Visualization container not found');
        return;
    }
    
    container.innerHTML = '';
    container.style.display = 'grid';
    container.style.gridTemplateColumns = '1fr 1fr';
    container.style.gap = '15px';
    container.style.padding = '20px';
    
    // Timeline Chart
    const timelineData = [{
        x: segmentTimes,
        y: aiProbs,
        type: 'scatter',
        mode: 'lines+markers',
        name: 'AI Probability',
        line: { color: '#F59E0B', width: 1.5 },
        marker: { size: 3 }
    }, {
        x: segmentTimes,
        y: fusionScores,
        type: 'scatter',
        mode: 'lines+markers',
        name: 'Fusion Score',
        line: { color: '#6366F1', width: 1.5 },
        marker: { size: 3, symbol: 'square' }
    }];
    
    const timelineLayout = {
        title: {
            text: 'AI Probability & Fusion Score Timeline',
            font: { color: '#FFFFFF', size: 14, family: 'Segoe UI' }
        },
        plot_bgcolor: '#1A1A1A',
        paper_bgcolor: '#1A1A1A',
        font: { color: '#B0B0B0', size: 11, family: 'Segoe UI' },
        xaxis: { 
            title: { text: 'Time (seconds)', font: { size: 12, color: '#FFFFFF' } },
            color: '#B0B0B0',
            gridcolor: '#333333',
            linecolor: '#666666',
            zerolinecolor: '#333333'
        },
        yaxis: { 
            title: { text: 'Probability', font: { size: 12, color: '#FFFFFF' } },
            range: [0, 1], 
            color: '#B0B0B0',
            gridcolor: '#333333',
            linecolor: '#666666',
            zerolinecolor: '#333333'
        },
        shapes: [{
            type: 'line',
            x0: 0,
            x1: 1,
            xref: 'paper',
            y0: 0.5,
            y1: 0.5,
            line: { color: '#EF4444', width: 2, dash: 'dash' }
        }],
        legend: { 
            bgcolor: '#1A1A1A', 
            bordercolor: '#6366F1', 
            borderwidth: 1,
            font: { color: '#FFFFFF', size: 11 },
            x: 1.02,
            y: 1
        },
        margin: { l: 60, r: 20, t: 60, b: 60 },
        autosize: true
    };
    
    const timelineDiv = document.createElement('div');
    timelineDiv.className = 'viz-chart';
    timelineDiv.style.width = '100%';
    timelineDiv.style.height = '400px';
    container.appendChild(timelineDiv);
    Plotly.newPlot(timelineDiv, timelineData, timelineLayout, { 
        displayModeBar: false,
        responsive: true,
        autosizable: true
    });
    
    // Risk Distribution Chart
    const riskCounts = { low: 0, medium: 0, high: 0 };
    riskFlags.forEach(risk => {
        riskCounts[risk.toLowerCase()] = (riskCounts[risk.toLowerCase()] || 0) + 1;
    });
    
    const riskLabels = [];
    const riskValues = [];
    const riskColors = [];
    
    Object.entries(riskCounts).forEach(([risk, count]) => {
        if (count > 0) {
            riskLabels.push(risk.toUpperCase());
            riskValues.push(count);
            if (risk === 'low') riskColors.push('#10B981');
            else if (risk === 'medium') riskColors.push('#F59E0B');
            else riskColors.push('#EF4444');
        }
    });
    
    if (riskValues.length > 0) {
        const riskData = [{
            labels: riskLabels,
            values: riskValues,
            type: 'pie',
            marker: { colors: riskColors },
            textfont: { color: '#FFFFFF', size: 10, family: 'Segoe UI' }
        }];
        
        const riskLayout = {
            title: {
                text: 'Risk Level Distribution',
                font: { color: '#FFFFFF', size: 14, family: 'Segoe UI' }
            },
            plot_bgcolor: '#1A1A1A',
            paper_bgcolor: '#1A1A1A',
            font: { color: '#FFFFFF', size: 12, family: 'Segoe UI' },
            margin: { l: 20, r: 20, t: 60, b: 20 },
            autosize: true
        };
        
        const riskDiv = document.createElement('div');
        riskDiv.className = 'viz-chart';
        riskDiv.style.width = '100%';
        riskDiv.style.height = '400px';
        container.appendChild(riskDiv);
        Plotly.newPlot(riskDiv, riskData, riskLayout, { 
            displayModeBar: false,
            responsive: true,
            autosizable: true
        });
    }
    
    // Stems Analysis Chart
    const stemData = {};
    stemTypes.forEach((stem, idx) => {
        if (!stemData[stem]) stemData[stem] = [];
        stemData[stem].push(aiProbs[idx]);
    });
    
    const stemAvgs = {};
    Object.entries(stemData).forEach(([stem, probs]) => {
        stemAvgs[stem] = probs.reduce((a, b) => a + b, 0) / probs.length;
    });
    
    if (Object.keys(stemAvgs).length > 0) {
        const stems = Object.keys(stemAvgs);
        const avgs = Object.values(stemAvgs);
        const colors = avgs.map(avg => avg > 0.5 ? '#F59E0B' : '#10B981');
        
        const stemsData = [{
            x: stems,
            y: avgs,
            type: 'bar',
            marker: { color: colors, line: { color: '#333333', width: 1.5 } },
            text: avgs.map(a => a.toFixed(2)),
            textposition: 'outside'
        }];
        
        const stemsLayout = {
            title: {
                text: 'Average AI Probability by Stem Type',
                font: { color: '#FFFFFF', size: 14, family: 'Segoe UI' }
            },
            plot_bgcolor: '#1A1A1A',
            paper_bgcolor: '#1A1A1A',
            font: { color: '#B0B0B0', size: 11, family: 'Segoe UI' },
            xaxis: { 
                title: { text: 'Stem Type', font: { size: 12, color: '#FFFFFF' } },
                color: '#B0B0B0',
                gridcolor: '#333333',
                linecolor: '#666666'
            },
            yaxis: { 
                title: { text: 'Average AI Probability', font: { size: 12, color: '#FFFFFF' } },
                range: [0, 1], 
                color: '#B0B0B0',
                gridcolor: '#333333',
                linecolor: '#666666',
                zerolinecolor: '#333333'
            },
            shapes: [{
                type: 'line',
                x0: 0,
                x1: 1,
                xref: 'paper',
                y0: 0.5,
                y1: 0.5,
                line: { color: '#EF4444', width: 2, dash: 'dash' }
            }],
            margin: { l: 60, r: 20, t: 60, b: 60 },
            autosize: true
        };
        
        const stemsDiv = document.createElement('div');
        stemsDiv.className = 'viz-chart';
        stemsDiv.style.width = '100%';
        stemsDiv.style.height = '400px';
        container.appendChild(stemsDiv);
        Plotly.newPlot(stemsDiv, stemsData, stemsLayout, { 
            displayModeBar: false,
            responsive: true,
            autosizable: true
        });
    }
    
    // Summary Pie Chart
    const overallAiProb = overall.overall_ai_probability || 0.0;
    const humanProb = 1.0 - overallAiProb;
    
    const summaryData = [{
        labels: ['Human', 'AI'],
        values: [humanProb, overallAiProb],
        type: 'pie',
        marker: { colors: ['#10B981', '#F59E0B'], line: { color: '#1A1A1A', width: 2 } },
        textfont: { color: '#FFFFFF', size: 12, family: 'Segoe UI' },
        textposition: 'outside',
        textinfo: 'label+percent',
        hovertemplate: '<b>%{label}</b><br>Probability: %{percent}<extra></extra>'
    }];
    
    const summaryLayout = {
        title: {
            text: 'Overall Content Classification',
            font: { color: '#FFFFFF', size: 14, family: 'Segoe UI' }
        },
        plot_bgcolor: '#1A1A1A',
        paper_bgcolor: '#1A1A1A',
        font: { color: '#FFFFFF', size: 12, family: 'Segoe UI' },
        margin: { l: 20, r: 20, t: 60, b: 20 },
        autosize: true,
        showlegend: true,
        legend: {
            bgcolor: '#1A1A1A',
            bordercolor: '#6366F1',
            borderwidth: 1,
            font: { color: '#FFFFFF', size: 11 },
            x: 1.02,
            y: 1
        }
    };
    
    const summaryDiv = document.createElement('div');
    summaryDiv.className = 'viz-chart';
    summaryDiv.style.width = '100%';
    summaryDiv.style.height = '400px';
    container.appendChild(summaryDiv);
    Plotly.newPlot(summaryDiv, summaryData, summaryLayout, { 
        displayModeBar: false,
        responsive: true,
        autosizable: true
    });
    
    appState.vizGenerated = true;
}

// Logger - matches GUI logger
function logMessage(message, level = 'INFO') {
    const timestamp = new Date().toLocaleTimeString();
    const colorMap = {
        'INFO': '#60A5FA',
        'SUCCESS': '#10B981',
        'WARNING': '#F59E0B',
        'ERROR': '#EF4444'
    };
    
    const logDisplay = document.getElementById('logDisplay');
    if (!logDisplay) return;
    
    const color = colorMap[level] || '#B0B0B0';
    
    logDisplay.textContent += `[${timestamp}] [${level}] ${message}\n`;
    logDisplay.scrollTop = logDisplay.scrollHeight;
    
    appState.logs.push({ timestamp, level, message });
}

// Display logs in the logs tab
function displayLogs() {
    const logDisplay = document.getElementById('logDisplay');
    if (!logDisplay) return;
    
    // Clear and rebuild log display from appState.logs
    logDisplay.textContent = '';
    appState.logs.forEach(log => {
        logDisplay.textContent += `[${log.timestamp}] [${log.level}] ${log.message}\n`;
    });
    
    // Scroll to bottom
    logDisplay.scrollTop = logDisplay.scrollHeight;
}

// Alert Dialog - matches GUI exactly
function showAlert(title, message, type = 'info') {
    const overlay = document.getElementById('alertOverlay');
    const alertTitle = document.getElementById('alertTitle');
    const alertMessage = document.getElementById('alertMessage');
    const alertIcon = document.getElementById('alertIcon');
    
    alertTitle.textContent = title;
    alertMessage.textContent = message;
    
    const icons = {
        success: { icon: '✓', color: '#10B981' },
        warning: { icon: '⚠', color: '#F59E0B' },
        error: { icon: '✕', color: '#EF4444' },
        info: { icon: 'ℹ', color: '#6366F1' }
    };
    
    const config = icons[type] || icons.info;
    alertIcon.textContent = config.icon;
    alertIcon.style.color = config.color;
    
    overlay.style.display = 'flex';
    
    // Close on Escape key
    const closeOnEscape = (e) => {
        if (e.key === 'Escape') {
            closeAlert();
            document.removeEventListener('keydown', closeOnEscape);
        }
    };
    document.addEventListener('keydown', closeOnEscape);
}

function closeAlert() {
    document.getElementById('alertOverlay').style.display = 'none';
}

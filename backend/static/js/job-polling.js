// backend/static/js/job-polling.js

// Job Polling - Poll for job status updates
(function() {
    'use strict';

    const POLL_INTERVAL = 5000; // 5 seconds
    const MAX_POLL_TIME = 600000; // 10 minutes

    function pollJobStatus(jobId, onUpdate, onComplete, onError) {
        const startTime = Date.now();
        let pollTimer;

        function poll() {
            fetch(`/api/jobs/${jobId}/status/`)
                .then(response => response.json())
                .then(data => {
                    if (onUpdate) onUpdate(data);

                    if (data.status === 'completed') {
                        clearInterval(pollTimer);
                        if (onComplete) onComplete(data);
                    } else if (data.status === 'failed') {
                        clearInterval(pollTimer);
                        if (onError) onError(data.error_message || 'Processing failed');
                    } else if (Date.now() - startTime > MAX_POLL_TIME) {
                        clearInterval(pollTimer);
                        if (onError) onError('Processing timed out. Please refresh.');
                    }
                })
                .catch(error => {
                    clearInterval(pollTimer);
                    if (onError) onError('Connection error: ' + error.message);
                });
        }

        // Initial poll
        poll();
        // Start polling
        pollTimer = setInterval(poll, POLL_INTERVAL);
    }

    // Expose to global scope
    window.pollJobStatus = pollJobStatus;

    // Auto-poll if on job detail page
    document.addEventListener('DOMContentLoaded', function() {
        const progressBar = document.querySelector('[data-job-id]');
        if (progressBar) {
            const jobId = progressBar.dataset.jobId;
            const statusEl = document.getElementById('job-status');
            const progressEl = document.getElementById('job-progress');

            pollJobStatus(
                jobId,
                function(data) {
                    // Update progress
                    if (progressEl) {
                        progressEl.style.width = data.progress + '%';
                        progressEl.textContent = data.progress + '%';
                    }
                    if (statusEl) {
                        statusEl.textContent = data.status_display;
                    }
                },
                function(data) {
                    // Job complete - reload page
                    window.location.reload();
                },
                function(error) {
                    if (statusEl) {
                        statusEl.textContent = 'Failed';
                        statusEl.className = 'px-2 py-1 rounded text-sm bg-red-100 text-red-800';
                    }
                }
            );
        }
    });
})();
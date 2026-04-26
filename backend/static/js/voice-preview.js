
// Voice Preview - Play voice samples for dubbing
(function() {
    'use strict';

    const VOICE_SAMPLES = {
        'luganda_male_1': '/static/audio/voices/luganda_male_1_sample.mp3',
        'luganda_female_1': '/static/audio/voices/luganda_female_1_sample.mp3',
        'english_male_1': '/static/audio/voices/english_male_1_sample.mp3',
        'english_female_1': '/static/audio/voices/english_female_1_sample.mp3',
    };

    let currentAudio = null;

    function previewVoice(voiceKey) {
        // Stop any currently playing preview
        if (currentAudio) {
            currentAudio.pause();
            currentAudio = null;
        }

        const sampleUrl = VOICE_SAMPLES[voiceKey];
        if (!sampleUrl) {
            showToast('No preview available for this voice', 'warning');
            return;
        }

        const audio = new Audio(sampleUrl);
        currentAudio = audio;

        audio.onloadeddata = function() {
            audio.play();
            showToast('Playing voice preview...', 'info');
        };

        audio.onerror = function() {
            showToast('Voice preview not available yet. Samples coming soon.', 'info');
            currentAudio = null;
        };

        audio.onended = function() {
            currentAudio = null;
        };
    }

    function stopPreview() {
        if (currentAudio) {
            currentAudio.pause();
            currentAudio = null;
        }
    }

    function showToast(message, type) {
        // Simple toast notification
        const toast = document.createElement('div');
        toast.className = 'fixed bottom-4 right-4 px-4 py-2 rounded-lg text-white text-sm z-50 ' +
            (type === 'warning' ? 'bg-yellow-500' : 'bg-blue-500');
        toast.textContent = message;
        document.body.appendChild(toast);

        setTimeout(function() {
            toast.remove();
        }, 3000);
    }

    // Expose to global scope
    window.previewVoice = previewVoice;
    window.stopPreview = stopPreview;

    // Attach event listeners to voice select dropdowns
    document.addEventListener('DOMContentLoaded', function() {
        const voiceSelects = document.querySelectorAll('select[name="voice_model"]');
        voiceSelects.forEach(function(select) {
            // Find or create preview button next to select
            const previewBtn = select.parentElement.querySelector('.voice-preview-btn');
            if (!previewBtn) {
                const btn = document.createElement('button');
                btn.type = 'button';
                btn.className = 'voice-preview-btn text-sm text-blue-600 hover:underline mt-1 ml-2';
                btn.textContent = '▶ Preview';
                btn.addEventListener('click', function(e) {
                    e.preventDefault();
                    const voiceKey = select.value;
                    if (voiceKey) {
                        previewVoice(voiceKey);
                    } else {
                        showToast('Please select a voice first', 'warning');
                    }
                });
                select.parentElement.appendChild(btn);

                // Stop button
                const stopBtn = document.createElement('button');
                stopBtn.type = 'button';
                stopBtn.className = 'text-sm text-red-600 hover:underline mt-1 ml-2';
                stopBtn.textContent = '■ Stop';
                stopBtn.addEventListener('click', function(e) {
                    e.preventDefault();
                    stopPreview();
                });
                select.parentElement.appendChild(stopBtn);
            }
        });
    });
})();

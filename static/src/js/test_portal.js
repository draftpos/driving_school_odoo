// Test Portal JavaScript - Handles AJAX save + navigation
(function() {
    'use strict';

    function getForm() {
        return document.querySelector('#test_question_form');
    }

    function getSurveyId() {
        var form = getForm();
        if (!form) return null;
        var m = form.action.match(/\/test\/take\/(\d+)\/answer/);
        return m ? m[1] : null;
    }

    // Submit form via AJAX and navigate to targetUrl on success
    function saveAndGo(targetUrl) {
        var form = getForm();
        if (!form) {
            window.location.href = targetUrl;
            return;
        }

        var formData = new FormData(form);
        var csrfInput = form.querySelector('input[name="csrf_token"]');
        if (!csrfInput) {
            window.location.href = targetUrl;
            return;
        }

        fetch(form.action, {
            method: 'POST',
            body: formData,
            credentials: 'same-origin',
        })
        .then(function() {
            window.location.href = targetUrl;
        })
        .catch(function() {
            // Even on error, navigate so user is not stuck
            window.location.href = targetUrl;
        });
    }

    function initAll() {
        var surveyId = getSurveyId();
        if (!surveyId) return;

        // --- NEXT button ---
        var nextBtns = document.querySelectorAll('.test-next-btn');
        Array.prototype.forEach.call(nextBtns, function(btn) {
            btn.addEventListener('click', function(e) {
                e.preventDefault();
                var form = getForm();
                var redirectQInput = form ? form.querySelector('input[name="redirect_q"]') : null;
                var nextQ = redirectQInput ? parseInt(redirectQInput.value, 10) : 1;
                var url = '/test/take/' + surveyId + '/question/' + nextQ;
                saveAndGo(url);
            });
        });

        // --- PREV button is a plain <a> link - no JS needed ---

        // --- Question number links: save in background before navigating ---
        var numLinks = document.querySelectorAll('.test-navigator-btn:not(.test-next-btn):not(.test-prev-btn)');
        Array.prototype.forEach.call(numLinks, function(link) {
            if (link.tagName !== 'A') return;
            link.addEventListener('click', function(e) {
                // Don't block navigation - just fire-and-forget save
                var form = getForm();
                if (!form) return;
                var fd = new FormData(form);
                fetch(form.action, { method: 'POST', body: fd, credentials: 'same-origin' })
                    .catch(function() {});
            });
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initAll);
    } else {
        initAll();
    }
})();

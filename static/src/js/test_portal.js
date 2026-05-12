// Test Portal JavaScript - Handles instant navigation for all buttons
(function() {
    'use strict';

    // Save answer via AJAX and navigate to next question
    function saveAnswerAndNavigate(form, targetUrl, buttonText) {
        // Get the button that was clicked
        var nextBtn = form.querySelector('.test-next-btn');
        var prevBtn = form.querySelector('.test-prev-btn');
        var finalBtn = form.querySelector('.test-final-btn');
        var activeBtn = nextBtn || prevBtn || finalBtn;
        
        if (activeBtn) {
            activeBtn.disabled = true;
            activeBtn.textContent = buttonText || 'Saving...';
            activeBtn.classList.add('saving');
        }

        // Collect form data
        var formData = new FormData(form);
        
        // Get CSRF token
        var csrfToken = form.querySelector('input[name="csrf_token"]').value;
        
        // Determine the action URL
        var actionUrl = form.action;
        
        // Use fetch API to submit the form data asynchronously
        fetch(actionUrl, {
            method: 'POST',
            body: formData,
            credentials: 'same-origin',
            headers: {
                'X-CSRF-Token': csrfToken,
                'Content-Type': 'application/x-www-form-urlencoded',
            }
        })
        .then(function(response) {
            // Only redirect after successful save
            if (response.ok || response.status === 200 || response.redirected) {
                window.location.href = targetUrl;
            } else {
                throw new Error('Save failed');
            }
        })
        .catch(function(error) {
            console.error('Error saving answer:', error);
            if (activeBtn) {
                activeBtn.disabled = false;
                if (nextBtn) activeBtn.textContent = 'Next';
                else if (prevBtn) activeBtn.textContent = 'Previous';
                else if (finalBtn) activeBtn.textContent = 'Finalise';
            }
        });
    }

    // Handle button click with AJAX save
    function handleButtonClick(form, targetUrl, buttonText) {
        if (!form) return;
        
        // Get the button that was clicked
        var nextBtn = form.querySelector('.test-next-btn');
        var prevBtn = form.querySelector('.test-prev-btn');
        var finalBtn = form.querySelector('.test-final-btn');
        var activeBtn = nextBtn || prevBtn || finalBtn;
        
        if (activeBtn) {
            activeBtn.disabled = true;
            activeBtn.textContent = 'Saving...';
        }

        // Collect form data
        var formData = new FormData(form);
        
        // Get CSRF token
        var csrfToken = form.querySelector('input[name="csrf_token"]').value;
        
        // Determine the action URL
        var actionUrl = form.action;
        
        // Use fetch API to submit the form data asynchronously
        fetch(actionUrl, {
            method: 'POST',
            body: formData,
            credentials: 'same-origin',
            headers: {
                'X-CSRF-Token': csrfToken,
                'Content-Type': 'application/x-www-form-urlencoded',
            }
        })
        .then(function(response) {
            if (response.ok || response.status === 200 || response.redirected) {
                window.location.href = targetUrl;
            } else {
                throw new Error('Save failed');
            }
        })
        .catch(function(error) {
            console.error('Error saving answer:', error);
            if (activeBtn) {
                activeBtn.disabled = false;
                if (nextBtn) activeBtn.textContent = 'Next';
                else if (prevBtn) activeBtn.textContent = 'Previous';
                else if (finalBtn) activeBtn.textContent = 'Finalise';
            }
        });
    }

    // Save answer in background (no navigation)
    function saveAnswerBackground() {
        var form = document.querySelector('.test-question-body form');
        if (!form) return;

        // Check if there's an answer to save
        var questionId = form.querySelector('input[name="question_id"]');
        if (!questionId) return;

        // Get CSRF token
        var csrfToken = form.querySelector('input[name="csrf_token"]');
        if (!csrfToken) return;
        
        var actionUrl = form.action;
        var formData = new FormData(form);
        
        fetch(actionUrl, {
            method: 'POST',
            body: formData,
            credentials: 'same-origin',
            headers: {
                'X-CSRF-Token': csrfToken.value,
            }
        })
        .catch(function(error) {
            console.log('Background save error (non-critical):', error);
        });
    }

    // Initialize Next button
    function initNextButton() {
        var form = document.querySelector('.test-question-body form');
        if (!form) return;

        var nextBtn = form.querySelector('.test-next-btn');
        if (!nextBtn) return;

        var redirectQInput = form.querySelector('input[name="redirect_q"]');
        if (!redirectQInput) return;

        var nextQuestionNum = parseInt(redirectQInput.value, 10);
        var actionMatch = form.action.match(/\/test\/take\/(\d+)\/answer/);
        if (!actionMatch) return;
        
        var surveyId = actionMatch[1];
        var nextQuestionUrl = '/test/take/' + surveyId + '/question/' + nextQuestionNum;

        nextBtn.addEventListener('click', function(e) {
            e.preventDefault();
            saveAnswerAndNavigate(form, nextQuestionUrl, 'Next');
        });
    }

    // Initialize Previous button
    function initPrevButton() {
        var form = document.querySelector('.test-question-body form');
        if (!form) return;

        var prevBtn = form.querySelector('.test-prev-btn');
        if (!prevBtn) return;

        var questionIdInput = form.querySelector('input[name="question_id"]');
        if (!questionIdInput) return;

        // Get current question number from URL
        var urlMatch = window.location.href.match(/\/question\/(\d+)/);
        if (!urlMatch) return;
        
        var currentNum = parseInt(urlMatch[1], 10);
        if (currentNum <= 1) return;
        
        var prevQuestionNum = currentNum - 1;
        var actionMatch = form.action.match(/\/test\/take\/(\d+)\/answer/);
        if (!actionMatch) return;
        
        var surveyId = actionMatch[1];
        var prevQuestionUrl = '/test/take/' + surveyId + '/question/' + prevQuestionNum;

        prevBtn.addEventListener('click', function(e) {
            e.preventDefault();
            saveAnswerAndNavigate(form, prevQuestionUrl, 'Previous');
        });
    }

    // Initialize Finalise button
    function initFinalButton() {
        var form = document.querySelector('.test-question-body form');
        if (!form) return;

        var finalBtn = form.querySelector('.test-final-btn');
        if (!finalBtn) return;

        var actionMatch = form.action.match(/\/test\/take\/(\d+)\/finish/);
        if (!actionMatch) return;
        
        var surveyId = actionMatch[1];
        var finishUrl = '/test/take/' + surveyId + '/finish';

        finalBtn.addEventListener('click', function(e) {
            e.preventDefault();
            handleButtonClick(form, finishUrl);
        });
    }

    // Initialize question navigator clicks
    function initNavigatorClicks() {
        var navButtons = document.querySelectorAll('.test-navigator-btn, .test-navigator a');
        
        navButtons.forEach(function(btn) {
            btn.addEventListener('click', function(e) {
                // Save current answer in background before navigating
                saveAnswerBackground();
                // Let normal navigation happen - it's fast enough for navigation links
            });
        });
    }

    // Initialize all buttons
    function initAll() {
        initNextButton();
        initPrevButton();
        initFinalButton();
        initNavigatorClicks();
    }

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initAll);
    } else {
        initAll();
    }
})();

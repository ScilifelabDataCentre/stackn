window.onload = (event) => {
    const email = document.getElementById('id_email');
    const choiceSelect = document.getElementById('id_affiliation');
    const request_account_field = document.getElementById('id_request_account_info');

    const domainRegex = /^(?:[A-Z0-9](?:[\.A-Z0-9-]{0,61}[A-Z0-9])?\.)*?(uu|lu|gu|su|umu|liu|ki|kth|chalmers|ltu|hhs|slu|kau|lnu|oru|miun|mau|mdu|bth|fhs|gih|hb|du|hig|hh|hkr|his|hv|ju|sh)\.se$/i;

    function changeVisibility() {
        let shouldHide = false;
        let match;

        if (email.value == '') {
            match = false;
            shouldHide = true;
        } else {
            const lst = email.value.split('@');
            const domainName = lst[lst.length - 1].toLowerCase();
            match = domainRegex.exec(domainName);
        }

        if (match) {
            const domain = match[1];
            choiceSelect.value = domain;
            shouldHide = true;
        } else {
            choiceSelect.value = 'other';  // Reset to default or empty value
        }

        if (shouldHide) {
            request_account_field.classList.add('hidden');
        } else {
            request_account_field.classList.remove('hidden');
        }
    }

    // Temporarily disable transitions
    request_account_field.style.transition = 'none';

    changeVisibility();

    // Restore transitions after a short delay
    setTimeout(() => {
        request_account_field.style.transition = '';
    }, 50);

    email.addEventListener('input', changeVisibility);
};


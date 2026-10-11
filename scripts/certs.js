const preview = document.getElementById('certs-preview');
const status = document.getElementById('certs-status');
const showAllButton = document.getElementById('show-all-certs');
const dialog = document.getElementById('certs-dialog');
const allCerts = document.getElementById('certs-all');
const searchInput = document.getElementById('certs-search');
const resultsStatus = document.getElementById('certs-results-status');

const PREVIEW_COUNT = 3;
let qualifications = [];

function createCertificateCard(certificate) {
    const card = document.createElement('article');
    card.className = 'cert-card';

    const link = document.createElement('a');
    link.href = `certs/${encodeURIComponent(certificate.file)}`;
    link.target = '_blank';
    link.rel = 'noopener noreferrer';
    link.setAttribute('aria-label', `Open ${certificate.title}`);

    if (certificate.file.toLowerCase().endsWith('.pdf')) {
        const pdfPreview = document.createElement('div');
        pdfPreview.className = 'cert-file-preview';

        const pdfIcon = document.createElement('i');
        pdfIcon.className = 'fas fa-file-pdf';
        pdfIcon.setAttribute('aria-hidden', 'true');

        const pdfLabel = document.createElement('span');
        pdfLabel.textContent = 'PDF certificate';
        pdfPreview.append(pdfIcon, pdfLabel);
        link.append(pdfPreview);
    } else {
        const image = document.createElement('img');
        image.src = `certs/${encodeURIComponent(certificate.file)}`;
        image.alt = certificate.title;
        image.loading = 'lazy';
        link.append(image);
    }

    const copy = document.createElement('div');
    copy.className = 'cert-card-copy';

    const title = document.createElement('h3');
    title.textContent = certificate.title;
    copy.append(title);

    if (certificate.issuer || certificate.date) {
        const details = document.createElement('p');
        details.textContent = [certificate.issuer, certificate.date].filter(Boolean).join(' · ');
        copy.append(details);
    }

    card.append(link, copy);
    return card;
}

function renderAllCertificates(query = '') {
    const normalizedQuery = query.trim().toLocaleLowerCase();
    const matches = qualifications.filter(certificate => {
        const searchable = [certificate.title, certificate.issuer, certificate.file]
            .filter(Boolean)
            .join(' ')
            .toLocaleLowerCase();
        return searchable.includes(normalizedQuery);
    });

    allCerts.replaceChildren(...matches.map(createCertificateCard));
    resultsStatus.textContent = matches.length
        ? `${matches.length} qualification${matches.length === 1 ? '' : 's'}`
        : 'No qualifications match your search.';
}

showAllButton.addEventListener('click', () => {
    searchInput.value = '';
    renderAllCertificates();
    dialog.showModal();
    searchInput.focus();
});

document.getElementById('close-certs').addEventListener('click', () => dialog.close());
searchInput.addEventListener('input', () => renderAllCertificates(searchInput.value));
dialog.addEventListener('click', event => {
    if (event.target === dialog) dialog.close();
});

fetch('certs/certs.json')
    .then(response => {
        if (!response.ok) throw new Error(`Could not load certificate list (${response.status}).`);
        return response.json();
    })
    .then(data => {
        if (!Array.isArray(data)) throw new Error('Certificate list must be a JSON array.');

        qualifications = data.filter(certificate =>
            certificate &&
            typeof certificate.file === 'string' &&
            typeof certificate.title === 'string' &&
            certificate.file.trim() &&
            certificate.title.trim() &&
            !certificate.file.includes('/') &&
            !certificate.file.includes('\\')
        );

        preview.replaceChildren(...qualifications.slice(0, PREVIEW_COUNT).map(createCertificateCard));
        if (qualifications.length > 0) showAllButton.hidden = false;

        status.textContent = qualifications.length
            ? `${qualifications.length} qualification${qualifications.length === 1 ? '' : 's'} listed.`
            : 'No qualifications added yet.';
    })
    .catch(error => {
        status.textContent = 'Qualifications could not be loaded.';
        console.error(error);
    });
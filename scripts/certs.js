const preview = document.getElementById('certs-preview');
const status = document.getElementById('certs-status');
const showAllButton = document.getElementById('show-all-certs');
const dialog = document.getElementById('certs-dialog');
const allCerts = document.getElementById('certs-all');
const searchInput = document.getElementById('certs-search');
const resultsStatus = document.getElementById('certs-results-status');
const viewer = document.getElementById('cert-viewer');
const viewerTitle = document.getElementById('cert-viewer-title');
const viewerStage = document.getElementById('cert-viewer-stage');
const zoomOutButton = document.getElementById('zoom-out');
const zoomResetButton = document.getElementById('zoom-reset');
const zoomInButton = document.getElementById('zoom-in');

const PREVIEW_COUNT = 3;
const MIN_ZOOM = 0.5;
const MAX_ZOOM = 3;
const ZOOM_STEP = 0.25;
let qualifications = [];
let zoom = 1;

function createCertificateCard(certificate) {
    const card = document.createElement('article');
    card.className = 'cert-card';

    const button = document.createElement('button');
    button.className = 'cert-card-button';
    button.type = 'button';
    button.setAttribute('aria-label', `View ${certificate.title}`);
    button.addEventListener('click', () => openCertificate(certificate));

    if (certificate.file.toLowerCase().endsWith('.pdf')) {
        const pdfPreview = document.createElement('div');
        pdfPreview.className = 'cert-file-preview';

        const pdfIcon = document.createElement('i');
        pdfIcon.className = 'fas fa-file-pdf';
        pdfIcon.setAttribute('aria-hidden', 'true');

        const pdfLabel = document.createElement('span');
        pdfLabel.textContent = 'PDF certificate';
        pdfPreview.append(pdfIcon, pdfLabel);
        button.append(pdfPreview);
    } else {
        const image = document.createElement('img');
        image.className = 'cert-thumbnail-image';
        image.src = `certs/${encodeURIComponent(certificate.file)}`;
        image.alt = certificate.title;
        image.loading = 'lazy';
        button.append(image);
    }

    const copy = document.createElement('div');
    copy.className = 'cert-card-copy';

    const title = document.createElement('h3');
    title.textContent = certificate.title;
    copy.append(title);

    if (certificate.issuer) {
        const details = document.createElement('p');
        details.textContent = certificate.issuer;
        copy.append(details);
    }

    card.append(button, copy);
    return card;
}

function updateZoom() {
    viewerStage.style.setProperty('--cert-zoom', zoom);
    zoomResetButton.textContent = `${Math.round(zoom * 100)}%`;
    zoomOutButton.disabled = zoom <= MIN_ZOOM;
    zoomInButton.disabled = zoom >= MAX_ZOOM;
}

function openCertificate(certificate) {
    viewerTitle.textContent = certificate.title;
    viewerStage.replaceChildren();
    zoom = 1;

    const fileUrl = `certs/${encodeURIComponent(certificate.file)}`;
    if (certificate.file.toLowerCase().endsWith('.pdf')) {
        const documentFrame = document.createElement('iframe');
        documentFrame.className = 'cert-viewer-document';
        documentFrame.src = fileUrl;
        documentFrame.title = certificate.title;
        viewerStage.append(documentFrame);
    } else {
        const image = document.createElement('img');
        image.className = 'cert-viewer-image';
        image.src = fileUrl;
        image.alt = certificate.title;
        viewerStage.append(image);
    }

    updateZoom();
    viewer.showModal();
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
document.getElementById('close-cert-viewer').addEventListener('click', () => viewer.close());
searchInput.addEventListener('input', () => renderAllCertificates(searchInput.value));
dialog.addEventListener('click', event => {
    if (event.target === dialog) dialog.close();
});
viewer.addEventListener('click', event => {
    if (event.target === viewer) viewer.close();
});
zoomOutButton.addEventListener('click', () => {
    zoom = Math.max(MIN_ZOOM, zoom - ZOOM_STEP);
    updateZoom();
});
zoomResetButton.addEventListener('click', () => {
    zoom = 1;
    updateZoom();
});
zoomInButton.addEventListener('click', () => {
    zoom = Math.min(MAX_ZOOM, zoom + ZOOM_STEP);
    updateZoom();
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
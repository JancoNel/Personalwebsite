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

const MAX_PREVIEW_COUNT = 5;
const MIN_ZOOM = 0.5;
const MAX_ZOOM = 3;
const ZOOM_STEP = 0.25;
let qualifications = [];
let zoom = 1;
let renderedPreviewCount = -1;

function createCertificateCard(certificate, showTags = false) {
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

        const documentFrame = document.createElement('iframe');
        documentFrame.src = `certs/${encodeURIComponent(certificate.file)}#page=1&toolbar=0&navpanes=0&zoom=page-fit`;
        documentFrame.title = `${certificate.title} preview`;
        documentFrame.loading = 'lazy';
        documentFrame.tabIndex = -1;
        documentFrame.setAttribute('aria-hidden', 'true');
        pdfPreview.append(documentFrame);
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

    const tags = certificate.tags || [];
    if (showTags && tags.length) {
        const tagList = document.createElement('div');
        tagList.className = 'cert-card-tags';
        tagList.setAttribute('aria-label', 'Certificate categories and tags');
        tags.forEach(tag => {
            const tagElement = document.createElement('span');
            tagElement.className = 'cert-card-tag';
            tagElement.textContent = tag;
            tagList.append(tagElement);
        });
        copy.append(tagList);
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
        const searchable = [
            certificate.title,
            certificate.issuer,
            certificate.file,
            ...(certificate.tags || [])
        ]
            .filter(Boolean)
            .join(' ')
            .toLocaleLowerCase();
        return searchable.includes(normalizedQuery);
    });

    allCerts.replaceChildren(...matches.map(certificate => createCertificateCard(certificate, true)));
    resultsStatus.textContent = matches.length
        ? `${matches.length} result${matches.length === 1 ? '' : 's'}`
        : 'No results match your search.';
}

function renderPreview() {
    const columns = getComputedStyle(preview).gridTemplateColumns.trim().split(/\s+/).length;
    const count = Math.min(qualifications.length, columns, MAX_PREVIEW_COUNT);
    if (count === renderedPreviewCount) return;

    preview.replaceChildren(...qualifications.slice(0, count).map(certificate => createCertificateCard(certificate)));
    renderedPreviewCount = count;
}

showAllButton.addEventListener('click', () => {
    searchInput.value = '';
    renderAllCertificates();
    dialog.showModal();
    searchInput.focus();
});
window.addEventListener('resize', renderPreview);

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
        ).map(certificate => ({
            ...certificate,
            tags: Array.isArray(certificate.tags)
                ? certificate.tags.filter(tag => typeof tag === 'string' && tag.trim())
                : []
        }));

        renderPreview();
        if (qualifications.length > 0) showAllButton.hidden = false;

        status.textContent = qualifications.length
            ? `${qualifications.length} item${qualifications.length === 1 ? '' : 's'} listed.`
            : 'No qualifications or awards added yet.';
    })
    .catch(error => {
        status.textContent = 'Qualifications and awards could not be loaded.';
        console.error(error);
    });
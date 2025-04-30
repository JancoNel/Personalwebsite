// === Add cache-busting query to static resources ===
(function () {
    const version = `v=${Date.now()}`;

    // Update all <link rel="stylesheet">
    document.querySelectorAll('link[rel="stylesheet"]').forEach(link => {
        if (!link.href.includes('v=')) {
            link.href += (link.href.includes('?') ? '&' : '?') + version;
        }
    });

    // Update all <script src=...> except the current one
    document.querySelectorAll('script[src]').forEach(script => {
        if (!script.src.includes('v=')) {
            script.src += (script.src.includes('?') ? '&' : '?') + version;
        }
    });

    // Update all <img src=...>
    document.querySelectorAll('img[src]').forEach(img => {
        if (!img.src.includes('v=')) {
            img.src += (img.src.includes('?') ? '&' : '?') + version;
        }
    });
})();

// === Auto-update copyright year ===
document.getElementById('current-year').textContent = new Date().getFullYear();

// === Smooth scrolling for navigation ===
document.querySelectorAll('nav a').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        document.querySelector(this.getAttribute('href')).scrollIntoView({
            behavior: 'smooth'
        });
    });
});

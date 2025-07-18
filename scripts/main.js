// Apologies to anyone reading this code , I had to do a shitload of comments so I dont forget (again)


// Update the copyright year dynamically 
document.getElementById('current-year').textContent = new Date().getFullYear();

// Smooth scrolling for navigation
document.querySelectorAll('nav a').forEach(anchor => {
    const href = anchor.getAttribute('href');

    // Only apply smooth scroll to internal links (starting with '#')
    if (href && href.startsWith('#')) { // For like parts of the same page
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(href);
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth'
                });
            }
        });
    }
    // All other links (like /blog.html) will now use default behavior
});

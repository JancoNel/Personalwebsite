// Apologies to anyone reading this code , I had to do a shitload of comments so I dont forget


// Update the copyright year dynamically 
document.getElementById('current-year').textContent = new Date().getFullYear();

// Select all <a> tags inside the <nav> element to add smooth scrolling behavior
document.querySelectorAll('nav a').forEach(anchor => {
    // Get the href attribute value of the current <a> tag
    const href = anchor.getAttribute('href');

    // Only add smooth scrolling if the href is an internal link starting with '#'
    // This avoids interfering with links to other pages (e.g., /blog.html)
    if (href && href.startsWith('#')) {
        // Add a click event listener to the anchor element
        anchor.addEventListener('click', function(e) {
            // Prevent the default jump-to-anchor behavior of the browser
            e.preventDefault();

            // Find the target element in the document that matches the href selector
            const target = document.querySelector(href);

            // If the target element exists, smoothly scroll it into view
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth'  // Defines smooth animation rather than instant jump
                });
            }
            // If target doesn't exist, do nothing (safe fallback)
        });
    }
});

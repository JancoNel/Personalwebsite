fetch('blogs/blog-dex.json')
  .then(res => res.json())
  .then(data => {
    const list = document.getElementById('blog-list');
    list.innerHTML = ''; // Clear "Loading..."
    data.forEach(entry => {
      const li = document.createElement('li');

      // Build tag elements
      let tagsHTML = '';
      if (entry.tags && Array.isArray(entry.tags)) {
        tagsHTML = entry.tags.map(tag => `<span class="tag ${tag}">${tag}</span>`).join(' ');
      }

      li.innerHTML = `<a href="blogs/${entry.file}">${entry.title}</a> ${tagsHTML} <small class="blog-date" data-date="${entry.date}"></small>`;
      list.appendChild(li);
    });

    updateTimestamps(); // Run after list is rendered
  })
  .catch(err => {
    document.getElementById('blog-list').innerHTML = '<li>Failed to load blog list.</li>';
    console.error(err);
  });

// Relative time formatter
function updateTimestamps() {
  const dateEls = document.querySelectorAll('.blog-date');
  dateEls.forEach(el => {
    const date = new Date(el.dataset.date);
    const now = new Date();
    const diff = (now - date) / 1000;

    let result = '';
    if (diff < 60) {
      const secs = Math.floor(diff);
      result = `${secs} second${secs !== 1 ? 's' : ''} ago`;
    } else if (diff < 3600) {
      const mins = Math.floor(diff / 60);
      result = `${mins} minute${mins !== 1 ? 's' : ''} ago`;
    } else if (diff < 86400) {
      const hrs = Math.floor(diff / 3600);
      result = `${hrs} hour${hrs !== 1 ? 's' : ''} ago`;
    } else {
      const options = { day: 'numeric', month: 'long', year: 'numeric', hour: 'numeric', minute: '2-digit' };
      result = date.toLocaleString(undefined, options);
    }

    el.textContent = ` - ${result}`;
  });
}


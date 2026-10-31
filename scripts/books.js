const booksPreview = document.getElementById('books-preview');
const booksStatus = document.getElementById('books-status');
const showAllBooksButton = document.getElementById('show-all-books');
const booksDialog = document.getElementById('books-dialog');
const allBooks = document.getElementById('books-all');
const booksSearch = document.getElementById('books-search');
const booksResultsStatus = document.getElementById('books-results-status');

const MAX_BOOK_PREVIEW_COUNT = 5;
const COMMENT_COLLAPSE_LENGTH = 160;
let books = [];

function createBookCard(book) {
    const card = document.createElement('article');
    card.className = 'book-card';

    const cover = document.createElement('img');
    cover.className = 'book-cover';
    cover.src = book.cover.split('/').map(encodeURIComponent).join('/');
    cover.alt = `Cover of ${book.title}`;
    cover.loading = 'lazy';

    const copy = document.createElement('div');
    copy.className = 'book-card-copy';

    const title = document.createElement('h3');
    title.textContent = book.title;
    copy.append(title);

    const author = document.createElement('p');
    author.className = 'book-author';
    author.textContent = `by ${book.author}`;
    copy.append(author);

    const comment = document.createElement('p');
    comment.className = 'book-comment';
    comment.textContent = book.comment;
    copy.append(comment);

    if (book.comment.length > COMMENT_COLLAPSE_LENGTH) {
        comment.classList.add('book-comment-collapsed');
        const toggle = document.createElement('button');
        toggle.className = 'book-comment-toggle';
        toggle.type = 'button';
        toggle.textContent = 'View more';
        toggle.setAttribute('aria-expanded', 'false');
        toggle.addEventListener('click', () => {
            const expanded = toggle.getAttribute('aria-expanded') === 'true';
            comment.classList.toggle('book-comment-collapsed', expanded);
            toggle.setAttribute('aria-expanded', String(!expanded));
            toggle.textContent = expanded ? 'View more' : 'View less';
        });
        copy.append(toggle);
    }

    if (book.rating !== undefined) {
        const rating = document.createElement('p');
        rating.className = 'book-rating';
        rating.textContent = `Rating: ${book.rating}/5`;
        copy.append(rating);
    }

    if (book.tags.length) {
        const tags = document.createElement('div');
        tags.className = 'cert-card-tags';
        tags.setAttribute('aria-label', 'Book categories');
        book.tags.forEach(tag => {
            const tagElement = document.createElement('span');
            tagElement.className = 'cert-card-tag';
            tagElement.textContent = tag;
            tags.append(tagElement);
        });
        copy.append(tags);
    }

    card.append(cover, copy);
    return card;
}

function renderAllBooks(query = '') {
    const normalizedQuery = query.trim().toLocaleLowerCase();
    const matches = books.filter(book => [
        book.title,
        book.author,
        book.comment,
        ...book.tags
    ].join(' ').toLocaleLowerCase().includes(normalizedQuery));

    allBooks.replaceChildren(...matches.map(createBookCard));
    booksResultsStatus.textContent = matches.length
        ? `${matches.length} book${matches.length === 1 ? '' : 's'}`
        : 'No books match your search.';
}

function renderBookPreview() {
    const columns = getComputedStyle(booksPreview)
        .gridTemplateColumns.trim().split(/\s+/).length;
    const count = Math.min(books.length, columns, MAX_BOOK_PREVIEW_COUNT);
    booksPreview.replaceChildren(...books.slice(0, count).map(createBookCard));
}

document.getElementById('show-all-books').addEventListener('click', () => {
    booksSearch.value = '';
    renderAllBooks();
    booksDialog.showModal();
    booksSearch.focus();
});
document.getElementById('close-books').addEventListener('click', () => booksDialog.close());
booksSearch.addEventListener('input', () => renderAllBooks(booksSearch.value));
booksDialog.addEventListener('click', event => {
    if (event.target === booksDialog) booksDialog.close();
});
window.addEventListener('resize', renderBookPreview);

fetch('books/books.json')
    .then(response => {
        if (!response.ok) throw new Error(`Could not load book list (${response.status}).`);
        return response.json();
    })
    .then(data => {
        if (!Array.isArray(data)) throw new Error('Book list must be a JSON array.');

        books = data.filter(book =>
            book &&
            typeof book.cover === 'string' &&
            typeof book.title === 'string' &&
            typeof book.author === 'string' &&
            typeof book.comment === 'string' &&
            book.cover.trim() &&
            book.title.trim() &&
            book.author.trim() &&
            book.comment.trim() &&
            book.cover.startsWith('books/') &&
            /\.(png|jpe?g)$/i.test(book.cover) &&
            !book.cover.includes('\\') &&
            !book.cover.split('/').includes('..') &&
            (book.rating === undefined ||
                (typeof book.rating === 'number' && book.rating >= 1 && book.rating <= 5))
        ).map(book => ({
            ...book,
            tags: Array.isArray(book.tags)
                ? book.tags.filter(tag => typeof tag === 'string' && tag.trim())
                : []
        }));

        renderBookPreview();
        if (books.length > 0) showAllBooksButton.hidden = false;

        booksStatus.textContent = books.length
            ? `${books.length} book${books.length === 1 ? '' : 's'} listed.`
            : 'No books added yet.';
    })
    .catch(error => {
        booksStatus.textContent = 'Books could not be loaded.';
        console.error(error);
    });

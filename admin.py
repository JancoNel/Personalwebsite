from __future__ import annotations

import json
import math
import re
import tkinter as tk
import unicodedata
from datetime import date, datetime, time, timezone
from html import escape
from html.parser import HTMLParser
from pathlib import Path
from pathlib import PurePosixPath
from tkinter import messagebox, ttk
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parent
BLOGS_DIR = ROOT / "blogs"
INDEX_PATH = BLOGS_DIR / "blog-dex.json"
CERTS_DIR = ROOT / "certs"
CERTS_PATH = CERTS_DIR / "certs.json"
BOOKS_DIR = ROOT / "books"
BOOKS_PATH = BOOKS_DIR / "books.json"
INDEX_HTML_PATH = ROOT / "index.html"

COLORS = {
    "background": "#171816",
    "surface": "#22231f",
    "surface_hover": "#30312b",
    "text": "#eee9dd",
    "muted": "#aaa69a",
    "accent": "#d47a61",
    "selection": "#40594b",
}


def make_slug(title: str) -> str:
    normalized = unicodedata.normalize("NFKD", title)
    ascii_title = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_title.lower()).strip("-")
    if not slug:
        raise ValueError("Use a title with at least one letter or number.")
    return slug


def build_post(title: str, posted: date, body_html: str) -> str:
    safe_title = escape(title)
    posted_text = posted.isoformat()
    template_path = BLOGS_DIR / "template.html"

    if template_path.exists():
        template = template_path.read_text(encoding="utf-8")
        return (
            template.replace("{{TITLE}}", safe_title)
            .replace("{{DATE}}", posted_text)
            .replace("{{CONTENT}}", body_html.strip())
        )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{safe_title}</title>
  <link rel="stylesheet" href="../stylesheets/main.css">
  <link rel="stylesheet" href="../stylesheets/blog.css">
</head>
<body>
  <div class="blog-container">
    <a class="back-button" href="/blog.html"><i class="fas fa-arrow-left"></i> Back to Blog Index</a>
    <h1>{safe_title}</h1>
    <div class="date">Posted: {posted_text}</div>

{body_html.strip()}
  </div>
</body>
</html>
"""


def publish_post(title: str, posted_text: str, tags_text: str, body_html: str) -> Path:
    title = title.strip()
    body_html = body_html.strip()
    if not title:
        raise ValueError("Enter a post title.")
    if not body_html:
        raise ValueError("Enter the post body.")

    try:
        posted = date.fromisoformat(posted_text.strip())
    except ValueError as error:
        raise ValueError("Enter the date in YYYY-MM-DD format.") from error

    slug = make_slug(title)
    filename = f"{slug}.html"
    post_path = BLOGS_DIR / filename

    BLOGS_DIR.mkdir(parents=True, exist_ok=True)
    entries = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    if not isinstance(entries, list):
        raise ValueError("The blog index must contain a JSON list.")
    if post_path.exists() or any(entry.get("file") == filename for entry in entries):
        raise ValueError(
            f"A post named '{filename}' already exists. Change the title to create a unique slug."
        )

    tags = [tag.strip().lower() for tag in tags_text.split(",") if tag.strip()]
    if any(not re.fullmatch(r"[a-z0-9-]+", tag) for tag in tags):
        raise ValueError("Tags may only contain letters, numbers, and hyphens.")

    published_at = (
        datetime.combine(posted, time.min, tzinfo=timezone.utc)
        .isoformat()
        .replace("+00:00", "Z")
    )
    entries.append(
        {
            "title": title,
            "file": filename,
            "date": published_at,
            "tags": tags,
        }
    )

    post_path.write_text(build_post(title, posted, body_html), encoding="utf-8")
    try:
        INDEX_PATH.write_text(
            json.dumps(entries, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
    except OSError:
        post_path.unlink(missing_ok=True)
        raise

    return post_path


def read_certificates(path: Path = CERTS_PATH) -> list[dict[str, str]]:
    entries = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(entries, list):
        raise ValueError("The certificate manifest must contain a JSON list.")
    if any(
        not isinstance(entry, dict)
        or not isinstance(entry.get("file"), str)
        or not isinstance(entry.get("title"), str)
        for entry in entries
    ):
        raise ValueError("Every certificate needs a file and title.")
    return entries


def write_certificates(entries: list[dict[str, str]], path: Path = CERTS_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(entries, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def upsert_certificate(
    entries: list[dict[str, str]],
    file_name: str,
    title: str,
    issuer: str,
    certificate_date: str,
) -> list[dict[str, str]]:
    file_name = file_name.strip()
    title = title.strip()
    if (
        not file_name
        or Path(file_name).name != file_name
        or "/" in file_name
        or "\\" in file_name
    ):
        raise ValueError("Choose a certificate file from the certs folder.")
    if not title:
        raise ValueError("Enter a certificate title.")

    updated = [dict(entry) for entry in entries]
    certificate = {"file": file_name, "title": title}
    if issuer.strip():
        certificate["issuer"] = issuer.strip()
    if certificate_date.strip():
        certificate["date"] = certificate_date.strip()

    for index, entry in enumerate(updated):
        if entry["file"] == file_name:
            updated[index] = {**entry, **certificate}
            if not issuer.strip():
                updated[index].pop("issuer", None)
            if not certificate_date.strip():
                updated[index].pop("date", None)
            return updated

    updated.append(certificate)
    return updated


def remove_certificate(
    entries: list[dict[str, str]], file_name: str
) -> list[dict[str, str]]:
    return [dict(entry) for entry in entries if entry["file"] != file_name]


def _validate_book_cover(cover: str) -> str:
    cover = cover.strip()
    cover_path = PurePosixPath(cover)
    if (
        not cover
        or "\\" in cover
        or cover_path.is_absolute()
        or len(cover_path.parts) < 2
        or cover_path.parts[0] != "books"
        or any(part in {"", ".", ".."} for part in cover_path.parts)
        or cover_path.suffix.lower() not in {".png", ".jpg", ".jpeg"}
    ):
        raise ValueError("Choose a PNG or JPEG cover image from the books/ folder.")
    return cover_path.as_posix()


def read_books(path: Path = BOOKS_PATH) -> list[dict[str, object]]:
    entries = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(entries, list):
        raise ValueError("The book manifest must contain a JSON list.")

    for entry in entries:
        if (
            not isinstance(entry, dict)
            or not all(
                isinstance(entry.get(field), str) and entry[field].strip()
                for field in ("cover", "title", "author", "comment")
            )
        ):
            raise ValueError("Every book needs a cover, title, author, and comment.")
        _validate_book_cover(entry["cover"])
        tags = entry.get("tags", [])
        if not isinstance(tags, list) or any(
            not isinstance(tag, str) or not tag.strip() for tag in tags
        ):
            raise ValueError("Book categories must be a list of non-empty strings.")
        if "rating" in entry and (
            type(entry["rating"]) is not int or not 1 <= entry["rating"] <= 5
        ):
            raise ValueError("Book ratings must be whole numbers from 1 to 5.")
    return entries


def write_books(entries: list[dict[str, object]], path: Path = BOOKS_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(entries, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def upsert_book(
    entries: list[dict[str, object]],
    cover: str,
    title: str,
    author: str,
    comment: str,
    categories: str,
    rating_text: str,
    existing_cover: str = "",
) -> list[dict[str, object]]:
    cover = _validate_book_cover(cover)
    title = title.strip()
    author = author.strip()
    comment = comment.strip()
    if not title or not author or not comment:
        raise ValueError("Enter a book title, author, and personal comment.")

    tags = [tag.strip() for tag in categories.split(",") if tag.strip()]
    book: dict[str, object] = {
        "cover": cover,
        "title": title,
        "author": author,
        "comment": comment,
    }
    if tags:
        book["tags"] = tags
    if rating_text.strip():
        try:
            rating = int(rating_text.strip())
        except ValueError as error:
            raise ValueError("Rating must be a whole number from 1 to 5.") from error
        if not 1 <= rating <= 5:
            raise ValueError("Rating must be a whole number from 1 to 5.")
        book["rating"] = rating

    updated = [dict(entry) for entry in entries]
    target_cover = existing_cover or cover
    matching_index = next(
        (
            index
            for index, entry in enumerate(updated)
            if entry.get("cover") == target_cover
        ),
        None,
    )
    if any(
        entry.get("cover") == cover and index != matching_index
        for index, entry in enumerate(updated)
    ):
        raise ValueError("That cover is already assigned to another book.")

    if matching_index is None:
        updated.append(book)
    else:
        updated[matching_index] = book
    return updated


def remove_book(
    entries: list[dict[str, object]], cover: str
) -> list[dict[str, object]]:
    return [dict(entry) for entry in entries if entry.get("cover") != cover]


class _PageResourceParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.resources: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if tag == "script" and attributes.get("src"):
            self.resources.append(attributes["src"])
        elif tag == "link" and "stylesheet" in (
            attributes.get("rel") or ""
        ).lower().split():
            if attributes.get("href"):
                self.resources.append(attributes["href"])


def estimate_page_load(root: Path = ROOT) -> tuple[int, int]:
    index_path = root / "index.html"
    parser = _PageResourceParser()
    parser.feed(index_path.read_text(encoding="utf-8"))
    assets = {index_path.resolve()}

    def add_asset(relative_path: str) -> Path:
        parsed_path = urlsplit(relative_path)
        if parsed_path.scheme or parsed_path.netloc:
            raise ValueError(f"Expected a local asset path, got '{relative_path}'.")
        decoded_path = unquote(parsed_path.path).lstrip("/")
        asset = (root / decoded_path).resolve()
        try:
            asset.relative_to(root.resolve())
        except ValueError as error:
            raise ValueError(
                f"Asset path escapes the website: '{relative_path}'."
            ) from error
        if not asset.is_file():
            raise FileNotFoundError(f"Referenced local asset was not found: {relative_path}")
        assets.add(asset)
        return asset

    for resource in parser.resources:
        parsed_resource = urlsplit(resource)
        if not parsed_resource.scheme and not parsed_resource.netloc:
            add_asset(resource)

    for manifest_path in (root / "certs" / "certs.json", root / "books" / "books.json"):
        add_asset(manifest_path.relative_to(root).as_posix())
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if not isinstance(manifest, list):
            raise ValueError(
                f"{manifest_path.relative_to(root)} must contain a JSON list."
            )
        for entry in manifest:
            if not isinstance(entry, dict):
                raise ValueError(
                    f"{manifest_path.relative_to(root)} contains an invalid entry."
                )
            if manifest_path.parent.name == "certs":
                file_name = entry.get("file")
                if isinstance(file_name, str) and file_name:
                    add_asset(f"certs/{file_name}")
            else:
                cover = entry.get("cover")
                if isinstance(cover, str) and cover:
                    add_asset(cover)

    total_bytes = sum(asset.stat().st_size for asset in assets)
    return total_bytes, len(assets)


def format_file_size(size_bytes: int) -> str:
    size = float(size_bytes)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024 or unit == "GB":
            return f"{size:.1f} {unit}" if unit != "B" else f"{size:.0f} B"
        size /= 1024
    return f"{size_bytes} B"


class AdminApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Personal Website Admin")
        self.geometry("860x760")
        self.minsize(680, 600)
        self.configure(background=COLORS["background"])

        self._configure_style()
        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=16, pady=16)

        self.blog_tab = ttk.Frame(notebook, style="App.TFrame", padding=18)
        self.certs_tab = ttk.Frame(notebook, style="App.TFrame", padding=18)
        self.books_tab = ttk.Frame(notebook, style="App.TFrame", padding=18)
        self.load_tab = ttk.Frame(notebook, style="App.TFrame", padding=18)
        notebook.add(self.blog_tab, text="Blog Post")
        notebook.add(self.certs_tab, text="Certificates")
        notebook.add(self.books_tab, text="Books")
        notebook.add(self.load_tab, text="Page Load")

        self._build_blog_tab()
        self._build_certs_tab()
        self._build_books_tab()
        self._build_load_tab()
        self.refresh_certificate_files()
        self.refresh_certificates()
        self.refresh_book_files()
        self.refresh_books()
        self.refresh_page_load_estimate()

    def _configure_style(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure(
            ".",
            background=COLORS["background"],
            foreground=COLORS["text"],
            font=("Segoe UI", 10),
        )
        style.configure("TFrame", background=COLORS["background"])
        style.configure("App.TFrame", background=COLORS["background"])
        style.configure(
            "TLabel", background=COLORS["background"], foreground=COLORS["text"]
        )
        style.configure(
            "Header.TLabel", font=("Segoe UI", 18, "bold"), foreground=COLORS["text"]
        )
        style.configure("Muted.TLabel", foreground=COLORS["muted"])
        style.configure(
            "TButton",
            background=COLORS["surface_hover"],
            foreground=COLORS["text"],
            padding=(12, 8),
            borderwidth=0,
        )
        style.map(
            "TButton",
            background=[("active", COLORS["accent"]), ("pressed", COLORS["selection"])],
            foreground=[("active", COLORS["background"])],
        )
        style.configure("TNotebook", background=COLORS["background"], borderwidth=0)
        style.configure(
            "TNotebook.Tab",
            background=COLORS["surface"],
            foreground=COLORS["muted"],
            padding=(16, 9),
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", COLORS["selection"])],
            foreground=[("selected", COLORS["text"])],
        )
        style.configure(
            "TEntry",
            fieldbackground=COLORS["surface"],
            foreground=COLORS["text"],
            insertcolor=COLORS["text"],
            padding=7,
        )
        style.configure(
            "TCombobox",
            fieldbackground=COLORS["surface"],
            foreground=COLORS["text"],
            arrowcolor=COLORS["text"],
            padding=6,
        )
        style.map(
            "TCombobox",
            fieldbackground=[("readonly", COLORS["surface"])],
            foreground=[("readonly", COLORS["text"])],
        )
        style.configure(
            "Treeview",
            background=COLORS["surface"],
            fieldbackground=COLORS["surface"],
            foreground=COLORS["text"],
            rowheight=28,
            borderwidth=0,
        )
        style.configure(
            "Treeview.Heading",
            background=COLORS["surface_hover"],
            foreground=COLORS["text"],
            padding=7,
        )
        style.map("Treeview", background=[("selected", COLORS["selection"])])

    def _build_blog_tab(self) -> None:
        self.blog_tab.columnconfigure(0, weight=1)
        self.blog_tab.rowconfigure(4, weight=1)
        ttk.Label(self.blog_tab, text="New blog post", style="Header.TLabel").grid(
            row=0, column=0, sticky="w", pady=(0, 14)
        )

        fields = ttk.Frame(self.blog_tab, style="App.TFrame")
        fields.grid(row=1, column=0, sticky="ew")
        fields.columnconfigure(1, weight=1)
        for row, label in enumerate(("Title", "Published date", "Tags")):
            ttk.Label(fields, text=label).grid(
                row=row, column=0, sticky="w", padx=(0, 12), pady=5
            )

        self.title_input = ttk.Entry(fields)
        self.title_input.grid(row=0, column=1, sticky="ew", pady=5)
        self.date_input = ttk.Entry(fields)
        self.date_input.insert(0, date.today().isoformat())
        self.date_input.grid(row=1, column=1, sticky="ew", pady=5)
        self.tags_input = ttk.Entry(fields)
        self.tags_input.grid(row=2, column=1, sticky="ew", pady=5)

        ttk.Label(self.blog_tab, text="Post body (HTML)").grid(
            row=2, column=0, sticky="w", pady=(14, 5)
        )
        self.body_input = tk.Text(
            self.blog_tab,
            wrap="word",
            undo=True,
            height=20,
            background=COLORS["surface"],
            foreground=COLORS["text"],
            insertbackground=COLORS["text"],
            selectbackground=COLORS["selection"],
            relief="flat",
            padx=10,
            pady=10,
        )
        self.body_input.grid(row=4, column=0, sticky="nsew")

        footer = ttk.Frame(self.blog_tab, style="App.TFrame")
        footer.grid(row=5, column=0, sticky="ew", pady=(14, 0))
        footer.columnconfigure(0, weight=1)
        ttk.Label(
            footer,
            text="Separate tags with commas. Body content accepts HTML.",
            style="Muted.TLabel",
        ).grid(row=0, column=0, sticky="w")
        ttk.Button(footer, text="Generate post", command=self.generate).grid(
            row=0, column=1, sticky="e"
        )
        self.title_input.focus_set()

    def _build_certs_tab(self) -> None:
        self.certs_tab.columnconfigure(0, weight=1)
        self.certs_tab.rowconfigure(4, weight=1)
        ttk.Label(
            self.certs_tab, text="Manage certificates", style="Header.TLabel"
        ).grid(row=0, column=0, sticky="w", pady=(0, 4))
        ttk.Label(
            self.certs_tab,
            text="Choose a file already in certs/, then add it or select an existing entry to edit.",
            style="Muted.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(0, 14))

        fields = ttk.Frame(self.certs_tab, style="App.TFrame")
        fields.grid(row=2, column=0, sticky="ew")
        fields.columnconfigure(1, weight=1)

        self.certificate_file = tk.StringVar()
        self.certificate_title = tk.StringVar()
        self.certificate_issuer = tk.StringVar()
        self.certificate_date = tk.StringVar()
        labels = ("File", "Title", "Issuer", "Date")
        for row, label in enumerate(labels):
            ttk.Label(fields, text=label).grid(
                row=row, column=0, sticky="w", padx=(0, 12), pady=5
            )

        self.file_picker = ttk.Combobox(
            fields, textvariable=self.certificate_file, state="readonly"
        )
        self.file_picker.grid(row=0, column=1, sticky="ew", pady=5)
        ttk.Button(
            fields, text="Refresh files", command=self.refresh_certificate_files
        ).grid(row=0, column=2, padx=(8, 0), pady=5)
        ttk.Entry(fields, textvariable=self.certificate_title).grid(
            row=1, column=1, columnspan=2, sticky="ew", pady=5
        )
        ttk.Entry(fields, textvariable=self.certificate_issuer).grid(
            row=2, column=1, columnspan=2, sticky="ew", pady=5
        )
        ttk.Entry(fields, textvariable=self.certificate_date).grid(
            row=3, column=1, columnspan=2, sticky="ew", pady=5
        )

        actions = ttk.Frame(self.certs_tab, style="App.TFrame")
        actions.grid(row=3, column=0, sticky="ew", pady=(10, 16))
        ttk.Button(actions, text="Add / update", command=self.save_certificate).pack(
            side="left"
        )
        ttk.Button(
            actions, text="Remove selected", command=self.delete_certificate
        ).pack(side="left", padx=(8, 0))
        ttk.Button(actions, text="Clear", command=self.clear_certificate_form).pack(
            side="left", padx=(8, 0)
        )

        self.certificate_tree = ttk.Treeview(
            self.certs_tab,
            columns=("title", "file", "issuer", "date"),
            show="headings",
            selectmode="browse",
        )
        for column, heading, width in (
            ("title", "Title", 230),
            ("file", "File", 150),
            ("issuer", "Issuer", 160),
            ("date", "Date", 100),
        ):
            self.certificate_tree.heading(column, text=heading)
            self.certificate_tree.column(
                column, width=width, minwidth=80, stretch=column == "title"
            )
        self.certificate_tree.grid(row=4, column=0, sticky="nsew")
        self.certificate_tree.bind("<<TreeviewSelect>>", self.select_certificate)

        self.certs_status = tk.StringVar(value="")
        ttk.Label(
            self.certs_tab, textvariable=self.certs_status, style="Muted.TLabel"
        ).grid(row=5, column=0, sticky="w", pady=(10, 0))

    def refresh_certificate_files(self) -> None:
        CERTS_DIR.mkdir(parents=True, exist_ok=True)
        allowed_extensions = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".pdf"}
        files = sorted(
            path.name
            for path in CERTS_DIR.iterdir()
            if path.is_file() and path.suffix.lower() in allowed_extensions
        )
        self.file_picker["values"] = files
        if self.certificate_file.get() not in files:
            self.certificate_file.set("")
        if not files:
            self.certs_status.set("No image or PDF files found in certs/.")

    def refresh_certificates(self) -> None:
        try:
            entries = read_certificates()
        except (OSError, ValueError, json.JSONDecodeError) as error:
            self.certs_status.set(f"Could not read certs/certs.json: {error}")
            entries = []

        self.certificate_tree.delete(*self.certificate_tree.get_children())
        for index, entry in enumerate(entries):
            self.certificate_tree.insert(
                "",
                "end",
                iid=f"certificate-{index}",
                values=(
                    entry["title"],
                    entry["file"],
                    entry.get("issuer", ""),
                    entry.get("date", ""),
                ),
            )
        if entries:
            self.certs_status.set(
                f"{len(entries)} certificate entr{'y' if len(entries) == 1 else 'ies'}."
            )

    def select_certificate(self, _event: tk.Event) -> None:
        selection = self.certificate_tree.selection()
        if not selection:
            return
        title, file_name, issuer, certificate_date = self.certificate_tree.item(
            selection[0], "values"
        )
        self.certificate_title.set(title)
        self.certificate_file.set(file_name)
        self.certificate_issuer.set(issuer)
        self.certificate_date.set(certificate_date)

    def save_certificate(self) -> None:
        file_name = self.certificate_file.get().strip()
        if not file_name or not (CERTS_DIR / file_name).is_file():
            messagebox.showerror(
                "Choose a certificate",
                "Select an image or PDF from certs/.",
                parent=self,
            )
            return

        try:
            entries = read_certificates()
            updated = upsert_certificate(
                entries,
                file_name,
                self.certificate_title.get(),
                self.certificate_issuer.get(),
                self.certificate_date.get(),
            )
            write_certificates(updated)
        except (OSError, ValueError, json.JSONDecodeError) as error:
            messagebox.showerror("Could not save certificate", str(error), parent=self)
            return

        self.refresh_certificates()
        self.clear_certificate_form()

    def delete_certificate(self) -> None:
        selection = self.certificate_tree.selection()
        if not selection:
            messagebox.showinfo(
                "Select a certificate", "Choose an entry to remove.", parent=self
            )
            return

        file_name = self.certificate_tree.item(selection[0], "values")[1]
        if not messagebox.askyesno(
            "Remove certificate entry",
            f"Remove '{file_name}' from certs.json?",
            parent=self,
        ):
            return

        try:
            updated = remove_certificate(read_certificates(), file_name)
            write_certificates(updated)
        except (OSError, ValueError, json.JSONDecodeError) as error:
            messagebox.showerror(
                "Could not remove certificate", str(error), parent=self
            )
            return

        self.refresh_certificates()
        self.clear_certificate_form()

    def clear_certificate_form(self) -> None:
        self.certificate_file.set("")
        self.certificate_title.set("")
        self.certificate_issuer.set("")
        self.certificate_date.set("")
        self.certificate_tree.selection_remove(self.certificate_tree.selection())

    def _build_books_tab(self) -> None:
        self.books_tab.columnconfigure(0, weight=1)
        self.books_tab.rowconfigure(4, weight=1)
        ttk.Label(self.books_tab, text="Manage books", style="Header.TLabel").grid(
            row=0, column=0, sticky="w", pady=(0, 4)
        )
        ttk.Label(
            self.books_tab,
            text="Choose a PNG or JPEG cover from books/, then add or edit its book details.",
            style="Muted.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(0, 14))

        fields = ttk.Frame(self.books_tab, style="App.TFrame")
        fields.grid(row=2, column=0, sticky="ew")
        fields.columnconfigure(1, weight=1)
        for row, label in enumerate(
            ("Cover", "Title", "Author", "Personal comment", "Categories", "Rating")
        ):
            ttk.Label(fields, text=label).grid(
                row=row,
                column=0,
                sticky="nw" if row == 3 else "w",
                padx=(0, 12),
                pady=5,
            )

        self.book_cover = tk.StringVar()
        self.book_title = tk.StringVar()
        self.book_author = tk.StringVar()
        self.book_categories = tk.StringVar()
        self.book_rating = tk.StringVar()
        self.selected_book_cover = ""
        self.book_file_picker = ttk.Combobox(
            fields, textvariable=self.book_cover, state="readonly"
        )
        self.book_file_picker.grid(row=0, column=1, sticky="ew", pady=5)
        ttk.Button(fields, text="Refresh files", command=self.refresh_book_files).grid(
            row=0, column=2, padx=(8, 0), pady=5
        )
        ttk.Entry(fields, textvariable=self.book_title).grid(
            row=1, column=1, columnspan=2, sticky="ew", pady=5
        )
        ttk.Entry(fields, textvariable=self.book_author).grid(
            row=2, column=1, columnspan=2, sticky="ew", pady=5
        )
        self.book_comment_input = tk.Text(
            fields,
            wrap="word",
            undo=True,
            height=4,
            background=COLORS["surface"],
            foreground=COLORS["text"],
            insertbackground=COLORS["text"],
            selectbackground=COLORS["selection"],
            relief="flat",
            padx=8,
            pady=7,
        )
        self.book_comment_input.grid(
            row=3, column=1, columnspan=2, sticky="ew", pady=5
        )
        ttk.Entry(fields, textvariable=self.book_categories).grid(
            row=4, column=1, columnspan=2, sticky="ew", pady=5
        )
        self.book_rating_picker = ttk.Combobox(
            fields,
            textvariable=self.book_rating,
            values=("", "1", "2", "3", "4", "5"),
            state="readonly",
            width=8,
        )
        self.book_rating_picker.grid(row=5, column=1, sticky="w", pady=5)

        actions = ttk.Frame(self.books_tab, style="App.TFrame")
        actions.grid(row=3, column=0, sticky="ew", pady=(10, 16))
        ttk.Button(actions, text="Add / update", command=self.save_book).pack(
            side="left"
        )
        ttk.Button(actions, text="Remove selected", command=self.delete_book).pack(
            side="left", padx=(8, 0)
        )
        ttk.Button(actions, text="Clear", command=self.clear_book_form).pack(
            side="left", padx=(8, 0)
        )

        self.book_tree = ttk.Treeview(
            self.books_tab,
            columns=("title", "author", "cover", "categories", "rating"),
            show="headings",
            selectmode="browse",
        )
        for column, heading, width in (
            ("title", "Title", 150),
            ("author", "Author", 100),
            ("cover", "Cover", 150),
            ("categories", "Categories", 120),
            ("rating", "Rating", 55),
        ):
            self.book_tree.heading(column, text=heading)
            self.book_tree.column(
                column, width=width, minwidth=65, stretch=column == "title"
            )
        self.book_tree.grid(row=4, column=0, sticky="nsew")
        self.book_tree.bind("<<TreeviewSelect>>", self.select_book)

        self.books_status = tk.StringVar(value="")
        ttk.Label(
            self.books_tab, textvariable=self.books_status, style="Muted.TLabel"
        ).grid(row=5, column=0, sticky="w", pady=(10, 0))

    def _build_load_tab(self) -> None:
        self.load_tab.columnconfigure(0, weight=1)
        ttk.Label(
            self.load_tab, text="Index page load estimate", style="Header.TLabel"
        ).grid(row=0, column=0, sticky="w", pady=(0, 8))
        ttk.Label(
            self.load_tab,
            text=(
                "Estimate the transfer time for index.html, its local styles and scripts, "
                "the certificates and books manifests, and all listed cover/certificate files. "
                "Remote assets, network latency, caching, compression, and browser rendering "
                "are not included."
            ),
            style="Muted.TLabel",
            wraplength=700,
            justify="left",
        ).grid(row=1, column=0, sticky="ew", pady=(0, 18))

        controls = ttk.Frame(self.load_tab, style="App.TFrame")
        controls.grid(row=2, column=0, sticky="w")
        ttk.Label(controls, text="Connection speed (Mbps)").pack(side="left")
        self.bandwidth_mbps = tk.StringVar(value="10")
        ttk.Entry(
            controls, textvariable=self.bandwidth_mbps, width=10
        ).pack(side="left", padx=(10, 8))
        ttk.Button(
            controls, text="Estimate", command=self.refresh_page_load_estimate
        ).pack(side="left")

        self.page_load_status = tk.StringVar(value="")
        ttk.Label(
            self.load_tab,
            textvariable=self.page_load_status,
            justify="left",
            wraplength=700,
        ).grid(row=3, column=0, sticky="nw", pady=(20, 0))

    def refresh_book_files(self) -> None:
        BOOKS_DIR.mkdir(parents=True, exist_ok=True)
        files = sorted(
            path.relative_to(ROOT).as_posix()
            for path in BOOKS_DIR.rglob("*")
            if path.is_file() and path.suffix.lower() in {".png", ".jpg", ".jpeg"}
        )
        self.book_file_picker["values"] = files
        if self.book_cover.get() not in files:
            self.book_cover.set("")
        if not files:
            self.books_status.set("No PNG or JPEG cover files found in books/.")

    def refresh_books(self) -> None:
        try:
            entries = read_books()
        except (OSError, ValueError, json.JSONDecodeError) as error:
            self.books_status.set(f"Could not read books/books.json: {error}")
            entries = []

        self.book_tree.delete(*self.book_tree.get_children())
        for index, entry in enumerate(entries):
            self.book_tree.insert(
                "",
                "end",
                iid=f"book-{index}",
                values=(
                    entry["title"],
                    entry["author"],
                    entry["cover"],
                    ", ".join(entry.get("tags", [])),
                    entry.get("rating", ""),
                ),
            )
        if entries:
            self.books_status.set(
                f"{len(entries)} book{'s' if len(entries) != 1 else ''} in the catalog."
            )
        elif not self.books_status.get().startswith("Could not read"):
            self.books_status.set("No books in the catalog.")

    def select_book(self, _event: tk.Event) -> None:
        selection = self.book_tree.selection()
        if not selection:
            return
        title, author, cover, categories, rating = self.book_tree.item(
            selection[0], "values"
        )
        self.selected_book_cover = cover
        self.book_cover.set(cover)
        self.book_title.set(title)
        self.book_author.set(author)
        self.book_categories.set(categories)
        self.book_rating.set(str(rating))
        try:
            entry = next(book for book in read_books() if book["cover"] == cover)
        except (OSError, ValueError, json.JSONDecodeError, StopIteration) as error:
            self.books_status.set(f"Could not load selected book: {error}")
            return
        self.book_comment_input.delete("1.0", "end")
        self.book_comment_input.insert("1.0", entry["comment"])

    def save_book(self) -> None:
        cover = self.book_cover.get().strip()
        if not cover or not (ROOT / PurePosixPath(cover)).is_file():
            messagebox.showerror(
                "Choose a book cover",
                "Select a PNG or JPEG cover image from books/.",
                parent=self,
            )
            return

        try:
            entries = read_books()
            updated = upsert_book(
                entries,
                cover,
                self.book_title.get(),
                self.book_author.get(),
                self.book_comment_input.get("1.0", "end-1c"),
                self.book_categories.get(),
                self.book_rating.get(),
                self.selected_book_cover,
            )
            write_books(updated)
        except (OSError, ValueError, json.JSONDecodeError) as error:
            messagebox.showerror("Could not save book", str(error), parent=self)
            return

        self.refresh_books()
        self.clear_book_form()

    def delete_book(self) -> None:
        selection = self.book_tree.selection()
        if not selection:
            messagebox.showinfo(
                "Select a book", "Choose an entry to remove.", parent=self
            )
            return

        cover = self.book_tree.item(selection[0], "values")[2]
        if not messagebox.askyesno(
            "Remove book entry",
            f"Remove '{cover}' from books/books.json? The cover file will not be deleted.",
            parent=self,
        ):
            return

        try:
            write_books(remove_book(read_books(), cover))
        except (OSError, ValueError, json.JSONDecodeError) as error:
            messagebox.showerror("Could not remove book", str(error), parent=self)
            return

        self.refresh_books()
        self.clear_book_form()

    def clear_book_form(self) -> None:
        self.selected_book_cover = ""
        self.book_cover.set("")
        self.book_title.set("")
        self.book_author.set("")
        self.book_categories.set("")
        self.book_rating.set("")
        self.book_comment_input.delete("1.0", "end")
        self.book_tree.selection_remove(self.book_tree.selection())

    def refresh_page_load_estimate(self) -> None:
        try:
            bandwidth = float(self.bandwidth_mbps.get().strip())
            if not math.isfinite(bandwidth) or bandwidth <= 0:
                raise ValueError("Connection speed must be a positive number.")
            total_bytes, asset_count = estimate_page_load()
        except (OSError, ValueError, json.JSONDecodeError) as error:
            self.page_load_status.set(f"Could not calculate estimate: {error}")
            return

        seconds = total_bytes * 8 / (bandwidth * 1_000_000)
        self.page_load_status.set(
            f"Local page assets: {format_file_size(total_bytes)} across "
            f"{asset_count} files.\nEstimated transfer time at {bandwidth:g} Mbps: "
            f"{seconds:.2f} seconds."
        )

    def generate(self) -> None:
        try:
            post_path = publish_post(
                self.title_input.get(),
                self.date_input.get(),
                self.tags_input.get(),
                self.body_input.get("1.0", "end-1c"),
            )
        except (OSError, ValueError, json.JSONDecodeError) as error:
            messagebox.showerror("Could not generate post", str(error), parent=self)
            return

        messagebox.showinfo(
            "Post generated", f"Created {post_path.relative_to(ROOT)}", parent=self
        )
        self.title_input.delete(0, "end")
        self.tags_input.delete(0, "end")
        self.body_input.delete("1.0", "end")
        self.title_input.focus_set()


if __name__ == "__main__":
    AdminApp().mainloop()

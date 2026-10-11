from __future__ import annotations

import json
import re
import tkinter as tk
import unicodedata
from datetime import date, datetime, time, timezone
from html import escape
from pathlib import Path
from tkinter import messagebox, ttk

ROOT = Path(__file__).resolve().parent
BLOGS_DIR = ROOT / "blogs"
INDEX_PATH = BLOGS_DIR / "blog-dex.json"
CERTS_DIR = ROOT / "certs"
CERTS_PATH = CERTS_DIR / "certs.json"

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
        notebook.add(self.blog_tab, text="Blog Post")
        notebook.add(self.certs_tab, text="Certificates")

        self._build_blog_tab()
        self._build_certs_tab()
        self.refresh_certificate_files()
        self.refresh_certificates()

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

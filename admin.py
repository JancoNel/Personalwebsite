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


class BlogAdmin(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Blog Post Generator")
        self.geometry("760x700")
        self.minsize(600, 520)

        self.columnconfigure(0, weight=1)
        self.rowconfigure(4, weight=1)

        ttk.Label(self, text="New blog post", font=("Segoe UI", 18, "bold")).grid(
            row=0, column=0, sticky="w", padx=20, pady=(18, 12)
        )

        fields = ttk.Frame(self)
        fields.grid(row=1, column=0, sticky="ew", padx=20)
        fields.columnconfigure(1, weight=1)

        ttk.Label(fields, text="Title").grid(
            row=0, column=0, sticky="w", padx=(0, 12), pady=5
        )
        self.title_input = ttk.Entry(fields)
        self.title_input.grid(row=0, column=1, sticky="ew", pady=5)

        ttk.Label(fields, text="Published date").grid(
            row=1, column=0, sticky="w", padx=(0, 12), pady=5
        )
        self.date_input = ttk.Entry(fields)
        self.date_input.insert(0, date.today().isoformat())
        self.date_input.grid(row=1, column=1, sticky="ew", pady=5)

        ttk.Label(fields, text="Tags").grid(
            row=2, column=0, sticky="w", padx=(0, 12), pady=5
        )
        self.tags_input = ttk.Entry(fields)
        self.tags_input.grid(row=2, column=1, sticky="ew", pady=5)

        ttk.Label(self, text="Post body (HTML)").grid(
            row=2, column=0, sticky="w", padx=20, pady=(14, 5)
        )
        self.body_input = tk.Text(self, wrap="word", undo=True, height=20)
        self.body_input.grid(row=4, column=0, sticky="nsew", padx=20)

        footer = ttk.Frame(self)
        footer.grid(row=5, column=0, sticky="ew", padx=20, pady=16)
        footer.columnconfigure(0, weight=1)
        ttk.Label(
            footer, text="Separate tags with commas. Body content accepts HTML."
        ).grid(row=0, column=0, sticky="w")
        ttk.Button(footer, text="Generate post", command=self.generate).grid(
            row=0, column=1, sticky="e"
        )
        self.title_input.focus_set()

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
    BlogAdmin().mainloop()

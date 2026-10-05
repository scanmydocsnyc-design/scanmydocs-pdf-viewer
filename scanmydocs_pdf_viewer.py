"""
ScanMyDocs PDF Viewer
------------------------------------
A friendly PDF *folder* browser. Point it at a folder of PDFs and:

  - Left panel:    list of every PDF in that folder
  - Middle panel:  page thumbnails for the selected PDF, scroll through them
  - Right panel:   large view of the page you click
  - Delete pages you don't want, then Save (or Save a Copy)
  - Drag page thumbnails to reorder (Ctrl/Shift-click to move several)
  - Print the current file

Built for quickly flipping through scanned documents - more capable than
File Explorer, simpler than Acrobat.

Requirements:
  pip install pymupdf

Run:
  python scanmydocs_pdf_viewer.py
"""

import os
import subprocess
import sys
import tempfile
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

try:
    import fitz  # PyMuPDF
except ImportError:
    raise SystemExit(
        "This program needs the 'PyMuPDF' library.\n\n"
        "Install it by opening a command prompt and typing:\n\n"
        "    pip install pymupdf\n"
    )

APP_NAME = "ScanMyDocs PDF Viewer"
HEADER_BG = "white"
BG = "#f3f6fa"
SIDEBAR_BG = "#e8eef6"
ACCENT = "#0a5bb5"        # ScanMyDocs blue (toolbar)
NAVY = "#0b3d7a"          # dark blue from the logo
SELECT_BLUE = "#0a5bb5"
CURRENT_BG = "#8db8e3"    # page being viewed (not selected)
VIEW_BG = "#d3dde9"
STRIP_BG = "#dfe7f1"
CANCEL_BG = "#e8eef6"
DROP_LINE = "#12a6e0"     # insertion line while dragging pages
GHOST_FG = "#a9c6e6"      # faint original page number on thumbnails
DRAG_THRESHOLD = 6        # pixels the mouse must move before a drag starts
COPYRIGHT = "\u00a9 2026 Scan My Docs, LLC"
THUMB_W = 150


# ScanMyDocs logo (80 px tall), built into the program so the .exe
# never needs a separate image file.
LOGO_PNG_B64 = (
    "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"
    "q2rMk9iDQI8AAAAASUVORK5CYII="
)


def resource_path(name):
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, name)


class PDFFolderViewer:
    def __init__(self, root):
        self.root = root
        self.root.title(APP_NAME)
        self.root.geometry("1280x820")
        self.root.configure(bg=BG)

        self.folder = None
        self.pdf_files = []
        self.doc = None
        self.current_pdf = None
        self.current_page = 0
        self.zoom = 1.0
        self.dirty = False

        self.page_thumb_images = []
        self.page_thumb_widgets = []
        # original page number of each page, as it was when the file was
        # opened; shown faintly on the thumbnails so moves can be checked
        self.orig_nums = []
        self.selected = set()
        self.anchor = None  # last single-clicked page, for shift-range select
        self.page_image = None
        self._thumb_job = None
        self._thumb_index = 0
        self._strip_job = None
        self._strip_index = 0
        self.file_strip_images = []
        self.file_strip_tiles = []
        self._thumb_cells = []
        self._cols = 2

        # drag-to-reorder state
        self._press = None        # (index, x_root, y_root, collapse_on_release)
        self._dragging = False
        self._drop_at = None      # insert position 0..len(doc)
        self._drop_line = None

        self._build_header()
        self._build_toolbar()
        self._build_body()
        self._build_statusbar()

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def _build_header(self):
        header = tk.Frame(self.root, bg=HEADER_BG, height=100)
        header.pack(side="top", fill="x")
        header.pack_propagate(False)
        title = "PDF Viewer"
        try:
            self.logo_img = tk.PhotoImage(data=LOGO_PNG_B64)
            tk.Label(header, image=self.logo_img, bg=HEADER_BG).pack(
                side="left", padx=(20, 16), pady=10)
        except Exception:
            title = "ScanMyDocs PDF Viewer"   # logo failed - show full name
        tk.Label(header, text=title, bg=HEADER_BG, fg=NAVY,
                 font=("Segoe UI", 18, "bold")).pack(side="left", padx=6)
        tk.Frame(self.root, bg="#d6e0ec", height=1).pack(side="top", fill="x")

    def _build_toolbar(self):
        bar = tk.Frame(self.root, bg=ACCENT, height=44)
        bar.pack(side="top", fill="x")

        def btn(text, cmd):
            b = tk.Button(bar, text=text, command=cmd, relief="flat",
                          bg="white", fg="#1e2a38", activebackground="#dbe7f5",
                          padx=10, pady=4, bd=0, cursor="hand2")
            b.pack(side="left", padx=4, pady=6)
            return b

        btn("Open Folder", self.open_folder)
        tk.Frame(bar, bg=ACCENT, width=16).pack(side="left")
        btn("Extract Selected Page(s)...", self.extract_selected)
        btn("Delete Selected Page(s)", self.delete_selected)
        tk.Frame(bar, bg=ACCENT, width=16).pack(side="left")
        btn("\u25b2 Move 1 Page Up", self.move_page_up)
        btn("\u25bc Move 1 Page Down", self.move_page_down)
        tk.Frame(bar, bg=ACCENT, width=16).pack(side="left")
        btn("Save", self.save)
        btn("Save a Copy...", self.save_as)
        btn("Print...", self.print_doc)
        tk.Frame(bar, bg=ACCENT, width=16).pack(side="left")
        btn("Zoom \u2212", self.zoom_out)
        btn("Zoom +", self.zoom_in)
        btn("Fit", self.zoom_fit)

    def _build_body(self):
        body = tk.Frame(self.root, bg=BG)
        body.pack(side="top", fill="both", expand=True)

        # ===== TOP: three resizable panes (drag the dividers) =====
        # visible blue-gray dividers you can grab and drag
        top = tk.PanedWindow(body, orient="horizontal", sashwidth=8,
                             sashrelief="flat", bg="#b9c8da", bd=0,
                             sashcursor="sb_h_double_arrow")
        top.pack(side="top", fill="both", expand=True)

        left = tk.Frame(top, bg=SIDEBAR_BG, width=260)
        tk.Label(left, text="PDF Files in Folder", bg=SIDEBAR_BG, fg="#444",
                 font=("Segoe UI", 10, "bold")).pack(pady=(8, 0))
        tk.Label(left, text="Long names? Drag the divider \u25b6", bg=SIDEBAR_BG,
                 fg="#5e6b7a", font=("Segoe UI", 8)).pack(pady=(0, 4))
        listwrap = tk.Frame(left, bg=SIDEBAR_BG)
        listwrap.pack(fill="both", expand=True, padx=8, pady=4)
        fscroll = ttk.Scrollbar(listwrap, orient="vertical")
        fxscroll = ttk.Scrollbar(listwrap, orient="horizontal")
        self.file_list = tk.Listbox(listwrap, yscrollcommand=fscroll.set,
                                    xscrollcommand=fxscroll.set, width=1,
                                    font=("Segoe UI", 9), activestyle="none",
                                    selectbackground=SELECT_BLUE,
                                    selectforeground="white", bd=1,
                                    relief="solid", highlightthickness=0)
        fscroll.config(command=self.file_list.yview)
        fxscroll.config(command=self.file_list.xview)
        fscroll.pack(side="right", fill="y")
        fxscroll.pack(side="bottom", fill="x")
        self.file_list.pack(side="left", fill="both", expand=True)
        self.file_list.bind("<<ListboxSelect>>", self.on_file_select)

        mid = tk.Frame(top, bg=SIDEBAR_BG, width=400)
        tk.Label(mid, text="Pages  (click \u2022 shift-click range \u2022 "
                 "ctrl-click to add)\n"
                 "Drag pages to reorder (faint number = original page)\n"
                 "Drag the divider \u25b6 to see more pages at once",
                 bg=SIDEBAR_BG, justify="left",
                 fg="#444", font=("Segoe UI", 9, "bold")).pack(pady=(8, 4))
        self.thumb_canvas = tk.Canvas(mid, bg=SIDEBAR_BG, highlightthickness=0)
        tscroll = ttk.Scrollbar(mid, orient="vertical",
                                command=self.thumb_canvas.yview)
        self.thumb_canvas.configure(yscrollcommand=tscroll.set)
        tscroll.pack(side="right", fill="y")
        self.thumb_canvas.pack(side="left", fill="both", expand=True)
        self.thumb_frame = tk.Frame(self.thumb_canvas, bg=SIDEBAR_BG)
        self.thumb_canvas.create_window((0, 0), window=self.thumb_frame,
                                        anchor="nw")
        self.thumb_frame.bind(
            "<Configure>",
            lambda e: self.thumb_canvas.configure(
                scrollregion=self.thumb_canvas.bbox("all")))
        # when the middle panel is resized, reflow thumbnails into more columns
        self.thumb_canvas.bind("<Configure>", self._on_thumb_canvas_resize)

        right = tk.Frame(top, bg=VIEW_BG)
        tk.Label(right, text="Page View", bg=VIEW_BG, fg="#444",
                 font=("Segoe UI", 10, "bold"), anchor="w").pack(
                     fill="x", padx=8, pady=(6, 0))
        canvaswrap = tk.Frame(right, bg=VIEW_BG)
        canvaswrap.pack(fill="both", expand=True)
        self.page_canvas = tk.Canvas(canvaswrap, bg=VIEW_BG,
                                     highlightthickness=0)
        vscroll = ttk.Scrollbar(canvaswrap, orient="vertical",
                                command=self.page_canvas.yview)
        hscroll = ttk.Scrollbar(canvaswrap, orient="horizontal",
                                command=self.page_canvas.xview)
        self.page_canvas.configure(yscrollcommand=vscroll.set,
                                   xscrollcommand=hscroll.set)
        vscroll.pack(side="right", fill="y")
        hscroll.pack(side="bottom", fill="x")
        self.page_canvas.pack(side="left", fill="both", expand=True)

        top.add(left, minsize=150, width=260, stretch="never")
        top.add(mid, minsize=200, width=400, stretch="never")
        top.add(right, minsize=300, stretch="always")

        # ===== BOTTOM: horizontal strip of file preview tiles =====
        bottom = tk.Frame(body, bg=STRIP_BG, height=170)
        bottom.pack(side="bottom", fill="x")
        bottom.pack_propagate(False)
        tk.Label(bottom, text="Files in Folder  (click a preview to open)",
                 bg=STRIP_BG, fg="#444",
                 font=("Segoe UI", 9, "bold"), anchor="w").pack(
                     fill="x", padx=8, pady=(4, 0))
        stripwrap = tk.Frame(bottom, bg=STRIP_BG)
        stripwrap.pack(fill="both", expand=True, padx=6, pady=4)
        self.file_strip_canvas = tk.Canvas(stripwrap, bg=STRIP_BG,
                                           highlightthickness=0, height=120)
        hsb = ttk.Scrollbar(stripwrap, orient="horizontal",
                            command=self.file_strip_canvas.xview)
        self.file_strip_canvas.configure(xscrollcommand=hsb.set)
        hsb.pack(side="bottom", fill="x")
        self.file_strip_canvas.pack(side="top", fill="both", expand=True)
        self.file_strip_frame = tk.Frame(self.file_strip_canvas, bg=STRIP_BG)
        self.file_strip_canvas.create_window((0, 0),
                                             window=self.file_strip_frame,
                                             anchor="nw")
        self.file_strip_frame.bind(
            "<Configure>",
            lambda e: self.file_strip_canvas.configure(
                scrollregion=self.file_strip_canvas.bbox("all")))

        self.root.bind_all("<MouseWheel>", self._on_mousewheel)

    def _build_statusbar(self):
        sbar = tk.Frame(self.root, bg=NAVY)
        sbar.pack(side="bottom", fill="x")
        tk.Label(sbar, text=COPYRIGHT, bg=NAVY, fg="white",
                 font=("Segoe UI", 9), padx=10).pack(side="right")
        self.status = tk.Label(sbar,
                               text="Open a folder of PDFs to begin.",
                               bg=NAVY, fg="white", anchor="w",
                               font=("Segoe UI", 9), padx=10, pady=3)
        self.status.pack(side="left", fill="x", expand=True)

    def _on_mousewheel(self, event):
        widget = self.root.winfo_containing(event.x_root, event.y_root)
        w = widget
        while w is not None:
            if w == self.page_canvas:
                self.page_canvas.yview_scroll(int(-event.delta / 120), "units")
                return
            if w in (self.thumb_canvas, self.thumb_frame):
                self.thumb_canvas.yview_scroll(int(-event.delta / 120), "units")
                return
            w = getattr(w, "master", None)

    def open_folder(self):
        if not self._confirm_discard():
            return
        folder = filedialog.askdirectory(title="Choose a folder of PDFs")
        if not folder:
            return
        self.folder = folder
        self.load_folder()

    def load_folder(self):
        self.pdf_files = sorted(
            f for f in os.listdir(self.folder)
            if f.lower().endswith(".pdf"))
        self.file_list.delete(0, "end")
        for f in self.pdf_files:
            self.file_list.insert("end", f)
        self._clear_pages()
        self.build_file_strip()
        if not self.pdf_files:
            self._set_status("No PDF files found in that folder.")
        else:
            self._set_status(
                f"{len(self.pdf_files)} PDF(s) found. "
                "Click one to view its pages.")

    def build_file_strip(self):
        # cancel any running strip job
        if self._strip_job is not None:
            self.root.after_cancel(self._strip_job)
            self._strip_job = None
        for w in self.file_strip_frame.winfo_children():
            w.destroy()
        self.file_strip_images = []
        self.file_strip_tiles = []
        if not self.pdf_files:
            return
        # build tiles instantly, fill first-page previews in background
        for i, fname in enumerate(self.pdf_files):
            cell = tk.Frame(self.file_strip_frame, bg=STRIP_BG, padx=5, pady=2)
            cell.pack(side="left", padx=4, pady=2)
            tile = tk.Label(cell, text="...", width=10, height=6,
                            bd=2, relief="solid", bg="white", fg="#bbb",
                            cursor="hand2")
            tile.pack()
            name = fname if len(fname) <= 16 else fname[:14] + "…"
            tk.Label(cell, text=name, bg=STRIP_BG, fg="#555",
                     font=("Segoe UI", 8)).pack()
            tile.bind("<Button-1>",
                      lambda e, idx=i: self.open_file_by_index(idx))
            self.file_strip_images.append(None)
            self.file_strip_tiles.append(tile)
        self._strip_index = 0
        self._strip_job = self.root.after(1, self._render_next_strip_tile)

    def _render_next_strip_tile(self):
        i = self._strip_index
        if i >= len(self.pdf_files):
            self._strip_job = None
            return
        try:
            path = os.path.join(self.folder, self.pdf_files[i])
            d = fitz.open(path)
            if len(d) > 0:
                page = d[0]
                scale = 90 / page.rect.width
                pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale),
                                      alpha=False)
                img = tk.PhotoImage(data=pix.tobytes("ppm"))
                self.file_strip_images[i] = img
                self.file_strip_tiles[i].config(image=img, text="",
                                                 width=0, height=0)
            d.close()
        except Exception:
            pass
        self._strip_index += 1
        self._strip_job = self.root.after(1, self._render_next_strip_tile)

    def open_file_by_index(self, idx):
        if idx < 0 or idx >= len(self.pdf_files):
            return
        self.file_list.selection_clear(0, "end")
        self.file_list.selection_set(idx)
        self.file_list.see(idx)
        self.on_file_select()

    def on_file_select(self, event=None):
        sel = self.file_list.curselection()
        if not sel:
            return
        if not self._confirm_discard():
            return
        fname = self.pdf_files[sel[0]]
        path = os.path.join(self.folder, fname)
        try:
            if self.doc:
                self.doc.close()
            self.doc = fitz.open(path)
        except Exception as e:
            messagebox.showerror("Could not open file", str(e))
            return
        self.current_pdf = path
        self.current_page = 0
        self.zoom = 1.0
        self.dirty = False
        self.selected.clear()
        self.anchor = None
        self.orig_nums = list(range(1, len(self.doc) + 1))
        self._highlight_strip_tile(sel[0])
        # Show the first page IMMEDIATELY so the window feels instant,
        # then build thumbnails in the background without freezing the UI.
        if len(self.doc) > 0:
            self.show_page(0)
        self.render_page_thumbnails()
        self._set_status()

    def _highlight_strip_tile(self, idx):
        for i, tile in enumerate(getattr(self, "file_strip_tiles", [])):
            tile.config(bd=3 if i == idx else 2,
                        bg=SELECT_BLUE if i == idx else "white")

    def render_page_thumbnails(self):
        # cancel any thumbnail job still running from a previous file
        if self._thumb_job is not None:
            self.root.after_cancel(self._thumb_job)
            self._thumb_job = None
        for w in self.thumb_frame.winfo_children():
            w.destroy()
        self.page_thumb_images = []
        self.page_thumb_widgets = []
        if not self.doc:
            return
        total = len(self.doc)
        # build placeholder cells instantly (cheap), fill images one by one
        self._build_thumb_placeholders(total)
        self._thumb_index = 0
        self._thumb_job = self.root.after(1, self._render_next_thumb)

    def _compute_cols(self):
        # how many thumbnail columns fit in the current canvas width
        w = self.thumb_canvas.winfo_width()
        if w <= 1:
            w = 320  # initial fallback before the canvas is realized
        cell_w = THUMB_W + 24  # thumbnail + padding
        return max(1, w // cell_w)

    def _build_thumb_placeholders(self, total):
        self._cols = self._compute_cols()
        self._thumb_cells = []
        for i in range(total):
            r, c = divmod(i, self._cols)
            cell = tk.Frame(self.thumb_frame, bg=SIDEBAR_BG, padx=4, pady=4)
            cell.grid(row=r, column=c, padx=4, pady=4)
            lbl = tk.Canvas(cell, width=THUMB_W, height=int(THUMB_W * 1.3),
                            bg="white", bd=0, cursor="hand2")
            lbl.pack()
            self._draw_ghost(lbl, i)
            tk.Label(cell, text=f"Page {i+1}", bg=SIDEBAR_BG, fg="#555",
                     font=("Segoe UI", 8)).pack()
            lbl.bind("<ButtonPress-1>",
                     lambda e, idx=i: self._thumb_press(idx, e))
            lbl.bind("<B1-Motion>", self._thumb_motion)
            lbl.bind("<ButtonRelease-1>", self._thumb_release)
            self.page_thumb_widgets.append(lbl)
            self.page_thumb_images.append(None)
            self._thumb_cells.append(cell)
        self._refresh_thumb_styles()
        self.thumb_canvas.yview_moveto(0)

    def _draw_ghost(self, cv, i):
        """Faint ORIGINAL page number in the middle of a thumbnail."""
        if i >= len(self.orig_nums):
            return
        cv.delete("ghost")
        w = int(cv.cget("width"))
        h = int(cv.cget("height"))
        cv.create_text(w // 2, h // 2, text=str(self.orig_nums[i]),
                       fill=GHOST_FG, font=("Segoe UI", 40, "bold"),
                       tags="ghost")

    def _on_thumb_canvas_resize(self, event=None):
        # keep scrollregion in sync
        self.thumb_canvas.configure(scrollregion=self.thumb_canvas.bbox("all"))
        # reflow the grid if the number of columns that fit has changed
        if not getattr(self, "_thumb_cells", None):
            return
        new_cols = self._compute_cols()
        if new_cols == getattr(self, "_cols", None):
            return
        self._cols = new_cols
        for i, cell in enumerate(self._thumb_cells):
            r, c = divmod(i, new_cols)
            cell.grid_configure(row=r, column=c)

    def _render_next_thumb(self):
        # render ONE thumbnail, then yield back to the UI loop
        if not self.doc:
            self._thumb_job = None
            return
        i = self._thumb_index
        if i >= len(self.doc):
            self._thumb_job = None
            return
        try:
            page = self.doc[i]
            scale = THUMB_W / page.rect.width
            # render at low DPI - thumbnails are tiny, no need for full quality
            pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=False)
            img = tk.PhotoImage(data=pix.tobytes("ppm"))
            self.page_thumb_images[i] = img
            lbl = self.page_thumb_widgets[i]
            lbl.config(width=pix.width, height=pix.height)
            lbl.delete("all")
            lbl.create_image(0, 0, anchor="nw", image=img)
            self._draw_ghost(lbl, i)
        except Exception:
            pass
        self._thumb_index += 1
        # schedule the next one; 'after' lets clicks/scroll happen in between
        self._thumb_job = self.root.after(1, self._render_next_thumb)

    def on_thumb_click(self, idx, event):
        ctrl = bool(event.state & 0x0004)
        shift = bool(event.state & 0x0001)
        if shift and self.anchor is not None:
            lo, hi = sorted((self.anchor, idx))
            self.selected = set(range(lo, hi + 1))
        elif ctrl:
            self.selected.symmetric_difference_update({idx})
            self.anchor = idx
        else:
            self.selected = {idx}
            self.anchor = idx
        self.current_page = idx
        self.show_page(idx)
        self._refresh_thumb_styles()

    # ---------- drag to reorder ----------

    def _thumb_press(self, idx, event):
        ctrl = bool(event.state & 0x0004)
        shift = bool(event.state & 0x0001)
        # Pressing (no Ctrl/Shift) on a page that's already part of a
        # multi-page selection keeps the selection, so the group can be
        # dragged. If the mouse is released without dragging, it collapses
        # to just that page, like a normal click.
        if not ctrl and not shift and idx in self.selected \
                and len(self.selected) > 1:
            self._press = (idx, event.x_root, event.y_root, True)
            self.current_page = idx
            self.show_page(idx)
            self._refresh_thumb_styles()
            return
        self._press = (idx, event.x_root, event.y_root, False)
        self.on_thumb_click(idx, event)

    def _thumb_motion(self, event):
        if not self._press or not self.doc:
            return
        idx, x0, y0, _ = self._press
        if not self._dragging:
            if (abs(event.x_root - x0) < DRAG_THRESHOLD
                    and abs(event.y_root - y0) < DRAG_THRESHOLD):
                return
            if idx not in self.selected:
                self.selected = {idx}
                self.anchor = idx
            self._dragging = True
            self.root.config(cursor="fleur")
            self._refresh_thumb_styles()
        self._autoscroll_thumbs(event.y_root)
        self._update_drop_target(event.x_root, event.y_root)

    def _thumb_release(self, event):
        press = self._press
        self._press = None
        if not self._dragging:
            if press and press[3]:          # plain click inside a group
                idx = press[0]
                self.selected = {idx}
                self.anchor = idx
                self._refresh_thumb_styles()
            return
        self._dragging = False
        self.root.config(cursor="")
        drop_at = self._drop_at
        self._hide_drop_line()
        if drop_at is None:
            self._refresh_thumb_styles()
            return
        self._drop_pages(drop_at)

    def _autoscroll_thumbs(self, y_root):
        top = self.thumb_canvas.winfo_rooty()
        bottom = top + self.thumb_canvas.winfo_height()
        if y_root < top + 30:
            self.thumb_canvas.yview_scroll(-1, "units")
        elif y_root > bottom - 30:
            self.thumb_canvas.yview_scroll(1, "units")

    def _update_drop_target(self, x_root, y_root):
        w = self.root.winfo_containing(x_root, y_root)
        if w is not None and w is self._drop_line:
            return                          # over the line itself: keep target
        cell_idx = None
        while w is not None:
            if w in self._thumb_cells:
                cell_idx = self._thumb_cells.index(w)
                break
            if w in (self.thumb_canvas, self.thumb_frame):
                break
            w = getattr(w, "master", None)
        if cell_idx is None:
            # over empty space in the pages panel: past the last page = end
            if w in (self.thumb_canvas, self.thumb_frame) and self._thumb_cells:
                last = self._thumb_cells[-1]
                if y_root > last.winfo_rooty() + last.winfo_height() // 2:
                    self._drop_at = len(self._thumb_cells)
                    self._show_drop_line(len(self._thumb_cells) - 1, after=True)
                    return
            self._drop_at = None
            self._hide_drop_line()
            return
        cell = self._thumb_cells[cell_idx]
        after = x_root > cell.winfo_rootx() + cell.winfo_width() // 2
        self._drop_at = cell_idx + 1 if after else cell_idx
        self._show_drop_line(cell_idx, after)

    def _show_drop_line(self, cell_idx, after):
        cell = self._thumb_cells[cell_idx]
        if self._drop_line is None or not self._drop_line.winfo_exists():
            self._drop_line = tk.Frame(self.thumb_frame, bg=DROP_LINE, width=4)
        x = cell.winfo_x() + cell.winfo_width() + 1 if after \
            else cell.winfo_x() - 5
        self._drop_line.place(x=max(0, x), y=cell.winfo_y(),
                              width=4, height=cell.winfo_height())
        self._drop_line.lift()

    def _hide_drop_line(self):
        if self._drop_line is not None and self._drop_line.winfo_exists():
            self._drop_line.place_forget()
        self._drop_at = None

    def _drop_pages(self, drop_at):
        n = len(self.doc)
        moving = sorted(self.selected)
        rest = [i for i in range(n) if i not in self.selected]
        # where the block lands among the pages that aren't moving
        pos = sum(1 for i in range(drop_at) if i not in self.selected)
        new_order = rest[:pos] + moving + rest[pos:]
        if new_order == list(range(n)):
            self._refresh_thumb_styles()      # dropped where it already was
            return
        before = (list(self.orig_nums), set(self.selected), self.anchor,
                  self.current_page, self.dirty)
        try:
            self.doc.select(new_order)
        except Exception as e:
            messagebox.showerror("Could not move pages", str(e))
            return
        self.orig_nums = [self.orig_nums[k] for k in new_order]
        self.dirty = True
        self.selected = set(range(pos, pos + len(moving)))
        self.anchor = pos
        self.current_page = pos
        self._rerender_keep_scroll()
        self.show_page(pos)
        count = len(moving)
        label = "page" if count == 1 else "pages"
        self._set_status(f"Moved {count} {label}. Not saved yet.")
        if self._ask_save_after_move(count, label) == "cancel":
            self._undo_drop(new_order, before)

    def _undo_drop(self, new_order, before):
        """Put the pages back exactly where they were before the drag."""
        back = [0] * len(new_order)
        for new_pos, old_pos in enumerate(new_order):
            back[old_pos] = new_pos
        try:
            self.doc.select(back)
        except Exception as e:
            messagebox.showerror("Could not undo the move", str(e))
            return
        (self.orig_nums, self.selected, self.anchor,
         self.current_page, self.dirty) = before
        self._rerender_keep_scroll()
        self.show_page(self.current_page)
        self._set_status("Move cancelled. Pages are back where they were.")

    def _rerender_keep_scroll(self):
        top = self.thumb_canvas.yview()[0]
        self.render_page_thumbnails()
        self.thumb_canvas.update_idletasks()
        self.thumb_canvas.yview_moveto(top)

    def _ask_save_after_move(self, count, label):
        dlg = tk.Toplevel(self.root)
        dlg.title("Save page order?")
        dlg.configure(bg=BG)
        dlg.transient(self.root)
        dlg.grab_set()
        dlg.resizable(False, False)
        tk.Label(dlg, text=f"You moved {count} {label}.", bg=BG,
                 font=("Segoe UI", 10, "bold")).pack(padx=24, pady=(16, 4))
        tk.Label(dlg, text="Save over "
                 f"{os.path.basename(self.current_pdf)} now?",
                 bg=BG, fg="#33475e",
                 font=("Segoe UI", 9)).pack(padx=24, pady=(0, 12))
        choice = {"val": "cancel"}

        def pick(val):
            choice["val"] = val
            dlg.destroy()

        bwrap = tk.Frame(dlg, bg=BG)
        bwrap.pack(padx=20, pady=(0, 16))
        tk.Button(bwrap, text="Save over original", bg=ACCENT, fg="white",
                  activebackground=NAVY, activeforeground="white",
                  relief="flat", cursor="hand2", padx=12, pady=5,
                  command=lambda: pick("over")).pack(side="left", padx=4)
        tk.Button(bwrap, text="Save a Copy...", bg="white", relief="flat",
                  cursor="hand2", padx=12, pady=5,
                  command=lambda: pick("copy")).pack(side="left", padx=4)
        tk.Button(bwrap, text="Not yet, keep arranging", bg="white",
                  relief="flat", cursor="hand2", padx=12, pady=5,
                  command=lambda: pick("keep")).pack(side="left", padx=4)
        tk.Button(bwrap, text="Cancel (undo move)", bg=CANCEL_BG,
                  relief="flat", cursor="hand2", padx=12, pady=5,
                  command=lambda: pick("cancel")).pack(side="left", padx=4)
        # closing the window with X or pressing Esc = Cancel (undo the move)
        dlg.protocol("WM_DELETE_WINDOW", lambda: pick("cancel"))
        dlg.bind("<Escape>", lambda e: pick("cancel"))
        dlg.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - dlg.winfo_width()) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - dlg.winfo_height()) // 2
        dlg.geometry(f"+{x}+{y}")
        self.root.wait_window(dlg)

        if choice["val"] == "over":
            self._save_over()
        elif choice["val"] == "copy":
            self.save_as()
        elif choice["val"] == "keep":
            self._set_status("Page order changed. Click Save when done.")
        return choice["val"]

    def _refresh_thumb_styles(self):
        for i, lbl in enumerate(self.page_thumb_widgets):
            # outline color: blue = selected, light blue = page in view
            if i in self.selected:
                lbl.config(bd=0, highlightthickness=4,
                           highlightbackground=SELECT_BLUE,
                           highlightcolor=SELECT_BLUE)
            elif i == self.current_page:
                lbl.config(bd=0, highlightthickness=4,
                           highlightbackground=CURRENT_BG,
                           highlightcolor=CURRENT_BG)
            else:
                lbl.config(bd=0, highlightthickness=1,
                           highlightbackground="#b9c8da",
                           highlightcolor="#b9c8da")

    def show_page(self, idx):
        if not self.doc or idx < 0 or idx >= len(self.doc):
            return
        page = self.doc[idx]
        mat = fitz.Matrix(2.0 * self.zoom, 2.0 * self.zoom)
        pix = page.get_pixmap(matrix=mat)
        self.page_image = tk.PhotoImage(data=pix.tobytes("ppm"))
        self.page_canvas.delete("all")
        self.page_canvas.create_image(0, 0, anchor="nw", image=self.page_image)
        self.page_canvas.configure(scrollregion=(0, 0, pix.width, pix.height))
        self.page_canvas.yview_moveto(0)
        self.current_page = idx
        self._set_status()

    def move_page_up(self):
        self._move_page(-1)

    def move_page_down(self):
        self._move_page(+1)

    def _move_page(self, direction):
        if not self.doc:
            return
        # operate on a single selected page (the current one)
        if len(self.selected) != 1:
            messagebox.showinfo(
                "Select one page",
                "Move Up / Move Down move one page at a time.\n"
                "Click a single page first.\n\n"
                "(To move several at once, select them and drag.)")
            return
        src = next(iter(self.selected))
        dst = src + direction
        if dst < 0 or dst >= len(self.doc):
            return  # already at top/bottom
        order = list(range(len(self.doc)))
        order[src], order[dst] = order[dst], order[src]
        try:
            self.doc.select(order)
        except Exception as e:
            messagebox.showerror("Could not move page", str(e))
            return
        self.orig_nums = [self.orig_nums[k] for k in order]
        self.dirty = True
        self.selected = {dst}
        self.anchor = dst
        self.current_page = dst
        self._rerender_keep_scroll()
        self.show_page(dst)
        self._set_status(f"Moved page to position {dst + 1}. Remember to Save.")

    def extract_selected(self):
        if not self.doc:
            return
        if not self.selected:
            messagebox.showinfo(
                "Nothing selected",
                "Click the pages you want to pull out first.\n\n"
                "  \u2022  Click a page to select it\n"
                "  \u2022  Shift + click another page to select the whole range\n"
                "  \u2022  Ctrl + click to add or remove single pages")
            return
        pages = sorted(self.selected)
        nums = ", ".join(str(p + 1) for p in pages)

        # ask destination: new PDF, or add to an existing PDF in the folder
        dlg = tk.Toplevel(self.root)
        dlg.title("Extract Pages")
        dlg.configure(bg=BG)
        dlg.transient(self.root)
        dlg.grab_set()
        dlg.resizable(False, False)
        tk.Label(dlg, text=f"Pull out page(s): {nums}", bg=BG,
                 font=("Segoe UI", 10, "bold")).pack(padx=20, pady=(16, 4))
        tk.Label(dlg, text="Where should these pages go?", bg=BG,
                 fg="#555", font=("Segoe UI", 9)).pack(padx=20, pady=(0, 12))

        choice = {"val": None}

        def pick(val):
            choice["val"] = val
            dlg.destroy()

        bwrap = tk.Frame(dlg, bg=BG)
        bwrap.pack(padx=20, pady=(0, 16))
        tk.Button(bwrap, text="Save as a NEW PDF", width=24,
                  bg="white", relief="flat", cursor="hand2", pady=6,
                  command=lambda: pick("new")).pack(pady=3)
        tk.Button(bwrap, text="Add to ANOTHER PDF in this folder", width=30,
                  bg="white", relief="flat", cursor="hand2", pady=6,
                  command=lambda: pick("append")).pack(pady=3)
        tk.Button(bwrap, text="Cancel", width=12,
                  bg=CANCEL_BG, relief="flat", cursor="hand2", pady=4,
                  command=lambda: pick(None)).pack(pady=(8, 0))

        dlg.update_idletasks()
        # center over main window
        x = self.root.winfo_x() + (self.root.winfo_width() - dlg.winfo_width()) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - dlg.winfo_height()) // 2
        dlg.geometry(f"+{x}+{y}")
        self.root.wait_window(dlg)

        if choice["val"] == "new":
            self._extract_to_new(pages)
        elif choice["val"] == "append":
            self._extract_to_existing(pages)

    def _extract_to_new(self, pages):
        path = filedialog.asksaveasfilename(
            title="Save extracted pages as a new PDF",
            defaultextension=".pdf", initialdir=self.folder,
            initialfile="extracted pages.pdf",
            filetypes=[("PDF files", "*.pdf")])
        if not path:
            return
        try:
            out = fitz.open()
            for p in pages:
                out.insert_pdf(self.doc, from_page=p, to_page=p)
            out.save(path)
            out.close()
        except Exception as e:
            messagebox.showerror("Could not save", str(e))
            return
        self._set_status(f"Saved {len(pages)} page(s) to "
                         f"{os.path.basename(path)}")
        self._offer_remove(pages, os.path.basename(path))
        if os.path.dirname(path) == self.folder:
            self._reload_keep_selection()

    def _extract_to_existing(self, pages):
        others = [f for f in self.pdf_files
                  if os.path.join(self.folder, f) != self.current_pdf]
        if not others:
            messagebox.showinfo(
                "No other PDFs",
                "There are no other PDF files in this folder to add to.")
            return
        target = self._choose_target_pdf(others)
        if not target:
            return
        target_path = os.path.join(self.folder, target)
        if not messagebox.askyesno(
                "Confirm",
                f"Add page(s) to the end of:\n\n{target}\n\n"
                "This changes that file. Continue?"):
            return
        try:
            tdoc = fitz.open(target_path)
            for p in pages:
                tdoc.insert_pdf(self.doc, from_page=p, to_page=p)
            tmp = target_path + ".tmp"
            tdoc.save(tmp)
            tdoc.close()
            os.replace(tmp, target_path)
        except Exception as e:
            messagebox.showerror("Could not add pages", str(e))
            return
        self._set_status(f"Added {len(pages)} page(s) to {target}")
        self._offer_remove(pages, target)

    def _choose_target_pdf(self, others):
        dlg = tk.Toplevel(self.root)
        dlg.title("Choose Destination PDF")
        dlg.configure(bg=BG)
        dlg.transient(self.root)
        dlg.grab_set()
        tk.Label(dlg, text="Add the pages to which PDF?", bg=BG,
                 font=("Segoe UI", 10, "bold")).pack(padx=20, pady=(16, 8))
        lbwrap = tk.Frame(dlg, bg=BG)
        lbwrap.pack(padx=20, pady=4, fill="both")
        sb = ttk.Scrollbar(lbwrap, orient="vertical")
        lb = tk.Listbox(lbwrap, width=40, height=min(12, len(others)),
                        yscrollcommand=sb.set, font=("Segoe UI", 9),
                        selectbackground=SELECT_BLUE, activestyle="none")
        sb.config(command=lb.yview)
        sb.pack(side="right", fill="y")
        lb.pack(side="left", fill="both", expand=True)
        for f in others:
            lb.insert("end", f)
        lb.selection_set(0)
        result = {"val": None}

        def ok():
            sel = lb.curselection()
            if sel:
                result["val"] = others[sel[0]]
            dlg.destroy()

        def cancel():
            dlg.destroy()

        lb.bind("<Double-Button-1>", lambda e: ok())
        bwrap = tk.Frame(dlg, bg=BG)
        bwrap.pack(pady=12)
        tk.Button(bwrap, text="Add to this PDF", bg="white", relief="flat",
                  cursor="hand2", padx=12, pady=4, command=ok).pack(
                      side="left", padx=4)
        tk.Button(bwrap, text="Cancel", bg=CANCEL_BG, relief="flat",
                  cursor="hand2", padx=12, pady=4, command=cancel).pack(
                      side="left", padx=4)
        dlg.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - dlg.winfo_width()) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - dlg.winfo_height()) // 2
        dlg.geometry(f"+{x}+{y}")
        self.root.wait_window(dlg)
        return result["val"]

    def _offer_remove(self, pages, dest_name):
        nums = ", ".join(str(p + 1) for p in pages)
        if messagebox.askyesno(
                "Remove from this file?",
                f"Page(s) {nums} were added to {dest_name}.\n\n"
                "Remove them from the current file now?\n"
                "(The current file will be saved.)"):
            for p in reversed(pages):
                self.doc.delete_page(p)
                del self.orig_nums[p]
            try:
                tmp = self.current_pdf + ".tmp"
                self.doc.save(tmp)
                self.doc.close()
                os.replace(tmp, self.current_pdf)
                self.doc = fitz.open(self.current_pdf)
                self.dirty = False
            except Exception as e:
                messagebox.showerror("Could not save", str(e))
            self.selected.clear()
            self.anchor = None
            self.current_page = min(self.current_page, len(self.doc) - 1)
            self.render_page_thumbnails()
            self.show_page(self.current_page)
            self._set_status(f"Removed page(s) {nums} from this file.")

    def _reload_keep_selection(self):
        self.load_folder()

    def delete_selected(self):
        if not self.doc:
            return
        if not self.selected:
            messagebox.showinfo(
                "Nothing selected",
                "Click one or more page thumbnails first.\n\n"
                "(Hold Ctrl and click to pick several pages.)")
            return
        if len(self.doc) - len(self.selected) < 1:
            messagebox.showwarning(
                "Cannot delete", "A PDF must keep at least one page.")
            return
        pages = sorted(self.selected)
        label = "page" if len(pages) == 1 else "pages"
        nums = ", ".join(str(p + 1) for p in pages)
        if not messagebox.askyesno(
                "Delete pages",
                f"Delete {label} {nums}?\n\nThe file on disk is not changed "
                "until you click Save."):
            return
        for p in reversed(pages):
            self.doc.delete_page(p)
            del self.orig_nums[p]
        self.dirty = True
        self.selected.clear()
        self.current_page = min(self.current_page, len(self.doc) - 1)
        self.render_page_thumbnails()
        self.show_page(self.current_page)
        self._set_status(f"Deleted {label} {nums}. Remember to Save.")

    def save(self):
        if not self.doc:
            return
        if not messagebox.askyesno(
                "Save",
                f"Overwrite the original file?\n\n"
                f"{os.path.basename(self.current_pdf)}\n\n"
                "Choose 'No' to keep the original and save a copy instead."):
            return self.save_as()
        self._save_over()

    def _save_over(self):
        try:
            tmp = self.current_pdf + ".tmp"
            self.doc.save(tmp)
            self.doc.close()
            os.replace(tmp, self.current_pdf)
            self.doc = fitz.open(self.current_pdf)
            self.dirty = False
            self._rerender_keep_scroll()
            self._set_status("Saved.")
        except Exception as e:
            messagebox.showerror("Could not save", str(e))

    # ---------- print ----------

    def print_doc(self):
        if not self.doc:
            return
        n = len(self.doc)
        sel = sorted(self.selected)
        dlg = tk.Toplevel(self.root)
        dlg.title("Print")
        dlg.configure(bg=BG)
        dlg.transient(self.root)
        dlg.grab_set()
        dlg.resizable(False, False)
        tk.Label(dlg, text="Print to your default printer", bg=BG,
                 font=("Segoe UI", 10, "bold")).pack(padx=24, pady=(16, 4))
        tk.Label(dlg, text="Prints the pages in the order shown, "
                 "including unsaved changes.", bg=BG, fg="#33475e",
                 font=("Segoe UI", 9)).pack(padx=24, pady=(0, 12))
        choice = {"val": None}

        def pick(val):
            choice["val"] = val
            dlg.destroy()

        bwrap = tk.Frame(dlg, bg=BG)
        bwrap.pack(padx=20, pady=(0, 16))
        tk.Button(bwrap, text=f"All {n} pages", width=24, bg="white",
                  relief="flat", cursor="hand2", pady=6,
                  command=lambda: pick("all")).pack(pady=3)
        if sel and len(sel) < n:
            word = "page" if len(sel) == 1 else "pages"
            tk.Button(bwrap, text=f"Selected {word} only ({len(sel)})",
                      width=24, bg="white", relief="flat", cursor="hand2",
                      pady=6, command=lambda: pick("sel")).pack(pady=3)
        tk.Button(bwrap, text="Cancel", width=12, bg=CANCEL_BG,
                  relief="flat", cursor="hand2", pady=4,
                  command=lambda: pick(None)).pack(pady=(8, 0))
        dlg.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - dlg.winfo_width()) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - dlg.winfo_height()) // 2
        dlg.geometry(f"+{x}+{y}")
        self.root.wait_window(dlg)
        if not choice["val"]:
            return
        pages = sel if choice["val"] == "sel" else list(range(n))
        try:
            # print from a temp copy so unsaved changes are included and
            # the original file is never touched
            base = os.path.splitext(os.path.basename(self.current_pdf))[0]
            fd, tmp = tempfile.mkstemp(prefix=f"{base} - print ",
                                       suffix=".pdf")
            os.close(fd)
            out = fitz.open()
            for p in pages:
                out.insert_pdf(self.doc, from_page=p, to_page=p)
            out.save(tmp)
            out.close()
            if sys.platform.startswith("win"):
                os.startfile(tmp, "print")
            else:
                subprocess.run(["lp", tmp], check=True)
        except Exception as e:
            messagebox.showerror(
                "Could not print",
                f"{e}\n\nOn Windows, printing uses your default PDF program "
                "(Adobe Reader works well). Make sure one is installed.")
            return
        word = "page" if len(pages) == 1 else "pages"
        self._set_status(f"Sent {len(pages)} {word} to the printer.")

    def save_as(self):
        if not self.doc:
            return
        base, ext = os.path.splitext(os.path.basename(self.current_pdf))
        path = filedialog.asksaveasfilename(
            title="Save a Copy", defaultextension=".pdf",
            initialfile=f"{base} - copy{ext}",
            initialdir=self.folder,
            filetypes=[("PDF files", "*.pdf")])
        if not path:
            return
        try:
            self.doc.save(path)
            self.dirty = False
            self._set_status(f"Saved a copy: {os.path.basename(path)}")
            if os.path.dirname(path) == self.folder:
                self.load_folder()
        except Exception as e:
            messagebox.showerror("Could not save", str(e))

    def zoom_in(self):
        if self.doc:
            self.zoom = min(self.zoom * 1.25, 6.0)
            self.show_page(self.current_page)

    def zoom_out(self):
        if self.doc:
            self.zoom = max(self.zoom / 1.25, 0.2)
            self.show_page(self.current_page)

    def zoom_fit(self):
        if not self.doc:
            return
        page = self.doc[self.current_page]
        avail_h = self.page_canvas.winfo_height() or 600
        self.zoom = max(0.2, min(6.0, avail_h / (page.rect.height * 2.0)))
        self.show_page(self.current_page)

    def _clear_pages(self):
        if self._thumb_job is not None:
            self.root.after_cancel(self._thumb_job)
            self._thumb_job = None
        for w in self.thumb_frame.winfo_children():
            w.destroy()
        self.page_thumb_images.clear()
        self.page_thumb_widgets = []
        self.page_canvas.delete("all")
        if self.doc:
            self.doc.close()
        self.doc = None
        self.current_pdf = None
        self.selected.clear()

    def _set_status(self, msg=None):
        if not self.doc:
            if self.folder:
                return
            self.status.config(text="Open a folder of PDFs to begin.")
            return
        name = os.path.basename(self.current_pdf)
        flag = "   \u2022  UNSAVED CHANGES" if self.dirty else ""
        base = (f"{name}    Page {self.current_page + 1} of {len(self.doc)}"
                f"    Zoom {int(self.zoom * 100)}%{flag}")
        self.status.config(text=(msg + "    |    " + base) if msg else base)

    def _confirm_discard(self):
        if self.dirty:
            return messagebox.askyesno(
                "Unsaved changes",
                "You have unsaved changes to this PDF. Continue anyway "
                "and lose them?")
        return True

    def on_close(self):
        if self.dirty and not messagebox.askyesno(
                "Unsaved changes", "Quit without saving your changes?"):
            return
        if self._thumb_job is not None:
            self.root.after_cancel(self._thumb_job)
        if self._strip_job is not None:
            self.root.after_cancel(self._strip_job)
        if self.doc:
            self.doc.close()
        self.root.destroy()


def main():
    root = tk.Tk()
    PDFFolderViewer(root)
    root.mainloop()


if __name__ == "__main__":
    main()

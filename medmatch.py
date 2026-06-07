import csv
from dataclasses import dataclass
import os
import tkinter as tk
from tkinter import ttk


# --- Theme Constants ---
COLOR_BG          = "#F8FAFC"
COLOR_PRIMARY     = "#1E3A5F"
COLOR_GREEN       = "#16A34A"
COLOR_AMBER       = "#D97706"
COLOR_CARD_BG     = "#FFFFFF"
COLOR_BORDER      = "#E2E8F0"
COLOR_TEXT_MUTED  = "#64748B"
COLOR_BADGE_BG    = "#DCFCE7"
COLOR_ERROR_BG    = "#FEE2E2"

FONT_HEADING      = ("Segoe UI", 11, "bold")
FONT_BODY         = ("Segoe UI", 10)
FONT_MUTED        = ("Segoe UI", 9)
FONT_BADGE        = ("Segoe UI", 8, "bold")

PADDING_CARD      = 10
PADDING_OUTER     = 16
MIN_COLUMN_WIDTH  = 300


@dataclass(frozen=True)
class Medicine:
    brand_name:   str
    generic_name: str
    manufacturer: str
    price_pkr:    float
    quantity:     int


medicine_db: list[Medicine] = []
parse_warnings: list[str] = []


def normalize_manufacturer(value: str) -> str:
    """Return 'Unknown Manufacturer' if value is blank; otherwise return stripped value."""
    stripped = value.strip()
    return "Unknown Manufacturer" if stripped == "" else stripped


def parse_row(row_number: int, row: dict) -> "Medicine | None":
    """Parse a CSV row dict into a Medicine instance.

    Returns None (and appends a warning) if any required field is missing or invalid.
    quantity defaults to 0 if missing, empty, or non-numeric.
    """
    # Strip all string fields
    brand_name   = str(row.get("brand_name",   "")).strip()
    generic_name = str(row.get("generic_name", "")).strip()
    manufacturer = str(row.get("manufacturer", "")).strip()
    price_raw    = str(row.get("price_pkr",    "")).strip()
    quantity_raw = str(row.get("quantity",      "")).strip()

    # Validate required: brand_name
    if not brand_name:
        parse_warnings.append(
            f"Row {row_number}: skipped — 'brand_name' is empty or missing"
        )
        return None

    # Validate required: generic_name
    if not generic_name:
        parse_warnings.append(
            f"Row {row_number}: skipped — 'generic_name' is empty or missing"
        )
        return None

    # Validate required: price_pkr (must convert to float and be >= 0)
    if not price_raw:
        parse_warnings.append(
            f"Row {row_number}: skipped — 'price_pkr' is empty or missing"
        )
        return None
    try:
        price_pkr = float(price_raw)
    except ValueError:
        parse_warnings.append(
            f"Row {row_number}: skipped — 'price_pkr' is not a valid number (got {price_raw!r})"
        )
        return None
    if price_pkr < 0:
        parse_warnings.append(
            f"Row {row_number}: skipped — 'price_pkr' must be >= 0 (got {price_pkr})"
        )
        return None

    # Parse quantity; default to 0 if missing, empty, or non-numeric
    try:
        quantity = int(quantity_raw) if quantity_raw else 0
    except ValueError:
        quantity = 0

    # Normalise manufacturer
    manufacturer = normalize_manufacturer(manufacturer)

    return Medicine(
        brand_name=brand_name,
        generic_name=generic_name,
        manufacturer=manufacturer,
        price_pkr=price_pkr,
        quantity=quantity,
    )


REQUIRED_COLUMNS = {"brand_name", "generic_name", "manufacturer", "price_pkr", "quantity"}


def load_csv(path: str) -> tuple[list[Medicine], list[str]]:
    """Load medicines from a CSV file at *path*.

    Returns (medicines, warnings) where:
      - medicines is a list of successfully parsed Medicine instances
      - warnings is a copy of all parse warnings accumulated during this load

    Raises:
      FileNotFoundError  — if *path* does not exist
      OSError            — if the file cannot be read (permissions, encoding, etc.)
      ValueError         — if any required column is absent from the CSV header
    """
    global parse_warnings
    parse_warnings.clear()

    try:
        file = open(path, encoding="utf-8-sig", newline="")
    except FileNotFoundError:
        raise
    except OSError as exc:
        raise OSError(f"Cannot read '{path}': {exc}") from exc

    with file:
        reader = csv.DictReader(file)

        # DictReader populates fieldnames on first access (when the file is read).
        # Access it now so we can validate the header before iterating rows.
        header = set(reader.fieldnames or [])
        missing = REQUIRED_COLUMNS - header
        if missing:
            missing_list = ", ".join(sorted(missing))
            raise ValueError(
                f"CSV file '{path}' is missing required column(s): {missing_list}"
            )

        medicines: list[Medicine] = []
        row_number = 2  # Row 1 is the header

        for row in reader:
            medicine = parse_row(row_number, row)
            if medicine is not None:
                medicines.append(medicine)
            row_number += 1

    # Return a snapshot copy of the warnings collected during this load
    warnings = list(parse_warnings)
    return (medicines, warnings)


# ---------------------------------------------------------------------------
# Business Logic Layer (Tasks 4.1 – 4.5)
# ---------------------------------------------------------------------------

def format_price(price: float) -> str:
    """Return a human-readable price string.

    Example: format_price(125.5) → '125.50 PKR'
    Requirements: 7.5
    """
    return f"{price:.2f} PKR"


def price_difference(selected_price: float, alternative_price: float) -> float:
    """Return how much cheaper the alternative is compared to the selected medicine.

    Returns selected_price - alternative_price (positive when alternative is cheaper).
    Requirements: 4.5
    """
    return selected_price - alternative_price


def search_medicines(query: str, db: list[Medicine]) -> list[Medicine]:
    """Search *db* for medicines whose brand_name contains *query* (case-insensitive).

    Returns [] when query is empty or whitespace-only.
    Pure function; no side effects.
    Requirements: 2.1, 2.2, 2.3, 2.6, 2.7
    """
    if not query or not query.strip():
        return []
    q = query.strip().lower()
    return [m for m in db if q in m.brand_name.lower()]


def find_alternatives(selected: Medicine, db: list[Medicine]) -> list[Medicine]:
    """Return cheaper, in-stock medicines that share the same generic formula.

    Filters db to records where:
      - generic_name matches selected.generic_name (case-insensitive)
      - price_pkr < selected.price_pkr
      - quantity > 0
      - the record is not the same object as selected

    Returns the filtered list sorted ascending by price_pkr.
    Returns [] if selected.price_pkr is not a valid positive float (i.e., <= 0).
    Pure function; no side effects.
    Requirements: 4.1, 4.2, 4.4, 11.1, 11.2, 11.4
    """
    try:
        if selected.price_pkr <= 0:
            return []
    except (TypeError, ValueError):
        return []

    selected_generic = selected.generic_name.lower()

    alternatives = [
        m for m in db
        if m is not selected
        and m.generic_name.lower() == selected_generic
        and m.price_pkr < selected.price_pkr
        and m.quantity > 0
    ]
    return sorted(alternatives, key=lambda m: m.price_pkr)


def best_price_indices(alternatives: list[Medicine]) -> list[int]:
    """Return the indices of all medicines tied for the lowest price.

    Returns [] if alternatives is empty.
    Pure function.
    Requirements: 10.1, 10.3, 10.5
    """
    if not alternatives:
        return []
    min_price = min(m.price_pkr for m in alternatives)
    return [i for i, m in enumerate(alternatives) if m.price_pkr == min_price]


# ---------------------------------------------------------------------------
# UI Layer — ErrorBanner (Task 6.2)
# ---------------------------------------------------------------------------

class ErrorBanner(tk.Label):
    """A red-background label that displays a load-error message.

    Shown in MainWindow when CSV fails to load (FileNotFoundError, OSError,
    or ValueError from a missing header).

    Requirements: 1.3, 1.4, 5.5
    """

    def __init__(self, parent: tk.Widget, message: str) -> None:
        super().__init__(
            parent,
            text=message,
            background=COLOR_ERROR_BG,
            foreground=COLOR_PRIMARY,
            font=FONT_BODY,
            wraplength=600,
            justify="left",
            padx=PADDING_OUTER,
            pady=PADDING_CARD,
        )


# ---------------------------------------------------------------------------
# UI Layer — ResultsPanel (Task 6.3)
# ---------------------------------------------------------------------------

class ResultsPanel(tk.Frame):
    """Two-column results area: left for the searched medicine, right for alternatives.

    Requirements: 3.2, 4.3, 7.1
    """

    def __init__(self, parent: tk.Widget, db: "list[Medicine]") -> None:
        super().__init__(parent, background=COLOR_BG)
        self._db = db

        # Configure two equal columns, each with a minimum width
        self.columnconfigure(0, weight=1, minsize=MIN_COLUMN_WIDTH)
        self.columnconfigure(1, weight=1, minsize=MIN_COLUMN_WIDTH)

        # --- Column headings ---
        tk.Label(
            self,
            text="Searched Medicine",
            font=FONT_HEADING,
            foreground=COLOR_PRIMARY,
            background=COLOR_BG,
            anchor="w",
            padx=PADDING_OUTER,
            pady=PADDING_CARD,
        ).grid(row=0, column=0, sticky="ew")

        tk.Label(
            self,
            text="Cheaper Alternatives",
            font=FONT_HEADING,
            foreground=COLOR_PRIMARY,
            background=COLOR_BG,
            anchor="w",
            padx=PADDING_OUTER,
            pady=PADDING_CARD,
        ).grid(row=0, column=1, sticky="ew")

        # --- Content frames ---
        self._left_frame = tk.Frame(self, background=COLOR_BG)
        self._left_frame.grid(row=1, column=0, sticky="nsew", padx=PADDING_OUTER)
        self._left_frame.columnconfigure(0, weight=1, minsize=MIN_COLUMN_WIDTH)

        self._right_frame = tk.Frame(self, background=COLOR_BG)
        self._right_frame.grid(row=1, column=1, sticky="nsew", padx=PADDING_OUTER)
        self._right_frame.columnconfigure(0, weight=1, minsize=MIN_COLUMN_WIDTH)

        self.rowconfigure(1, weight=1)

    def show_medicine(self, medicine: "Medicine") -> None:
        """Render a MedicineCard for *medicine* and its alternatives.

        Clears both frames, renders MedicineCard in _left_frame, calls
        find_alternatives, renders AlternativesPanel in _right_frame.

        Requirements: 2.4, 3.1, 4.1, 4.2, 7.3, 7.4
        """
        self.clear()

        # Left frame: medicine card
        card = MedicineCard(self._left_frame, medicine)
        card.pack(fill="x", padx=0, pady=(0, PADDING_CARD))

        # Right frame: alternatives panel
        alternatives = find_alternatives(medicine, self._db)
        panel = AlternativesPanel(self._right_frame, alternatives, medicine.price_pkr)
        panel.pack(fill="both", expand=True)

    def show_picklist(self, matches: "list[Medicine]") -> None:
        """Render a pick-list of *matches* in the left frame.

        Renders a tk.Listbox listing medicine brand names; on <<ListboxSelect>>
        calls show_medicine with the selected medicine.

        Requirements: 2.5, 7.3, 7.4
        """
        self.clear()

        listbox = tk.Listbox(
            self._left_frame,
            font=FONT_BODY,
            foreground=COLOR_PRIMARY,
            background=COLOR_CARD_BG,
            selectbackground=COLOR_PRIMARY,
            selectforeground=COLOR_CARD_BG,
            highlightbackground=COLOR_BORDER,
            highlightthickness=1,
            relief="flat",
            activestyle="none",
        )
        listbox.pack(fill="both", expand=True)

        for medicine in matches:
            listbox.insert(tk.END, medicine.brand_name)

        def _on_select(event=None):
            selection = listbox.curselection()
            if selection:
                index = selection[0]
                self.show_medicine(matches[index])

        listbox.bind("<<ListboxSelect>>", _on_select)

    def clear(self) -> None:
        """Destroy all child widgets in both content frames.

        Requirements: 2.6, 7.4
        """
        for widget in self._left_frame.winfo_children():
            widget.destroy()
        for widget in self._right_frame.winfo_children():
            widget.destroy()


# ---------------------------------------------------------------------------
# UI Layer — SearchBar placeholder (Task 6.4 dependency; fully implemented in 7.1)
# ---------------------------------------------------------------------------

class SearchBar(tk.Frame):
    """Live search bar with 50 ms debounce.

    Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 7.4
    """

    def __init__(self, parent, db, results_panel):
        super().__init__(parent, background=COLOR_BG)
        self._db = db
        self._results_panel = results_panel
        self._after_id = None

        self._entry = ttk.Entry(self, font=FONT_BODY)
        self._entry.pack(fill="x", padx=PADDING_OUTER, pady=PADDING_CARD)
        self._entry.bind("<KeyRelease>", self._on_key_release)

    def _on_key_release(self, event=None):
        """Debounce: cancel previous pending callback, schedule new one."""
        if self._after_id is not None:
            self.after_cancel(self._after_id)
        self._after_id = self.after(50, self._run_search)

    def _run_search(self):
        self._after_id = None
        query = self._entry.get()
        if not query or not query.strip():
            self._results_panel.clear()
            return
        matches = search_medicines(query, self._db)
        if len(matches) == 0:
            self._results_panel.clear()
            # Show "No results found" in left column
            for widget in self._results_panel._left_frame.winfo_children():
                widget.destroy()
            tk.Label(
                self._results_panel._left_frame,
                text="No results found",
                font=FONT_BODY,
                foreground=COLOR_TEXT_MUTED,
                background=COLOR_BG,
            ).pack(anchor="w", padx=PADDING_CARD, pady=PADDING_CARD)
        elif len(matches) == 1:
            self._results_panel.show_medicine(matches[0])
        else:
            self._results_panel.show_picklist(matches)

    def disable(self):
        """Disable the search entry widget."""
        self._entry.configure(state="disabled")


# ---------------------------------------------------------------------------
# UI Layer — MedicineCard (Task 8.1)
# ---------------------------------------------------------------------------

class MedicineCard(tk.Frame):
    """Read-only display widget for one medicine in the left column.

    Displays brand_name (bold, navy), generic_name, manufacturer (muted),
    and formatted price — in that order.

    Requirements: 3.1, 9.1, 9.2
    """

    def __init__(self, parent: tk.Widget, medicine: Medicine) -> None:
        super().__init__(
            parent,
            background=COLOR_CARD_BG,
            highlightbackground=COLOR_BORDER,
            highlightthickness=1,
            padx=PADDING_CARD,
            pady=PADDING_CARD,
        )

        # Brand name — bold, primary navy
        tk.Label(
            self,
            text=medicine.brand_name,
            font=FONT_HEADING,
            foreground=COLOR_PRIMARY,
            background=COLOR_CARD_BG,
            anchor="w",
        ).pack(fill="x", pady=(0, 2))

        # Generic name / formula
        tk.Label(
            self,
            text=medicine.generic_name,
            font=FONT_BODY,
            foreground=COLOR_PRIMARY,
            background=COLOR_CARD_BG,
            anchor="w",
        ).pack(fill="x", pady=(0, 2))

        # Manufacturer — muted style
        tk.Label(
            self,
            text=medicine.manufacturer,
            font=FONT_MUTED,
            foreground=COLOR_TEXT_MUTED,
            background=COLOR_CARD_BG,
            anchor="w",
        ).pack(fill="x", pady=(0, 2))

        # Price
        tk.Label(
            self,
            text=format_price(medicine.price_pkr),
            font=FONT_BODY,
            foreground=COLOR_PRIMARY,
            background=COLOR_CARD_BG,
            anchor="w",
        ).pack(fill="x")


# ---------------------------------------------------------------------------
# UI Layer — AlternativeCard (Task 8.2)
# ---------------------------------------------------------------------------

class AlternativeCard(tk.Frame):
    """Card widget for one cheaper alternative in the right column.

    Shows an optional BEST PRICE badge, brand name, manufacturer, price,
    and the price-difference savings line.

    Requirements: 4.2, 4.5, 9.2, 10.1, 10.2, 10.3, 10.5
    """

    def __init__(
        self,
        parent: tk.Widget,
        medicine: Medicine,
        is_best: bool,
        price_diff: float,
    ) -> None:
        super().__init__(
            parent,
            background=COLOR_CARD_BG,
            highlightbackground=COLOR_BORDER,
            highlightthickness=1,
            padx=PADDING_CARD,
            pady=PADDING_CARD,
        )

        # BEST PRICE badge — only when this card has the lowest price
        if is_best:
            tk.Label(
                self,
                text="BEST PRICE",
                font=FONT_BADGE,
                foreground=COLOR_GREEN,
                background=COLOR_BADGE_BG,
                padx=4,
                pady=2,
                anchor="w",
            ).pack(fill="x", pady=(0, 4))

        # Brand name
        tk.Label(
            self,
            text=medicine.brand_name,
            font=FONT_HEADING,
            foreground=COLOR_PRIMARY,
            background=COLOR_CARD_BG,
            anchor="w",
        ).pack(fill="x", pady=(0, 2))

        # Manufacturer — muted
        tk.Label(
            self,
            text=medicine.manufacturer,
            font=FONT_MUTED,
            foreground=COLOR_TEXT_MUTED,
            background=COLOR_CARD_BG,
            anchor="w",
        ).pack(fill="x", pady=(0, 2))

        # Price
        tk.Label(
            self,
            text=format_price(medicine.price_pkr),
            font=FONT_BODY,
            foreground=COLOR_PRIMARY,
            background=COLOR_CARD_BG,
            anchor="w",
        ).pack(fill="x", pady=(0, 2))

        # Low-stock warning — amber, shown only when quantity is 1–5
        if 0 < medicine.quantity <= 5:
            tk.Label(
                self,
                text="⚠ Low stock",
                font=FONT_MUTED,
                foreground=COLOR_AMBER,
                background=COLOR_CARD_BG,
                anchor="w",
            ).pack(fill="x", pady=(0, 2))

        # Savings line — green
        tk.Label(
            self,
            text=f"Rs. {price_diff:.2f} cheaper",
            font=FONT_BODY,
            foreground=COLOR_GREEN,
            background=COLOR_CARD_BG,
            anchor="w",
        ).pack(fill="x")


# ---------------------------------------------------------------------------
# UI Layer — AlternativesPanel (Task 8.3)
# ---------------------------------------------------------------------------

class AlternativesPanel(tk.Frame):
    """Scrollable panel that lists zero or more AlternativeCard widgets.

    Uses a tk.Canvas + tk.Scrollbar + inner tk.Frame pattern so the list
    can scroll when there are many alternatives.

    Constructor:
        parent            — parent widget
        alternatives      — list of Medicine objects (already filtered/sorted)
        selected_price    — price of the selected medicine (for price_diff calc)

    Requirements: 4.4, 7.2, 10.4
    """

    def __init__(
        self,
        parent: tk.Widget,
        alternatives: list,
        selected_price: float,
    ) -> None:
        super().__init__(parent, background=COLOR_BG)

        if not alternatives:
            tk.Label(
                self,
                text="No cheaper alternatives found",
                font=FONT_BODY,
                foreground=COLOR_TEXT_MUTED,
                background=COLOR_BG,
                anchor="w",
                padx=PADDING_CARD,
                pady=PADDING_CARD,
            ).pack(fill="x")
            return

        # Determine which indices share the best (lowest) price
        best_indices = set(best_price_indices(alternatives))

        # --- Scrollable area: canvas + scrollbar ---
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        canvas = tk.Canvas(self, background=COLOR_BG, highlightthickness=0)
        scrollbar = tk.Scrollbar(self, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        inner_frame = tk.Frame(canvas, background=COLOR_BG)
        inner_frame.columnconfigure(0, weight=1)

        window_id = canvas.create_window((0, 0), window=inner_frame, anchor="nw")

        def _on_inner_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))

        def _on_canvas_configure(event):
            canvas.itemconfig(window_id, width=event.width)

        inner_frame.bind("<Configure>", _on_inner_configure)
        canvas.bind("<Configure>", _on_canvas_configure)

        # Render one AlternativeCard per alternative
        for i, medicine in enumerate(alternatives):
            diff = price_difference(selected_price, medicine.price_pkr)
            card = AlternativeCard(
                inner_frame,
                medicine=medicine,
                is_best=(i in best_indices),
                price_diff=diff,
            )
            card.pack(fill="x", padx=PADDING_CARD, pady=(0, PADDING_CARD))


# ---------------------------------------------------------------------------
# UI Layer — MainWindow (Task 6.4)
# ---------------------------------------------------------------------------

class MainWindow(tk.Tk):
    """Root application window.

    Loads the CSV at startup; shows an ErrorBanner and disables the search bar
    if loading fails for any reason.

    Requirements: 1.1, 1.2, 1.3, 1.4
    """

    def __init__(self) -> None:
        super().__init__()
        self.title("MedMatch")
        self.configure(background=COLOR_BG)

        # Attempt to load the CSV from the same directory as this script
        csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "medicines.csv")
        db: list[Medicine] = []
        load_error: str | None = None

        try:
            db, _warnings = load_csv(csv_path)
        except FileNotFoundError:
            load_error = (
                f"medicines.csv not found.\nExpected path: {csv_path}\n"
                "Please place the file alongside medmatch.py and restart."
            )
        except OSError as exc:
            load_error = f"Could not read medicines.csv:\n{exc}"
        except ValueError as exc:
            load_error = f"medicines.csv has an invalid format:\n{exc}"

        # Show error banner if loading failed
        if load_error is not None:
            ErrorBanner(self, load_error).pack(
                fill="x", padx=PADDING_OUTER, pady=(PADDING_OUTER, 0)
            )

        # Build child widgets
        self._results_panel = ResultsPanel(self, db)
        self._search_bar = SearchBar(self, db, self._results_panel)

        # Pack search bar above results panel
        self._search_bar.pack(fill="x", padx=0, pady=(PADDING_OUTER, 0))
        self._results_panel.pack(fill="both", expand=True, padx=0, pady=PADDING_OUTER)

        # Disable search if CSV could not be loaded
        if load_error is not None:
            self._search_bar.disable()


if __name__ == "__main__":
    app = MainWindow()
    app.mainloop()

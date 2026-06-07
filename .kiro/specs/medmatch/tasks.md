# Implementation Plan: MedMatch

## Overview

Build a single-file Python/Tkinter desktop application (`medmatch.py`) that lets pharmacy staff search for medicines and instantly view cheaper alternatives sharing the same active formula. Implementation proceeds bottom-up: seed data → data layer → business logic → UI shell → search bar → cards & panels → polish → tests.

## Tasks

- [x] 1. Create medicines.csv seed data
  - [x] 1.1 Write medicines.csv with 40 medicine records
    - Create `medicines.csv` in the project root with header row: `brand_name,generic_name,manufacturer,price_pkr,quantity`
    - Include medicines sold in the Pakistani market with realistic PKR prices
    - Cover all five required categories: Analgesic, Antibiotic, Antacid, Antihistamine, Vitamin
    - Provide at least 3 different brand names per active formula (generic_name) so `find_alternatives()` has meaningful data to return
    - Vary quantities: some records `quantity=0` to verify zero-stock filtering, most `quantity > 0`
    - Vary prices within each formula group so the BEST PRICE badge logic is exercised
    - _Requirements: 5.1, 5.4, 11.1, 11.3_

- [x] 2. Implement the data model and CSV layer
  - [x] 2.1 Define the `Medicine` dataclass and module-level globals
    - Create `medmatch.py`; add the frozen `Medicine` dataclass with fields: `brand_name: str`, `generic_name: str`, `manufacturer: str`, `price_pkr: float`, `quantity: int`
    - Add module-level `medicine_db: list[Medicine] = []` and `parse_warnings: list[str] = []`
    - _Requirements: 5.2, 6.1_

  - [x] 2.2 Implement `normalize_manufacturer(value: str) -> str`
    - Return `"Unknown Manufacturer"` if `value.strip()` is empty; otherwise return `value.strip()`
    - _Requirements: 9.3_

  - [x] 2.3 Implement `parse_row(row_number: int, row: dict) -> Medicine | None`
    - Strip all string fields; pass `manufacturer` through `normalize_manufacturer()`
    - Skip row (return `None`) if `brand_name`, `generic_name`, or `price_pkr` is empty or invalid; append a warning identifying the row number and offending field
    - Validate `price_pkr` converts to `float` and is `>= 0`; skip if not
    - Parse `quantity` as `int`; default to `0` if missing, empty, or non-numeric
    - _Requirements: 5.3, 6.2, 11.3_

  - [x] 2.4 Implement `load_csv(path: str) -> tuple[list[Medicine], list[str]]`
    - Open with `utf-8-sig` encoding; use `csv.DictReader`
    - Raise `FileNotFoundError` if file missing; raise `OSError` on permission/encoding errors
    - Raise `ValueError` if any required column (`brand_name`, `generic_name`, `manufacturer`, `price_pkr`, `quantity`) is absent from the header
    - Call `parse_row()` for every data row; collect valid `Medicine` instances and accumulated warnings
    - Return `(medicines, warnings)`
    - _Requirements: 5.2, 5.4, 5.5, 1.3, 1.4_

- [x] 3. Checkpoint — CSV layer
  - Verify `load_csv("medicines.csv")` returns 40 `Medicine` objects with no unexpected warnings when run against the seed file.

- [x] 4. Implement the business logic layer
  - [x] 4.1 Implement `format_price(price: float) -> str`
    - Return `f"{price:.2f} PKR"`
    - _Requirements: 7.5_

  - [x] 4.2 Implement `price_difference(selected_price: float, alternative_price: float) -> float`
    - Return `selected_price - alternative_price`
    - _Requirements: 4.5_

  - [x] 4.3 Implement `search_medicines(query: str, db: list[Medicine]) -> list[Medicine]`
    - Return `[]` if `query` is empty or whitespace-only
    - Return all medicines whose `brand_name` contains `query` as a case-insensitive substring
    - Pure function; no side effects
    - _Requirements: 2.1, 2.2, 2.3, 2.6, 2.7_

  - [x] 4.4 Implement `find_alternatives(selected: Medicine, db: list[Medicine]) -> list[Medicine]`
    - Filter `db` to records where `generic_name` matches case-insensitively, `price_pkr < selected.price_pkr`, and `quantity > 0`, and record is not `selected`
    - Return list sorted ascending by `price_pkr`
    - Return `[]` if `selected.price_pkr` is not a valid positive float
    - Pure function; no side effects
    - _Requirements: 4.1, 4.2, 4.4, 11.1, 11.2, 11.4_

  - [x] 4.5 Implement `best_price_indices(alternatives: list[Medicine]) -> list[int]`
    - Return `[]` if `alternatives` is empty
    - Return all indices `i` where `alternatives[i].price_pkr == min(a.price_pkr for a in alternatives)`
    - Pure function
    - _Requirements: 10.1, 10.3, 10.5_

- [x] 5. Checkpoint — business logic
  - Run quick manual checks: `search_medicines("Pan", medicine_db)` returns paracetamol brands; `find_alternatives(panadol, medicine_db)` returns cheaper in-stock paracetamols sorted ascending; `best_price_indices([...])` marks the correct indices.

- [x] 6. Build the Tkinter UI shell (MainWindow + ResultsPanel layout)
  - [x] 6.1 Define all theme constants at the top of `medmatch.py`
    - Add `COLOR_BG`, `COLOR_PRIMARY`, `COLOR_GREEN`, `COLOR_AMBER`, `COLOR_CARD_BG`, `COLOR_BORDER`, `COLOR_TEXT_MUTED`, `COLOR_BADGE_BG`, `COLOR_ERROR_BG`
    - Add `FONT_HEADING`, `FONT_BODY`, `FONT_MUTED`, `FONT_BADGE`
    - Add `PADDING_CARD = 10`, `PADDING_OUTER = 16`, `MIN_COLUMN_WIDTH = 300`
    - _Requirements: 7.1_

  - [x] 6.2 Implement `ErrorBanner(tk.Label)`
    - Red-background label (`COLOR_ERROR_BG`) that wraps a message string
    - Shown in `MainWindow` when CSV fails to load
    - _Requirements: 1.3, 1.4, 5.5_

  - [x] 6.3 Implement `ResultsPanel(tk.Frame)` skeleton
    - Two-column frame: `_left_frame` and `_right_frame`, each with `minwidth=MIN_COLUMN_WIDTH` via `columnconfigure`
    - Add stub methods: `show_medicine(medicine)`, `show_picklist(matches)`, `clear()`
    - Column headings: left "Searched Medicine", right "Cheaper Alternatives" (using `FONT_HEADING`, `COLOR_PRIMARY`)
    - _Requirements: 3.2, 4.3, 7.1_

  - [x] 6.4 Implement `MainWindow(tk.Tk)`
    - Root window: title `"MedMatch"`, background `COLOR_BG`
    - In `__init__`: call `load_csv()`, catch `FileNotFoundError` / `OSError` / `ValueError` → show `ErrorBanner`, disable search bar
    - Construct `SearchBar` and `ResultsPanel` as child widgets; pass `medicine_db` to `SearchBar`
    - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [x] 7. Build the live search bar with debounce
  - [x] 7.1 Implement `SearchBar(tk.Frame)`
    - Contains a single `ttk.Entry`; bind `<KeyRelease>` → `_on_key_release`
    - `_on_key_release`: cancel any pending `after` callback, then call `self.after(50, self._run_search)` (debounce 50 ms)
    - `_run_search`: call `search_medicines(query, db)` then dispatch to `ResultsPanel`:
      - 0 results → `results_panel.clear()` + show "No results found" in left column
      - 1 result → `results_panel.show_medicine(match)`
      - >1 results → `results_panel.show_picklist(matches)`
    - Empty / whitespace query → `results_panel.clear()`
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 7.4_

- [x] 8. Build medicine cards and alternatives panel
  - [x] 8.1 Implement `MedicineCard(tk.Frame)`
    - Display fields in order: `brand_name` (bold, `COLOR_PRIMARY`), `generic_name`, `manufacturer`, `format_price(price_pkr)`
    - Use `FONT_HEADING` for brand name, `FONT_BODY` for formula and price, `FONT_MUTED` + `COLOR_TEXT_MUTED` for manufacturer
    - Internal padding `PADDING_CARD`; background `COLOR_CARD_BG`; border via `highlightbackground=COLOR_BORDER`
    - _Requirements: 3.1, 9.1, 9.2_

  - [x] 8.2 Implement `AlternativeCard(tk.Frame)`
    - Accept `medicine: Medicine`, `is_best: bool`, `price_diff: float`
    - If `is_best` is `True`: render BEST PRICE badge label (`COLOR_GREEN` text on `COLOR_BADGE_BG` background, `FONT_BADGE`)
    - Display: `brand_name`, `manufacturer`, `format_price(price_pkr)`, `f"Rs. {price_diff:.2f} cheaper"` in `COLOR_GREEN`
    - _Requirements: 4.2, 4.5, 9.2, 10.1, 10.2, 10.3, 10.5_

  - [x] 8.3 Implement `AlternativesPanel(tk.Frame)` with scrollable canvas
    - Contain a `tk.Canvas` + vertical `tk.Scrollbar` + inner `tk.Frame` for `AlternativeCard` widgets
    - Render zero or more `AlternativeCard` widgets; call `best_price_indices()` to determine badge assignment
    - If `alternatives` list is empty: show label `"No cheaper alternatives found"`
    - _Requirements: 4.4, 7.2, 10.4_

  - [x] 8.4 Wire `ResultsPanel.show_medicine` and `show_picklist` fully
    - `show_medicine`: destroy existing children in both frames, render `MedicineCard` in `_left_frame`, call `find_alternatives`, render `AlternativesPanel` in `_right_frame`
    - `show_picklist`: render a `tk.Listbox` in `_left_frame`; on `<<ListboxSelect>>` call `show_medicine(selected_medicine)`
    - `clear()`: destroy all child widgets in both frames
    - _Requirements: 2.4, 2.5, 3.1, 4.1, 4.2, 7.3, 7.4_

- [x] 9. Checkpoint — functional UI
  - Launch `python medmatch.py`, type a medicine name, verify left column shows medicine details and right column shows sorted alternatives with BEST PRICE badge on cheapest entry; verify zero-stock medicines are absent from the right column.

- [x] 10. Polish: low-stock warning and entry point
  - [x] 10.1 Add amber low-stock warning to `AlternativeCard`
    - When `medicine.quantity > 0` and `medicine.quantity <= 5` (low-stock threshold), display a `"⚠ Low stock"` label in `COLOR_AMBER` below the price on the alternative card
    - _Requirements: 11.1 (quantity context)_

  - [x] 10.2 Add `if __name__ == "__main__":` entry point
    - Instantiate `MainWindow`, call `mainloop()`
    - Confirm the app launches cleanly from `python medmatch.py`
    - _Requirements: 1.1, 1.2_

- [x] 11. Write property-based tests (Hypothesis)
  - Create `tests/test_properties.py`; configure each test with `@settings(max_examples=100)`
  - Define shared Hypothesis strategies at module level: `medicine_strategy()`, `medicine_list_strategy()`, `query_strategy()`, `price_strategy()`, `manufacturer_strategy()`

  - [x] 11.1 Write property test for search inclusion/exclusion (Property 1)
    - **Property 1: Search Inclusion/Exclusion**
    - **Validates: Requirements 2.3, 2.7**
    - `@given(db=medicine_list_strategy(), query=query_strategy())`: every result must contain `query` case-insensitively; every matching medicine must appear in results

  - [x] 11.2 Write property test for medicine card field presence (Property 2)
    - **Property 2: Medicine Card Renders All Required Fields**
    - **Validates: Requirements 3.1, 9.1, 9.2**
    - `@given(med=medicine_strategy())`: construct a `MedicineCard` (or extract its label texts); assert `brand_name`, `generic_name`, `manufacturer`, and `format_price(price_pkr)` all appear

  - [x] 11.3 Write property test for alternatives query correctness (Property 3)
    - **Property 3: Alternatives Query Correctness**
    - **Validates: Requirements 4.1, 4.2, 4.4, 11.1, 11.2**
    - `@given(selected=medicine_strategy(), db=medicine_list_strategy())`: assert result set equals exact filter predicate; assert result is sorted ascending by price

  - [x] 11.4 Write property test for price difference accuracy (Property 4)
    - **Property 4: Price Difference Is Positive and Accurate**
    - **Validates: Requirements 4.5**
    - For each alternative returned by `find_alternatives`, assert `price_difference(selected.price_pkr, alt.price_pkr) == selected.price_pkr - alt.price_pkr > 0`

  - [x] 11.5 Write property test for CSV round-trip integrity (Property 5)
    - **Property 5: CSV Round-Trip Integrity**
    - **Validates: Requirements 5.2, 6.1, 6.3**
    - `@given(med=medicine_strategy())`: format fields as CSV row string, parse through `parse_row()`, assert identical string fields and numerically equal price

  - [x] 11.6 Write property test for invalid row skipping and warning (Property 6)
    - **Property 6: Invalid Row Is Skipped and Warning Is Logged**
    - **Validates: Requirements 5.3, 6.2**
    - `@given(...)` with generated rows missing/corrupting `brand_name`, `generic_name`, or `price_pkr`: assert `parse_row()` returns `None` and warning contains row number and field name

  - [x] 11.7 Write property test for price formatting consistency (Property 7)
    - **Property 7: Price Formatting Consistency**
    - **Validates: Requirements 7.5**
    - `@given(price=price_strategy())`: assert `format_price(price)` matches `^\d+\.\d{2} PKR$`

  - [x] 11.8 Write property test for manufacturer normalization (Property 8)
    - **Property 8: Manufacturer Normalization**
    - **Validates: Requirements 9.3**
    - `@given(value=manufacturer_strategy())`: assert returns `"Unknown Manufacturer"` iff `value.strip() == ""`; otherwise returns `value.strip()`

  - [x] 11.9 Write property test for best price label accuracy (Property 9)
    - **Property 9: Best Price Label Accuracy**
    - **Validates: Requirements 10.1, 10.3, 10.5**
    - `@given(alts=medicine_list_strategy().filter(lambda l: len(l) > 0))`: assert `best_price_indices` returns exactly the indices with minimum price, non-empty

  - [x] 11.10 Write property test for invalid quantity treated as zero (Property 10)
    - **Property 10: Invalid Quantity Treated as Zero**
    - **Validates: Requirements 11.3, 11.1**
    - `@given(...)` with rows where `quantity` field is missing/empty/non-numeric: assert parsed `Medicine.quantity == 0` and that medicine is absent from `find_alternatives()` results

- [x] 12. Write unit tests (pytest)
  - Create `tests/test_medmatch.py`

  - [x] 12.1 `test_load_csv_missing_file` — assert `FileNotFoundError` raised when path does not exist
    - _Requirements: 1.3_

  - [x] 12.2 `test_load_csv_unreadable` — mock `open` to raise `PermissionError`; assert `OSError` propagates
    - _Requirements: 1.4_

  - [x] 12.3 `test_load_csv_missing_header` — write temp CSV with wrong column names; assert `ValueError` raised
    - _Requirements: 5.5_

  - [x] 12.4 `test_search_empty_query_clears` — assert `search_medicines("", db)` returns `[]`
    - _Requirements: 2.6_

  - [x] 12.5 `test_single_match_shows_details` — build db with one matching medicine; assert `search_medicines` returns that medicine
    - _Requirements: 2.4_

  - [x] 12.6 `test_multiple_matches_shows_picklist` — build db with two matching medicines; assert `search_medicines` returns both
    - _Requirements: 2.5_

  - [x] 12.7 `test_no_alternatives_message` — build db with no cheaper in-stock alternatives; call `find_alternatives`; assert empty list (UI will show the message)
    - _Requirements: 4.4_

  - [x] 12.8 `test_clear_search_resets_panels` — instantiate `MainWindow` headlessly (tk.Tk without mainloop); call `results_panel.clear()`; assert both frames have no children
    - _Requirements: 7.4_

  - [x] 12.9 `test_headings_present` — inspect `ResultsPanel` widget tree; assert "Searched Medicine" and "Cheaper Alternatives" labels exist
    - _Requirements: 3.2, 4.3_

  - [x] 12.10 `test_invalid_price_no_alternatives` — create selected `Medicine` with `price_pkr=0.0`; assert `find_alternatives` returns `[]`
    - _Requirements: 4.6_

  - [x] 12.11 `test_best_price_single_alternative` — build list with one alternative; assert `best_price_indices` returns `[0]`
    - _Requirements: 10.3_

  - [x] 12.12 `test_no_best_price_when_no_alternatives` — assert `best_price_indices([])` returns `[]`
    - _Requirements: 10.4_

- [x] 13. Final checkpoint — all tests pass
  - Run `pytest tests/ -v` and confirm all non-optional and all property tests pass with no errors.
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for a faster MVP; they do not block the application from running.
- All property tests use `@settings(max_examples=100)` and the tag `# Feature: medmatch, Property N: <title>`.
- Checkpoints in tasks 3, 5, 9, and 13 are manual validation gates — they are not automated tests.
- The final distributable is just `medmatch.py` + `medicines.csv`; the `tests/` directory is development-only.
- Theme constants (task 6.1) must be defined before any widget class references them.

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1"] },
    { "id": 1, "tasks": ["2.1"] },
    { "id": 2, "tasks": ["2.2", "2.3"] },
    { "id": 3, "tasks": ["2.4"] },
    { "id": 4, "tasks": ["4.1", "4.2", "4.3", "4.4", "4.5"] },
    { "id": 5, "tasks": ["6.1", "6.2"] },
    { "id": 6, "tasks": ["6.3", "6.4"] },
    { "id": 7, "tasks": ["7.1"] },
    { "id": 8, "tasks": ["8.1", "8.2", "8.3"] },
    { "id": 9, "tasks": ["8.4"] },
    { "id": 10, "tasks": ["10.1", "10.2"] },
    { "id": 11, "tasks": ["11.1", "11.2", "11.3", "11.4", "11.5", "11.6", "11.7", "11.8", "11.9", "11.10"] },
    { "id": 12, "tasks": ["12.1", "12.2", "12.3", "12.4", "12.5", "12.6", "12.7", "12.8", "12.9", "12.10", "12.11", "12.12"] }
  ]
}
```

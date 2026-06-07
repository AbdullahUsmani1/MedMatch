# MedMatch

A desktop application that helps users find cheaper generic alternatives to branded medicines in Pakistan. Built with Python and Tkinter, it loads a local CSV medicine database and lets you search by brand name to instantly see cost-saving alternatives with the same active formula.

---

## Features

- **Live search** — results update as you type (50 ms debounce)
- **Cheaper alternatives** — finds in-stock medicines with the same generic formula at a lower price
- **Best Price badge** — highlights the cheapest alternative(s) at a glance
- **Savings display** — shows how much cheaper each alternative is (in PKR)
- **Low-stock warning** — flags alternatives with 5 or fewer units remaining
- **Graceful error handling** — shows a clear error banner if the CSV is missing or malformed

---

## Project Structure

```
.
├── medmatch.py          # Main application (data model, business logic, UI)
├── medicines.csv        # Medicine database (must be in the same directory)
└── tests/
    ├── test_medmatch.py     # Unit tests (pytest)
    └── test_properties.py   # Property-based tests (Hypothesis)
```

---

## Requirements

- Python 3.10+
- Tkinter (bundled with most Python distributions)
- `pytest` (for running tests)
- `hypothesis` (for property-based tests)

Install test dependencies:

```bash
pip install pytest hypothesis
```

---

## CSV Format

The application reads `medicines.csv` from the same directory as `medmatch.py`. The file must include these exact column headers:

| Column          | Type    | Required | Notes                                    |
|-----------------|---------|----------|------------------------------------------|
| `brand_name`    | string  | Yes      | Cannot be empty                          |
| `generic_name`  | string  | Yes      | Used for matching alternatives           |
| `manufacturer`  | string  | No       | Defaults to `Unknown Manufacturer`       |
| `price_pkr`     | float   | Yes      | Must be a non-negative number            |
| `quantity`      | integer | No       | Defaults to `0` if missing or non-numeric|

Example rows:

```csv
brand_name,generic_name,manufacturer,price_pkr,quantity
Panadol,Paracetamol,GSK Pakistan,45.00,150
Brufen,Ibuprofen,Abbott Pakistan,55.00,120
```

Rows with an empty `brand_name`, `generic_name`, or invalid `price_pkr` are skipped with a warning logged internally.

---

## Running the Application

```bash
python medmatch.py
```

The window will open with a search bar at the top. Type a brand name to search; if there is more than one match a pick-list appears — click an entry to view its details and alternatives.

---

## Running the Tests

Run all tests from the project root:

```bash
pytest
```

Run only the unit tests:

```bash
pytest tests/test_medmatch.py
```

Run only the property-based tests:

```bash
pytest tests/test_properties.py
```

---

## How It Works

### Data Layer

`load_csv(path)` reads the CSV and returns a `(medicines, warnings)` tuple. It raises:
- `FileNotFoundError` — if the file does not exist
- `OSError` — if the file cannot be read
- `ValueError` — if any required column is missing from the header

Each valid row is parsed into a frozen `Medicine` dataclass:

```python
@dataclass(frozen=True)
class Medicine:
    brand_name:   str
    generic_name: str
    manufacturer: str
    price_pkr:    float
    quantity:     int
```

### Business Logic

| Function | Description |
|---|---|
| `search_medicines(query, db)` | Case-insensitive substring match on `brand_name`; returns `[]` for blank queries |
| `find_alternatives(selected, db)` | Returns cheaper, in-stock medicines with the same `generic_name`, sorted by price ascending |
| `best_price_indices(alternatives)` | Returns the indices of all entries tied for the lowest price |
| `price_difference(selected_price, alt_price)` | Returns how much cheaper the alternative is |
| `format_price(price)` | Formats a float as `"125.50 PKR"` |
| `normalize_manufacturer(value)` | Returns `"Unknown Manufacturer"` for blank values |

### UI Layer

| Class | Role |
|---|---|
| `MainWindow` | Root `tk.Tk` window; loads CSV on startup |
| `SearchBar` | Debounced entry widget; drives search and panel updates |
| `ResultsPanel` | Two-column layout: searched medicine (left) / alternatives (right) |
| `MedicineCard` | Displays brand name, generic name, manufacturer, and price |
| `AlternativeCard` | Same as `MedicineCard` plus Best Price badge, low-stock warning, and savings line |
| `AlternativesPanel` | Scrollable container for zero or more `AlternativeCard` widgets |
| `ErrorBanner` | Red label shown when the CSV fails to load |

---

## Test Coverage

### Unit Tests (`test_medmatch.py`)

| Test | Requirement |
|---|---|
| `test_load_csv_missing_file` | FileNotFoundError on missing path |
| `test_load_csv_unreadable` | OSError on unreadable file |
| `test_load_csv_missing_header` | ValueError on wrong CSV columns |
| `test_search_empty_query_clears` | Empty/whitespace query returns `[]` |
| `test_single_match_shows_details` | Exact match returns the correct medicine |
| `test_multiple_matches_shows_picklist` | Multiple matches all returned |
| `test_no_alternatives_message` | No cheaper/in-stock alternatives → empty list |
| `test_clear_search_resets_panels` | `clear()` destroys all child widgets |
| `test_headings_present` | Column headings rendered correctly |
| `test_invalid_price_no_alternatives` | Price of 0.0 → no alternatives |
| `test_best_price_single_alternative` | Single alternative → index `[0]` |
| `test_no_best_price_when_no_alternatives` | Empty list → `[]` |

### Property-Based Tests (`test_properties.py`, via Hypothesis)

| Property | What it verifies |
|---|---|
| Search inclusion/exclusion | Every result contains the query; no results are missed |
| Price difference accuracy | `price_difference` is exact and always positive |
| Alternatives query correctness | Alternatives match all filter criteria and are sorted ascending |
| CSV round-trip integrity | `parse_row` reconstructs a medicine faithfully |
| Medicine card field presence | All four fields are rendered in the card |
| Invalid row skipped and warned | Empty required fields → `None` + warning logged |
| Price formatting consistency | Output always matches `^\d+\.\d{2} PKR$` |
| Manufacturer normalization | Blank → `"Unknown Manufacturer"`, otherwise stripped |
| Best price label accuracy | Indices match all entries tied at the minimum price |
| Invalid quantity treated as zero | Non-numeric quantity → `quantity=0`, excluded from alternatives |

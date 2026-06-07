"""
Unit tests for MedMatch — Tasks 12.1 through 12.5.

Validates:
  12.1 — Req 1.3: FileNotFoundError raised when path does not exist
  12.2 — Req 1.4: OSError propagates when file is unreadable
  12.3 — Req 5.5: ValueError raised when CSV is missing required columns
  12.4 — Req 2.6: search_medicines returns [] for empty/whitespace query
  12.5 — Req 2.4: search_medicines returns exactly the matching medicine
"""

import os
import tempfile
from unittest.mock import patch

import pytest

from medmatch import Medicine, load_csv, search_medicines

# ---------------------------------------------------------------------------
# Tk availability guard — some environments have a broken Tcl/Tk installation.
# A single hidden root is created once at module level and reused by all
# Tk-dependent tests (avoids the cost of repeated Tk init and works around
# partially-broken installations that fail on a second tk.Tk() call).
# ---------------------------------------------------------------------------
_tk_root = None
try:
    import tkinter as tk
    _tk_root = tk.Tk()
    _tk_root.withdraw()
except Exception:
    _tk_root = None

requires_tk = pytest.mark.skipif(_tk_root is None, reason="Tk/Tcl not available on this system")


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def make_med(brand="BrandA", generic="GenA", manufacturer="MfgA", price=100.0, quantity=10):
    return Medicine(
        brand_name=brand,
        generic_name=generic,
        manufacturer=manufacturer,
        price_pkr=price,
        quantity=quantity,
    )


# ---------------------------------------------------------------------------
# 12.1 — Req 1.3: missing file raises FileNotFoundError
# ---------------------------------------------------------------------------

def test_load_csv_missing_file():
    with pytest.raises(FileNotFoundError):
        load_csv("nonexistent_path_xyz.csv")


# ---------------------------------------------------------------------------
# 12.2 — Req 1.4: unreadable file propagates OSError
# ---------------------------------------------------------------------------

def test_load_csv_unreadable():
    with patch("builtins.open", side_effect=PermissionError("Permission denied")):
        with pytest.raises(OSError):
            load_csv("any_path.csv")


# ---------------------------------------------------------------------------
# 12.3 — Req 5.5: wrong column names raise ValueError
# ---------------------------------------------------------------------------

def test_load_csv_missing_header():
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".csv", delete=False, encoding="utf-8"
    ) as f:
        f.write("wrong_col1,wrong_col2\n")
        f.write("val1,val2\n")
        tmp_path = f.name
    try:
        with pytest.raises(ValueError):
            load_csv(tmp_path)
    finally:
        os.unlink(tmp_path)


# ---------------------------------------------------------------------------
# 12.4 — Req 2.6: empty / whitespace query returns []
# ---------------------------------------------------------------------------

def test_search_empty_query_clears():
    db = [make_med("Panadol"), make_med("Disprin")]
    assert search_medicines("", db) == []
    assert search_medicines("   ", db) == []


# ---------------------------------------------------------------------------
# 12.5 — Req 2.4: single match returns exactly that medicine
# ---------------------------------------------------------------------------

def test_single_match_shows_details():
    med = make_med("Panadol Extra")
    db = [med, make_med("Disprin")]
    results = search_medicines("Panadol Extra", db)
    assert len(results) == 1
    assert results[0] is med


# ---------------------------------------------------------------------------
# Additional imports needed for tasks 12.6 – 12.10
# ---------------------------------------------------------------------------

from medmatch import ResultsPanel, find_alternatives, best_price_indices  # noqa: F811 (already imported above)


# ---------------------------------------------------------------------------
# 12.6 — Req 2.5: multiple matches returned in picklist
# ---------------------------------------------------------------------------

def test_multiple_matches_shows_picklist():
    med1 = make_med("Panadol Extra", "Paracetamol 500mg")
    med2 = make_med("Panadol CF", "Paracetamol 500mg")
    db = [med1, med2, make_med("Disprin", "Aspirin")]
    results = search_medicines("Panadol", db)
    assert len(results) == 2
    assert med1 in results
    assert med2 in results


# ---------------------------------------------------------------------------
# 12.7 — Req 4.4: no cheaper in-stock alternatives → empty list
# ---------------------------------------------------------------------------

def test_no_alternatives_message():
    selected = make_med("Panadol", "Paracetamol 500mg", price=50.0)
    # All other same-formula meds are either more expensive or zero stock
    expensive = make_med("Generic Para", "Paracetamol 500mg", price=100.0, quantity=10)
    zero_stock = make_med("Cheapo Para", "Paracetamol 500mg", price=20.0, quantity=0)
    db = [selected, expensive, zero_stock]
    alts = find_alternatives(selected, db)
    assert alts == []


# ---------------------------------------------------------------------------
# 12.8 — Req 7.4: clear() destroys all children in both frames
# ---------------------------------------------------------------------------

@requires_tk
def test_clear_search_resets_panels():
    root = _tk_root
    panel = ResultsPanel(root, [])
    panel.pack()
    # Populate both frames with widgets
    tk.Label(panel._left_frame, text="test").pack()
    tk.Label(panel._right_frame, text="test").pack()
    panel.clear()
    assert panel._left_frame.winfo_children() == []
    assert panel._right_frame.winfo_children() == []
    panel.destroy()


# ---------------------------------------------------------------------------
# 12.9 — Req 3.2, 4.3: column headings "Searched Medicine" and "Cheaper Alternatives"
# ---------------------------------------------------------------------------

@requires_tk
def test_headings_present():
    root = _tk_root
    panel = ResultsPanel(root, [])
    panel.pack()

    def collect_texts(widget):
        texts = []
        if isinstance(widget, tk.Label):
            texts.append(widget.cget("text"))
        for child in widget.winfo_children():
            texts.extend(collect_texts(child))
        return texts

    all_texts = collect_texts(panel)
    panel.destroy()
    assert "Searched Medicine" in all_texts
    assert "Cheaper Alternatives" in all_texts


# ---------------------------------------------------------------------------
# 12.10 — Req 4.6: price_pkr == 0.0 → find_alternatives returns []
# ---------------------------------------------------------------------------

def test_invalid_price_no_alternatives():
    selected = make_med("ZeroPriceMed", "GenA", price=0.0)
    db = [selected, make_med("Cheaper", "GenA", price=0.0, quantity=10)]
    alts = find_alternatives(selected, db)
    assert alts == []


# ---------------------------------------------------------------------------
# 12.11 — Req 10.3: single alternative → best_price_indices returns [0]
# ---------------------------------------------------------------------------

def test_best_price_single_alternative():
    alt = make_med("CheapMed", price=50.0)
    assert best_price_indices([alt]) == [0]


# ---------------------------------------------------------------------------
# 12.12 — Req 10.4: empty list → best_price_indices returns []
# ---------------------------------------------------------------------------

def test_no_best_price_when_no_alternatives():
    assert best_price_indices([]) == []

"""
Property-based tests for MedMatch using Hypothesis.
**Validates: Requirements 2.3, 2.7** (Property 1)
"""

import math
from hypothesis import given, settings, strategies as st
from medmatch import (
    Medicine,
    search_medicines,
    find_alternatives,
    best_price_indices,
    format_price,
    normalize_manufacturer,
    parse_row,
    price_difference,
)

# ---------------------------------------------------------------------------
# Shared strategies
# ---------------------------------------------------------------------------

medicine_strategy = st.builds(
    Medicine,
    brand_name=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs'))),
    generic_name=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs'))),
    manufacturer=st.text(min_size=0, max_size=50),
    price_pkr=st.floats(min_value=0.01, max_value=999999.99, allow_nan=False, allow_infinity=False),
    quantity=st.integers(min_value=0, max_value=9999),
)
medicine_list_strategy = st.lists(medicine_strategy, min_size=0, max_size=50)
query_strategy = st.text(min_size=1, max_size=30)
price_strategy = st.floats(min_value=0.0, max_value=999999999.99, allow_nan=False, allow_infinity=False)
manufacturer_strategy = st.one_of(st.text(), st.just(""), st.just("   "))


# ---------------------------------------------------------------------------
# Property 1: Search Inclusion/Exclusion
# Validates: Requirements 2.3, 2.7
# ---------------------------------------------------------------------------

@given(db=medicine_list_strategy, query=query_strategy)
@settings(max_examples=100)
def test_search_inclusion_exclusion(db, query):
    # Feature: medmatch, Property 1: search inclusion/exclusion
    results = search_medicines(query, db)
    for m in results:
        assert query.lower() in m.brand_name.lower()
    expected = [m for m in db if query.lower() in m.brand_name.lower()]
    assert sorted(results, key=lambda m: m.brand_name) == sorted(expected, key=lambda m: m.brand_name)


# ---------------------------------------------------------------------------
# Property 4: Price Difference Is Positive and Accurate
# Validates: Requirements 4.5
# ---------------------------------------------------------------------------

@given(selected=medicine_strategy, db=medicine_list_strategy)
@settings(max_examples=100)
def test_price_difference_accuracy(selected, db):
    # Feature: medmatch, Property 4: price difference is positive and accurate
    # Validates: Requirements 4.5
    alternatives = find_alternatives(selected, db)
    for alt in alternatives:
        diff = price_difference(selected.price_pkr, alt.price_pkr)
        assert math.isclose(diff, selected.price_pkr - alt.price_pkr, rel_tol=1e-9)
        assert diff > 0


# ---------------------------------------------------------------------------
# Property 3: Alternatives Query Correctness
# Validates: Requirements 4.1, 4.2, 4.4, 11.1, 11.2
# ---------------------------------------------------------------------------

@given(selected=medicine_strategy, db=medicine_list_strategy)
@settings(max_examples=100)
def test_alternatives_query_correctness(selected, db):
    # Feature: medmatch, Property 3: alternatives query correctness
    results = find_alternatives(selected, db)

    # If price <= 0, should return empty
    if selected.price_pkr <= 0:
        assert results == []
        return

    # Manually compute expected set
    expected = [
        m for m in db
        if m is not selected
        and m.generic_name.lower() == selected.generic_name.lower()
        and m.price_pkr < selected.price_pkr
        and m.quantity > 0
    ]

    assert sorted(results, key=lambda m: m.price_pkr) == sorted(expected, key=lambda m: m.price_pkr)

    # Assert sorted ascending by price
    prices = [m.price_pkr for m in results]
    assert prices == sorted(prices)


# ---------------------------------------------------------------------------
# Property 5: CSV Round-Trip Integrity
# Validates: Requirements 5.2, 6.1, 6.3
# ---------------------------------------------------------------------------

@given(med=medicine_strategy)
@settings(max_examples=100)
def test_csv_round_trip_integrity(med):
    # Feature: medmatch, Property 5: CSV round-trip integrity
    # Format the medicine as a CSV row dict
    row = {
        "brand_name": med.brand_name,
        "generic_name": med.generic_name,
        "manufacturer": med.manufacturer,
        "price_pkr": str(med.price_pkr),
        "quantity": str(med.quantity),
    }
    # parse_row strips all string fields before creating the Medicine, so
    # we compare against the stripped values (same transformation parse_row applies).
    stripped_brand = med.brand_name.strip()
    stripped_generic = med.generic_name.strip()

    # If stripping produces an empty brand_name or generic_name, parse_row returns
    # None (those are required fields).  Skip the round-trip check in that case.
    if not stripped_brand or not stripped_generic:
        return

    result = parse_row(1, row)
    assert result is not None
    assert result.brand_name == stripped_brand
    assert result.generic_name == stripped_generic
    # manufacturer goes through normalize_manufacturer; if it's all whitespace, result is "Unknown Manufacturer"
    expected_manufacturer = med.manufacturer.strip() if med.manufacturer.strip() else "Unknown Manufacturer"
    assert result.manufacturer == expected_manufacturer
    assert math.isclose(result.price_pkr, med.price_pkr, rel_tol=1e-9)


# ---------------------------------------------------------------------------
# Property 2: Medicine Card Renders All Required Fields
# Validates: Requirements 3.1, 9.1, 9.2
# ---------------------------------------------------------------------------

import tkinter as tk
from hypothesis import HealthCheck
from medmatch import MedicineCard

# Create a single hidden root for all MedicineCard tests to avoid
# the cost of spinning up a new Tk instance for every example.
_tk_root = tk.Tk()
_tk_root.withdraw()


@given(med=medicine_strategy)
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_medicine_card_field_presence(med):
    # Feature: medmatch, Property 2: medicine card renders all required fields
    card = MedicineCard(_tk_root, med)
    try:
        texts = [w.cget("text") for w in card.winfo_children() if isinstance(w, tk.Label)]
        assert med.brand_name in texts
        assert med.generic_name in texts
        assert med.manufacturer in texts
        assert format_price(med.price_pkr) in texts
    finally:
        card.destroy()


# ---------------------------------------------------------------------------
# Property 6: Invalid Row Is Skipped and Warning Is Logged
# Validates: Requirements 5.3, 6.2
# ---------------------------------------------------------------------------

import medmatch as _medmatch_module


@given(
    row_number=st.integers(min_value=2, max_value=10000),
    bad_field=st.sampled_from(["brand_name", "generic_name", "price_pkr"]),
    valid_brand=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs'))),
    valid_generic=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs'))),
)
@settings(max_examples=100)
def test_invalid_row_skipped_and_warned(row_number, bad_field, valid_brand, valid_generic):
    # Feature: medmatch, Property 6: invalid row is skipped and warning is logged
    row = {
        "brand_name": valid_brand,
        "generic_name": valid_generic,
        "manufacturer": "Test Mfg",
        "price_pkr": "100.0",
        "quantity": "10",
    }
    # Corrupt the selected field
    row[bad_field] = ""  # empty = invalid for brand_name, generic_name, price_pkr

    _medmatch_module.parse_warnings.clear()
    result = _medmatch_module.parse_row(row_number, row)

    assert result is None
    assert len(_medmatch_module.parse_warnings) >= 1
    warning = _medmatch_module.parse_warnings[-1]
    assert str(row_number) in warning
    assert bad_field in warning


# ---------------------------------------------------------------------------
# Property 7: Price Formatting Consistency
# Validates: Requirements 7.5
# ---------------------------------------------------------------------------

import re


@given(price=price_strategy)
@settings(max_examples=100)
def test_price_formatting_consistency(price):
    # Feature: medmatch, Property 7: price formatting consistency
    result = format_price(price)
    assert re.match(r'^\d+\.\d{2} PKR$', result) is not None


# ---------------------------------------------------------------------------
# Property 8: Manufacturer Normalization
# Validates: Requirements 9.3
# ---------------------------------------------------------------------------

@given(value=manufacturer_strategy)
@settings(max_examples=100)
def test_manufacturer_normalization(value):
    # Feature: medmatch, Property 8: manufacturer normalization
    result = normalize_manufacturer(value)
    if value.strip() == "":
        assert result == "Unknown Manufacturer"
    else:
        assert result == value.strip()


# ---------------------------------------------------------------------------
# Property 9: Best Price Label Accuracy
# Validates: Requirements 10.1, 10.3, 10.5
# ---------------------------------------------------------------------------

@given(alts=medicine_list_strategy.filter(lambda l: len(l) > 0))
@settings(max_examples=100)
def test_best_price_label_accuracy(alts):
    # Feature: medmatch, Property 9: best price label accuracy
    indices = best_price_indices(alts)
    assert len(indices) > 0
    min_price = min(m.price_pkr for m in alts)
    expected = [i for i, m in enumerate(alts) if m.price_pkr == min_price]
    assert indices == expected


# ---------------------------------------------------------------------------
# Property 10: Invalid Quantity Treated as Zero
# Validates: Requirements 11.3, 11.1
# ---------------------------------------------------------------------------

@given(
    brand=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu','Ll','Nd','Zs'))),
    generic=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu','Ll','Nd','Zs'))),
    price=st.floats(min_value=0.01, max_value=999999.99, allow_nan=False, allow_infinity=False),
    invalid_qty=st.one_of(st.just(""), st.just("abc"), st.just("1.5"), st.just("--1")),
    selected_price=st.floats(min_value=1000.0, max_value=999999.99, allow_nan=False, allow_infinity=False),
)
@settings(max_examples=100)
def test_invalid_quantity_treated_as_zero(brand, generic, price, invalid_qty, selected_price):
    # Feature: medmatch, Property 10: invalid quantity treated as zero
    row = {
        "brand_name": brand,
        "generic_name": generic,
        "manufacturer": "Test Mfg",
        "price_pkr": str(price),
        "quantity": invalid_qty,
    }
    result = parse_row(1, row)
    assert result is not None
    assert result.quantity == 0

    # Also verify it's excluded from find_alternatives
    selected = Medicine(
        brand_name="SelectedBrand",
        generic_name=generic,
        manufacturer="Test",
        price_pkr=selected_price,
        quantity=10,
    )
    alternatives = find_alternatives(selected, [result, selected])
    assert result not in alternatives

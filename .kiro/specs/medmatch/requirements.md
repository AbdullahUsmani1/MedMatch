# Requirements Document

## Introduction

MedMatch is a desktop application for pharmacy staff that allows them to search for a medicine by name and instantly see cheaper alternatives sharing the same active formula. The application is built with Python and Tkinter, uses a CSV file as its data source, and requires no login — staff open it and start using it immediately. The interface presents a two-column layout: the left column shows the searched medicine's details, and the right column lists cheaper alternatives sorted ascending by price.

## Glossary

- **MedMatch**: The desktop application described in this document.
- **Medicine**: A drug product stored in the CSV database, identified by its trade name, active formula, price, manufacturer, and stock quantity.
- **Formula**: The active ingredient(s) shared by a group of medicines, used as the basis for finding alternatives.
- **Alternative**: A medicine that shares the same Formula as the searched medicine, has a lower price, and has a quantity greater than zero.
- **CSV_Database**: The CSV file that serves as MedMatch's persistent data source, containing all medicine records.
- **Search_Bar**: The text input field where pharmacy staff type a medicine name.
- **Results_Panel**: The two-column display area that shows the searched medicine on the left and its alternatives on the right.
- **Staff**: A pharmacy employee who operates MedMatch.
- **Manufacturer**: The company responsible for producing a Medicine, stored as a field in the CSV_Database.
- **Best_Price_Label**: A green "BEST PRICE" visual badge displayed on the alternative with the lowest price among all displayed alternatives.
- **Quantity**: The stock count of a Medicine record in the CSV_Database, representing the number of units currently available.

---

## Requirements

### Requirement 1: Application Launch

**User Story:** As a staff member, I want to open MedMatch and immediately start using it, so that I do not waste time on setup or authentication.

#### Acceptance Criteria

1. WHEN the Staff launches MedMatch, THE MedMatch SHALL display the main window as visible and interactive with the Search_Bar and Results_Panel within 5 seconds, without requiring any login or configuration step.
2. WHEN the Staff launches MedMatch, THE MedMatch SHALL load the CSV_Database into memory and enable the Search_Bar for input within 5 seconds of application start.
3. IF the CSV_Database file is missing at launch, THEN THE MedMatch SHALL display an error message stating the expected file path and that the file was not found; the main window SHALL remain visible and the Search_Bar SHALL be disabled.
4. IF the CSV_Database file exists but cannot be read at launch, THEN THE MedMatch SHALL display an error message stating the file path and the reason the file is unreadable; the main window SHALL remain visible and the Search_Bar SHALL be disabled.

---

### Requirement 2: Medicine Search

**User Story:** As a staff member, I want to type a medicine name and see results instantly, so that I can serve customers without delays.

#### Acceptance Criteria

1. WHEN the Staff types a character into the Search_Bar, THE MedMatch SHALL filter and display matching medicines with a fully rendered result list within 300 milliseconds, without requiring a separate submit action.
2. THE Search_Bar SHALL accept medicine name input as a case-insensitive string.
3. WHEN the Staff types text into the Search_Bar, THE MedMatch SHALL match medicines whose names contain the entered text as a substring, using case-insensitive comparison.
4. WHEN exactly one medicine matches the search input, THE MedMatch SHALL populate the left column of the Results_Panel with that medicine's trade name, active formula, manufacturer name, and price.
5. WHEN more than one medicine matches the search input, THE MedMatch SHALL display a selectable list of matching medicine trade names so the Staff can choose one to view in detail; selecting a name from the list SHALL populate the left column with that medicine's full details.
6. IF the Search_Bar contains fewer than 1 character, THEN THE MedMatch SHALL clear both columns of the Results_Panel and display no results.
7. IF no medicine matches the search input, THEN THE MedMatch SHALL display a "No results found" message in the Results_Panel and clear any previously displayed results.

---

### Requirement 3: Display Searched Medicine Details

**User Story:** As a staff member, I want to see the full details of the medicine I searched for, so that I can confirm it is the correct product.

#### Acceptance Criteria

1. WHEN a medicine is selected for display, THE Results_Panel SHALL show the medicine's trade name, active formula, manufacturer name, and price in the left column, in that order.
2. WHEN a medicine is selected for display, THE Results_Panel SHALL display a non-empty text heading in the left column that reads "Searched Medicine" to identify that column's purpose.

---

### Requirement 4: Display Cheaper Alternatives

**User Story:** As a staff member, I want to see cheaper medicines with the same formula sorted by price, so that I can quickly recommend the most affordable option.

#### Acceptance Criteria

1. WHEN a medicine is selected for display, THE MedMatch SHALL query the CSV_Database for all medicines that share the same Formula (case-insensitive) and have a strictly lower price.
2. WHEN cheaper alternatives exist, THE Results_Panel SHALL display each alternative's trade name, active formula, and price in the right column, sorted in ascending order by price.
3. WHEN a medicine is selected for display, THE Results_Panel SHALL display a non-empty text heading in the right column that reads "Cheaper Alternatives" to identify that column's purpose.
4. WHEN no cheaper alternatives exist for the selected medicine, THE MedMatch SHALL display a "No cheaper alternatives found" message in the right column.
5. WHEN cheaper alternatives exist, THE MedMatch SHALL display alongside each alternative entry a price difference value equal to the selected medicine's price minus that alternative's price, expressed as a positive number.
6. IF the selected medicine has no valid numeric price, THEN THE MedMatch SHALL display a "No cheaper alternatives found" message in the right column and not attempt a price comparison.

---

### Requirement 5: CSV Database Structure

**User Story:** As a staff member or administrator, I want the application to read medicine data from a structured CSV file, so that the database can be updated without modifying application code.

#### Acceptance Criteria

1. THE CSV_Database SHALL contain at minimum the following columns: medicine trade name, active formula, price (non-negative decimal), manufacturer name, and quantity.
2. WHEN the CSV_Database is loaded, THE MedMatch SHALL parse each row into a Medicine record containing trade name, formula, price, manufacturer, and quantity fields.
3. IF a row in the CSV_Database is missing a required column value or contains a non-numeric value where a number is expected, THEN THE MedMatch SHALL skip that row and log a warning message identifying the row number and the missing or invalid field.
4. THE CSV_Database SHALL support a header row that labels each column; THE MedMatch SHALL use column names rather than positional indices to read values.
5. IF the CSV_Database file does not contain the expected header row, THEN THE MedMatch SHALL display an error message stating the file path and that the required header row is missing, and disable the Search_Bar.

---

### Requirement 6: Data Parsing Round-Trip Integrity

**User Story:** As a developer, I want medicine records parsed from the CSV to be accurately represented in memory, so that search and comparison logic operates on correct data.

#### Acceptance Criteria

1. WHEN the CSV_Database is parsed, THE MedMatch SHALL represent each Medicine's price as a floating-point value in the range 0.00 to 999,999,999.99 inclusive, suitable for arithmetic comparison.
2. IF a price value in the CSV_Database cannot be converted to a number, THEN THE MedMatch SHALL skip that row and log a warning identifying the row number and the invalid value.
3. THE MedMatch SHALL ensure that for all valid Medicine records loaded from the CSV_Database, formatting a record's string fields back into CSV columns and re-parsing them produces character-for-character identical trade name, formula, and manufacturer values, and a numerically equal price value.

---

### Requirement 7: Results Panel Layout

**User Story:** As a staff member, I want the two-column layout to be clear and easy to read, so that I can compare the searched medicine and alternatives at a glance.

#### Acceptance Criteria

1. THE Results_Panel SHALL divide the application window into two equal-width columns — left for the searched medicine and right for alternatives — each with a minimum width of 300 pixels.
2. WHILE alternatives are displayed, THE Results_Panel SHALL allow the Staff to scroll the right column independently if the list of alternatives exceeds the visible area.
3. WHILE the searched medicine detail is displayed, THE Results_Panel SHALL allow the Staff to scroll the left column independently if the content exceeds the visible area.
4. WHEN the Staff clears the Search_Bar, THE MedMatch SHALL simultaneously reset both columns of the Results_Panel so that no medicine data or alternative entries are visible.
5. THE MedMatch SHALL display all prices in a format consisting of a numeric value with exactly 2 decimal places followed by the currency symbol (e.g., "12.50 USD"), using no mixed formats throughout the Results_Panel.

---

### Requirement 8: Performance

**User Story:** As a staff member, I want search results to appear without noticeable delay, so that I can help customers efficiently.

#### Acceptance Criteria

1. WHEN the Staff types a character into the Search_Bar, THE MedMatch SHALL update the Results_Panel with a fully rendered result list within 300 milliseconds for a CSV_Database containing up to 10,000 medicine records.
2. WHEN the application starts, THE MedMatch SHALL complete CSV_Database loading and enable the Search_Bar for input within 3 seconds of application start, for a file containing up to 10,000 records.

---

### Requirement 9: Display Manufacturer Name

**User Story:** As a staff member, I want to see the manufacturer name on every medicine card, so that I can identify the producing company for both the searched medicine and any alternatives.

#### Acceptance Criteria

1. WHEN a medicine is selected for display, THE Results_Panel SHALL show the medicine's fields in the left column in the following order: trade name, active formula, manufacturer name, price.
2. WHEN cheaper alternatives are displayed, THE Results_Panel SHALL show the Manufacturer name on each alternative card in the right column.
3. IF a Medicine record in the CSV_Database has a manufacturer value that is null, empty, or contains only whitespace, THEN THE MedMatch SHALL display "Unknown Manufacturer" in place of the Manufacturer name on that medicine's card.

---

### Requirement 10: Best Price Label

**User Story:** As a staff member, I want the cheapest alternative to be visually highlighted, so that I can recommend the most affordable option at a glance without reading all prices.

#### Acceptance Criteria

1. WHEN cheaper alternatives are displayed, THE Results_Panel SHALL identify the alternative with the lowest price and render a Best_Price_Label on its card.
2. THE Best_Price_Label SHALL display the text "BEST PRICE" in green color, rendered as a visual badge with a distinct background that is visually separate from the other text fields on the card.
3. WHEN only one cheaper alternative exists, THE Results_Panel SHALL apply the Best_Price_Label to that single alternative.
4. WHEN no cheaper alternatives exist, THE MedMatch SHALL not render any Best_Price_Label.
5. WHEN multiple alternatives share the same lowest price, THE Results_Panel SHALL apply the Best_Price_Label to all alternatives sharing that lowest price.

---

### Requirement 11: Hide Zero-Stock Alternatives

**User Story:** As a staff member, I want alternatives with no stock to be hidden from the list, so that I only recommend medicines that are actually available.

#### Acceptance Criteria

1. WHEN MedMatch queries for cheaper alternatives, THE MedMatch SHALL exclude any Medicine whose Quantity is zero or less from the alternatives list.
2. WHEN cheaper alternatives exist but all have a Quantity of zero or less, THE MedMatch SHALL display a "No cheaper alternatives found" message in the right column.
3. WHEN a Medicine record in the CSV_Database has a missing or non-numeric Quantity value, THE MedMatch SHALL treat that record's Quantity as zero and exclude it from alternatives.
4. WHEN MedMatch queries for cheaper alternatives, THE MedMatch SHALL apply the zero-stock filter before sorting alternatives by price and before applying the Best_Price_Label.

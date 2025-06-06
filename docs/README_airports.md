# Airports Data – SimRoster

## Purpose

This document describes the structure, filtering process, and maintenance workflow for the `airports.csv` dataset used in the SimRoster project. The goal is to ensure that only realistic, airline-usable airports are included—removing thousands of “junk” airfields (FAA/FAA pseudo-ICAO, military, heliports, seaplane bases, etc.) found in global open data.

---

## 1. **Source Dataset**

- **Original file:** `airports_old.csv`  
  (Located in `data/` or backup folder. This file is never edited directly; always keep a full copy for reproducibility and future filtering.)

- **Columns included:**  
  `icao`, `name`, `city`, `country`, `latitude`, `longitude`, `type` (plus any additional metadata)

---

## 2. **Business Rules for Filtering**

We want to retain only **realistic, civil-use airports relevant to airline and regular commercial operations.**

### **INCLUDE only:**
- Airports with an **ICAO code of exactly 4 uppercase letters** (A-Z), e.g. `LFPG`, `KJFK`, `EGLL`, `RJAA`, `UUEE`, etc.
- **Types:** `large_airport`, `medium_airport`, `small_airport`
    - (Keep “small_airport” for handmade/exotic sceneries such as Lukla, Courchevel, etc.)

### **EXCLUDE:**
- Any code that:
    - Contains a number (e.g., `AK47`, `0NY8`, `1TE3`)
    - Is less or more than 4 characters
    - Contains a dash, space, or special character (e.g., `US-1`, `EG-LL`)
    - Has a prefix like `US-`
    - Type is not `large_airport`, `medium_airport`, or `small_airport` (e.g., `heliport`, `seaplane_base`, `balloonport`, etc.)

---

## 3. **Filtering Workflow**

### **Scripted process:**

1. **Start with** `airports_old.csv` (full worldwide open-source dataset)
2. **Apply filtering rule in Python:**
    ```python
    import pandas as pd
    import re

    df = pd.read_csv('airports_old.csv', dtype=str)
    df['icao'] = df['icao'].astype(str).str.strip().str.upper()
    types_wanted = {"large_airport", "medium_airport", "small_airport"}
    df['type'] = df['type'].astype(str).str.strip().str.lower()

    # Only 4-letter alpha ICAO, valid types
    mask = df['icao'].apply(lambda x: bool(re.match(r'^[A-Z]{4}$', x))) & df['type'].isin(types_wanted)
    df_filtered = df[mask].reset_index(drop=True)
    df_filtered.to_csv('airports.csv', index=False, encoding='utf-8-sig')
    ```
3. **Check for blank rows:** Remove any empty lines (should not exist, but check if needed).
4. **Resulting file:**  
    - `airports.csv` (main, ready for production)
    - `airports_old.csv` (backup, raw source, to never be deleted)

---

## 4. **Usage**

- The `airports.csv` file is used both for:
    - **Add-on/Community content scanning**
    - **Interactive map display in the GUI**
    - **Flight planning and airline route validation**

- If a user wants to “rebuild” or update this file, **always redo the filtering from the latest `airports_old.csv`**, never edit `airports.csv` by hand (except to manually add rare sceneries).

---

## 5. **Why this workflow?**

- **Performance:** Avoids thousands of “fake” US FAA strips that pollute search, map, and logic.
- **Professional focus:** Only real airports that can be used by actual airline ops and commercial flights.
- **Reproducibility:** The process is always the same; anyone can re-create or extend the dataset with the Python snippet above.
- **Clean code base:** Keeps everything readable, maintainable, and relevant for real-world airline use.

---

## 6. **Tips for future contributors**

- If you add a new data source or update the CSV:
    - Always keep the **full backup** (`airports_old.csv`)
    - Always re-apply the filtering script
    - Always verify there is **no blank line at the end**
- For rare exceptions (handmade airports with weird codes), edit `airports.csv` in Excel/LibreOffice/VSCode and document the reason in this README.

---

**Maintainer: Bertrand / wildbill75**  
_Last updated: June 2025_

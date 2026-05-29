<div align="center">

<!-- Replace with your project logo or banner -->
<img src="https://via.placeholder.com/120x120.png?text=LOGO" alt="Project Logo" width="120" height="120" />

<h1>ALN Auto Supply POS</h1>

<p><em>A simple desktop point-of-sale app for ALN Auto Supply — built with Python and Tkinter for fast, straightforward cashier operations.</em></p>

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-1.0.0-green.svg)](https://github.com/Nmsrt/ALN_Auto_Supply_POS_App/releases)
[![Build Status](https://img.shields.io/github/actions/workflow/status/Nmsrt/ALN_Auto_Supply_POS_App/ci.yml?branch=main)](https://github.com/Nmsrt/ALN_Auto_Supply_POS_App/actions)
[![Issues](https://img.shields.io/github/issues/Nmsrt/ALN_Auto_Supply_POS_App)](https://github.com/Nmsrt/ALN_Auto_Supply_POS_App/issues)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

</div>

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
- [Usage](#usage)
- [Product Management](#product-management)
- [Data Storage](#data-storage)
- [Project Structure](#project-structure)
- [License](#license)
- [Contact](#contact)

---

## Overview

ALN Auto Supply POS is a lightweight desktop application designed to handle basic cashier operations for a small auto supply store. It covers the full sales flow — browsing products, building a cart, applying discounts, computing change, and generating receipts — with no external libraries required.

The app is intentionally simple so it's easy to understand, maintain, and extend.

---

## Features

- ✅ **Cart & checkout** — Browse products, add items to a cart, and complete sales with automatic subtotal, discount, and change computation.
- ✅ **Receipt generation** — Each transaction produces a uniquely numbered receipt, saved as a plain text file in the `receipts/` folder.
- ✅ **Receipt history viewer** — Built-in viewer for opening and reviewing past transactions.
- ✅ **Product management** — Admin panel for adding, updating, and removing products from the local database.
- ✅ **Sales logging** — All completed transactions are logged to `transactions.csv` for easy analysis in Excel or Google Sheets.
- ✅ **No external libraries** — Runs on a plain Python installation; nothing extra to install.
- 🔜 **Thermal printer support** — Receipts are saved as plain text to make future printer integration straightforward.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | [Python 3.10+](https://www.python.org/) |
| GUI | [Tkinter](https://docs.python.org/3/library/tkinter.html) (built-in) |
| Database | [SQLite](https://www.sqlite.org/) (via `sqlite3`, built-in) |
| Config | `settings.json` |
| Sales Log | CSV (`transactions.csv`) |

---

## Getting Started

### Prerequisites

- [Python](https://www.python.org/downloads/) `>= 3.10`
- No external packages required — all libraries used are part of Python's standard library.

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Nmsrt/aln-auto-supply-pos.git
   cd aln-auto-supply-pos
   ```

2. **Run the app:**
   ```bash
   python main.py
   ```

That's it — no `pip install` needed.

---

## Usage

On launch, the app opens the cashier interface. From there you can:

1. Browse the product list and add items to the cart.
2. Enter the cash amount — subtotal, discount, and change are computed automatically.
3. Complete the sale to generate and save a receipt.
4. Use the receipt history viewer to look up any past transaction.

---

## Product Management

Products are stored in a local SQLite database (`aln_auto_supply.db`) and managed through the built-in admin panel, which allows you to add new items, update prices, and remove products.

> ⚠️ **Access to the admin panel is protected by an admin code.**

| Setting | Default |
|---|---|
| Default admin code | `1234` |
| Config file | `settings.json` |

It's recommended to change the default admin code after first launch by editing `settings.json`.

---

## Data Storage

The app stores data across three locations:

| Location | Contents |
|---|---|
| `aln_auto_supply.db` | Main SQLite database — products and receipt records |
| `transactions.csv` | Log of all completed sales; one row per line item |
| `receipts/` | Plain text copies of generated receipts |

The CSV format stores each item in a transaction as its own row, making it straightforward to filter, sort, and analyze in Excel or Google Sheets.

---

## Project Structure

```
aln-auto-supply-pos/
├── receipts/                 # Auto-generated text receipts
├── main.py                   # App entry point
├── aln_auto_supply.db        # SQLite database (auto-created on first run)
├── transactions.csv          # Sales log (auto-created on first sale)
├── settings.json             # App configuration (admin code, preferences)
└── README.md
```

---

## License

This project is open-source and available for personal use and inspiration.

---

## Contact

**Neo Monserrat** — neo.monserrat@gmail.com

Project Link: [https://github.com/Nmsrt/ALN_Auto_Supply_POS_App](https://github.com/Nmsrt/ALN_Auto_Supply_POS_App)

---

<div align="center">
  <sub>Built with ❤️ by <a href="https://github.com/Nmsrt">Nmsrt</a></sub>
</div>

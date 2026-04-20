# ALN Auto Supply POS

This is a simple desktop POS app for ALN Auto Supply. It’s built using Python (Tkinter) and is meant to handle basic cashier operations like adding products, generating receipts, and keeping track of sales.

## What it can do

You can browse your product list, add items to a cart, and complete a sale. The app automatically computes the subtotal, applies any discount, and calculates the change based on the cash entered.

Each completed transaction generates a receipt with a unique receipt number. A text copy of that receipt is saved in the `receipts` folder.

There’s also a built-in receipt history viewer where you can open and review past transactions.

## Product management

Products are stored in a local SQLite database. You can manage them through the admin panel — add new items, update prices, or remove products.

Access to this is protected by an admin code.

Default admin code:
1234

You can change this later in `settings.json`.

## Data storage

The app stores data in a few places:

- `aln_auto_supply.db` → main database (products + receipts)
- `transactions.csv` → log of all completed sales
- `receipts/` → text copies of receipts

For the CSV:
- each item in a transaction is saved as its own row  
- this makes it easier to filter and analyze in Excel or Google Sheets  

## How to run

Make sure you have Python installed (3.10 or newer should be fine).

Open the folder in terminal or command prompt, then run:

python main.py

## Notes

This app is intentionally simple so it’s easy to modify later.  
It doesn’t require any external libraries.

Receipts are saved as plain text for now, which makes it easier to adapt later if you want to connect a thermal receipt printer.

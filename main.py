
import csv
import json
import os
import sqlite3
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

APP_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(APP_DIR, "aln_auto_supply.db")
SETTINGS_PATH = os.path.join(APP_DIR, "settings.json")
RECEIPTS_DIR = os.path.join(APP_DIR, "receipts")
TRANSACTIONS_CSV_PATH = os.path.join(APP_DIR, "transactions.csv")

DEFAULT_SETTINGS = {
    "shop_name": "ALN Auto Supply",
    "shop_address": "Your shop address here",
    "shop_contact": "Contact number here",
    "admin_code": "1234",
}


def ensure_dirs():
    os.makedirs(RECEIPTS_DIR, exist_ok=True)


def ensure_transactions_csv():
    if not os.path.exists(TRANSACTIONS_CSV_PATH):
        with open(TRANSACTIONS_CSV_PATH, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "receipt_id",
                "receipt_no",
                "created_at",
                "customer_name",
                "product_name",
                "quantity",
                "unit_price",
                "line_total",
                "subtotal",
                "discount",
                "total",
                "cash",
                "change_amount",
            ])


def load_settings():
    if not os.path.exists(SETTINGS_PATH):
        save_settings(DEFAULT_SETTINGS)
        return DEFAULT_SETTINGS.copy()
    with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    settings = DEFAULT_SETTINGS.copy()
    settings.update(data)
    return settings


def save_settings(settings):
    with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2)


class Database:
    def __init__(self, path):
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self.setup()

    def setup(self):
        cur = self.conn.cursor()

        cur.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                price REAL NOT NULL DEFAULT 0,
                stock INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS receipts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                receipt_no TEXT NOT NULL UNIQUE,
                customer_name TEXT,
                subtotal REAL NOT NULL,
                discount REAL NOT NULL,
                total REAL NOT NULL,
                cash REAL NOT NULL,
                change_amount REAL NOT NULL,
                created_at TEXT NOT NULL
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS receipt_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                receipt_id INTEGER NOT NULL,
                product_name TEXT NOT NULL,
                qty INTEGER NOT NULL,
                unit_price REAL NOT NULL,
                line_total REAL NOT NULL,
                FOREIGN KEY (receipt_id) REFERENCES receipts(id)
            )
        """)

        self.conn.commit()
        self.seed_products()

    def seed_products(self):
        cur = self.conn.cursor()
        cur.execute("SELECT COUNT(*) FROM products")
        if cur.fetchone()[0] == 0:
            now = datetime.now().isoformat(timespec="seconds")
            sample = [
                ("Engine Oil 1L", 350.0, 25, now),
                ("Brake Fluid", 180.0, 20, now),
                ("Spark Plug", 120.0, 50, now),
                ("Air Filter", 280.0, 15, now),
                ("Coolant", 220.0, 18, now),
                ("Motorcycle Chain Lube", 260.0, 12, now),
            ]
            cur.executemany(
                "INSERT INTO products(name, price, stock, created_at) VALUES (?, ?, ?, ?)",
                sample,
            )
            self.conn.commit()

    def get_products(self, search=""):
        cur = self.conn.cursor()
        if search.strip():
            cur.execute(
                "SELECT * FROM products WHERE name LIKE ? ORDER BY name",
                (f"%{search.strip()}%",),
            )
        else:
            cur.execute("SELECT * FROM products ORDER BY name")
        return cur.fetchall()

    def get_product_by_id(self, product_id):
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM products WHERE id=?", (int(product_id),))
        return cur.fetchone()

    def add_product(self, name, price, stock):
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO products(name, price, stock, created_at) VALUES (?, ?, ?, ?)",
            (name.strip(), float(price), int(stock), datetime.now().isoformat(timespec="seconds")),
        )
        self.conn.commit()

    def update_product(self, product_id, name, price, stock):
        cur = self.conn.cursor()
        cur.execute(
            "UPDATE products SET name=?, price=?, stock=? WHERE id=?",
            (name.strip(), float(price), int(stock), int(product_id)),
        )
        self.conn.commit()

    def delete_product(self, product_id):
        cur = self.conn.cursor()
        cur.execute("DELETE FROM products WHERE id=?", (int(product_id),))
        self.conn.commit()

    def get_receipts(self):
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM receipts ORDER BY id DESC")
        return cur.fetchall()

    def get_receipt_items(self, receipt_id):
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM receipt_items WHERE receipt_id=? ORDER BY id", (int(receipt_id),))
        return cur.fetchall()

    def next_receipt_no(self):
        cur = self.conn.cursor()
        cur.execute("SELECT id FROM receipts ORDER BY id DESC LIMIT 1")
        row = cur.fetchone()
        next_id = row["id"] + 1 if row else 1
        return f"ALN-{datetime.now():%Y%m%d}-{next_id:04d}"

    def append_receipt_to_csv(
        self,
        receipt_id,
        receipt_no,
        created_at,
        customer_name,
        items,
        subtotal,
        discount,
        total,
        cash,
        change_amount,
    ):
        ensure_transactions_csv()
        with open(TRANSACTIONS_CSV_PATH, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            for item in items:
                writer.writerow([
                    receipt_id,
                    receipt_no,
                    created_at,
                    customer_name,
                    item["name"],
                    item["qty"],
                    f"{float(item['unit_price']):.2f}",
                    f"{float(item['line_total']):.2f}",
                    f"{float(subtotal):.2f}",
                    f"{float(discount):.2f}",
                    f"{float(total):.2f}",
                    f"{float(cash):.2f}",
                    f"{float(change_amount):.2f}",
                ])

    def save_receipt(self, customer_name, items, subtotal, discount, total, cash, change_amount):
        receipt_no = self.next_receipt_no()
        created_at = datetime.now().isoformat(timespec="seconds")
        cur = self.conn.cursor()

        cur.execute("""
            INSERT INTO receipts(receipt_no, customer_name, subtotal, discount, total, cash, change_amount, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (receipt_no, customer_name.strip(), subtotal, discount, total, cash, change_amount, created_at))

        receipt_id = cur.lastrowid

        for item in items:
            cur.execute("""
                INSERT INTO receipt_items(receipt_id, product_name, qty, unit_price, line_total)
                VALUES (?, ?, ?, ?, ?)
            """, (receipt_id, item["name"], item["qty"], item["unit_price"], item["line_total"]))

            cur.execute("""
                UPDATE products
                SET stock = CASE WHEN stock - ? < 0 THEN 0 ELSE stock - ? END
                WHERE name = ?
            """, (item["qty"], item["qty"], item["name"]))

        self.conn.commit()
        self.append_receipt_to_csv(
            receipt_id,
            receipt_no,
            created_at,
            customer_name.strip() or "Walk-in",
            items,
            subtotal,
            discount,
            total,
            cash,
            change_amount,
        )
        return receipt_id, receipt_no, created_at


class POSApp(tk.Tk):
    def __init__(self):
        super().__init__()
        ensure_dirs()
        ensure_transactions_csv()

        self.settings = load_settings()
        self.db = Database(DB_PATH)

        self.title(f"{self.settings['shop_name']} POS")
        self.geometry("1500x900")
        self.minsize(1320, 800)
        self.configure(bg="#f3f6fb")

        self.cart = []

        self.search_var = tk.StringVar()
        self.customer_var = tk.StringVar()
        self.discount_var = tk.StringVar(value="0.00")
        self.cash_var = tk.StringVar(value="0.00")
        self.subtotal_var = tk.StringVar(value="₱0.00")
        self.total_var = tk.StringVar(value="₱0.00")
        self.change_var = tk.StringVar(value="₱0.00")
        self.receipt_info_var = tk.StringVar(value="0 item(s) in cart")

        self._style_ui()
        self._build_ui()
        self.refresh_products()
        self.refresh_cart()

    def _style_ui(self):
        style = ttk.Style(self)
        style.theme_use("clam")

        style.configure("Root.TFrame", background="#f3f6fb")
        style.configure("Card.TFrame", background="white")
        style.configure("Topbar.TFrame", background="#f3f6fb")
        style.configure("Header.TLabel", font=("Segoe UI", 24, "bold"), background="#f3f6fb", foreground="#152033")
        style.configure("SubHeader.TLabel", font=("Segoe UI", 11), background="#f3f6fb", foreground="#667085")
        style.configure("SectionTitle.TLabel", font=("Segoe UI", 16, "bold"), background="white", foreground="#152033")
        style.configure("Muted.TLabel", font=("Segoe UI", 10), background="white", foreground="#667085")
        style.configure("MetricTitle.TLabel", font=("Segoe UI", 11), background="#eef3fb", foreground="#667085")
        style.configure("BigValue.TLabel", font=("Segoe UI", 22, "bold"), background="#eef3fb", foreground="#111827")
        style.configure("TEntry", padding=8, font=("Segoe UI", 11))
        style.configure("Treeview", rowheight=32, font=("Segoe UI", 10), fieldbackground="white", background="white")
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))
        style.map("Treeview", background=[("selected", "#dbeafe")], foreground=[("selected", "#111827")])

        style.configure(
            "Primary.TButton",
            font=("Segoe UI", 10, "bold"),
            padding=(12, 10),
            foreground="white",
            background="#0b74d1",
            borderwidth=1,
            focusthickness=0,
        )
        style.map(
            "Primary.TButton",
            background=[("active", "#095fb0"), ("pressed", "#074f92")],
            foreground=[("disabled", "#d1d5db"), ("!disabled", "white")],
        )

        style.configure(
            "Secondary.TButton",
            font=("Segoe UI", 10, "bold"),
            padding=(12, 10),
            foreground="#1f2937",
            background="#e8eef7",
            borderwidth=1,
            focusthickness=0,
        )
        style.map(
            "Secondary.TButton",
            background=[("active", "#dbe7f5"), ("pressed", "#cfdef0")],
            foreground=[("!disabled", "#1f2937")],
        )

        style.configure(
            "Danger.TButton",
            font=("Segoe UI", 10, "bold"),
            padding=(12, 10),
            foreground="#7f1d1d",
            background="#fde8e8",
            borderwidth=1,
            focusthickness=0,
        )
        style.map(
            "Danger.TButton",
            background=[("active", "#fbd5d5"), ("pressed", "#f9c4c4")],
            foreground=[("!disabled", "#7f1d1d")],
        )

    def _build_ui(self):
        root = ttk.Frame(self, style="Root.TFrame", padding=18)
        root.pack(fill="both", expand=True)

        topbar = ttk.Frame(root, style="Topbar.TFrame")
        topbar.pack(fill="x", pady=(0, 14))
        ttk.Label(topbar, text=self.settings["shop_name"], style="Header.TLabel").pack(side="left")
        ttk.Label(
            topbar,
            text="POS System",
            style="SubHeader.TLabel",
        ).pack(side="left", padx=(14, 0), pady=(8, 0))
        ttk.Button(
            topbar,
            text="Admin Panel",
            command=self.open_admin_login,
            style="Secondary.TButton",
        ).pack(side="right")

        body = ttk.Frame(root, style="Root.TFrame")
        body.pack(fill="both", expand=True)
        body.columnconfigure(0, weight=7)
        body.columnconfigure(1, weight=6)
        body.rowconfigure(0, weight=1)

        left = ttk.Frame(body, style="Card.TFrame", padding=16)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        right = ttk.Frame(body, style="Card.TFrame", padding=16)
        right.grid(row=0, column=1, sticky="nsew")

        self._build_products_panel(left)
        self._build_receipt_panel(right)

    def _build_products_panel(self, parent):
        parent.rowconfigure(2, weight=1)
        parent.columnconfigure(0, weight=1)

        header = ttk.Frame(parent, style="Card.TFrame")
        header.grid(row=0, column=0, sticky="ew")
        ttk.Label(header, text="Product Catalog", style="SectionTitle.TLabel").pack(side="left")
        ttk.Label(header, text="Select a product and add it to the cart", style="Muted.TLabel").pack(side="left", padx=(12, 0), pady=(2, 0))

        search_row = ttk.Frame(parent, style="Card.TFrame")
        search_row.grid(row=1, column=0, sticky="ew", pady=(12, 10))
        search_row.columnconfigure(0, weight=1)

        search_entry = ttk.Entry(search_row, textvariable=self.search_var)
        search_entry.grid(row=0, column=0, sticky="ew")
        search_entry.bind("<KeyRelease>", lambda _e: self.refresh_products())

        ttk.Button(search_row, text="Refresh", command=self.refresh_products, style="Secondary.TButton").grid(row=0, column=1, padx=8)
        ttk.Button(search_row, text="Quick Add", command=self.add_selected_product_to_cart, style="Primary.TButton").grid(row=0, column=2)

        tree_wrap = ttk.Frame(parent, style="Card.TFrame")
        tree_wrap.grid(row=2, column=0, sticky="nsew")
        tree_wrap.rowconfigure(0, weight=1)
        tree_wrap.columnconfigure(0, weight=1)

        columns = ("id", "name", "price", "stock")
        self.products_tree = ttk.Treeview(tree_wrap, columns=columns, show="headings", selectmode="browse")
        self.products_tree.grid(row=0, column=0, sticky="nsew")
        self.products_tree.heading("id", text="ID")
        self.products_tree.heading("name", text="Product")
        self.products_tree.heading("price", text="Price")
        self.products_tree.heading("stock", text="Stock")
        self.products_tree.column("id", width=70, anchor="center", stretch=False)
        self.products_tree.column("name", width=380, anchor="w")
        self.products_tree.column("price", width=130, anchor="e", stretch=False)
        self.products_tree.column("stock", width=100, anchor="center", stretch=False)
        self.products_tree.bind("<Double-1>", lambda _e: self.add_selected_product_to_cart())

        product_scroll = ttk.Scrollbar(tree_wrap, orient="vertical", command=self.products_tree.yview)
        product_scroll.grid(row=0, column=1, sticky="ns")
        self.products_tree.configure(yscrollcommand=product_scroll.set)

        controls = ttk.Frame(parent, style="Card.TFrame")
        controls.grid(row=3, column=0, sticky="ew", pady=(12, 0))
        controls.columnconfigure(4, weight=1)

        self.qty_spin = tk.Spinbox(
            controls,
            from_=1,
            to=999,
            width=6,
            font=("Segoe UI", 11),
            relief="solid",
            bd=1,
            justify="center",
        )
        self.qty_spin.grid(row=0, column=0, sticky="w")

        ttk.Button(
            controls,
            text="Add Selected Product",
            command=self.add_selected_product_to_cart,
            style="Primary.TButton",
        ).grid(row=0, column=1, padx=(8, 8), sticky="w")

        ttk.Button(
            controls,
            text="Remove Selected Cart Item",
            command=self.remove_selected_cart_item,
            style="Secondary.TButton",
        ).grid(row=0, column=2, padx=(0, 8), sticky="w")

        ttk.Button(
            controls,
            text="Clear Cart",
            command=self.clear_cart,
            style="Danger.TButton",
        ).grid(row=0, column=3, sticky="w")

    def _build_receipt_panel(self, parent):
        parent.rowconfigure(2, weight=1)
        parent.columnconfigure(0, weight=1)

        top = ttk.Frame(parent, style="Card.TFrame")
        top.grid(row=0, column=0, sticky="ew")
        ttk.Label(top, text="Receipt Panel", style="SectionTitle.TLabel").pack(side="left")
        ttk.Label(top, textvariable=self.receipt_info_var, style="Muted.TLabel").pack(side="right", pady=(2, 0))

        info = ttk.Frame(parent, style="Card.TFrame")
        info.grid(row=1, column=0, sticky="ew", pady=(12, 10))
        for col, weight in [(0, 2), (1, 1), (2, 1)]:
            info.columnconfigure(col, weight=weight)

        ttk.Label(info, text="Customer Name", style="Muted.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(info, text="Discount (₱)", style="Muted.TLabel").grid(row=0, column=1, sticky="w", padx=(10, 0))
        ttk.Label(info, text="Cash (₱)", style="Muted.TLabel").grid(row=0, column=2, sticky="w", padx=(10, 0))

        ttk.Entry(info, textvariable=self.customer_var).grid(row=1, column=0, sticky="ew", pady=(4, 0))
        ttk.Entry(info, textvariable=self.discount_var).grid(row=1, column=1, sticky="ew", padx=(10, 0), pady=(4, 0))
        ttk.Entry(info, textvariable=self.cash_var).grid(row=1, column=2, sticky="ew", padx=(10, 0), pady=(4, 0))

        for variable in (self.discount_var, self.cash_var):
            variable.trace_add("write", lambda *_args: self.refresh_cart())

        cart_area = ttk.Frame(parent, style="Card.TFrame")
        cart_area.grid(row=2, column=0, sticky="nsew")
        cart_area.rowconfigure(0, weight=1)
        cart_area.columnconfigure(0, weight=1)

        cols = ("product", "qty", "unit_price", "line_total")
        self.cart_tree = ttk.Treeview(cart_area, columns=cols, show="headings", selectmode="browse")
        self.cart_tree.grid(row=0, column=0, sticky="nsew")
        self.cart_tree.heading("product", text="Product")
        self.cart_tree.heading("qty", text="Qty")
        self.cart_tree.heading("unit_price", text="Unit Price")
        self.cart_tree.heading("line_total", text="Line Total")
        self.cart_tree.column("product", width=260, anchor="w")
        self.cart_tree.column("qty", width=80, anchor="center", stretch=False)
        self.cart_tree.column("unit_price", width=120, anchor="e", stretch=False)
        self.cart_tree.column("line_total", width=130, anchor="e", stretch=False)

        cart_scroll = ttk.Scrollbar(cart_area, orient="vertical", command=self.cart_tree.yview)
        cart_scroll.grid(row=0, column=1, sticky="ns")
        self.cart_tree.configure(yscrollcommand=cart_scroll.set)

        bottom = ttk.Frame(parent, style="Card.TFrame")
        bottom.grid(row=3, column=0, sticky="ew", pady=(12, 0))
        bottom.columnconfigure(0, weight=1)

        metrics = ttk.Frame(bottom, style="Card.TFrame")
        metrics.grid(row=0, column=0, sticky="ew")
        metrics.columnconfigure((0, 1, 2), weight=1)

        self._metric_card(metrics, "Subtotal", self.subtotal_var).grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self._metric_card(metrics, "Total", self.total_var).grid(row=0, column=1, sticky="ew", padx=4)
        self._metric_card(metrics, "Change", self.change_var).grid(row=0, column=2, sticky="ew", padx=(8, 0))

        actions = ttk.Frame(bottom, style="Card.TFrame")
        actions.grid(row=1, column=0, sticky="ew", pady=(12, 0))
        actions.columnconfigure(0, weight=2)
        actions.columnconfigure(1, weight=1)
        actions.columnconfigure(2, weight=1)

        ttk.Button(
            actions,
            text="Checkout & Save Receipt",
            command=self.checkout,
            style="Primary.TButton",
        ).grid(row=0, column=0, sticky="ew", padx=(0, 8))

        ttk.Button(
            actions,
            text="Receipt History",
            command=self.open_receipt_history,
            style="Secondary.TButton",
        ).grid(row=0, column=1, sticky="ew", padx=4)

        ttk.Button(
            actions,
            text="Preview Text Receipt",
            command=self.preview_current_receipt,
            style="Secondary.TButton",
        ).grid(row=0, column=2, sticky="ew", padx=(8, 0))

    def _metric_card(self, parent, title, variable):
        frame = tk.Frame(parent, bg="#eef3fb", highlightthickness=1, highlightbackground="#d8e3f0", bd=0, padx=14, pady=12)
        ttk.Label(frame, text=title, style="MetricTitle.TLabel").pack(anchor="w")
        ttk.Label(frame, textvariable=variable, style="BigValue.TLabel").pack(anchor="w", pady=(6, 0))
        return frame

    def money(self, value):
        return f"₱{float(value):,.2f}"

    def parse_float(self, raw, default=0.0):
        try:
            return float(str(raw).replace("₱", "").replace(",", "").strip())
        except Exception:
            return default

    def refresh_products(self):
        for row in self.products_tree.get_children():
            self.products_tree.delete(row)

        for product in self.db.get_products(self.search_var.get()):
            self.products_tree.insert(
                "",
                "end",
                iid=str(product["id"]),
                values=(product["id"], product["name"], self.money(product["price"]), product["stock"]),
            )

    def add_selected_product_to_cart(self):
        selected = self.products_tree.selection()
        if not selected:
            messagebox.showwarning("No product selected", "Please select a product first.")
            return

        product = self.db.get_product_by_id(int(selected[0]))
        if product is None:
            return

        try:
            qty = int(self.qty_spin.get())
        except ValueError:
            messagebox.showerror("Invalid quantity", "Quantity must be a whole number.")
            return

        if qty <= 0:
            messagebox.showerror("Invalid quantity", "Quantity must be at least 1.")
            return

        existing = next((item for item in self.cart if item["name"] == product["name"]), None)
        if existing:
            existing["qty"] += qty
            existing["line_total"] = existing["qty"] * existing["unit_price"]
        else:
            self.cart.append({
                "name": product["name"],
                "qty": qty,
                "unit_price": float(product["price"]),
                "line_total": qty * float(product["price"]),
            })

        self.refresh_cart()

    def refresh_cart(self):
        for row in self.cart_tree.get_children():
            self.cart_tree.delete(row)

        subtotal = 0.0
        for idx, item in enumerate(self.cart):
            subtotal += item["line_total"]
            self.cart_tree.insert(
                "",
                "end",
                iid=str(idx),
                values=(
                    item["name"],
                    item["qty"],
                    self.money(item["unit_price"]),
                    self.money(item["line_total"]),
                ),
            )

        discount = max(self.parse_float(self.discount_var.get()), 0.0)
        total = max(subtotal - discount, 0.0)
        cash = max(self.parse_float(self.cash_var.get()), 0.0)
        change = cash - total if cash >= total else 0.0

        self.subtotal_var.set(self.money(subtotal))
        self.total_var.set(self.money(total))
        self.change_var.set(self.money(change))
        self.receipt_info_var.set(f"{len(self.cart)} item(s) in cart")

    def remove_selected_cart_item(self):
        selected = self.cart_tree.selection()
        if not selected:
            messagebox.showwarning("No cart item selected", "Please select an item from the receipt panel.")
            return

        idx = int(selected[0])
        if 0 <= idx < len(self.cart):
            self.cart.pop(idx)
            self.refresh_cart()

    def clear_cart(self):
        self.cart.clear()
        self.customer_var.set("")
        self.discount_var.set("0.00")
        self.cash_var.set("0.00")
        self.refresh_cart()

    def build_receipt_text(
        self,
        receipt_no="DRAFT",
        created_at=None,
        items=None,
        customer_name="Walk-in",
        subtotal=None,
        discount=None,
        total=None,
        cash=None,
        change=None,
    ):
        items = items if items is not None else self.cart
        subtotal = self.parse_float(subtotal if subtotal is not None else self.subtotal_var.get())
        discount = self.parse_float(discount if discount is not None else self.discount_var.get())
        total = self.parse_float(total if total is not None else self.total_var.get())
        cash = self.parse_float(cash if cash is not None else self.cash_var.get())
        change = self.parse_float(change if change is not None else self.change_var.get())
        created_at = created_at or datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        line = "-" * 40
        lines = [
            self.settings["shop_name"],
            self.settings["shop_address"],
            self.settings["shop_contact"],
            line,
            f"Receipt No: {receipt_no}",
            f"Date: {created_at}",
            f"Customer: {customer_name or 'Walk-in'}",
            line,
            f"{'Item':20}{'Qty':>5}{'Price':>7}{'Amt':>8}",
            line,
        ]

        for item in items:
            name = item["name"][:20]
            lines.append(f"{name:20}{item['qty']:>5}{item['unit_price']:>7.0f}{item['line_total']:>8.0f}")

        lines.extend([
            line,
            f"Subtotal: {self.money(subtotal)}",
            f"Discount: {self.money(discount)}",
            f"Total:    {self.money(total)}",
            f"Cash:     {self.money(cash)}",
            f"Change:   {self.money(change)}",
            line,
            "Thank you for your purchase!",
        ])
        return "\n".join(lines)

    def preview_current_receipt(self):
        if not self.cart:
            messagebox.showwarning("Empty cart", "Add at least one item first.")
            return

        win = tk.Toplevel(self)
        win.title("Receipt Preview")
        win.geometry("430x620")

        text = tk.Text(win, font=("Consolas", 11), wrap="word", bg="white")
        text.pack(fill="both", expand=True)
        text.insert("1.0", self.build_receipt_text(customer_name=self.customer_var.get() or "Walk-in"))
        text.config(state="disabled")

    def open_receipt_preview_from_text(self, receipt_no, receipt_text):
        win = tk.Toplevel(self)
        win.title(f"Receipt {receipt_no}")
        win.geometry("430x620")

        text = tk.Text(win, font=("Consolas", 11), wrap="word", bg="white")
        text.pack(fill="both", expand=True)
        text.insert("1.0", receipt_text)
        text.config(state="disabled")

    def checkout(self):
        if not self.cart:
            messagebox.showwarning("Empty cart", "Add products before checking out.")
            return

        subtotal = sum(item["line_total"] for item in self.cart)
        discount = max(self.parse_float(self.discount_var.get()), 0.0)
        total = max(subtotal - discount, 0.0)
        cash = self.parse_float(self.cash_var.get())

        if cash < total:
            messagebox.showerror("Insufficient cash", "Cash provided is less than the total amount.")
            return

        change = cash - total
        customer_name = self.customer_var.get().strip() or "Walk-in"

        receipt_id, receipt_no, created_at = self.db.save_receipt(
            customer_name, self.cart, subtotal, discount, total, cash, change
        )

        receipt_text = self.build_receipt_text(
            receipt_no=receipt_no,
            created_at=created_at,
            customer_name=customer_name,
            subtotal=subtotal,
            discount=discount,
            total=total,
            cash=cash,
            change=change,
        )

        txt_path = os.path.join(RECEIPTS_DIR, f"{receipt_no}.txt")
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(receipt_text)

        self.clear_cart()
        self.refresh_products()

        messagebox.showinfo(
            "Receipt saved",
            f"Receipt {receipt_no} saved successfully.\n\nText copy:\n{txt_path}\n\nTransactions CSV:\n{TRANSACTIONS_CSV_PATH}",
        )
        self.open_receipt_preview_from_text(receipt_no, receipt_text)

    def open_admin_login(self):
        code = simpledialog.askstring("Admin Access", "Enter admin code:", parent=self, show="*")
        if code is None:
            return
        if code != self.settings["admin_code"]:
            messagebox.showerror("Access denied", "Invalid admin code.")
            return
        self.open_admin_panel()

    def open_admin_panel(self):
        win = tk.Toplevel(self)
        win.title("Admin Panel")
        win.geometry("920x650")
        win.configure(bg="#f3f6fb")

        notebook = ttk.Notebook(win)
        notebook.pack(fill="both", expand=True, padx=12, pady=12)

        products_tab = ttk.Frame(notebook, padding=14)
        settings_tab = ttk.Frame(notebook, padding=14)
        notebook.add(products_tab, text="Products")
        notebook.add(settings_tab, text="Settings")

        self._build_admin_products(products_tab)
        self._build_admin_settings(settings_tab)

    def _build_admin_products(self, parent):
        form = ttk.Frame(parent)
        form.pack(fill="x")

        ttk.Label(form, text="Product Name").grid(row=0, column=0, sticky="w")
        ttk.Label(form, text="Price").grid(row=0, column=1, sticky="w", padx=(10, 0))
        ttk.Label(form, text="Stock").grid(row=0, column=2, sticky="w", padx=(10, 0))

        name_var = tk.StringVar()
        price_var = tk.StringVar()
        stock_var = tk.StringVar()
        id_var = tk.StringVar()

        ttk.Entry(form, textvariable=name_var).grid(row=1, column=0, sticky="ew", pady=(4, 0))
        ttk.Entry(form, textvariable=price_var).grid(row=1, column=1, sticky="ew", padx=(10, 0), pady=(4, 0))
        ttk.Entry(form, textvariable=stock_var).grid(row=1, column=2, sticky="ew", padx=(10, 0), pady=(4, 0))

        form.columnconfigure(0, weight=2)
        form.columnconfigure(1, weight=1)
        form.columnconfigure(2, weight=1)

        btns = ttk.Frame(parent)
        btns.pack(fill="x", pady=10)

        tree = ttk.Treeview(parent, columns=("id", "name", "price", "stock"), show="headings")
        for col, text, width in [
            ("id", "ID", 60),
            ("name", "Name", 320),
            ("price", "Price", 120),
            ("stock", "Stock", 100),
        ]:
            tree.heading(col, text=text)
            tree.column(col, width=width)
        tree.pack(fill="both", expand=True)

        def refresh_admin_products():
            for row in tree.get_children():
                tree.delete(row)
            for p in self.db.get_products():
                tree.insert("", "end", iid=str(p["id"]), values=(p["id"], p["name"], self.money(p["price"]), p["stock"]))
            self.refresh_products()

        def on_select(_event=None):
            selected = tree.selection()
            if not selected:
                return
            product = self.db.get_product_by_id(int(selected[0]))
            if not product:
                return
            id_var.set(str(product["id"]))
            name_var.set(product["name"])
            price_var.set(str(product["price"]))
            stock_var.set(str(product["stock"]))

        def add_product():
            try:
                self.db.add_product(name_var.get(), float(price_var.get()), int(stock_var.get()))
                refresh_admin_products()
                id_var.set("")
                name_var.set("")
                price_var.set("")
                stock_var.set("")
            except sqlite3.IntegrityError:
                messagebox.showerror("Duplicate product", "That product name already exists.")
            except Exception as e:
                messagebox.showerror("Error", str(e))

        def update_product():
            if not id_var.get():
                messagebox.showwarning("No selection", "Select a product first.")
                return
            try:
                self.db.update_product(int(id_var.get()), name_var.get(), float(price_var.get()), int(stock_var.get()))
                refresh_admin_products()
            except sqlite3.IntegrityError:
                messagebox.showerror("Duplicate product", "That product name already exists.")
            except Exception as e:
                messagebox.showerror("Error", str(e))

        def delete_product():
            if not id_var.get():
                messagebox.showwarning("No selection", "Select a product first.")
                return
            if messagebox.askyesno("Confirm delete", "Delete this product?"):
                self.db.delete_product(int(id_var.get()))
                refresh_admin_products()
                id_var.set("")
                name_var.set("")
                price_var.set("")
                stock_var.set("")

        ttk.Button(btns, text="Add Product", command=add_product, style="Primary.TButton").pack(side="left")
        ttk.Button(btns, text="Update Selected", command=update_product, style="Secondary.TButton").pack(side="left", padx=8)
        ttk.Button(btns, text="Delete Selected", command=delete_product, style="Danger.TButton").pack(side="left")

        tree.bind("<<TreeviewSelect>>", on_select)
        refresh_admin_products()

    def _build_admin_settings(self, parent):
        shop_name = tk.StringVar(value=self.settings["shop_name"])
        shop_address = tk.StringVar(value=self.settings["shop_address"])
        shop_contact = tk.StringVar(value=self.settings["shop_contact"])
        admin_code = tk.StringVar(value=self.settings["admin_code"])

        fields = [
            ("Shop Name", shop_name),
            ("Shop Address", shop_address),
            ("Shop Contact", shop_contact),
            ("Admin Code", admin_code),
        ]

        for idx, (label, var) in enumerate(fields):
            ttk.Label(parent, text=label).grid(row=idx, column=0, sticky="w", pady=(0, 8))
            ttk.Entry(parent, textvariable=var, width=45).grid(row=idx, column=1, sticky="ew", pady=(0, 8))

        parent.columnconfigure(1, weight=1)

        def save_admin_settings():
            self.settings["shop_name"] = shop_name.get().strip() or "ALN Auto Supply"
            self.settings["shop_address"] = shop_address.get().strip()
            self.settings["shop_contact"] = shop_contact.get().strip()
            self.settings["admin_code"] = admin_code.get().strip() or "1234"
            save_settings(self.settings)
            self.title(f"{self.settings['shop_name']} POS")
            messagebox.showinfo("Saved", "Settings updated. Restart the app to refresh all top labels.")

        ttk.Button(parent, text="Save Settings", command=save_admin_settings, style="Primary.TButton").grid(
            row=len(fields), column=1, sticky="e", pady=(10, 0)
        )

    def open_receipt_history(self):
        win = tk.Toplevel(self)
        win.title("Receipt History")
        win.geometry("980x620")
        win.configure(bg="#f3f6fb")

        tree = ttk.Treeview(
            win,
            columns=("receipt_no", "customer", "total", "cash", "change", "date"),
            show="headings",
        )

        for col, text, width in [
            ("receipt_no", "Receipt No", 190),
            ("customer", "Customer", 160),
            ("total", "Total", 110),
            ("cash", "Cash", 110),
            ("change", "Change", 110),
            ("date", "Date", 180),
        ]:
            tree.heading(col, text=text)
            tree.column(col, width=width)

        tree.pack(fill="both", expand=True, padx=12, pady=12)

        receipts = self.db.get_receipts()
        for r in receipts:
            tree.insert(
                "",
                "end",
                iid=str(r["id"]),
                values=(
                    r["receipt_no"],
                    r["customer_name"],
                    self.money(r["total"]),
                    self.money(r["cash"]),
                    self.money(r["change_amount"]),
                    r["created_at"],
                ),
            )

        def open_selected():
            selected = tree.selection()
            if not selected:
                return
            receipt_id = int(selected[0])
            receipt = next((r for r in receipts if r["id"] == receipt_id), None)
            if not receipt:
                return

            items = []
            for row in self.db.get_receipt_items(receipt_id):
                items.append({
                    "name": row["product_name"],
                    "qty": row["qty"],
                    "unit_price": row["unit_price"],
                    "line_total": row["line_total"],
                })

            receipt_text = self.build_receipt_text(
                receipt_no=receipt["receipt_no"],
                created_at=receipt["created_at"],
                items=items,
                customer_name=receipt["customer_name"],
                subtotal=receipt["subtotal"],
                discount=receipt["discount"],
                total=receipt["total"],
                cash=receipt["cash"],
                change=receipt["change_amount"],
            )
            self.open_receipt_preview_from_text(receipt["receipt_no"], receipt_text)

        ttk.Button(win, text="Open Selected Receipt", command=open_selected, style="Primary.TButton").pack(pady=(0, 12))
        tree.bind("<Double-1>", lambda _e: open_selected())


if __name__ == "__main__":
    app = POSApp()
    app.mainloop()

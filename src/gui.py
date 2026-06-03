import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib
matplotlib.use("TkAgg")

from src.database import Database
from src.profit_calculator import ProfitCalculator
from src.etl import ETLPipeline
from src.analytics import Analytics
from tkinter import filedialog

# Color palette
BG        = "#F7F8FA"
CARD      = "#FFFFFF"
PRIMARY   = "#4361EE"
SUCCESS   = "#2DC653"
DANGER    = "#E5383B"
WARNING   = "#F4A261"
TEXT      = "#1A1A2E"
MUTED     = "#6C757D"
BORDER    = "#E0E0E0"

CHART_COLORS = ["#4361EE", "#F4A261", "#2DC653", "#E5383B", "#7B2FBE", "#06D6A0"]


def card_frame(parent, title="", **kwargs):
    """A modern card-style LabelFrame."""
    f = tk.LabelFrame(
        parent, text=title,
        bg=CARD, fg=TEXT,
        font=("Segoe UI", 10, "bold"),
        relief="flat", bd=0,
        highlightbackground=BORDER,
        highlightthickness=1,
        **kwargs
    )
    return f


def styled_button(parent, text, command, color=PRIMARY, width=18):
    """Flat modern button."""
    btn = tk.Button(
        parent, text=text, command=command,
        bg=color, fg="white",
        font=("Segoe UI", 9, "bold"),
        relief="flat", bd=0,
        cursor="hand2",
        activebackground=color,
        activeforeground="white",
        padx=10, pady=6,
        width=width
    )
    return btn


def styled_entry(parent, width=22):
    e = ttk.Entry(parent, width=width, font=("Segoe UI", 10))
    return e


class EditDialog(tk.Toplevel):
    """Reusable popup dialog for editing a record."""
    def __init__(self, parent, title, fields, values, callback):
        super().__init__(parent)
        self.title(title)
        self.configure(bg=BG)
        self.resizable(False, False)
        self.grab_set()

        self.callback = callback
        self.entries = {}

        tk.Label(self, text=title, bg=BG, fg=TEXT,
                 font=("Segoe UI", 12, "bold")).pack(pady=(16, 8), padx=20)

        form = tk.Frame(self, bg=BG)
        form.pack(padx=20, pady=8)

        for i, (field, value) in enumerate(zip(fields, values)):
            tk.Label(form, text=field, bg=BG, fg=MUTED,
                     font=("Segoe UI", 9)).grid(row=i, column=0, sticky="w", pady=4)
            e = ttk.Entry(form, width=22, font=("Segoe UI", 10))
            e.insert(0, str(value))
            e.grid(row=i, column=1, padx=(10, 0), pady=4)
            self.entries[field] = e

        btn_row = tk.Frame(self, bg=BG)
        btn_row.pack(pady=(8, 16), padx=20)
        styled_button(btn_row, "Save", self._save, color=SUCCESS, width=10).pack(side="left", padx=4)
        styled_button(btn_row, "Cancel", self.destroy, color=MUTED, width=10).pack(side="left", padx=4)

        self.geometry("+%d+%d" % (parent.winfo_rootx()+100, parent.winfo_rooty()+100))

    def _save(self):
        values = {k: e.get().strip() for k, e in self.entries.items()}
        self.callback(values)
        self.destroy()


class App:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Profit Calculation System")
        self.root.geometry("900x650")
        self.root.configure(bg=BG)

        self.db = Database()
        self.calculator = ProfitCalculator()
        self.analytics = Analytics(self.calculator)

        self._build_header()
        self._build_notebook()
        self._refresh_all()

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    # Header
    def _build_header(self):
        header = tk.Frame(self.root, bg=PRIMARY, height=52)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(header, text="📊  Profit Calculation System",
                 bg=PRIMARY, fg="white",
                 font=("Segoe UI", 14, "bold")).pack(side="left", padx=20, pady=12)

    # Notebook 
    def _build_notebook(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TNotebook", background=BG, borderwidth=0)
        style.configure("TNotebook.Tab", font=("Segoe UI", 10),
                        padding=[16, 8], background=BG, foreground=MUTED)
        style.map("TNotebook.Tab",
                  background=[("selected", CARD)],
                  foreground=[("selected", PRIMARY)])
        style.configure("Treeview", font=("Segoe UI", 9), rowheight=28,
                        background=CARD, fieldbackground=CARD, foreground=TEXT)
        style.configure("Treeview.Heading", font=("Segoe UI", 9, "bold"),
                        background=BG, foreground=TEXT)

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=12, pady=8)

        self.tab_t   = tk.Frame(self.notebook, bg=BG)
        self.tab_c   = tk.Frame(self.notebook, bg=BG)
        self.tab_dash = tk.Frame(self.notebook, bg=BG)
        self.tab_data = tk.Frame(self.notebook, bg=BG)
        self.tab_etl      = tk.Frame(self.notebook, bg=BG)
        self.tab_whatif   = tk.Frame(self.notebook, bg=BG)
        self.tab_funnel   = tk.Frame(self.notebook, bg=BG)
        self.tab_stats    = tk.Frame(self.notebook, bg=BG)

        self.notebook.add(self.tab_t,    text="  Transactions  ")
        self.notebook.add(self.tab_c,    text="  Cost Centers  ")
        self.notebook.add(self.tab_dash, text="  Dashboard  ")
        self.notebook.add(self.tab_data, text="  Data Table  ")
        self.notebook.add(self.tab_etl,    text="  ETL Import  ")
        self.notebook.add(self.tab_whatif, text="  What-if  ")
        self.notebook.add(self.tab_funnel, text="  Funnel  ")
        self.notebook.add(self.tab_stats,  text="  Statistics  ")

        self._build_transactions_tab()
        self._build_costs_tab()
        self._build_dashboard_tab()
        self._build_data_tab()
        self._build_etl_tab()
        self._build_whatif_tab()
        self._build_funnel_tab()
        self._build_stats_tab()
        self.notebook.bind("<<NotebookTabChanged>>", lambda e: self._refresh_all())



    # Tab 1: Transactions
    def _build_transactions_tab(self):
        left = card_frame(self.tab_t, "Add Transaction", padx=14, pady=10)
        left.pack(side="left", fill="y", padx=(10, 5), pady=10)

        fields = [("Product name", "t_name"), ("Price per unit ($)", "t_price"), ("Quantity sold", "t_qty")]
        self.t_entries = {}
        for i, (label, key) in enumerate(fields):
            tk.Label(left, text=label, bg=CARD, fg=MUTED,
                     font=("Segoe UI", 9)).grid(row=i*2, column=0, sticky="w", pady=(6,0))
            e = styled_entry(left)
            e.grid(row=i*2+1, column=0, pady=(2, 4))
            self.t_entries[key] = e

        styled_button(left, "＋  Add Transaction", self._add_transaction).grid(
            row=7, column=0, pady=12, sticky="ew")

        right = card_frame(self.tab_t, "Transaction Records", padx=8, pady=8)
        right.pack(side="left", fill="both", expand=True, padx=(5, 10), pady=10)

        cols = ("ID", "Product", "Price", "Qty", "Revenue")
        self.t_tree = ttk.Treeview(right, columns=cols, show="headings", height=14)
        widths = [40, 180, 90, 60, 100]
        for col, w in zip(cols, widths):
            self.t_tree.heading(col, text=col)
            self.t_tree.column(col, width=w, anchor="center")
        self.t_tree.pack(fill="both", expand=True)

        btn_row = tk.Frame(right, bg=CARD)
        btn_row.pack(pady=6)
        styled_button(btn_row, "✏  Edit", self._edit_transaction, color=WARNING, width=12).pack(side="left", padx=4)
        styled_button(btn_row, "🗑  Delete", self._delete_transaction, color=DANGER, width=12).pack(side="left", padx=4)

    # Tab 2: Cost Centers
    def _build_costs_tab(self):
        left = card_frame(self.tab_c, "Add Cost Center", padx=14, pady=10)
        left.pack(side="left", fill="y", padx=(10, 5), pady=10)

        tk.Label(left, text="Fixed cost: paid regardless of output\n(e.g. rent, salaries)",
                 bg=CARD, fg=MUTED, font=("Segoe UI", 8), justify="left",
                 wraplength=190).grid(row=0, column=0, sticky="w", pady=(0, 8))

        fields = [("Cost center name", "c_name"), ("Fixed cost ($)", "c_fixed"), ("Variable cost ($)", "c_variable")]
        self.c_entries = {}
        for i, (label, key) in enumerate(fields):
            tk.Label(left, text=label, bg=CARD, fg=MUTED,
                     font=("Segoe UI", 9)).grid(row=i*2+1, column=0, sticky="w", pady=(6,0))
            e = styled_entry(left)
            e.grid(row=i*2+2, column=0, pady=(2, 4))
            self.c_entries[key] = e

        styled_button(left, "＋  Add Cost Center", self._add_cost_center).grid(
            row=8, column=0, pady=12, sticky="ew")

        right = card_frame(self.tab_c, "Cost Center Records", padx=8, pady=8)
        right.pack(side="left", fill="both", expand=True, padx=(5, 10), pady=10)

        cols = ("ID", "Name", "Fixed ($)", "Variable ($)", "Total ($)")
        self.c_tree = ttk.Treeview(right, columns=cols, show="headings", height=14)
        widths = [40, 160, 100, 100, 100]
        for col, w in zip(cols, widths):
            self.c_tree.heading(col, text=col)
            self.c_tree.column(col, width=w, anchor="center")
        self.c_tree.pack(fill="both", expand=True)

        btn_row = tk.Frame(right, bg=CARD)
        btn_row.pack(pady=6)
        styled_button(btn_row, "✏  Edit", self._edit_cost_center, color=WARNING, width=12).pack(side="left", padx=4)
        styled_button(btn_row, "🗑  Delete", self._delete_cost_center, color=DANGER, width=12).pack(side="left", padx=4)

    # Tab 3: Dashboard 
    def _build_dashboard_tab(self):
        self.kpi_frame = tk.Frame(self.tab_dash, bg=BG)
        self.kpi_frame.pack(fill="x", padx=12, pady=(10, 4))

        self.fig, self.axes = plt.subplots(2, 2, figsize=(10, 5))
        self.fig.patch.set_facecolor(BG)

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.tab_dash)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=6)

    def _build_kpi_cards(self, revenue, costs, profit, margin, breakeven):
        for w in self.kpi_frame.winfo_children():
            w.destroy()

        kpis = [
            ("Revenue",       f"${revenue:,.2f}",   PRIMARY),
            ("Costs",         f"${costs:,.2f}",     DANGER),
            ("Profit",        f"${profit:,.2f}",    SUCCESS if profit >= 0 else DANGER),
            ("Profit margin", f"{margin:.1f}%",     SUCCESS if margin >= 0 else DANGER),
            ("Break-even",    f"{breakeven:.0f} units", WARNING),
        ]
        for label, value, color in kpis:
            card = tk.Frame(self.kpi_frame, bg=CARD,
                            highlightbackground=BORDER, highlightthickness=1)
            card.pack(side="left", expand=True, fill="both", padx=4)
            tk.Label(card, text=value, bg=CARD, fg=color,
                     font=("Segoe UI", 13, "bold")).pack(pady=(10, 2))
            tk.Label(card, text=label, bg=CARD, fg=MUTED,
                     font=("Segoe UI", 8)).pack(pady=(0, 10))

    # Tab 4: Data Table
    def _build_data_tab(self):
        t_frame = card_frame(self.tab_data, "All Transactions", padx=8, pady=8)
        t_frame.pack(fill="both", expand=True, padx=12, pady=(10, 5))

        cols = ("ID", "Product", "Price", "Qty", "Revenue", "Date")
        self.dt_tree = ttk.Treeview(t_frame, columns=cols, show="headings", height=7)
        widths = [40, 180, 90, 60, 100, 130]
        for col, w in zip(cols, widths):
            self.dt_tree.heading(col, text=col)
            self.dt_tree.column(col, width=w, anchor="center")
        self.dt_tree.pack(fill="both", expand=True)

        c_frame = card_frame(self.tab_data, "All Cost Centers", padx=8, pady=8)
        c_frame.pack(fill="both", expand=True, padx=12, pady=(5, 10))

        cols2 = ("ID", "Name", "Fixed ($)", "Variable ($)", "Total ($)", "Date")
        self.dc_tree = ttk.Treeview(c_frame, columns=cols2, show="headings", height=5)
        widths2 = [40, 160, 100, 100, 100, 130]
        for col, w in zip(cols2, widths2):
            self.dc_tree.heading(col, text=col)
            self.dc_tree.column(col, width=w, anchor="center")
        self.dc_tree.pack(fill="both", expand=True)


# Tab 5: Break even table
    def _build_breakeven_table(self, parent):
        frame = card_frame(parent, "Break-even Analysis per Product", padx=8, pady=8)
        frame.pack(fill="x", padx=10, pady=(4, 10))

        cols = ("Product", "Avg Price/unit", "Variable Cost/unit", "Contribution Margin", "Break-even Units", "Status")
        tree = ttk.Treeview(frame, columns=cols, show="headings", height=5)
        widths = [150, 110, 130, 150, 130, 120]
        for col, w in zip(cols, widths):
            tree.heading(col, text=col)
            tree.column(col, width=w, anchor="center")

        tree.tag_configure("ok",      background="#EDF7ED", foreground="#1E4620")
        tree.tag_configure("warning", background="#FFF8E1", foreground="#7A4F00")
        tree.tag_configure("danger",  background="#FDEDED", foreground="#5F2120")

        tree.pack(fill="x")
        return tree

# Tab 6: ETL Import
    def _build_etl_tab(self):
        info = card_frame(self.tab_etl, "CSV Import Pipeline (ETL)", padx=14, pady=12)
        info.pack(fill="x", padx=12, pady=10)

        tk.Label(info, text="Expected CSV format: product_name, price, quantity_sold",
                bg=CARD, fg=MUTED, font=("Segoe UI", 9)).pack(anchor="w")
        tk.Label(info, text="The pipeline will automatically clean, validate, and load your data.",
                bg=CARD, fg=MUTED, font=("Segoe UI", 9)).pack(anchor="w", pady=(2, 8))

        styled_button(info, "📂  Choose CSV file", self._run_etl, width=22).pack(anchor="w")

        log_frame = card_frame(self.tab_etl, "Pipeline Log", padx=10, pady=10)
        log_frame.pack(fill="both", expand=True, padx=12, pady=5)

        self.etl_log = tk.Text(log_frame, font=("Courier New", 10), height=15,
                            bg="#1A1A2E", fg="#00FF99", relief="flat",
                            state="disabled", padx=10, pady=10)
        self.etl_log.pack(fill="both", expand=True)

        export_frame = card_frame(self.tab_etl, "Export", padx=10, pady=10)
        export_frame.pack(fill="x", padx=12, pady=5)
        tk.Label(export_frame, text="Export all data + summary stats to Excel",
                bg=CARD, fg=MUTED, font=("Segoe UI", 9)).pack(anchor="w", pady=(0, 6))
        styled_button(export_frame, "💾  Export to Excel", self._export_excel, color=SUCCESS, width=22).pack(anchor="w")

    def _run_etl(self):
        filepath = filedialog.askopenfilename(
            title="Select CSV file",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if not filepath:
            return
        pipeline = ETLPipeline(self.db)
        result = pipeline.run(filepath)
        self._write_etl_log(result["log"])
        if result["success"]:
            messagebox.showinfo("ETL Complete", f"Successfully loaded {result['rows_loaded']} rows.")
            self._refresh_all()
        else:
            messagebox.showerror("ETL Failed", "Check the pipeline log for details.")

    def _write_etl_log(self, log_lines: list):
        self.etl_log.config(state="normal")
        self.etl_log.delete("1.0", tk.END)
        self.etl_log.insert(tk.END, "── ETL Pipeline Run ──────────────────────\n\n")
        for line in log_lines:
            self.etl_log.insert(tk.END, line + "\n")
        self.etl_log.config(state="disabled")

    def _export_excel(self):
        filepath = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx")],
            title="Save Excel export"
        )
        if not filepath:
            return
        try:
            self.analytics.export_to_csv(filepath)
            messagebox.showinfo("Export complete", f"Data saved to:\n{filepath}")
        except Exception as e:
            messagebox.showerror("Export failed", str(e))

    # Tab 7: What-if Simulator
    def _build_whatif_tab(self):
        ctrl = card_frame(self.tab_whatif, "Sensitivity Controls", padx=14, pady=12)
        ctrl.pack(fill="x", padx=12, pady=10)

        tk.Label(ctrl, text="Price change (%)", bg=CARD, fg=MUTED,
                font=("Segoe UI", 9)).grid(row=0, column=0, sticky="w", pady=4)
        self.price_slider = tk.Scale(ctrl, from_=-50, to=50, orient="horizontal",
                                    length=300, bg=CARD, fg=TEXT,
                                    highlightthickness=0, troughcolor=BORDER,
                                    command=lambda _: self._refresh_whatif())
        self.price_slider.grid(row=0, column=1, padx=12)
        self.price_val_label = tk.Label(ctrl, text="0%", bg=CARD, fg=PRIMARY,
                                        font=("Segoe UI", 10, "bold"), width=5)
        self.price_val_label.grid(row=0, column=2)

        tk.Label(ctrl, text="Variable cost change (%)", bg=CARD, fg=MUTED,
                font=("Segoe UI", 9)).grid(row=1, column=0, sticky="w", pady=4)
        self.cost_slider = tk.Scale(ctrl, from_=-50, to=50, orient="horizontal",
                                    length=300, bg=CARD, fg=TEXT,
                                    highlightthickness=0, troughcolor=BORDER,
                                    command=lambda _: self._refresh_whatif())
        self.cost_slider.grid(row=1, column=1, padx=12)
        self.cost_val_label = tk.Label(ctrl, text="0%", bg=CARD, fg=DANGER,
                                        font=("Segoe UI", 10, "bold"), width=5)
        self.cost_val_label.grid(row=1, column=2)

        result = card_frame(self.tab_whatif, "Projected Results", padx=14, pady=12)
        result.pack(fill="x", padx=12, pady=5)
        self.whatif_labels = {}
        rows = [
            ("revenue",       "Revenue",       0, 0),
            ("costs",         "Total Costs",   1, 0),
            ("profit",        "Profit",        2, 0),
            ("profit_change", "Profit Change", 0, 2),
            ("margin_change", "Margin Change", 1, 2),
        ]
        for key, label, row, col in rows:
            tk.Label(result, text=label, bg=CARD, fg=MUTED,
                    font=("Segoe UI", 9)).grid(row=row, column=col, sticky="w",
                                                padx=(0 if col == 0 else 40, 8), pady=6)
            lbl = tk.Label(result, text="—", bg=CARD, fg=TEXT,
                        font=("Segoe UI", 12, "bold"))
            lbl.grid(row=row, column=col+1, sticky="w", pady=6)
            self.whatif_labels[key] = lbl

        chart_frame = card_frame(self.tab_whatif, "Base vs Projected", padx=8, pady=8)
        chart_frame.pack(fill="both", expand=True, padx=12, pady=5)
        self.whatif_fig, self.whatif_ax = plt.subplots(1, 1, figsize=(8, 2.8))
        self.whatif_fig.patch.set_facecolor(BG)
        self.whatif_canvas = FigureCanvasTkAgg(self.whatif_fig, master=chart_frame)
        self.whatif_canvas.get_tk_widget().pack(fill="both", expand=True)

    def _refresh_whatif(self):
        price_pct = self.price_slider.get()
        cost_pct  = self.cost_slider.get()
        self.price_val_label.config(text=f"{price_pct:+}%")
        self.cost_val_label.config(text=f"{cost_pct:+}%")

        s = self.analytics.get_sensitivity(price_pct, cost_pct)
        if not s:
            return

        def color(val):
            return SUCCESS if val >= 0 else DANGER

        self.whatif_labels["revenue"].config(
            text=f"${s['base_revenue']:,.2f}  →  ${s['new_revenue']:,.2f}",
            fg=PRIMARY)
        self.whatif_labels["costs"].config(
            text=f"${s['base_costs']:,.2f}  →  ${s['new_costs']:,.2f}",
            fg=DANGER)
        self.whatif_labels["profit"].config(
            text=f"${s['base_profit']:,.2f}  →  ${s['new_profit']:,.2f}",
            fg=color(s["new_profit"]))
        self.whatif_labels["profit_change"].config(
            text=f"{s['profit_change']:+,.2f}",
            fg=color(s["profit_change"]))
        self.whatif_labels["margin_change"].config(
            text=f"{s['margin_change']:+.1f}%",
            fg=color(s["margin_change"]))

        # Update chart
        self.whatif_ax.clear()
        categories = ["Revenue", "Costs", "Profit"]
        base   = [s["base_revenue"],  s["base_costs"],  s["base_profit"]]
        new    = [s["new_revenue"],   s["new_costs"],   s["new_profit"]]
        x      = range(len(categories))
        width  = 0.35
        self.whatif_ax.bar([i - width/2 for i in x], base, width,
                            label="Base", color=PRIMARY, alpha=0.7)
        self.whatif_ax.bar([i + width/2 for i in x], new,  width,
                            label="Projected", color=WARNING, alpha=0.9)
        self.whatif_ax.set_xticks(list(x))
        self.whatif_ax.set_xticklabels(categories)
        self.whatif_ax.legend(fontsize=9)
        self.whatif_ax.yaxis.set_major_formatter(
            plt.FuncFormatter(lambda v, _: f"${v:,.0f}"))
        self.whatif_ax.set_facecolor(CARD)
        self.whatif_ax.spines[["top", "right"]].set_visible(False)
        self.whatif_fig.tight_layout()
        self.whatif_canvas.draw()

    # Tab 8: Funnel
    def _build_funnel_tab(self):
        self.funnel_frame = tk.Frame(self.tab_funnel, bg=BG)
        self.funnel_frame.pack(fill="both", expand=True, padx=12, pady=10)

        self.funnel_fig, self.funnel_ax = plt.subplots(figsize=(8, 4))
        self.funnel_fig.patch.set_facecolor(BG)
        self.funnel_canvas = FigureCanvasTkAgg(self.funnel_fig, master=self.funnel_frame)
        self.funnel_canvas.get_tk_widget().pack(fill="both", expand=True)

    def _refresh_funnel(self):
        funnel = self.analytics.get_funnel()
        self.funnel_ax.clear()

        if not funnel:
            self.funnel_ax.text(0.5, 0.5, "No data yet", ha="center", va="center")
            self.funnel_canvas.draw()
            return

        labels = [f[0] for f in funnel]
        values = [f[1] for f in funnel]
        colors = [PRIMARY, WARNING, SUCCESS, "#7B2FBE"]
        max_val = max(values) if values else 1

        self.funnel_ax.set_xlim(0, 1)
        self.funnel_ax.set_ylim(-0.5, len(funnel) - 0.5)
        self.funnel_ax.axis("off")

        for i, (label, value, color) in enumerate(zip(labels, values, colors)):
            bar_width = value / max_val * 0.8
            x_start   = (1 - bar_width) / 2
            y         = len(funnel) - 1 - i

            self.funnel_ax.barh(y, bar_width, left=x_start, height=0.55,
                                color=color, alpha=0.85)
            self.funnel_ax.text(0.5, y, f"{label}  —  {value}",
                                ha="center", va="center",
                                fontsize=11, fontweight="bold", color="white")

            if i > 0:
                prev_val = values[i - 1]
                conv = (value / prev_val * 100) if prev_val > 0 else 0
                self.funnel_ax.text(0.92, y, f"{conv:.0f}%",
                                    ha="left", va="center",
                                    fontsize=9, color=MUTED)

        self.funnel_ax.set_title("Product Conversion Funnel", fontsize=13,
                                fontweight="bold", pad=12)
        self.funnel_fig.tight_layout()
        self.funnel_canvas.draw()

    # Tab 9: Statistics
    def _build_stats_tab(self):
        self.stats_kpi  = tk.Frame(self.tab_stats, bg=BG)
        self.stats_kpi.pack(fill="x", padx=12, pady=10)

        self.stats_fig, self.stats_axes = plt.subplots(1, 2, figsize=(10, 3.5))
        self.stats_fig.patch.set_facecolor(BG)
        self.stats_canvas = FigureCanvasTkAgg(self.stats_fig, master=self.tab_stats)
        self.stats_canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=5)

    def _refresh_stats(self):
        stats = self.analytics.get_summary_stats()

        for w in self.stats_kpi.winfo_children():
            w.destroy()

        if not stats:
            tk.Label(self.stats_kpi, text="No data yet", bg=BG,
                    fg=MUTED, font=("Segoe UI", 11)).pack()
            return

        kpis = [
            ("Transactions",    str(stats["total_transactions"]),  PRIMARY),
            ("Units sold",      str(stats["total_units_sold"]),    PRIMARY),
            ("Avg revenue",     f"${stats['avg_revenue']:,.2f}",   SUCCESS),
            ("Median revenue",  f"${stats['median_revenue']:,.2f}",SUCCESS),
            ("Std deviation",   f"${stats['std_revenue']:,.2f}",   WARNING),
            ("Rev / unit",      f"${stats['revenue_per_unit']:,.2f}", SUCCESS),
            ("Top product",     stats["top_product"],              PRIMARY),
        ]
        for label, value, color in kpis:
            card = tk.Frame(self.stats_kpi, bg=CARD,
                            highlightbackground=BORDER, highlightthickness=1)
            card.pack(side="left", expand=True, fill="both", padx=3)
            tk.Label(card, text=value, bg=CARD, fg=color,
                    font=("Segoe UI", 10, "bold"), wraplength=90).pack(pady=(8, 2))
            tk.Label(card, text=label, bg=CARD, fg=MUTED,
                    font=("Segoe UI", 8)).pack(pady=(0, 8))

        # Charts: revenue distribution + top products bar
        for ax in self.stats_axes:
            ax.clear()

        transactions = self.calculator.transactions
        if transactions:
            import pandas as pd
            df = pd.DataFrame(transactions, columns=[
                "id", "product_name", "price", "quantity_sold", "revenue", "created_at"
            ])

            # Revenue distribution histogram
            self.stats_axes[0].hist(df["revenue"], bins=min(10, len(df)),
                                    color=PRIMARY, alpha=0.8, edgecolor="white")
            self.stats_axes[0].set_title("Revenue distribution", fontweight="bold", fontsize=10)
            self.stats_axes[0].set_xlabel("Revenue ($)")
            self.stats_axes[0].set_ylabel("Count")
            self.stats_axes[0].set_facecolor(CARD)
            self.stats_axes[0].spines[["top", "right"]].set_visible(False)

            # Top products by revenue
            top = df.groupby("product_name")["revenue"].sum().nlargest(8)
            self.stats_axes[1].barh(top.index, top.values, color=CHART_COLORS[:len(top)], alpha=0.85)
            self.stats_axes[1].set_title("Top products by revenue", fontweight="bold", fontsize=10)
            self.stats_axes[1].xaxis.set_major_formatter(
                plt.FuncFormatter(lambda x, _: f"${x:,.0f}"))
            self.stats_axes[1].set_facecolor(CARD)
            self.stats_axes[1].spines[["top", "right"]].set_visible(False)

        self.stats_fig.tight_layout(pad=2)
        self.stats_canvas.draw()

    # CRUD actions 
    def _add_transaction(self):
        try:
            name  = self.t_entries["t_name"].get().strip()
            price = float(self.t_entries["t_price"].get())
            qty   = int(self.t_entries["t_qty"].get())
            if not name:
                raise ValueError("Product name cannot be empty")
            self.db.insert_transaction(name, price, qty, price * qty)
            for e in self.t_entries.values():
                e.delete(0, tk.END)
            self._refresh_all()
        except ValueError as ex:
            messagebox.showerror("Input Error", str(ex))

    def _add_cost_center(self):
        try:
            name     = self.c_entries["c_name"].get().strip()
            fixed    = float(self.c_entries["c_fixed"].get())
            variable = float(self.c_entries["c_variable"].get())
            if not name:
                raise ValueError("Name cannot be empty")
            self.db.insert_cost_center(name, fixed, variable)
            for e in self.c_entries.values():
                e.delete(0, tk.END)
            self._refresh_all()
        except ValueError as ex:
            messagebox.showerror("Input Error", str(ex))

    def _get_selected_t_id(self):
        sel = self.t_tree.selection()
        if not sel:
            messagebox.showwarning("No selection", "Please select a transaction first.")
            return None
        return int(self.t_tree.item(sel[0])["values"][0])

    def _get_selected_c_id(self):
        sel = self.c_tree.selection()
        if not sel:
            messagebox.showwarning("No selection", "Please select a cost center first.")
            return None
        return int(self.c_tree.item(sel[0])["values"][0])

    def _edit_transaction(self):
        record_id = self._get_selected_t_id()
        if record_id is None:
            return
        row = next((r for r in self.calculator.transactions if r[0] == record_id), None)
        if not row:
            return

        def save(values):
            try:
                name  = values["Product name"]
                price = float(values["Price per unit ($)"])
                qty   = int(values["Quantity sold"])
                self.db.conn.execute(
                    "UPDATE transactions SET product_name=?, price=?, quantity_sold=?, revenue=? WHERE id=?",
                    (name, price, qty, price * qty, record_id)
                )
                self.db.conn.commit()
                self._refresh_all()
            except ValueError:
                messagebox.showerror("Error", "Invalid values entered.")

        EditDialog(self.root, "Edit Transaction",
                   ["Product name", "Price per unit ($)", "Quantity sold"],
                   [row[1], row[2], row[3]], save)

    def _edit_cost_center(self):
        record_id = self._get_selected_c_id()
        if record_id is None:
            return
        row = next((r for r in self.calculator.cost_centers if r[0] == record_id), None)
        if not row:
            return

        def save(values):
            try:
                name     = values["Name"]
                fixed    = float(values["Fixed cost ($)"])
                variable = float(values["Variable cost ($)"])
                self.db.conn.execute(
                    "UPDATE cost_centers SET name=?, fixed_cost=?, variable_cost=? WHERE id=?",
                    (name, fixed, variable, record_id)
                )
                self.db.conn.commit()
                self._refresh_all()
            except ValueError:
                messagebox.showerror("Error", "Invalid values entered.")

        EditDialog(self.root, "Edit Cost Center",
                   ["Name", "Fixed cost ($)", "Variable cost ($)"],
                   [row[1], row[2], row[3]], save)

    def _delete_transaction(self):
        record_id = self._get_selected_t_id()
        if record_id and messagebox.askyesno("Confirm", "Delete this transaction?"):
            self.db.delete_transaction(record_id)
            self._refresh_all()

    def _delete_cost_center(self):
        record_id = self._get_selected_c_id()
        if record_id and messagebox.askyesno("Confirm", "Delete this cost center?"):
            self.db.delete_cost_center(record_id)
            self._refresh_all()

    # Refresh
    def _refresh_all(self):
        transactions = self.db.get_all_transactions()
        cost_centers = self.db.get_all_cost_centers()
        total_units  = self.db.get_total_units_sold()
        self.calculator.load_from_db(transactions, cost_centers, total_units)

        self._refresh_t_tree(transactions)
        self._refresh_c_tree(cost_centers, total_units)
        self._refresh_data_table(transactions, cost_centers, total_units)
        self._refresh_dashboard()
        self._refresh_whatif()
        self._refresh_funnel()
        self._refresh_stats()

    def _refresh_t_tree(self, rows):
        self.t_tree.delete(*self.t_tree.get_children())
        for r in rows:
            self.t_tree.insert("", tk.END, values=(r[0], r[1], f"${r[2]:.2f}", r[3], f"${r[4]:.2f}"))

    def _refresh_c_tree(self, rows, total_units):
        self.c_tree.delete(*self.c_tree.get_children())
        for r in rows:
            total = r[2] + (r[3] * total_units)
            self.c_tree.insert("", tk.END, values=(
                r[0], r[1], f"${r[2]:.2f}", f"${r[3]:.2f}/unit", f"${total:.2f}"
            ))

    def _refresh_data_table(self, transactions, cost_centers, total_units):
        self.dt_tree.delete(*self.dt_tree.get_children())
        for r in transactions:
            self.dt_tree.insert("", tk.END, values=(
                r[0], r[1], f"${r[2]:.2f}", r[3], f"${r[4]:.2f}", r[5][:10]
            ))
        self.dc_tree.delete(*self.dc_tree.get_children())
        for r in cost_centers:
            total = r[2] + (r[3] * total_units)
            self.dc_tree.insert("", tk.END, values=(
                r[0], r[1], f"${r[2]:.2f}", f"${r[3]:.2f}/unit",
                f"${total:.2f}", r[4][:10]
            ))

    def _refresh_dashboard(self):
        revenue       = self.calculator.get_total_revenue()
        costs         = self.calculator.get_total_costs()
        profit        = self.calculator.get_profit()
        margin        = (profit / revenue * 100) if revenue > 0 else 0
        total_units   = self.calculator.total_units_sold
        total_fixed   = self.calculator.get_total_fixed_costs()
        transactions  = self.calculator.transactions
        cost_centers  = self.calculator.cost_centers

        avg_var_cost_per_unit = (
            sum(r[3] for r in cost_centers) if cost_centers else 0
        )

        # Simple overall break-even for KPI card
        avg_price = (revenue / total_units) if total_units > 0 else 1
        contribution = avg_price - avg_var_cost_per_unit
        breakeven_overall = (total_fixed / contribution) if contribution > 0 else float("inf")

        self._build_kpi_cards(revenue, costs, profit, margin, breakeven_overall)

        for ax in self.axes.flat:
            ax.clear()

        # Chart 1: Overview bar
        ax1 = self.axes[0, 0]
        bars = ax1.bar(["Revenue", "Costs", "Profit"],
                    [revenue, costs, profit],
                    color=[PRIMARY, DANGER, SUCCESS if profit >= 0 else DANGER],
                    width=0.5, edgecolor="white")
        ax1.bar_label(bars, fmt="$%.0f", fontsize=8, padding=3)
        ax1.set_title("Overview", fontweight="bold", fontsize=10)
        ax1.set_facecolor(CARD)
        ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"${x:,.0f}"))
        ax1.spines[["top", "right"]].set_visible(False)

        # Chart 2: Revenue by product pie
        ax2 = self.axes[0, 1]
        if transactions:
            labels = [r[1] for r in transactions]
            values = [r[4] for r in transactions]
            ax2.pie(values, labels=labels, autopct="%1.1f%%",
                    colors=CHART_COLORS[:len(values)],
                    startangle=90, textprops={"fontsize": 8})
        else:
            ax2.text(0.5, 0.5, "No data", ha="center", va="center")
        ax2.set_title("Revenue by product", fontweight="bold", fontsize=10)

        # Chart 3: Fixed vs variable stacked bar
        ax3 = self.axes[1, 0]
        if cost_centers:
            names  = [r[1] for r in cost_centers]
            fixed  = [r[2] for r in cost_centers]
            variab = [r[3] * total_units for r in cost_centers]
            x = range(len(names))
            ax3.bar(x, fixed,  label="Fixed",    color=WARNING, width=0.5)
            ax3.bar(x, variab, label="Variable", color=DANGER,  width=0.5, bottom=fixed)
            ax3.set_xticks(list(x))
            ax3.set_xticklabels(names, fontsize=8, rotation=15, ha="right")
            ax3.legend(fontsize=8)
            ax3.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"${x:,.0f}"))
        else:
            ax3.text(0.5, 0.5, "No data", ha="center", va="center")
        ax3.set_title("Fixed vs variable costs", fontweight="bold", fontsize=10)
        ax3.set_facecolor(CARD)
        ax3.spines[["top", "right"]].set_visible(False)

        # Chart 4: Cumulative profit line
        ax4 = self.axes[1, 1]
        if transactions:
            cumulative = []
            running = 0
            for r in transactions:
                running += r[4]
                cumulative.append(running - costs)
            ax4.plot(range(1, len(cumulative)+1), cumulative,
                    marker="o", color=PRIMARY, linewidth=2, markersize=5)
            ax4.fill_between(range(1, len(cumulative)+1), cumulative,
                            alpha=0.1, color=PRIMARY)
            ax4.axhline(0, color="gray", linewidth=0.8, linestyle="--")
            ax4.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"${x:,.0f}"))
            ax4.set_xlabel("Transactions", fontsize=8)
        else:
            ax4.text(0.5, 0.5, "No data", ha="center", va="center")
        ax4.set_title("Cumulative profit", fontweight="bold", fontsize=10)
        ax4.set_facecolor(CARD)
        ax4.spines[["top", "right"]].set_visible(False)

        self.fig.tight_layout(pad=2.5)
        self.canvas.draw()

        # Per-product break-even table
        # Clear and rebuild the table each refresh
        for widget in self.tab_dash.winfo_children():
            if isinstance(widget, tk.LabelFrame):
                widget.destroy()

        be_tree = self._build_breakeven_table(self.tab_dash)

        # Group transactions by product name, compute avg price
        product_data = {}
        for r in transactions:
            name = r[1]
            if name not in product_data:
                product_data[name] = {"total_revenue": 0, "total_qty": 0}
            product_data[name]["total_revenue"] += r[4]
            product_data[name]["total_qty"]     += r[3]

        for product_name, data in product_data.items():
            avg_price_product = (
                data["total_revenue"] / data["total_qty"]
                if data["total_qty"] > 0 else 0
            )
            contribution = avg_price_product - avg_var_cost_per_unit
            fixed_share  = total_fixed / len(product_data) if product_data else total_fixed

            if contribution > 0:
                be_units = fixed_share / contribution
                status   = "✔ Profitable"
                tag      = "ok"
            elif contribution == 0:
                be_units = float("inf")
                status   = "⚠ Marginal"
                tag      = "warning"
            else:
                be_units = float("inf")
                status   = "❌ Loses per unit"
                tag      = "danger"

            be_units_str = f"{be_units:.0f}" if be_units != float("inf") else "∞"

            be_tree.insert("", tk.END, values=(
                product_name,
                f"${avg_price_product:.2f}",
                f"${avg_var_cost_per_unit:.2f}",
                f"${contribution:.2f}",
                be_units_str,
                status
            ), tags=(tag,))

    def _on_close(self):
        self.db.close()
        plt.close("all")
        self.root.destroy()
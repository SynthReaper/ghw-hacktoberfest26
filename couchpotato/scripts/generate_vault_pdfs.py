"""
Generate sample PDF statements for CouchPotato encrypted vault.
Uses ReportLab to produce clean, realistic statements with exact amounts and metadata.
"""

import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

VAULT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "storage", "vault"))
os.makedirs(VAULT_DIR, exist_ok=True)

STATEMENTS = [
    {
        "filename": "pge_statement_2026_10.pdf",
        "vendor": "Pacific Gas & Electric",
        "date": "2026-10-15",
        "due_date": "2026-11-05",
        "account": "Account # 8821-4920-11",
        "amount": 268.40,
        "description": "Commercial Electric & Gas Service (Peak Summer Tariff Adjustment)",
        "tag": "ANOMALY SPIKE: Heatwave surge vs seasonal baseline"
    },
    {
        "filename": "verizon_fios_2026_10.pdf",
        "vendor": "Verizon Fios Business",
        "date": "2026-10-18",
        "due_date": "2026-11-02",
        "account": "Account # 4102-8831-09",
        "amount": 89.99,
        "description": "High-speed gigabit fiber internet office connection",
        "tag": "Recurring Monthly Commercial Broadband"
    },
    {
        "filename": "aws_tax_invoice_2026_10.pdf",
        "vendor": "AWS Cloud Infrastructure",
        "date": "2026-10-20",
        "due_date": "2026-10-28",
        "account": "Account # 9940-1288-02",
        "amount": 341.25,
        "description": "Elastic compute ec2 and s3 storage backend hosting",
        "tag": "Cloud Compute & Storage"
    },
    {
        "filename": "google_ads_receipt_2026_10.pdf",
        "vendor": "Google Ads",
        "date": "2026-10-21",
        "due_date": "2026-10-21",
        "account": "Account # 5512-3011-84",
        "amount": 460.00,
        "description": "Targeted search engine marketing for SaaS launch",
        "tag": "Search Engine Marketing"
    },
    {
        "filename": "wework_invoice_2026_10.pdf",
        "vendor": "WeWork Coworking",
        "date": "2026-10-01",
        "due_date": "2026-10-01",
        "account": "Account # 1098-4421-50",
        "amount": 550.00,
        "description": "Dedicated desk and team conference room monthly lease",
        "tag": "Office Lease & Workspace"
    },
    {
        "filename": "github_receipt_2026_10.pdf",
        "vendor": "GitHub Enterprise",
        "date": "2026-10-05",
        "due_date": "2026-10-05",
        "account": "Account # 3341-9012-77",
        "amount": 42.00,
        "description": "Team developer seats and code repository licensing",
        "tag": "Developer Tools & Version Control"
    },
    {
        "filename": "vercel_invoice_2026_10.pdf",
        "vendor": "Vercel Pro",
        "date": "2026-10-08",
        "due_date": "2026-10-08",
        "account": "Account # 3341-8910-12",
        "amount": 40.00,
        "description": "Edge web deployment and Next.js frontend hosting",
        "tag": "Frontend Cloud Deployment"
    },
    {
        "filename": "openai_receipt_2026_10.pdf",
        "vendor": "OpenAI API Platform",
        "date": "2026-10-12",
        "due_date": "2026-10-12",
        "account": "Account # 9940-7712-45",
        "amount": 85.71,
        "description": "LLM token generation inference and embeddings API",
        "tag": "AI Model Inference API"
    }
]

def generate_pdf(stmt):
    path = os.path.join(VAULT_DIR, stmt["filename"])
    c = canvas.Canvas(path, pagesize=letter)
    width, height = letter

    # Header Banner
    c.setFont("Helvetica-Bold", 18)
    c.drawString(72, height - 72, f"STATEMENT / TAX INVOICE: {stmt['vendor']}")

    c.setFont("Helvetica", 10)
    c.drawString(72, height - 92, stmt["tag"])

    # Divider line
    c.setLineWidth(1)
    c.line(72, height - 102, width - 72, height - 102)

    # Metadata Details
    c.setFont("Helvetica-Bold", 12)
    c.drawString(72, height - 130, stmt["account"])
    c.drawString(72, height - 150, f"Statement Date: {stmt['date']}")
    c.drawString(72, height - 170, f"Due Date: {stmt['due_date']}")

    c.setFont("Helvetica", 11)
    c.drawString(72, height - 200, f"Description: {stmt['description']}")

    # Amount box
    c.setFont("Helvetica-Bold", 16)
    formatted_amount = f"${stmt['amount']:.2f}"
    c.drawString(72, height - 240, f"Total Amount Due: {formatted_amount}")

    # Security Footprint
    c.setFont("Helvetica-Oblique", 9)
    c.drawString(72, height - 280, "Confidential & Proprietary - Auto-filed in CouchPotato Local Vault.")
    c.drawString(72, height - 295, "Parsed 100% offline via Local Gemma 2 (Ollama). Zero cloud leakage.")
    c.drawString(72, height - 310, "Classified via Prior Labs TabPFN-3.5 FastMCP for IRS Schedule C.")

    c.save()
    print(f"Generated {stmt['filename']}: {formatted_amount}")

if __name__ == "__main__":
    for s in STATEMENTS:
        generate_pdf(s)
    print("All 8 vault statements generated successfully.")

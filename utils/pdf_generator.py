from io import BytesIO
from fpdf import FPDF


def generate_pdf(bill_data):
    pdf = BillPDF(bill_data)
    return pdf.generate()


class BillPDF(FPDF):
    def __init__(self, bill):
        super().__init__(orientation="P", unit="mm", format="A4")
        self.bill = bill
        self.set_auto_page_break(auto=True, margin=20)

    def generate(self):
        self.add_page()
        self._header_section()
        self._customer_section()
        self._items_table()
        self._totals_section()
        self._footer_section()
        pdf_bytes = BytesIO()
        self.output(pdf_bytes)
        pdf_bytes.seek(0)
        return pdf_bytes

    def _header_section(self):
        self.set_font("Helvetica", "B", 20)
        self.set_text_color(26, 26, 46)
        self.cell(0, 10, "DENTAL BILLING", align="C")
        self.ln(6)
        self.set_font("Helvetica", "", 10)
        self.set_text_color(100, 100, 100)
        self.cell(0, 5, "Dental Clinic & Services", align="C")
        self.ln(8)

        is_gst = self.bill.get("is_gst", False)
        label = "GST INVOICE" if is_gst else "NON-GST INVOICE"
        self.set_font("Helvetica", "B", 10)
        if is_gst:
            self.set_text_color(46, 125, 50)
            self.set_draw_color(46, 125, 50)
        else:
            self.set_text_color(198, 40, 40)
            self.set_draw_color(198, 40, 40)
        self.set_line_width(0.5)
        self.cell(0, 7, label, align="C", border=1)
        self.ln(12)

    def _customer_section(self):
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(100, 100, 100)
        self.cell(95, 5, "BILL TO", align="L")
        self.cell(95, 5, "INVOICE", align="R")
        self.ln(5)

        self.set_font("Helvetica", "", 9)
        self.set_text_color(26, 26, 46)
        name = self.bill.get("customer_name", "Walk-in Customer")
        phone = self.bill.get("customer_phone", "")
        address = self.bill.get("customer_address", "")
        gstin = self.bill.get("customer_gstin", "")
        bill_no = self.bill.get("bill_number", "")
        is_gst = self.bill.get("is_gst", False)

        self.cell(95, 5, f"{name}", align="L")
        self.cell(95, 5, f"{bill_no}", align="R")
        self.ln(5)

        if phone:
            self.cell(95, 5, f"{phone}", align="L")
        else:
            self.cell(95, 5, "", align="L")
        self.cell(95, 5, "Date: Today", align="R")
        self.ln(5)

        if address:
            self.cell(95, 5, f"{address}", align="L")
        else:
            self.cell(95, 5, "", align="L")
        self.cell(95, 5, "", align="R")
        self.ln(5)

        if is_gst and gstin:
            self.cell(95, 5, f"GSTIN: {gstin}", align="L")
            self.ln(5)

        self.ln(5)

    def _items_table(self):
        col_w = [10, 75, 18, 18, 25, 22, 22]
        headers = ["#", "Item", "HSN", "Qty", "Rate", "GST%", "Total"]

        self.set_font("Helvetica", "B", 8)
        self.set_fill_color(26, 26, 46)
        self.set_text_color(255, 255, 255)
        for i, h in enumerate(headers):
            self.cell(col_w[i], 7, h, border=1, align="C", fill=True)
        self.ln()

        self.set_font("Helvetica", "", 8)
        self.set_text_color(26, 26, 46)
        fill = False
        for idx, item in enumerate(self.bill.get("items", []), 1):
            if fill:
                self.set_fill_color(245, 245, 245)
            else:
                self.set_fill_color(255, 255, 255)

            row = [
                str(idx),
                item.get("product_name", ""),
                item.get("hsn_code", ""),
                str(item.get("quantity", 1)),
                f'Rs. {item.get("price", 0):.2f}',
                f'{item.get("gst_rate", 0):.1f}%',
                f'Rs. {item.get("total", 0):.2f}',
            ]
            for i, val in enumerate(row):
                self.cell(col_w[i], 6, val, border=1, align="C", fill=True)
            self.ln()
            fill = not fill

        self.ln(5)

    def _totals_section(self):
        is_gst = self.bill.get("is_gst", False)
        subtotal = self.bill.get("subtotal", 0)
        gst_total = self.bill.get("gst_total", 0)
        grand_total = self.bill.get("grand_total", 0)

        col_w1 = 120
        col_w2 = 50

        self.set_font("Helvetica", "", 9)
        self.set_text_color(26, 26, 46)

        x_start = self.get_x()
        self.cell(col_w1, 6, "Subtotal:", align="R")
        self.set_x(x_start + col_w1)
        self.cell(col_w2, 6, f"Rs. {subtotal:.2f}", align="R")
        self.ln()

        if is_gst and gst_total > 0:
            self.cell(col_w1, 6, f"CGST @ 50%:", align="R")
            self.set_x(x_start + col_w1)
            self.cell(col_w2, 6, f"Rs. {gst_total / 2:.2f}", align="R")
            self.ln()

            self.cell(col_w1, 6, f"SGST @ 50%:", align="R")
            self.set_x(x_start + col_w1)
            self.cell(col_w2, 6, f"Rs. {gst_total / 2:.2f}", align="R")
            self.ln()

            self.cell(col_w1, 6, f"GST Total:", align="R")
            self.set_x(x_start + col_w1)
            self.cell(col_w2, 6, f"Rs. {gst_total:.2f}", align="R")
            self.ln()

        self.set_font("Helvetica", "B", 12)
        self.set_draw_color(26, 26, 46)
        self.set_line_width(0.5)
        y = self.get_y()
        self.set_y(y + 1)
        self.cell(col_w1, 8, "Grand Total:", align="R")
        self.set_x(x_start + col_w1)
        self.cell(col_w2, 8, f"Rs. {grand_total:.2f}", align="R", border="T")
        self.ln(10)

    def _footer_section(self):
        self.set_font("Helvetica", "", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 5, "Thank you for your visit! This is a computer-generated invoice.", align="C")

from fpdf import FPDF
from pathlib import Path


_FONT = "DejaVu"


class DiagnosticPDF(FPDF):
    def __init__(self):
        super().__init__()
        self.add_font("DejaVu", "", r"C:\Windows\Fonts\DejaVuSans.ttf", uni=True)
        self.add_font("DejaVu", "B", r"C:\Windows\Fonts\DejaVuSans-Bold.ttf", uni=True)
        self.add_font("DejaVu", "I", r"C:\Windows\Fonts\DejaVuSans-Oblique.ttf", uni=True)

    def header(self):
        self.set_font(_FONT, "B", 9)
        self.set_text_color(100, 100, 100)
        self.cell(0, 6, "UM_DIAGNOST", align="L")
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font(_FONT, "I", 7)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C")

    def section_title(self, title):
        self.set_font(_FONT, "B", 13)
        self.set_text_color(30, 64, 175)
        self.cell(0, 8, title)
        self.ln(4)
        self.set_draw_color(30, 64, 175)
        self.line(self.get_x(), self.get_y(), self.get_x() + 190, self.get_y())
        self.ln(5)

    def kv_row(self, key, val):
        self.set_font(_FONT, "B", 10)
        self.set_text_color(50, 50, 50)
        self.cell(60, 6, key)
        self.set_font(_FONT, "", 10)
        self.set_text_color(20, 20, 20)
        self.cell(0, 6, str(val))
        self.ln(6)

    def colored_cell(self, w, h, text, fill_color, align="C"):
        self.set_fill_color(*fill_color)
        self.set_text_color(255, 255, 255)
        self.set_font(_FONT, "B", 9)
        self.cell(w, h, text, align=align, fill=True)

    def data_cell(self, w, h, text, align="C"):
        self.set_font(_FONT, "", 9)
        self.set_text_color(20, 20, 20)
        self.cell(w, h, text, align=align)

    def label_cell(self, w, h, text):
        self.set_font(_FONT, "", 9)
        self.set_text_color(50, 50, 50)
        self.cell(w, h, text, align="L")


def generate_pdf(result, output_path=None):
    pdf = DiagnosticPDF()
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()

    s = result["summary"]
    file_name = result.get("file_name", "report")
    analysis_date = result.get("analysis_date", "")

    # Title
    pdf.set_font(_FONT, "B", 20)
    pdf.set_text_color(30, 64, 175)
    pdf.cell(0, 12, "Diagnostic Report", align="L")
    pdf.ln(14)

    pdf.set_font(_FONT, "", 9)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 5, f"File: {file_name}")
    pdf.ln(5)
    pdf.cell(0, 5, f"Date: {analysis_date}")
    pdf.ln(10)

    # 1. Summary
    pdf.section_title("1. Summary")
    quality = s.get("data_quality", "unknown")
    quality_colors = {"good": (22, 163, 74), "normal": (245, 158, 11), "bad": (220, 38, 38)}
    qc = quality_colors.get(quality.lower() if isinstance(quality, str) else "unknown", (100, 100, 100))

    pdf.kv_row("Rows:", s["rows"])
    pdf.kv_row("Columns:", s["columns"])
    pdf.kv_row("Missing:", f'{s["missing_pct"]}% ({s["total_missing"]} cells)')
    pdf.kv_row("Duplicates:", f'{s["duplicate_pct"]}% ({s["total_duplicates"]} rows)')

    pdf.set_font(_FONT, "B", 10)
    pdf.set_text_color(*qc)
    pdf.cell(60, 6, "Quality:")
    pdf.set_font(_FONT, "", 10)
    pdf.cell(0, 6, quality.upper() if isinstance(quality, str) else str(quality))
    pdf.ln(8)

    # 2. Grade Stats
    grade_stats = result.get("grade_stats")
    if grade_stats:
        pdf.section_title("2. Grade Statistics")
        criteria = list(grade_stats["per_criterion"].keys())

        col_w = [10, 72, 18, 18, 18, 18, 18]
        headers = ["#", "Criterion", "A", "B", "C", "Other", "Total"]

        pdf.set_font(_FONT, "B", 8)
        pdf.set_fill_color(30, 64, 175)
        pdf.set_text_color(255, 255, 255)
        for i, h in enumerate(headers):
            pdf.cell(col_w[i], 7, h, align="C" if i > 0 else "L", fill=True)
        pdf.ln()

        pdf.set_font(_FONT, "", 8)
        pdf.set_text_color(20, 20, 20)
        fill = False
        for idx, col_name in enumerate(criteria):
            g = grade_stats["per_criterion"][col_name]
            name_display = col_name if len(col_name) <= 60 else col_name[:57] + "..."

            if fill:
                pdf.set_fill_color(245, 247, 250)
            else:
                pdf.set_fill_color(255, 255, 255)

            pdf.cell(col_w[0], 6, str(idx + 1), align="C", fill=True)
            pdf.cell(col_w[1], 6, name_display, align="L", fill=True)
            pdf.cell(col_w[2], 6, str(g["A"]), align="C", fill=True)
            pdf.cell(col_w[3], 6, str(g["B"]), align="C", fill=True)
            pdf.cell(col_w[4], 6, str(g["C"]), align="C", fill=True)
            pdf.cell(col_w[5], 6, str(g.get("other", 0)), align="C", fill=True)
            pdf.cell(col_w[6], 6, str(g["total"]), align="C", fill=True)
            pdf.ln()
            fill = not fill

        pdf.ln(3)
        t = grade_stats["totals"]
        pdf.kv_row("Total assessments:", t["total"])
        pdf.kv_row("A (excellent):", f'{t["A"]} ({round(t["A"]/t["total"]*100, 1) if t["total"] else 0}%)')
        pdf.kv_row("B (good):", f'{t["B"]} ({round(t["B"]/t["total"]*100, 1) if t["total"] else 0}%)')
        pdf.kv_row("C (satisfactory):", f'{t["C"]} ({round(t["C"]/t["total"]*100, 1) if t["total"] else 0}%)')

        pdf.set_font(_FONT, "B", 11)
        pdf.set_text_color(30, 64, 175)
        pdf.cell(0, 7, f"Learning level (A+B): {grade_stats['learning_level']}%")
        pdf.ln(6)
        pdf.cell(0, 7, f"Independence (A): {grade_stats['independence']}%")
        pdf.ln(8)

    # 3. Problems
    problems = result.get("problems", [])
    if problems:
        section_num = "3" if not grade_stats else "3"
        pdf.section_title(f"{section_num}. Problems")

        p_col_w = [8, 30, 80, 40, 32]
        p_headers = ["#", "Type", "Description", "Rows", "Severity"]

        pdf.set_font(_FONT, "B", 8)
        pdf.set_fill_color(220, 38, 38)
        pdf.set_text_color(255, 255, 255)
        for i, h in enumerate(p_headers):
            pdf.cell(p_col_w[i], 7, h, align="C" if i > 0 else "L", fill=True)
        pdf.ln()

        sev_colors = {"red": (254, 242, 242), "yellow": (255, 251, 235), "green": (240, 253, 244)}
        for p in problems[:10]:
            sev = p.get("severity", "")
            if sev == "Высокая":
                bg = sev_colors["red"]
            elif sev == "Средняя":
                bg = sev_colors["yellow"]
            else:
                bg = sev_colors["green"]

            pdf.set_fill_color(*bg)
            pdf.set_font(_FONT, "", 7)
            pdf.set_text_color(30, 30, 30)

            desc = p.get("description", "")
            if len(desc) > 75:
                desc = desc[:72] + "..."

            pdf.cell(p_col_w[0], 6, str(p["id"]), align="C", fill=True)
            pdf.cell(p_col_w[1], 6, p["type"], align="L", fill=True)
            pdf.cell(p_col_w[2], 6, desc, align="L", fill=True)
            pdf.cell(p_col_w[3], 5, str(p.get("rows", "")), align="C", fill=True)
            pdf.cell(p_col_w[4], 6, sev, align="C", fill=True)
            pdf.ln()

        pdf.ln(3)

    # 4. Conclusions
    conclusions = result.get("conclusions", [])
    if conclusions:
        section_num = "4" if not grade_stats else "4"
        pdf.section_title(f"{section_num}. Conclusions")
        pdf.set_font(_FONT, "", 9)
        pdf.set_text_color(30, 30, 30)
        for c in conclusions:
            pdf.cell(0, 6, f" - {c}")
            pdf.ln(6)
        pdf.ln(2)

    # 5. Recommendations
    recommendations = result.get("recommendations", [])
    if recommendations:
        section_num = "5" if not grade_stats else "5"
        pdf.section_title(f"{section_num}. Recommendations")

        rec_col_w = [25, 85, 80]
        rec_headers = ["Priority", "Action", "Expected Effect"]

        pdf.set_font(_FONT, "B", 8)
        pdf.set_fill_color(30, 64, 175)
        pdf.set_text_color(255, 255, 255)
        for i, h in enumerate(rec_headers):
            pdf.cell(rec_col_w[i], 7, h, align="C", fill=True)
        pdf.ln()

        for r in recommendations:
            priority = r.get("priority", "")
            action = r.get("action", "")
            effect = r.get("expected_effect", "")

            if len(action) > 70:
                action = action[:67] + "..."

            pdf.set_font(_FONT, "", 8)
            pdf.set_text_color(30, 30, 30)

            pri_color = (220, 38, 38) if priority == "Высокий" else (245, 158, 11) if priority == "Средний" else (34, 197, 94)
            pdf.set_text_color(*pri_color)
            pdf.set_font(_FONT, "B", 8)
            pdf.cell(rec_col_w[0], 6, priority, align="C")

            pdf.set_text_color(30, 30, 30)
            pdf.set_font(_FONT, "", 8)
            pdf.cell(rec_col_w[1], 6, action, align="L")
            pdf.cell(rec_col_w[2], 6, effect, align="L")
            pdf.ln()

    if output_path:
        pdf.output(str(output_path))
    return str(output_path)


def save_pdf(result, output_path=None):
    if output_path is None:
        output_path = Path("reports") / f"{result.get('file_name', 'report')}.pdf"
    return generate_pdf(result, output_path)

import os
import glob
from datetime import datetime
from docx import Document
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH

# Paths (adjust if you move the folders)
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
SCREENS_DIR = os.path.join(PROJECT_ROOT, "screenshots")
OUTPUT_DOCX = os.path.join(PROJECT_ROOT, "BTP_Report.docx")

# Helper to add a heading with proper style
def add_heading(doc, text, level=1):
    heading = doc.add_heading(text, level=level)
    heading.alignment = WD_ALIGN_PARAGRAPH.CENTER
    return heading

# Helper to add a paragraph with optional bold/italic
def add_paragraph(doc, text, bold=False, italic=False, size=12, align="left"):
    p = doc.add_paragraph()
    run = p.add_run(text)
    run.bold = bold
    run.italic = italic
    font = run.font
    font.size = Pt(size)
    if align == "center":
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    elif align == "right":
        p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    else:
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    return p

# -----------------------------------------------------------------------------
# 1. Create document and title page
# -----------------------------------------------------------------------------

doc = Document()

# Title page
add_heading(doc, "Kerala Climate Network (Vyuham)", level=0)
add_paragraph(doc, "Bachelor Thesis Project (BTP)", bold=True, size=14, align="center")
add_paragraph(doc, "Submitted by: <YOUR NAME>", size=12, align="center")
add_paragraph(doc, f"Date: {datetime.now().strftime('%d %B %Y')}", size=12, align="center")
# add a page break after title page
doc.add_page_break()

# -----------------------------------------------------------------------------
# 2. Abstract
# -----------------------------------------------------------------------------
add_heading(doc, "Abstract", level=1)
abstract_text = (
    "This project builds a synchronized monsoon‑precipitation network for Kerala, "
    "evaluates its robustness to node removal, and validates network centrality "
    "against observed landslide events.  The end‑to‑end Python pipeline generates "
    "contract files that are visualised in a React‑Vite dashboard.  Results show "
    "that random failures have little impact, whereas targeted removal of high‑" 
    "centrality nodes quickly fragments the network.  All centrality metrics are "
    "significantly positively correlated with landslide density, demonstrating "
    "the relevance of network topology for hazard assessment."
)
add_paragraph(doc, abstract_text, size=11)

doc.add_page_break()

# -----------------------------------------------------------------------------
# 3. Introduction
# -----------------------------------------------------------------------------
add_heading(doc, "Introduction", level=1)
intro_text = (
    "Kerala experiences intense monsoon precipitation that drives river discharge "
    "and landslide activity.  Understanding how precipitation synchronises across "
    "the state can reveal hidden connectivity and resilience properties.  This "
    "project constructs a precipitation synchronisation network, investigates its "
    "structural robustness, and tests whether network centrality predicts observed "
    "landslide occurrences."
)
add_paragraph(doc, intro_text)

doc.add_page_break()

# -----------------------------------------------------------------------------
# 4. Methodology (pipeline overview)
# -----------------------------------------------------------------------------
add_heading(doc, "Methodology", level=1)
method_steps = [
    "Stage 1 – Download raw datasets (rainfall, DEM, basin shapefiles, landslide points).",
    "Stage 2 – Build a 0.25° land‑mask grid and assign each cell to a river basin.",
    "Stage 3 – Extract JJAS extreme wet‑day events per grid cell.",
    "Stage 4 – Compute pair‑wise event‑synchronisation matrix (Numba accelerated).",
    "Stage 5 – Construct weighted network, keep top 5 % links, compute centralities (degree, betweenness, eigenvector, clustering).",
    "Stage 6 – Robustness experiments: random, degree‑based, betweenness‑based node removal; measure LCC size & global efficiency.",
    "Stage 7 – Landslide validation: attach landslide points and slope to cells; bootstrap Spearman correlations between centralities (and slope) and landslide density.",
    "Stage 8 – Export all results as JSON/GeoJSON contract files for the front‑end."
]
for step in method_steps:
    add_paragraph(doc, f"• {step}")

doc.add_page_break()

# -----------------------------------------------------------------------------
# 5. Results (with screenshots)
# -----------------------------------------------------------------------------
add_heading(doc, "Results", level=1)

# We assume screenshots are named with a numeric prefix to enforce order, e.g.
# 01_overview.png, 02_robustness.png, 03_landslide.png …
image_files = sorted(glob.glob(os.path.join(SCREENS_DIR, "*.png")))
if not image_files:
    add_paragraph(doc, "*No screenshots found in the 'screenshots' folder. Please capture the required UI pages and place them there before re‑running this script.*", italic=True)
else:
    for img_path in image_files:
        img_name = os.path.basename(img_path)
        # Derive a friendly caption from the file name (strip extension, replace '_' with ' ')
        caption = os.path.splitext(img_name)[0].replace('_', ' ').title()
        add_heading(doc, caption, level=2)
        # Insert image – width limited to 6 inches to keep layout nice
        doc.add_picture(img_path, width=Inches(6))
        # Add a brief description (you may edit this later manually)
        add_paragraph(doc, f"Figure: {caption} – captured from the web dashboard.", italic=True)
        doc.add_paragraph()  # blank line

# -----------------------------------------------------------------------------
# 6. Discussion
# -----------------------------------------------------------------------------
add_heading(doc, "Discussion", level=1)
discussion_text = (
    "The robustness analysis shows that the precipitation synchronisation network is "
    "highly resilient to random node loss but fragile when hub nodes (high degree or "
    "betweenness) are removed.  This suggests that localized disturbances, such as "
    "extreme rainfall events concentrated in hub cells, could disproportionately "
    "disrupt regional hydrology.\n\n"
    "Landslide validation demonstrates that cells with high centrality exhibit a "
    "significant positive correlation with observed landslide density, even after "
    "controlling for terrain slope.  Thus, network topology provides additional "
    "predictive insight beyond traditional topographic analysis."
)
add_paragraph(doc, discussion_text)

doc.add_page_break()

# -----------------------------------------------------------------------------
# 7. Conclusion
# -----------------------------------------------------------------------------
add_heading(doc, "Conclusion", level=1)
conclusion_text = (
    "We have built a reproducible end‑to‑end workflow that integrates data acquisition, "
    "network construction, robustness experiments, and landslide validation, and we have "
    "exposed the results through an interactive React dashboard.  The scientific "
    "findings confirm that the monsoon precipitation network is structurally vulnerable "
    "to targeted attacks and that network centrality is a meaningful predictor of landslide "
    "risk.  These insights are directly applicable to climate‑hazard risk assessment "
    "in the Kerala region."
)
add_paragraph(doc, conclusion_text)

doc.add_page_break()

# -----------------------------------------------------------------------------
# 8. Appendix – all screenshots
# -----------------------------------------------------------------------------
add_heading(doc, "Appendix – Screenshots", level=1)
if image_files:
    for img_path in image_files:
        img_name = os.path.basename(img_path)
        caption = os.path.splitext(img_name)[0].replace('_', ' ').title()
        add_heading(doc, caption, level=2)
        doc.add_picture(img_path, width=Inches(6))
        add_paragraph(doc, f"Figure: {caption}", italic=True)
        doc.add_paragraph()
else:
    add_paragraph(doc, "No screenshots were provided.")

# Save the document
doc.save(OUTPUT_DOCX)
print(f"Word report generated: {OUTPUT_DOCX}")

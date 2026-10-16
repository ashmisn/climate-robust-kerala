# RUN_INSTRUCTIONS.md

---

## How to run the Kerala Climate Network (Vyuham) project and create a BTP‑style Word report

### 1. Prerequisites
1. **Node.js** (v24+). Make sure it is on your `PATH`:
   ```powershell
   $env:PATH = "C:\Program Files\nodejs;" + $env:PATH
   ```
2. **Python 3.12** (already used for the data pipeline).
3. **PowerShell** (built‑in on Windows) for the commands below.
4. **Optional – python‑docx** (for the automatic Word generation step). Install it once:
   ```powershell
   pip install python-docx
   ```

---

### 2. Run the data pipeline (only needed if you want to rebuild the contracts)
```powershell
# From the project root
cd "C:\Users\Ashmi_SN\Desktop\btpproject"
# Execute the full pipeline (stages 1‑8)
powershell -File run_pipeline.ps1
```
All contract files will appear under `web/public/data/`.

---

### 3. Launch the React + Vite front‑end
```powershell
cd "C:\Users\Ashmi_SN\Desktop\btpproject\web"
npm install            # one‑time dependency install
npm run dev            # starts dev server on http://localhost:3000
```
Your default browser should automatically open the dashboard.

---

### 4. Capture screenshots
1. **Create a folder for the images**
   ```powershell
   mkdir "C:\Users\Ashmi_SN\Desktop\btpproject\screenshots"
   ```
2. **Use the Windows Snipping Tool (Win+Shift+S)**
   * Press `Win+Shift+S` → select *Rectangular Snip*.
   * Capture the part of the browser you want (e.g., Overview page, Robustness curves, Landslide validation).
   * After you release the mouse, the image is copied to the clipboard.
   * Open *Paint* (or any image editor), paste (`Ctrl+V`), and **save** the file as `screenshots/01_overview.png`, `screenshots/02_robustness.png`, etc.
3. **Alternative – PowerShell one‑liner** (captures the whole primary monitor):
   ```powershell
   Add-Type -AssemblyName System.Windows.Forms
   $bounds = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
   $bitmap = New-Object System.Drawing.Bitmap $bounds.Width, $bounds.Height
   $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
   $graphics.CopyFromScreen($bounds.Location, [System.Drawing.Point]::Empty, $bounds.Size)
   $filename = "C:\Users\Ashmi_SN\Desktop\btpproject\screenshots\$(Get-Date -Format 'yyyyMMdd_HHmmss')_full.png"
   $bitmap.Save($filename, [System.Drawing.Imaging.ImageFormat]::Png)
   $graphics.Dispose()
   $bitmap.Dispose()
   Write-Host "Saved screenshot to $filename"
   ```
   Run this command after you have the UI on the screen you want to capture – it will store a timestamped PNG in the `screenshots` folder.

---

### 5. Generate the Word document automatically (optional)
The script **generate_report.py** (see next section) reads all PNG files in the `screenshots` folder and creates a nicely formatted Word (`.docx`) file called `BTP_Report.docx`.

**Steps:**
1. Save the script below as `generate_report.py` in the project root.
2. Make sure you have `python-docx` installed (`pip install python-docx`).
3. Run the script:
   ```powershell
   python generate_report.py
   ```
4. The file `BTP_Report.docx` will appear in the project root. Open it in Microsoft Word, adjust any formatting, and you are ready to submit.

---

### 6. What the final Word document contains
| Section | Content |
|---------|---------|
| **Title page** | Project title, your name, course, date. |
| **Abstract** | One‑paragraph summary of the problem, approach, and main findings. |
| **Introduction** | Scientific background and objectives. |
| **Methodology** | Pipeline stages (1‑8) and brief description of each. |
| **Results** | • Robustness curves (with screenshot) <br>• Landslide‑validation scatter plot (with screenshot) |
| **Discussion** | Interpretation of the findings (robustness, centrality‑landslide link). |
| **Conclusion** | Key take‑aways for a BTP. |
| **Appendix** | All captured screenshots in order, plus any extra notes. |

---

### 7. Quick checklist for a BTP submission
1. Run the pipeline (or verify the contract files exist).  
2. Launch the UI, navigate to each page you want to showcase.  
3. Capture screenshots and store them in `screenshots/` with meaningful names.  
4. Run `python generate_report.py` to build the Word file.  
5. Open `BTP_Report.docx`, review formatting, add the title page and your personal details.  
6. Export to PDF if required by your university.

---

**You are now ready to run the application, document the results with screenshots, and generate a professional BTP‑style Word report.**

# Professional PDF Export Improvements

## Overview
The PDF export functionality has been completely redesigned to produce professional, office-quality PDFs with headers, footers, and proper formatting - similar to invoices and professional reports.

## What Changed

### Before
- Plain table export with minimal formatting
- No headers or footers
- Basic gray background for table headers
- No company information
- No page numbers
- No professional styling

### After
- **Professional header** with:
  - Company/farm name (large, bold, white text)
  - Company address and phone
  - Report title (right-aligned)
  - Subtitle (if provided)
  - Date and page numbers
  - Professional blue background (#2980b9)

- **Professional footer** with:
  - Company information
  - Generation timestamp
  - Page numbers (Page X of Y)
  - Light gray background

- **Enhanced table styling**:
  - Professional blue header (#3498db)
  - White header text (bold)
  - Alternating row colors (white/light gray)
  - Proper borders and spacing
  - Optimized column widths
  - Support for totals row (if needed)

- **Multi-page support**:
  - Automatic pagination
  - Headers and footers on every page
  - Proper page numbering

## New Files Created

1. **`egg_farm_system/utils/pdf_exporter.py`**
   - `ProfessionalPDFExporter` class
   - Handles all PDF generation with professional formatting
   - Supports headers, footers, multi-page, totals rows

## Files Updated

1. **`egg_farm_system/ui/widgets/datatable.py`**
   - Updated `export_pdf()` method to use `ProfessionalPDFExporter`
   - Added automatic title detection from parent widgets
   - Supports custom titles, subtitles, and company information

2. **`egg_farm_system/config.py`**
   - Added company information settings:
     - `COMPANY_NAME`
     - `COMPANY_ADDRESS`
     - `COMPANY_PHONE`

3. **`egg_farm_system/ui/reports/report_viewer.py`**
   - Updated to pass report titles and subtitles to PDF export
   - Extracts report metadata for better PDF headers

## Usage

### Basic Usage (Automatic)
```python
# In any DataTableWidget
table.export_pdf()  # Uses defaults, detects title from parent
```

### Advanced Usage (Custom)
```python
table.export_pdf(
    path="report.pdf",
    title="Sales Report",
    subtitle="Q1 2024",
    company_name="My Farm",
    company_address="123 Farm Road",
    company_phone="+93 700 123 456"
)
```

## Configuration

Edit `egg_farm_system/config.py` to set default company information:

```python
COMPANY_NAME = "Your Farm Name"
COMPANY_ADDRESS = "Your Address"
COMPANY_PHONE = "Your Phone Number"
```

## Features

### ✅ Professional Header
- Company name and details
- Report title and subtitle
- Date and page numbers
- Professional blue color scheme

### ✅ Professional Footer
- Company information
- Generation timestamp
- Page numbers

### ✅ Enhanced Table
- Professional styling
- Alternating row colors
- Proper borders
- Optimized column widths
- Support for totals row

### ✅ Multi-page Support
- Automatic pagination
- Headers/footers on all pages
- Proper page numbering

### ✅ Smart Title Detection
- Automatically detects title from parent widgets
- Falls back to sensible defaults

## PDF Structure

```
┌─────────────────────────────────────┐
│  HEADER (Blue Background)           │
│  Company Name | Title | Date | Page │
├─────────────────────────────────────┤
│                                     │
│  TABLE (Professional Styling)       │
│  - Blue header                      │
│  - Alternating rows                 │
│  - Proper borders                   │
│                                     │
├─────────────────────────────────────┤
│  FOOTER (Gray Background)           │
│  Company Info | Timestamp | Page    │
└─────────────────────────────────────┘
```

## Color Scheme

- **Header Background**: #2980b9 (Professional Blue)
- **Table Header**: #3498db (Lighter Blue)
- **Alternating Rows**: White / #f5f5f5 (Light Gray)
- **Footer Background**: #ecf0f1 (Very Light Gray)
- **Text Colors**: White (headers), Black (content), Gray (footer)

## Examples

### Sales Report PDF
- Title: "Sales Report"
- Subtitle: "Period: 2024-01-01 to 2024-01-31"
- Company: "Egg Farm Management System"
- Includes all sales transactions in professional table format

### Production Report PDF
- Title: "Production Report"
- Subtitle: "Farm: Main Farm"
- Company: "Egg Farm Management System"
- Includes production data with proper formatting

## Benefits

1. **Professional Appearance**: PDFs now look like official business documents
2. **Branding**: Company information prominently displayed
3. **Information**: Date, page numbers, and generation timestamp included
4. **Readability**: Better formatting and spacing
5. **Multi-page**: Proper handling of large datasets
6. **Customizable**: Easy to customize company info and titles

## Future Enhancements (Optional)

1. Logo support in header
2. Custom color schemes
3. Watermark support
4. Additional summary sections
5. Charts/graphs in PDF
6. Custom footer templates

---

**Status**: ✅ **COMPLETE - Professional PDF Export Implemented**

All PDF exports throughout the application now use the professional exporter automatically.


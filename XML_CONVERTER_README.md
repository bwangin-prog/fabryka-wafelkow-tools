# XML to CSV Converter - Streamlit App

Web application for converting supplier XML feeds to CSV format for BaseLinker import.

## Features

- **7 Supplier Integrations**: Scandinavian Baby, Jabadabadoo, Kids Inspirations, Solution BC, B.toys, Maxima, Bristle Blocks
- **Real-time Conversion**: Fetches and parses XML feeds on demand
- **Filtering**: Filter by producer name and minimum stock levels
- **Producer Analytics**: View product breakdown by producer
- **Data Preview**: See first 10 products before downloading
- **CSV Export**: Download with semicolon delimiter for BaseLinker

## Installation

```bash
# Install dependencies
pip install -r requirements.txt
```

## Running Locally

```bash
# Start the Streamlit app
streamlit run xml_converter_app.py
```

The app will open in your browser at `http://localhost:8501`

## Deployment Options

### Streamlit Community Cloud

1. Push code to GitHub repository
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub account
4. Deploy from repository
5. App will be live at `https://your-app.streamlit.app`

### Docker

```bash
# Build image
docker build -t xml-converter .

# Run container
docker run -p 8501:8501 xml-converter
```

### Heroku

```bash
# Create Procfile
echo "web: streamlit run xml_converter_app.py --server.port=\$PORT" > Procfile

# Deploy
heroku create your-app-name
git push heroku main
```

## Usage

1. **Select Supplier**: Choose from dropdown in sidebar
2. **Apply Filters** (optional):
   - Filter by producer name
   - Set minimum stock threshold
3. **Click "Convert to CSV"**: Fetches and parses XML
4. **Review Results**:
   - View statistics (total products, stock count, producers)
   - Check producer breakdown
   - Preview first 10 products
5. **Download CSV**: Click download button for full CSV file

## CSV Format

Output CSV uses semicolon (`;`) delimiter with these columns:

- `product_id`: Supplier product ID
- `ean`: EAN/GTIN barcode
- `name`: Product name (Polish)
- `producer`: Manufacturer/brand name
- `category`: Product category
- `category_path`: Full category hierarchy
- `version`: Product variant (if applicable)
- `price_gross`: Gross price
- `price_net`: Net price
- `vat`: VAT rate
- `currency`: Currency code (PLN)
- `stock`: Available stock quantity
- `url`: Product URL
- `description`: Product description (truncated to 500 chars)

## Supported Suppliers

| Supplier | Products | Format | Description |
|----------|----------|--------|-------------|
| Scandinavian Baby | 1800+ | IOF 3.0 | Baby Dan, Leander |
| Jabadabadoo | 500+ | Soteshop | Wooden toys |
| Kids Inspirations | 2000+ | IOF 3.0 | Multi-brand toys |
| Solution BC | 1500+ | IOF 3.0 | Lilliputiens, Janod, EZPZ |
| B.toys | 300+ | Soteshop | B.toys products |
| Maxima | 1000+ | Custom XML | Maxima toys |
| Bristle Blocks | 200+ | Soteshop | Construction toys |

## Architecture

- **Frontend**: Streamlit (Python-based web framework)
- **XML Parsing**: ElementTree (Python stdlib)
- **CSV Generation**: Python csv module
- **No Database**: Stateless, fetches fresh data on each conversion

## Adding New Suppliers

Edit `xml_converter_app.py` and add to `SUPPLIERS` dict:

```python
"New Supplier": {
    "url": "https://supplier.com/feed.xml",
    "parser": "iof_format",  # or soteshop_format, maxima_format
    "description": "Product description"
}
```

For custom XML formats, create new parser function:

```python
def parse_custom_format(xml_data: bytes) -> List[Dict]:
    # Parse XML and return list of product dicts
    pass
```

## Troubleshooting

**Timeout errors**: Some XML feeds are large (10+ MB). Increase timeout:
```python
urllib.request.urlopen(url, timeout=60)
```

**Missing products**: Check XML structure matches parser expectations

**Encoding issues**: All parsers use UTF-8. If supplier uses different encoding, add:
```python
xml_data.decode('iso-8859-2')  # Example for Latin-2
```

## License

Internal tool for Fabryka Wafelkow operations.

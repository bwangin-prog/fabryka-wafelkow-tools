# Enhanced Features Guide

## 🎉 New Features

### 1. **XML File Upload**
- No longer limited to predefined URLs
- Upload any XML file from your computer
- Auto-detects XML format (IOF, Soteshop, Maxima)
- Works offline with local files

**How to use:**
1. Go to "XML to CSV Converter" tab
2. Select "Upload XML File"
3. Click "Browse files" and select your XML
4. App automatically detects format and parses

---

### 2. **Tabbed Preview Interface**

Three organized tabs for better data exploration:

**📊 Summary Tab:**
- Total stock across all products
- Average price
- Average stock per product
- Quick overview metrics

**📋 Data Preview Tab:**
- View first 50 products in table format
- See EAN, Name, Producer, Stock, Price
- Clean, easy-to-scan interface
- Download CSV for full data

**🏭 Producers Tab:**
- Breakdown by producer/brand
- Product count per producer
- Total stock per producer
- Average stock per producer
- Sorted by product count

---

### 3. **BaseLinker API Manager** 🔌

**Natural Language Action Builder:**

Simply type what you want to do in plain English:

**Example Commands:**
- `list products` - Get all products from inventory
- `get inventories` - See all your inventories
- `get categories` - List all categories
- `search ean 1234567890` - Find product by barcode
- `get product details 12345` - Get specific product info
- `get warehouses` - List all warehouses

**Quick Action Buttons:**
- 📦 List Products
- 📂 Get Categories
- 🏢 Get Inventories
- 🏭 Get Warehouses

**Features:**
- Translates plain English to API calls
- Shows API method and parameters
- Displays results in formatted tables
- Handles errors gracefully
- No coding required!

---

## 🔧 Configuration

### For Streamlit Cloud:

Add to your app secrets (Settings → Secrets):

```toml
# Password protection
password = "your_secure_password"

# BaseLinker API (for API Manager tab)
baselinker_token = "your-baselinker-token"
baselinker_inventory_id = "81501"
```

### For Local Development:

Edit `.streamlit/secrets.toml`:

```toml
password = "your_password"
baselinker_token = "5016123-5062031-..."
baselinker_inventory_id = "81501"
```

---

## 📋 Supported API Commands

### Products
- `list products` - Get product list (paginated)
- `get product details [ID]` - Get specific product
- `search ean [barcode]` - Search by EAN/barcode

### Inventory Management
- `get inventories` - List all inventories
- `get categories` - List categories
- `get warehouses` - List warehouses

### Coming Soon
- Stock updates
- Price changes
- Bulk operations
- Category assignments

---

## 💡 Tips

1. **XML Upload**: Perfect for testing feeds before they go live
2. **Filters**: Use producer filter + min stock to focus on available products
3. **Tabs**: Switch between tabs to analyze data from different angles
4. **API Builder**: Start with simple commands like "list products"
5. **CSV Export**: All filters apply to the downloaded CSV

---

## 🆘 Troubleshooting

**XML Upload not working?**
- Ensure file is valid XML (not corrupted)
- Check file size (<10MB recommended)
- Try a different XML format

**API not responding?**
- Verify `baselinker_token` is set in secrets
- Check your BaseLinker account has API access
- Ensure inventory_id is correct

**Can't see Producers tab?**
- Make sure products were successfully parsed
- Check that XML contains producer/brand information

---

## 🚀 Quick Start

1. **XML Conversion:**
   - Upload file OR select supplier
   - Click "Convert to CSV"
   - Use filters if needed
   - Download CSV

2. **API Management:**
   - Go to "BaseLinker API" tab
   - Type command (e.g., "list products")
   - Click "Execute"
   - View results

---

Your app now has:
✅ File upload capability
✅ Three-tab preview system
✅ BaseLinker API integration
✅ Natural language command interface
✅ Enhanced data visualization

Deployed at: https://github.com/bwangin-prog/fabryka-wafelkow-tools

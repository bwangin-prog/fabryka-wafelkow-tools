#!/usr/bin/env python3
"""
XML to CSV Converter & BaseLinker API Manager - Streamlit Web Application
Unified interface for converting supplier XML feeds to CSV format and managing BaseLinker inventory
"""

import streamlit as st
import urllib.request
import xml.etree.ElementTree as ET
import csv
import io
import re
import json
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import time
import hmac
from urllib import parse


# Supplier configurations
SUPPLIERS = {
    "Scandinavian Baby": {
        "url": "https://hurt.scandinavianbaby.pl/edi/export-offer.php?client=kamila.wangin@fabrykawafelkow.pl&language=pol&token=866e053c7cc228fc5301f65&shop=6&type=full&format=xml&iof_3_0",
        "parser": "iof_format",
        "description": "Baby Dan, Leander products"
    },
    "Jabadabadoo": {
        "url": "https://jabadabado.pl/module/xmlfeeds/api?id=7",
        "parser": "soteshop_format",
        "description": "Jabadabadoo wooden toys"
    },
    "Kids Inspirations": {
        "url": "https://kidsinspirations.pl/module/xmlfeeds/api?id=11",
        "parser": "iof_format",
        "description": "Multiple toy producers"
    },
    "Solution BC": {
        "url": "https://hurtownia.solutionbc.pl/module/xmlfeeds/api?id=11",
        "parser": "iof_format",
        "description": "Lilliputiens, Janod, EZPZ"
    },
    "B.toys": {
        "url": "https://btoys.com.pl/module/xmlfeeds/api?id=7",
        "parser": "soteshop_format",
        "description": "B.toys products"
    },
    "Maxima": {
        "url": "https://maxima-zabawki.pl/xml/xml7.xml",
        "parser": "maxima_format",
        "description": "Maxima toys"
    },
    "Bristle Blocks": {
        "url": "https://bristleblocks.pl/module/xmlfeeds/api?id=7",
        "parser": "soteshop_format",
        "description": "Bristle Blocks construction toys"
    }
}


def clean_html(text: str) -> str:
    """Remove HTML tags and clean text."""
    if not text:
        return ''
    text = re.sub(r'<[^>]+>', '', text)
    text = text.replace('&gt;', '>').replace('&lt;', '<').replace('&amp;', '&')
    text = text.replace('&nbsp;', ' ').replace('&quot;', '"')
    text = ' '.join(text.split())
    return text.strip()


def extract_text(element, path: str, default: str = '') -> str:
    """Safely extract text from XML element."""
    if element is None:
        return default
    found = element.find(path)
    if found is not None and found.text:
        return found.text.strip()
    return default


def extract_cdata(element, tag: str, lang: str = 'pol') -> str:
    """Extract CDATA content from description tags with language attribute."""
    if element is None:
        return ''
    
    for child in element.findall(tag):
        if child.get('{http://www.w3.org/XML/1998/namespace}lang') == lang:
            if child.text:
                return clean_html(child.text)
    
    first = element.find(tag)
    if first is not None and first.text:
        return clean_html(first.text)
    
    return ''


def parse_iof_format(xml_data: bytes) -> List[Dict]:
    """Parse IOF format XML (Scandinavian Baby, Kids Inspirations, Solution BC)."""
    root = ET.fromstring(xml_data)
    products = []
    
    for prod in root.findall('.//product'):
        product_id = prod.get('id', '')
        ean = prod.get('code_on_card', '')
        vat = prod.get('vat', '23.0')
        currency = prod.get('currency', 'PLN')
        
        producer_elem = prod.find('producer')
        producer = producer_elem.get('name', '') if producer_elem is not None else ''
        
        category_elem = prod.find('category')
        category = category_elem.get('name', '') if category_elem is not None else ''
        
        category_idosell = prod.find('category_idosell')
        category_path = category_idosell.get('path', '') if category_idosell is not None else ''
        
        card_elem = prod.find('card')
        url = card_elem.get('url', '') if card_elem is not None else ''
        
        desc_elem = prod.find('description')
        name_pol = extract_cdata(desc_elem, 'name', 'pol')
        long_desc = extract_cdata(desc_elem, 'long_desc', 'pol')
        
        version_elem = desc_elem.find('version') if desc_elem is not None else None
        version = ''
        if version_elem is not None:
            version_name = version_elem.find('name[@{http://www.w3.org/XML/1998/namespace}lang="pol"]')
            if version_name is not None and version_name.text:
                version = version_name.text.strip()
            elif version_elem.get('name'):
                version = version_elem.get('name')
        
        price_gross = ''
        price_net = ''
        stock_quantity = '0'
        
        price_elem = prod.find('price')
        if price_elem is not None:
            price_gross = price_elem.get('gross', '')
            price_net = price_elem.get('net', '')
        
        stock_elem = prod.find('stock')
        if stock_elem is not None:
            stock_quantity = stock_elem.get('quantity', '0')
        
        sizes_elem = prod.find('sizes')
        if sizes_elem is not None:
            size_price = sizes_elem.find('price')
            if size_price is not None:
                price_gross = size_price.get('gross', price_gross)
                price_net = size_price.get('net', price_net)
            
            size_stock = sizes_elem.find('stock')
            if size_stock is not None:
                stock_quantity = size_stock.get('quantity', stock_quantity)
            
            for size in sizes_elem.findall('size'):
                size_price = size.find('price')
                if size_price is not None and not price_gross:
                    price_gross = size_price.get('gross', price_gross)
                    price_net = size_price.get('net', price_net)
                
                size_stock = size.find('stock')
                if size_stock is not None:
                    qty = size_stock.get('quantity', '0')
                    try:
                        stock_quantity = str(int(float(stock_quantity)) + int(float(qty)))
                    except (ValueError, TypeError):
                        pass
        
        products.append({
            'product_id': product_id,
            'ean': ean,
            'name': name_pol,
            'producer': producer,
            'category': category,
            'category_path': category_path,
            'version': version,
            'price_gross': price_gross,
            'price_net': price_net,
            'vat': vat,
            'currency': currency,
            'stock': stock_quantity,
            'url': url,
            'description': long_desc[:500]
        })
    
    return products


def parse_soteshop_format(xml_data: bytes) -> List[Dict]:
    """Parse Soteshop format XML (Jabadabadoo, B.toys, Bristle Blocks)."""
    root = ET.fromstring(xml_data)
    products = []
    
    for prod in root.findall('.//product'):
        product_id = prod.get('id', '')
        ean = extract_text(prod, 'producer_code', '')
        name = extract_text(prod, 'name', '')
        producer = extract_text(prod, 'producer', '')
        
        category_elem = prod.find('category')
        category = category_elem.text.strip() if category_elem is not None and category_elem.text else ''
        
        description_elem = prod.find('description')
        description = clean_html(description_elem.text) if description_elem is not None and description_elem.text else ''
        
        price_elem = prod.find('price')
        price_gross = price_elem.get('gross', '0') if price_elem is not None else '0'
        price_net = price_elem.get('net', '0') if price_elem is not None else '0'
        
        stock_elem = prod.find('stock')
        stock = stock_elem.get('quantity', '0') if stock_elem is not None else '0'
        
        url = extract_text(prod, 'url', '')
        
        products.append({
            'product_id': product_id,
            'ean': ean,
            'name': name,
            'producer': producer,
            'category': category,
            'category_path': '',
            'version': '',
            'price_gross': price_gross,
            'price_net': price_net,
            'vat': '23.0',
            'currency': 'PLN',
            'stock': stock,
            'url': url,
            'description': description[:500]
        })
    
    return products


def parse_maxima_format(xml_data: bytes) -> List[Dict]:
    """Parse Maxima format XML."""
    root = ET.fromstring(xml_data)
    products = []
    
    for prod in root.findall('.//product'):
        product_id = prod.get('id', '')
        ean = extract_text(prod, 'ean', '')
        name = extract_text(prod, 'name', '')
        producer = extract_text(prod, 'producer', '')
        category = extract_text(prod, 'category', '')
        description = extract_text(prod, 'description', '')
        
        price_gross = extract_text(prod, 'price_gross', '0')
        price_net = extract_text(prod, 'price_net', '0')
        stock = extract_text(prod, 'stock', '0')
        url = extract_text(prod, 'url', '')
        
        products.append({
            'product_id': product_id,
            'ean': ean,
            'name': name,
            'producer': producer,
            'category': category,
            'category_path': '',
            'version': '',
            'price_gross': price_gross,
            'price_net': price_net,
            'vat': '23.0',
            'currency': 'PLN',
            'stock': stock,
            'url': url,
            'description': clean_html(description)[:500]
        })
    
    return products


def fetch_and_parse(supplier_name: str, config: Dict) -> Tuple[List[Dict], Optional[str]]:
    """Fetch XML and parse into products."""
    try:
        with st.spinner(f'Fetching XML from {supplier_name}...'):
            with urllib.request.urlopen(config['url'], timeout=30) as response:
                xml_data = response.read()
        
        with st.spinner(f'Parsing {supplier_name} products...'):
            if config['parser'] == 'iof_format':
                products = parse_iof_format(xml_data)
            elif config['parser'] == 'soteshop_format':
                products = parse_soteshop_format(xml_data)
            elif config['parser'] == 'maxima_format':
                products = parse_maxima_format(xml_data)
            else:
                return [], f"Unknown parser: {config['parser']}"
        
        return products, None
        
    except Exception as e:
        return [], str(e)


def create_csv(products: List[Dict]) -> str:
    """Convert products to CSV string."""
    output = io.StringIO()
    
    fieldnames = [
        'product_id', 'ean', 'name', 'producer', 'category', 'category_path',
        'version', 'price_gross', 'price_net', 'vat', 'currency', 'stock',
        'url', 'description'
    ]
    
    writer = csv.DictWriter(output, fieldnames=fieldnames, delimiter=';')
    writer.writeheader()
    writer.writerows(products)
    
    return output.getvalue()


def check_password():
    """Returns `True` if the user had the correct password."""

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if "password" not in st.secrets:
            # No password configured, allow access
            st.session_state["password_correct"] = True
            return
        
        if hmac.compare_digest(st.session_state["password"], st.secrets["password"]):
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Don't store the password
        else:
            st.session_state["password_correct"] = False

    # Return True if the password is validated
    if st.session_state.get("password_correct", False):
        return True

    # Show input for password
    st.text_input(
        "🔒 Enter Password", type="password", on_change=password_entered, key="password"
    )
    if "password_correct" in st.session_state:
        st.error("😕 Password incorrect")
    return False


def baselinker_api_call(method: str, parameters: Dict) -> Dict:
    """Make a call to BaseLinker API"""
    if "baselinker_token" not in st.secrets:
        return {"status": "ERROR", "error": "BaseLinker API token not configured in secrets"}
    
    url = 'https://api.baselinker.com/connector.php'
    payload = {
        'method': method,
        'parameters': json.dumps(parameters)
    }
    data = parse.urlencode(payload).encode('utf-8')
    
    try:
        req = urllib.request.Request(url, data=data, headers={
            'X-BLToken': st.secrets["baselinker_token"]
        })
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except Exception as e:
        return {"status": "ERROR", "error": str(e)}


def parse_natural_language_action(user_input: str) -> Tuple[Optional[str], Optional[Dict], str]:
    """Parse natural language into BaseLinker API call"""
    user_input = user_input.lower().strip()
    
    # Get products / List products
    if any(word in user_input for word in ["list products", "get products", "show products", "view products"]):
        inventory_id = st.secrets.get("baselinker_inventory_id", "81501")
        return "getInventoryProductsList", {"inventory_id": int(inventory_id), "page": 1}, "Listing products from inventory"
    
    # Get product details by ID
    if "product details" in user_input or "get product" in user_input:
        match = re.search(r'\d+', user_input)
        if match:
            product_id = match.group()
            inventory_id = st.secrets.get("baselinker_inventory_id", "81501")
            return "getInventoryProductsData", {
                "inventory_id": int(inventory_id),
                "products": [product_id]
            }, f"Getting details for product {product_id}"
        return None, None, "Please specify product ID (e.g., 'get product details 12345')"
    
    # Get inventories
    if "inventories" in user_input or "list inventory" in user_input:
        return "getInventories", {}, "Getting list of inventories"
    
    # Get categories
    if "categories" in user_input:
        inventory_id = st.secrets.get("baselinker_inventory_id", "81501")
        return "getInventoryCategories", {"inventory_id": int(inventory_id)}, "Getting categories"
    
    # Search by EAN
    if "ean" in user_input or "barcode" in user_input:
        match = re.search(r'\d{8,13}', user_input)
        if match:
            ean = match.group()
            return "getInventoryProductsList", {
                "inventory_id": int(st.secrets.get("baselinker_inventory_id", "81501")),
                "filter_ean": ean,
                "page": 1
            }, f"Searching for product with EAN {ean}"
        return None, None, "Please specify EAN number"
    
    # Update stock
    if "update stock" in user_input or "set stock" in user_input:
        return None, None, "Stock updates require: 'update stock [product_id] to [quantity]' (e.g., 'update stock 12345 to 50')"
    
    # Get warehouses
    if "warehouse" in user_input:
        return "getInventoryWarehouses", {}, "Getting list of warehouses"
    
    return None, None, "I don't understand that command. Try: 'list products', 'get inventories', 'get categories', 'search ean 1234567890'"


def xml_converter_tab():
    """Tab for XML to CSV conversion"""
    st.markdown("### 📄 XML to CSV Converter")
    st.markdown("Convert supplier XML feeds to CSV format for BaseLinker import")
    
    # Two modes: URL or Upload
    mode = st.radio("Choose input method:", ["Fetch from URL", "Upload XML File"], horizontal=True)
    
    if mode == "Upload XML File":
        uploaded_file = st.file_uploader("Upload XML file", type=['xml'])
        
        if uploaded_file is not None:
            xml_content = uploaded_file.read()
            
            # Try to detect format
            st.info("Detecting XML format...")
            try:
                root = ET.fromstring(xml_content)
                
                # Detect format
                if root.tag == 'products' and root.find('.//product/producer') is not None:
                    parser_type = "iof_format"
                    st.success("✅ Detected: IOF 3.0 format")
                elif root.tag == 'offer' and root.find('.//products/product') is not None:
                    parser_type = "soteshop_format"
                    st.success("✅ Detected: Soteshop format")
                elif root.find('.//product') is not None:
                    parser_type = "maxima_format"
                    st.success("✅ Detected: Maxima format")
                else:
                    st.error("❌ Unknown XML format")
                    return
                
                # Parse based on detected format
                if parser_type == "iof_format":
                    products = parse_iof_format(root)
                elif parser_type == "soteshop_format":
                    products = parse_soteshop_format(root)
                else:
                    products = parse_maxima_format(root)
                
                display_products_and_export(products, "Uploaded XML")
                
            except ET.ParseError as e:
                st.error(f"❌ XML Parse Error: {e}")
            except Exception as e:
                st.error(f"❌ Error: {e}")
    
    else:  # Fetch from URL
        st.sidebar.header("Configuration")
        
        selected_supplier = st.sidebar.selectbox(
            "Select Supplier",
            options=list(SUPPLIERS.keys()),
            help="Choose which supplier XML feed to convert"
        )
        
        config = SUPPLIERS[selected_supplier]
        
        st.sidebar.markdown(f"**Description:** {config['description']}")
        st.sidebar.markdown(f"**Parser:** {config['parser']}")
        
        # Main area
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown(f"### {selected_supplier}")
            st.markdown(f"**Feed URL:** `{config['url']}`")
        
        with col2:
            convert_button = st.button("🚀 Convert to CSV", type="primary", use_container_width=True)
        
        if convert_button:
            products, error = fetch_and_parse(selected_supplier, config)
            
            if error:
                st.error(f"❌ Error: {error}")
                return
            
            if not products:
                st.warning("⚠️ No products found in XML feed")
                return
            
            display_products_and_export(products, selected_supplier)


def display_products_and_export(products: List[Dict], source_name: str):
    """Display products with filters and export options"""
    # Get unique producers for dropdown
    unique_producers = sorted(set(p['producer'] for p in products))
    
    # Filters in sidebar
    st.sidebar.subheader("Filters")
    
    filter_producer = st.sidebar.selectbox(
        "Filter by Producer",
        options=["All Producers"] + unique_producers,
        help="Select a specific producer or view all"
    )
    
    filter_min_stock = st.sidebar.number_input(
        "Minimum Stock",
        min_value=0,
        value=0,
        help="Only show products with stock >= this value"
    )
    
    # Apply filters
    filtered_products = products
    
    if filter_producer != "All Producers":
        filtered_products = [
            p for p in filtered_products 
            if p['producer'] == filter_producer
        ]
    
    if filter_min_stock > 0:
        filtered_products = [
            p for p in filtered_products 
            if int(float(p.get('stock', 0))) >= filter_min_stock
        ]
    
    # Display statistics
    st.success(f"✅ Successfully parsed {len(products)} products")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Products", len(products))
    
    with col2:
        products_with_stock = sum(1 for p in products if int(float(p.get('stock', 0))) > 0)
        st.metric("With Stock", products_with_stock)
    
    with col3:
        unique_producers_count = len(set(p['producer'] for p in products))
        st.metric("Unique Producers", unique_producers_count)
    
    with col4:
        st.metric("After Filters", len(filtered_products))
    
    # Tabs for different views
    tab1, tab2, tab3 = st.tabs(["📊 Summary", "📋 Data Preview", "🏭 Producers"])
    
    with tab1:
        st.subheader("Summary Statistics")
        
        total_stock = sum(int(float(p.get('stock', 0))) for p in filtered_products)
        avg_price = sum(float(p.get('price', 0)) for p in filtered_products) / len(filtered_products) if filtered_products else 0
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Stock", f"{total_stock:,}")
        with col2:
            st.metric("Avg Price", f"{avg_price:.2f} PLN")
        with col3:
            avg_stock = total_stock / len(filtered_products) if filtered_products else 0
            st.metric("Avg Stock/Product", f"{avg_stock:.1f}")
    
    with tab2:
        st.subheader("Product Data Preview")
        if filtered_products:
            # Convert to dataframe-like display
            preview_data = []
            for p in filtered_products[:50]:  # Show first 50
                preview_data.append({
                    "EAN": p.get('ean', ''),
                    "Name": p.get('name', '')[:50] + "..." if len(p.get('name', '')) > 50 else p.get('name', ''),
                    "Producer": p.get('producer', ''),
                    "Stock": int(float(p.get('stock', 0))),
                    "Price": f"{float(p.get('price', 0)):.2f}"
                })
            st.dataframe(preview_data, use_container_width=True, height=400)
            if len(filtered_products) > 50:
                st.info(f"Showing first 50 of {len(filtered_products)} products. Download CSV for full data.")
        else:
            st.info("No products match the current filters")
    
    with tab3:
        st.subheader("📊 Producer Breakdown")
        if products:
            producer_counts = {}
            producer_stock = {}
            for p in products:
                prod = p['producer']
                stock = int(float(p.get('stock', 0)))
                if prod not in producer_counts:
                    producer_counts[prod] = 0
                    producer_stock[prod] = 0
                producer_counts[prod] += 1
                producer_stock[prod] += stock
            
            producer_data = [
                {
                    "Producer": k,
                    "Products": v,
                    "Total Stock": producer_stock[k],
                    "Avg Stock": f"{producer_stock[k] / v:.1f}"
                }
                for k, v in sorted(producer_counts.items(), key=lambda x: -x[1])
            ]
            st.dataframe(producer_data, use_container_width=True)
    
    # CSV Export
    st.markdown("---")
    st.subheader("📥 Download CSV")
    
    if filtered_products:
        csv_data = create_csv(filtered_products)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{source_name.lower().replace(' ', '_')}_{timestamp}.csv"
        
        st.download_button(
            label="⬇️ Download CSV File",
            data=csv_data,
            file_name=filename,
            mime="text/csv",
            use_container_width=True
        )
    else:
        st.info("No products to export with current filters")


def baselinker_api_tab():
    """Tab for BaseLinker API management"""
    st.markdown("### 🔌 BaseLinker API Manager")
    st.markdown("Interact with your BaseLinker inventory using natural language commands")
    
    # Check if API is configured
    if "baselinker_token" not in st.secrets:
        st.warning("⚠️ BaseLinker API token not configured")
        st.markdown("""
        To use this feature, add to your Streamlit secrets:
        ```toml
        baselinker_token = "your-token-here"
        baselinker_inventory_id = "81501"
        ```
        """)
        return
    
    st.success("✅ BaseLinker API configured")
    
    # Natural language interface
    st.subheader("💬 Action Builder")
    st.markdown("Tell me what you want to do in plain English, and I'll translate it to an API call.")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        user_command = st.text_input(
            "What would you like to do?",
            placeholder="e.g., 'list products', 'get inventories', 'search ean 1234567890'",
            help="Examples: 'list products', 'get categories', 'get product details 12345', 'search ean 1234567890'"
        )
    
    with col2:
        execute_button = st.button("🚀 Execute", type="primary", use_container_width=True)
    
    # Common actions shortcuts
    st.markdown("**Quick Actions:**")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("📦 List Products", use_container_width=True):
            user_command = "list products"
            execute_button = True
    
    with col2:
        if st.button("📂 Get Categories", use_container_width=True):
            user_command = "get categories"
            execute_button = True
    
    with col3:
        if st.button("🏢 Get Inventories", use_container_width=True):
            user_command = "get inventories"
            execute_button = True
    
    with col4:
        if st.button("🏭 Get Warehouses", use_container_width=True):
            user_command = "get warehouses"
            execute_button = True
    
    if execute_button and user_command:
        method, params, description = parse_natural_language_action(user_command)
        
        if method is None:
            st.error(f"❌ {description}")
        else:
            st.info(f"🔄 {description}...")
            st.code(f"API Method: {method}\nParameters: {json.dumps(params, indent=2)}", language="json")
            
            with st.spinner("Calling BaseLinker API..."):
                result = baselinker_api_call(method, params)
            
            if result.get("status") == "SUCCESS":
                st.success("✅ API call successful!")
                
                # Display results based on method
                if method == "getInventoryProductsList":
                    products = result.get("products", {})
                    st.metric("Products Found", len(products))
                    if products:
                        product_list = [{"ID": k, "Name": v} for k, v in list(products.items())[:20]]
                        st.dataframe(product_list, use_container_width=True)
                        if len(products) > 20:
                            st.info(f"Showing first 20 of {len(products)} products")
                
                elif method == "getInventories":
                    inventories = result.get("inventories", [])
                    st.metric("Inventories Found", len(inventories))
                    if inventories:
                        inv_data = [{
                            "ID": inv.get("inventory_id"),
                            "Name": inv.get("name"),
                            "Products": inv.get("products_quantity", 0)
                        } for inv in inventories]
                        st.dataframe(inv_data, use_container_width=True)
                
                elif method == "getInventoryCategories":
                    categories = result.get("categories", [])
                    st.metric("Categories Found", len(categories))
                    if categories:
                        cat_data = [{
                            "ID": cat.get("category_id"),
                            "Name": cat.get("name"),
                            "Parent ID": cat.get("parent_id", "-")
                        } for cat in categories]
                        st.dataframe(cat_data, use_container_width=True)
                
                else:
                    st.json(result)
            
            else:
                st.error(f"❌ API Error: {result.get('error_message', result.get('error', 'Unknown error'))}")
                st.json(result)


def main():
    st.set_page_config(
        page_title="XML Converter & BaseLinker Manager",
        page_icon="📊",
        layout="wide"
    )
    
    # Check password first
    if not check_password():
        st.stop()  # Do not continue if check_password is not True
    
    st.title("🔄 XML Converter & BaseLinker API Manager")
    st.markdown("Manage supplier feeds and BaseLinker inventory in one place")
    
    # Main tabs
    tab1, tab2 = st.tabs(["📄 XML to CSV Converter", "🔌 BaseLinker API"])
    
    with tab1:
        xml_converter_tab()
    
    with tab2:
        baselinker_api_tab()


if __name__ == "__main__":
    main()

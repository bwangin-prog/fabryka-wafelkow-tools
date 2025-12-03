#!/usr/bin/env python3
"""
XML to CSV Converter - Streamlit Web Application
Unified interface for converting supplier XML feeds to CSV format
"""

import streamlit as st
import urllib.request
import xml.etree.ElementTree as ET
import csv
import io
import re
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import time


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


def main():
    st.set_page_config(
        page_title="XML to CSV Converter",
        page_icon="📊",
        layout="wide"
    )
    
    st.title("🔄 XML to CSV Converter")
    st.markdown("Convert supplier XML feeds to CSV format for BaseLinker import")
    
    # Sidebar - Supplier selection
    st.sidebar.header("Configuration")
    
    selected_supplier = st.sidebar.selectbox(
        "Select Supplier",
        options=list(SUPPLIERS.keys()),
        help="Choose which supplier XML feed to convert"
    )
    
    config = SUPPLIERS[selected_supplier]
    
    st.sidebar.markdown(f"**Description:** {config['description']}")
    st.sidebar.markdown(f"**Parser:** {config['parser']}")
    
    # Filters
    st.sidebar.subheader("Filters")
    
    filter_producer = st.sidebar.text_input(
        "Filter by Producer",
        help="Leave empty for all producers, or enter producer name"
    )
    
    filter_min_stock = st.sidebar.number_input(
        "Minimum Stock",
        min_value=0,
        value=0,
        help="Only show products with stock >= this value"
    )
    
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
        
        # Apply filters
        filtered_products = products
        
        if filter_producer:
            filtered_products = [
                p for p in filtered_products 
                if filter_producer.lower() in p['producer'].lower()
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
            unique_producers = len(set(p['producer'] for p in products))
            st.metric("Unique Producers", unique_producers)
        
        with col4:
            st.metric("After Filters", len(filtered_products))
        
        # Producer breakdown
        if products:
            producer_counts = {}
            for p in products:
                prod = p['producer']
                if prod not in producer_counts:
                    producer_counts[prod] = 0
                producer_counts[prod] += 1
            
            st.subheader("📊 Producer Breakdown")
            producer_df_data = [
                {"Producer": k, "Count": v} 
                for k, v in sorted(producer_counts.items(), key=lambda x: -x[1])
            ]
            st.dataframe(producer_df_data, use_container_width=True, height=200)
        
        # Preview data
        st.subheader("👀 Data Preview")
        preview_data = filtered_products[:10]
        preview_display = [
            {
                'EAN': p['ean'],
                'Name': p['name'][:50] + '...' if len(p['name']) > 50 else p['name'],
                'Producer': p['producer'],
                'Price': f"{p['price_gross']} {p['currency']}",
                'Stock': p['stock']
            }
            for p in preview_data
        ]
        st.dataframe(preview_display, use_container_width=True)
        
        # Generate CSV
        csv_content = create_csv(filtered_products)
        
        # Download button
        filename = f"{selected_supplier.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        st.download_button(
            label="📥 Download CSV",
            data=csv_content,
            file_name=filename,
            mime="text/csv",
            use_container_width=True
        )
        
        st.info(f"💡 CSV contains {len(filtered_products)} products with semicolon (;) delimiter")


if __name__ == "__main__":
    main()

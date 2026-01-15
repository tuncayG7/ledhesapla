import streamlit as st
import pandas as pd
import math
from fpdf import FPDF
from datetime import datetime
import requests
from io import BytesIO
from PIL import Image

# --- KONFIGURASYON ---
SHEET_ID = "1a6P6Jr_yaiDvbnh3OJ8z_whw1txGOjmyzT0U0jWZTDw"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"
LOGO_URL = "https://raw.githubusercontent.com/tuncayG7/ledhesapla/main/G7_logo_lacivert.png"

st.set_page_config(page_title="G7 TEKNOLOJI | Teklif Paneli", layout="wide")

def tr(text):
    m = {"ç":"c","Ç":"C","ğ":"g","Ğ":"G","ı":"i","İ":"I","ö":"o","Ö":"O","ş":"s","Ş":"S","ü":"u","Ü":"U"}
    for k, v in m.items(): text = str(text).replace(k, v)
    return text

@st.cache_data(ttl=10)
def load_data():
    try:
        df = pd.read_csv(SHEET_URL)
        df.columns = df.columns.str.strip().str.lower()
        return df
    except Exception as e:
        st.error(f"Veri hatasi: {e}")
        return None

# --- PROFESYONEL PDF SINIFI ---
class G7_Technical_PDF(FPDF):
    def header(self):
        try:
            resp = requests.get(LOGO_URL, timeout=10)
            if resp.status_code == 200:
                img = Image.open(BytesIO(resp.content))
                self.image(img, 10, 8, 40)
        except:
            pass
        self.set_font('Arial', 'B', 15)
        self.set_text_color(22, 43, 72)
        self.set_x(55)
        self.cell(0, 10, 'TEKNIK TEKLIF VE CIHAZ LISTESI', ln=True, align='L')
        self.ln(15)
        self.set_draw_color(22, 43, 72)
        self.line(10, 35, 200, 35)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Sayfa {self.page_no()} | G7 Teknoloji', 0, 0, 'C')

df = load_data()

if df is not None:
    with st.sidebar:
        st.header("📋 PROJE AYARLARI")
        customer = st.text_input("Musteri / Proje Adi", "Sayin Musteri")
        moduller = df[df['tip'].str.contains('modul', case=False, na=False)]
        
        env_choice = st.selectbox("Ortam", sorted(moduller['ortam'].unique()))
        tech_choice = st.selectbox("Teknoloji", sorted(moduller[moduller['ortam'] == env_choice]['teknoloji'].unique()))
        final_list = moduller[(moduller['ortam'] == env_choice) & (moduller['teknoloji'] == tech_choice)]['model'].tolist()
        sel_model = st.selectbox("Modul Secin", final_list)
        
        w_mm = st.number_input("Genislik (mm)", value=3840, step=320)
        h_mm = st.number_input("Yukseklik (mm)", value=2160, step=160)
        profit = st.slider("Kar Marji (%)", 0, 100, 25)

    # --- HESAPLAMA MOTORU ---
    m = df[df['model'] == sel_model].iloc[0]
    nw, nh = math.ceil(w_mm / m['genislik']), math.ceil(h_mm / m['yukseklik'])
    total_mod = nw * nh
    res_w, res_h = int(nw * m['res_w']), int(nh * m['res_h'])
    total_px = res_w * res_h
    m2 = (w_mm * h_mm) / 1_000_000
    
    # Bilesenleri Cek
    psu_count = math.ceil(total_mod / 8)
    psu_row = df[df['tip'].str.contains('psu|power', case=False, na=False)].iloc[0]
    recv_count = math.ceil(total_px / 32768)
    recv_row = df[df['tip'].str.contains('receiver', case=False, na=False)].iloc[0]
    procs = df[df['tip'].str.contains('processor', case=False, na=False)].sort_values('res_w')
    selected_proc = procs[procs['res_w'] >= total_px].iloc[0] if not procs[procs['res_w'] >= total_px].empty else procs.iloc[-1]

    # --- MALZEME LISTESI ---
    box_unit = 170 if env_choice.lower() == "outdoor" else 80
    items = [
        {"Urun": f"LED Modul: {m['model']}", "Adet": total_mod, "Birim": "Adet", "B_Fiyat": float(m['msrp'])},
        {"Urun": f"Receiver Kart: {recv_row['model']}", "Adet": recv_count, "Birim": "Adet", "B_Fiyat": float(recv_row['msrp'])},
        {"Urun": f"Guc Kaynagi: {psu_row['model']}", "Adet": psu_count, "Birim": "Adet", "B_Fiyat": float(psu_row['msrp'])},
        {"Urun": f"Video Processor: {selected_proc['model']}", "Adet": 1, "Birim": "Adet", "B_Fiyat": float(selected_proc['msrp'])},
        {"Urun": f"Kasa ve Montaj Sasesi ({env_choice})", "Adet": round(m2, 2), "Birim": "m2", "B_Fiyat": box_unit}
    ]
    
    # Genel Toplam Hesaplama (Hizmet %10 + Kar Marji)
    raw_cost = sum(i['Adet'] * i['B_Fiyat'] for i in items)
    grand_total = (raw_cost * 1.10) * (1 + profit/100)

    # --- EKRAN GOSTERIMI ---
    st.title(f"🚀 G7 TEKNOLOJI | {customer}")
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("TOPLAM TEKLIF", f"$ {grand_total:,.2f}")
    c2.metric("COZUNURLUK", f"{res_w}x{res_h}")
    c3.metric("TOPLAM MODUL", f"{total_mod} Adet")
    c4.metric("TOPLAM PSU", f"{psu_count} Adet")

    st.divider()
    st.subheader("📦 Detayli Malzeme Listesi")
    
    ui_df = pd.DataFrame(items)
    # Hata veren satir burada duzeltildi:
    ui_df['Birim Satis ($)'] = ui_df['B_Fiyat'] * 1.10 * (1 + profit/100)
    ui_df['Toplam ($)'] = ui_df['Adet'] * ui_df['Birim Satis ($)']
    
    st.table(ui_df[['Urun', 'Adet', 'Birim', 'Birim Satis ($)', 'Toplam ($)']].style.format(precision=2))

    # --- PDF GENERATOR ---
    def generate_pdf():
        pdf = G7_Technical_PDF()
        pdf.add_page()
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, tr(f"PROJE: {customer.upper()}"), 0, 1)
        pdf.set_font('Arial', '', 10)
        pdf.cell(100, 6, f"Tarih: {datetime.now().strftime('%d.%m.%Y')}", 0, 0)
        pdf.cell(0, 6, tr(f"Ekran: {w_mm}x{h_mm} mm | Alan: {m2:.2f} m2"), 0, 1, 'R')
        pdf.ln(5)

        # Tablo Basligi
        pdf.set_fill_color(22, 43, 72); pdf.set_text_color(255, 255, 255)
        pdf.cell(85, 10, tr(" Urun Tanimi"), 1, 0, 'L', True)
        pdf.cell(25, 10, tr(" Miktar"), 1, 0, 'C', True)
        pdf.cell(40, 10, tr(" Birim Fiyat"), 1, 0, 'C', True)
        pdf.cell(40, 10, tr(" Toplam"), 1, 1, 'C', True)

        # Tablo Icerigi
        pdf.set_text_color(0, 0, 0); pdf.set_font('Arial', '', 9)
        for i in items:
            s_birim = i['B_Fiyat'] * 1.10 * (1 + profit/100)
            s_toplam = i['Adet'] * s_birim
            pdf.cell(85, 10, tr(f" {i['Urun']}"), 1)
            pdf.cell(25, 10, f"{i['Adet']} {i['Birim']}", 1, 0, 'C')
            pdf.cell(40, 10, f"$ {s_birim:,.2f}", 1, 0, 'R')
            pdf.cell(40, 10, f"$ {s_toplam:,.2f}", 1, 1, 'R')

        # Toplam Satiri
        pdf.ln(5)
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(150, 10, tr("GENEL TOPLAM (KDV HARIC): "), 0, 0, 'R')
        pdf.cell(40, 10, f"$ {grand_total:,.2f}", 1, 1, 'R')
        
        return pdf.output(dest='S').encode('latin-1', 'ignore')

    st.download_button("📥 Profesyonel PDF Teklifini Indir", generate_pdf(), f"G7_Teklif_{customer}.pdf", "application/pdf", use_container_width=True)

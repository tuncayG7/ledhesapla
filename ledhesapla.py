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

@st.cache_data(ttl=10) # Test aşamasında hızlı yenileme için 10 saniye
def load_data():
    try:
        df = pd.read_csv(SHEET_URL)
        df.columns = df.columns.str.strip().str.lower()
        return df
    except Exception as e:
        st.error(f"⚠️ Tablo Okunurken Hata Oluştu: {e}")
        return None

# PDF SINIFI
class G7_PDF(FPDF):
    def header(self):
        try:
            resp = requests.get(LOGO_URL, timeout=5)
            img = Image.open(BytesIO(resp.content))
            self.image(img, 10, 8, 45)
        except: pass
        self.set_font('Arial', 'B', 16)
        self.set_text_color(22, 43, 72)
        self.set_x(60)
        self.cell(0, 10, 'G7 TEKNOLOJI', ln=True, align='L')
        self.line(10, 32, 200, 32)
        self.ln(15)

df = load_data()

# --- VERI KONTROLÜ VE UYGULAMA ---
if df is not None:
    if 'tip' not in df.columns:
        st.warning("❌ HATA: Google Sheets'te 'tip' sütunu bulunamadı. Lütfen sütun isimlerini kontrol edin.")
        st.write("Mevcut Sütunlar:", list(df.columns))
    else:
        # --- SIDEBAR ---
        with st.sidebar:
            st.header("🔍 ÜRÜN SEÇİMİ")
            customer = st.text_input("Müşteri Adı", "Sayın Müşteri")
            
            moduller = df[df['tip'].str.contains('modul', case=False, na=False)]
            
            if not moduller.empty:
                env_choice = st.selectbox("Kullanım Ortamı", sorted(moduller['ortam'].unique()))
                tech_choice = st.selectbox("Teknoloji", sorted(moduller[moduller['ortam'] == env_choice]['teknoloji'].unique()))
                
                final_list = moduller[(moduller['ortam'] == env_choice) & (moduller['teknoloji'] == tech_choice)]['model'].tolist()
                
                if final_list:
                    sel_model = st.selectbox("Model Seçin", final_list)
                    w_mm = st.number_input("Genişlik (mm)", value=3840, step=320)
                    h_mm = st.number_input("Yükseklik (mm)", value=2160, step=160)
                    profit = st.slider("Kar Marjı (%)", 0, 100, 25)
                    has_box = st.checkbox("Kasa Dahil", value=True)
                else:
                    st.error("Model Bulunamadı.")
                    st.stop()
            else:
                st.error("Tabloda hiç modül tanımlanmamış!")
                st.stop()

        # --- HESAPLAMA ---
        m = df[df['model'] == sel_model].iloc[0]
        nw, nh = math.ceil(w_mm / m['genislik']), math.ceil(h_mm / m['yukseklik'])
        total_mod = nw * nh
        total_px = (nw * m['res_w']) * (nh * m['res_h'])
        m2 = (w_mm * h_mm) / 1_000_000
        
        procs = df[df['tip'].str.contains('processor', case=False, na=False)].sort_values('res_w')
        selected_proc = procs[procs['res_w'] >= total_px].iloc[0] if not procs[procs['res_w'] >= total_px].empty else procs.iloc[-1]
        
        elek_maliyet = (total_mod * float(m['msrp'])) + (math.ceil(total_px/32000) * 35) + (math.ceil(total_mod/8) * 22) + float(selected_proc['msrp'])
        box_unit = 170 if env_choice.lower() == "outdoor" else 80
        box_maliyet = (m2 * box_unit) if has_box else 0
        hizmet = (elek_maliyet + box_maliyet) * 0.10
        final_sale = (elek_maliyet + box_maliyet + hizmet) * (1 + profit/100)

        # --- GÖRÜNÜM ---
        st.title(f"🚀 G7 TEKNOLOJİ | {sel_model}")
        st.subheader(f"Teklif Özeti - {customer}")
        
        c1, c2, c3 = st.columns(3)
        c1.metric("TOPLAM SATIŞ", f"$ {final_sale:,.2f}")
        c2.metric("Hizmet Payı", f"$ {hizmet*(1+profit/100):,.2f}")
        c3.metric("Çözünürlük", f"{int(nw*m['res_w'])}x{int(nh*m['res_h'])}")
        
        st.divider()
        st.table([
            {"Kalem": "Elektronik", "Detay": f"{sel_model} + {selected_proc['model']}", "Tutar": f"$ {elek_maliyet*(1+profit/100):,.2f}"},
            {"Kalem": "Kasa", "Detay": f"{env_choice} ({m2:.2f} m2)", "Tutar": f"$ {box_maliyet*(1+profit/100):,.2f}"}
        ])

        # PDF Butonu (Basitleştirilmiş)
        def make_pdf():
            pdf = G7_PDF()
            pdf.add_page()
            pdf.set_font('Arial', 'B', 14)
            pdf.cell(0, 10, tr(f"TEKLIF: {customer.upper()}"), ln=True)
            pdf.cell(0, 10, f"TOPLAM: $ {final_sale:,.2f}", ln=True)
            return pdf.output(dest='S').encode('latin-1', 'ignore')

        st.download_button("📥 PDF İndir", make_pdf(), f"Teklif_{customer}.pdf", "application/pdf")

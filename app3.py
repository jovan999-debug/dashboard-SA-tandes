import os
import json
import re
import plotly.express as px
import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- 1. KONFIGURASI HALAMAN (DIUPDATE UNTUK TAMPILAN APP) ---
st.set_page_config(
    page_title="Dashboard Teknisi & Performansi", 
    layout="wide",
    page_icon="🚀",
    initial_sidebar_state="collapsed"  # TAMBAHAN: Agar menu samping tertutup otomatis di HP
)

# --- TAMBAHAN: HIDE STREAMLIT STYLE (Agar terlihat seperti App Native) ---
hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)
# -----------------------------------------------------------------------

def set_background(image_url):
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url("{image_url}");
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }}
        [data-testid="stHeader"] {{
            background-color: rgba(0,0,0,0);
        }}
        </style>
        """,
        unsafe_allow_html=True
)

# Background
url_gambar = "https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=2072&auto=format&fit=crop"
set_background(url_gambar)

# ==========================================
#  KONFIGURASI GOOGLE SHEET
# ==========================================

MAIN_SPREADSHEET_ID = "1mSHW1FQG19MTRD6nbqFdrP_6klm_uUD-XhWIHEaup_o"
SECOND_SPREADSHEET_ID = "19l9TLgZb8kjNnq3wbxG2U5slNphOQhNbBy4KK3zoXnA" 

TAB_NAME_TEKNISI = "ALL TEKNISI TNS"
TAB_NAME_IOAN    = "CEK IOAN"
TAB_NAME_PSB     = "CEK PSB"
TAB_NAME_B2B     = "Data B2B"
TAB_NAME_RAW_DATA = "BANK DATA ALL 2025" 

# ==========================================

# --- FUNGSI TAMBAHAN: MEMBERSIHKAN NAMA KOLOM ---
def bersihkan_nama_kolom_display(df_input):
    df_display = df_input.copy()
    new_column_names = {}
    for col in df_display.columns:
        clean_name = re.sub(r'_\d+$', '', col)
        new_column_names[col] = clean_name
    df_display = df_display.rename(columns=new_column_names)
    return df_display

# --- 2. FUNGSI KONEKSI ---
@st.cache_data(ttl=60)
def load_data(sheet_id, nama_tab_spesifik, range_cell=None):
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        
        if "GCP_JSON" in os.environ:
            creds_dict = json.loads(os.environ["GCP_JSON"])
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        elif "gcp_service_account" in st.secrets:
            creds_dict = st.secrets["gcp_service_account"]
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        else:
            creds = ServiceAccountCredentials.from_json_keyfile_name("kredensial.json", scope)

        client = gspread.authorize(creds)
        sh = client.open_by_key(sheet_id)
        worksheet = sh.worksheet(nama_tab_spesifik)

        if range_cell:
            data = worksheet.get(range_cell)
        else:
            data = worksheet.get_all_values()
        
        if len(data) > 0:
            headers = data[0]
            seen = {}
            new_headers = []
            for h in headers:
                h = str(h).strip() 
                if h in seen:
                    seen[h] += 1
                    new_headers.append(f"{h}_{seen[h]}")
                else:
                    seen[h] = 0
                    new_headers.append(h)
            
            df = pd.DataFrame(data[1:], columns=new_headers)
            
            for col in df.columns:
                try:
                    if df[col].astype(str).str.isnumeric().all():
                        df[col] = pd.to_numeric(df[col], errors='ignore')
                except:
                    pass
            return df
        else:
            return pd.DataFrame()

    except Exception as e:
        st.error(f"❌ Terjadi Kesalahan Koneksi: {e}")
        return pd.DataFrame()

# --- 3. FUNGSI PEWARNAAN ---
def highlight_dynamic(row, nama_kolom):
    try:
        nilai = float(row[nama_kolom])
        if nilai < 100:
            return ['background-color: #ffcccc; color: black'] * len(row)
        else:
            return [''] * len(row)
    except:
        return [''] * len(row)

# --- 4. NAVIGASI ---
if 'page' not in st.session_state:
    st.session_state.page = 'landing'

def go_to(page_name):
    st.session_state.page = page_name

# --- 5. HALAMAN: LANDING PAGE ---
def show_landing_page():
    st.markdown("<h1 style='text-align: center;'>Monitoring Dashboard Performansi SA TANDES</h1>", unsafe_allow_html=True)
    st.markdown("---")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.info("👥 DATA PEGAWAI")
        if st.button("DAFTAR TEKNISI", use_container_width=True):
            go_to('teknisi_menu_pilihan')
            st.rerun()
            
    with col2:
        st.success("📊 DATA IOAN")
        # [UPDATE] Tombol ini sekarang ke menu pilihan, bukan langsung dashboard
        if st.button("PERFORMANSI IOAN", use_container_width=True):
            go_to('ioan_menu_pilihan') 
            st.rerun()
            
    with col3:
        st.warning("📈 DATA PSB")
        if st.button("PERFORMANSI PSB", use_container_width=True):
            go_to('psb_menu_pilihan')
            st.rerun()
            
    with col4:
        st.error("🏢 DATA B2B")
        if st.button("PERFORMANSI B2B", use_container_width=True):
            go_to('b2b')
            st.rerun()

# --- 6. HALAMAN: MENU PILIHAN TEKNISI ---
def show_teknisi_menu_pilihan():
    st.button("⬅️ Kembali ke Menu Utama", on_click=lambda: go_to('landing'))
    st.title("Pilih Kategori Teknisi")
    
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("TEKNISI IOAN", use_container_width=True):
            go_to('teknisi_ioan_detail')
            st.rerun()
    with c2:
        if st.button("TEKNISI PSB", use_container_width=True):
            go_to('teknisi_psb_detail')
            st.rerun()
    with c3:
        if st.button("TEKNISI B2B", use_container_width=True):
            go_to('teknisi_b2b_detail')
            st.rerun()

# --- 7. HALAMAN: MENU PILIHAN PSB ---
def show_psb_menu_pilihan():
    st.button("⬅️ Kembali ke Menu Utama", on_click=lambda: go_to('landing'))
    st.title("Pilih Dashboard PSB")
    
    c1, c2 = st.columns(2)
    with c1:
        st.info("PSB B2C")
        if st.button("Dashboard KPI IMBAL JASA PROVISIONING SA TANDES", use_container_width=True):
            go_to('psb_utama')
            st.rerun()
            
    with c2:
        st.warning("ANALISA DATA PS PSB")
        if st.button("Dashboard Data PS PSB", use_container_width=True):
            go_to('psb_pivot_interaktif')
            st.rerun()

# --- [UPDATE] 8. HALAMAN: MENU PILIHAN IOAN (3 MENU) ---
def show_ioan_menu_pilihan():
    st.button("⬅️ Kembali ke Menu Utama", on_click=lambda: go_to('landing'))
    st.title("Pilih Dashboard IOAN")
    
    c1, c2, c3 = st.columns(3)
    
    # Menu 1: Data Lama (A1:K29)
    with c1:
        if st.button("Performansi SLA Imbal jasa IOAN", use_container_width=True):
            go_to('ioan') 
            st.rerun()
            
    # Menu 2: Data Kedua (M9:Q25)
    with c2:
        if st.button("Performansi MSA-WSA IOAN", use_container_width=True):
            go_to('ioan_tambahan') 
            st.rerun()

    # Menu 3: Data Baru (T9:Y21)
    with c3:
        if st.button("Performansi PI LATEN", use_container_width=True):
            go_to('ioan_baru_lagi') # Ke Dashboard Baru
            st.rerun()

# --- 9. HALAMAN: DETAIL TEKNISI ---
def show_teknisi_detail(jenis, kolom_start, kolom_end):
    st.button("⬅️ Kembali ke Pilihan Teknisi", on_click=lambda: go_to('teknisi_menu_pilihan'))
    st.title(f"Data Teknisi - {jenis}")
    
    with st.spinner('Mengambil data...'):
        df_full = load_data(MAIN_SPREADSHEET_ID, TAB_NAME_TEKNISI)
    
    if not df_full.empty:
        try:
            df_filtered = df_full.iloc[:, kolom_start:kolom_end]
            df_filtered = df_filtered[df_filtered.iloc[:, 0].astype(str).str.strip() != ""]
            df_clean = bersihkan_nama_kolom_display(df_filtered)
            st.dataframe(df_clean, use_container_width=True, hide_index=True)
        except Exception as e:
            st.error(f"Gagal memotong kolom: {e}")
    else:
        st.warning("Data teknisi kosong.")

# --- 10. HALAMAN: DASHBOARD STANDAR ---
def show_dashboard(judul, nama_tab, target_sheet_id, range_khusus=None, kolom_kunci="SCORE", back_to='landing'):
    # Logika Tombol Kembali
    if back_to == 'landing':
        st.button("⬅️ Kembali ke Menu Utama", on_click=lambda: go_to('landing'))
    elif back_to == 'psb_menu':
        st.button("⬅️ Kembali ke Pilihan PSB", on_click=lambda: go_to('psb_menu_pilihan'))
    elif back_to == 'ioan_menu':
        st.button("⬅️ Kembali ke Pilihan IOAN", on_click=lambda: go_to('ioan_menu_pilihan'))

    st.title(f"Dashboard {judul}")
    
    with st.spinner('Sedang memuat data...'):
        df = load_data(target_sheet_id, nama_tab, range_khusus)

    if not df.empty:
        if kolom_kunci in df.columns:
            df_display = df.copy() 
            df_display[kolom_kunci] = df_display[kolom_kunci].astype(str).str.replace(',', '.', regex=False)
            df_display[kolom_kunci] = pd.to_numeric(df_display[kolom_kunci], errors='coerce').fillna(0)
            
            styled_df = df_display.style.apply(lambda row: highlight_dynamic(row, kolom_kunci), axis=1)
            styled_df = styled_df.format({kolom_kunci: "{:.2f}"})
            st.dataframe(styled_df, use_container_width=True, hide_index=True)
        else:
            st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.warning(f"Data tidak ditemukan di tab: {nama_tab}")

# --- 11. HALAMAN BARU: PIVOT TABLE (FINAL + GRAFIK INTERAKTIF) ---
def show_interactive_pivot():
    st.button("⬅️ Kembali ke Pilihan PSB", on_click=lambda: go_to('psb_menu_pilihan'))
    st.title("🔧 Analisa Data PS PSB")
    
    with st.spinner('Mengambil data mentah harian...'):
        df = load_data(SECOND_SPREADSHEET_ID, TAB_NAME_RAW_DATA)
        
    if not df.empty:
        df = df.loc[:, ~df.columns.duplicated()]
        for col in df.columns:
            try:
                if df[col].astype(str).str.isnumeric().all():
                    df[col] = pd.to_numeric(df[col], errors='ignore')
            except: pass

        all_columns = df.columns.tolist()
        
        # --- FILTER SIDEBAR ---
        st.sidebar.markdown("### 🔎 Panel Filter Data")
        st.sidebar.info("Gunakan menu ini untuk menyaring data.")
        kolom_filter = st.sidebar.selectbox("Pilih Kolom:", ["- Tidak Ada -"] + all_columns)
        
        if kolom_filter != "- Tidak Ada -":
            unique_values = df[kolom_filter].unique().tolist()
            selected_values = st.sidebar.multiselect(f"Pilih isi '{kolom_filter}':", unique_values)
            if selected_values:
                df = df[df[kolom_filter].isin(selected_values)]
                st.sidebar.success(f"✅ {len(df)} baris data ditemukan.")
            else:
                st.warning(f"⚠️ Anda memilih filter '{kolom_filter}' tapi belum memilih isinya.")
                df = pd.DataFrame() 

        st.markdown("---")
        
        if not df.empty:
            st.write("Silakan atur tampilan Pivot Table:")
            with st.expander("⚙️ PENGATURAN PIVOT", expanded=True):
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.markdown("**1. Pilih Baris (Rows)**")
                    rows = st.multiselect("Pilih kolom untuk Baris:", all_columns, default=all_columns[0] if len(all_columns)>0 else None)
                with col2:
                    st.markdown("**2. Pilih Kolom (Cols - Opsional)**")
                    cols = st.multiselect("Pilih kolom untuk Kolom:", all_columns)
                with col3:
                    st.markdown("**3. Pilih Data Dihitung (Values)**")
                    values = st.selectbox("Pilih data yg mau dihitung:", all_columns, index=1 if len(all_columns)>1 else 0)
                with col4:
                    st.markdown("**4. Jenis Hitungan**")
                    agg_type = st.selectbox("Rumus:", ["count (Hitung Data)", "sum (Total Angka)", "mean (Rata-rata)", "min", "max"])
                    agg_func = 'count'
                    if "sum" in agg_type: agg_func = 'sum'
                    elif "mean" in agg_type: agg_func = 'mean'
                    elif "min" in agg_type: agg_func = 'min'
                    elif "max" in agg_type: agg_func = 'max'

            st.markdown("---")
            if rows:
                try:
                    if agg_func != 'count':
                        df[values] = pd.to_numeric(df[values], errors='coerce').fillna(0)

                    pivot_result = pd.pivot_table(
                        df, index=rows, columns=cols if cols else None, 
                        values=values, aggfunc=agg_func, fill_value=0,
                        margins=True, margins_name='Grand Total'
                    )

                    def smart_sort_index(index_obj):
                        try:
                            labels = index_obj.astype(str).tolist()
                            try:
                                dates = pd.to_datetime(labels, dayfirst=True, errors='coerce')
                                if dates.notna().sum() > len(dates) * 0.5: return dates.argsort()
                            except: pass
                            bulan_map = {'JANUARI':1,'JAN':1,'FEBRUARI':2,'FEB':2,'MARET':3,'MAR':3,'APRIL':4,'APR':4,'MEI':5,'MAY':5,'JUNI':6,'JUN':6,'JULI':7,'JUL':7,'AGUSTUS':8,'AGT':8,'SEPTEMBER':9,'SEP':9,'OKTOBER':10,'OKT':10,'NOVEMBER':11,'NOV':11,'DESEMBER':12,'DES':12,'GRAND TOTAL':999}
                            sample = labels[0].strip().upper().split(' ')[0]
                            if sample in bulan_map:
                                rank_list = [bulan_map.get(i.strip().upper().split(' ')[0], 50) for i in labels]
                                return pd.Series(rank_list).argsort()
                            return index_obj.argsort()
                        except: return range(len(index_obj))

                    if cols:
                        is_grand_total = pivot_result.columns == 'Grand Total'
                        if not is_grand_total.all():
                            data_cols = pivot_result.columns[~is_grand_total]
                            total_col = pivot_result.columns[is_grand_total]
                            pivot_result = pivot_result[data_cols[smart_sort_index(data_cols)].tolist() + total_col.tolist()]

                    if 'Grand Total' in pivot_result.index:
                        data_rows = pivot_result.index.drop('Grand Total')
                        pivot_result = pivot_result.reindex(data_rows[smart_sort_index(data_rows)].tolist() + ['Grand Total'])

                    st.subheader(f"📊 Hasil Analisa: {agg_func.upper()} of {values}")
                    st.dataframe(pivot_result, use_container_width=True)

                    # VISUALISASI GRAFIK
                    st.markdown("### 📈 Visualisasi Grafik")
                    chart_df = pivot_result.copy()
                    if 'Grand Total' in chart_df.index: chart_df = chart_df.drop('Grand Total', axis=0)
                    if 'Grand Total' in chart_df.columns: chart_df = chart_df.drop(columns=['Grand Total'])
                    
                    if isinstance(chart_df.columns, pd.MultiIndex):
                        chart_df.columns = [' - '.join(map(str, col)).strip() for col in chart_df.columns.values]

                    if not chart_df.empty:
                        chart_data_clean = chart_df.reset_index()
                        x_axis_name = chart_data_clean.columns[0]
                        
                        jenis_grafik = st.radio("Tampilan Grafik:", ["📊 Bar Chart (Perbandingan)", "📈 Line Chart (Tren Waktu)", "🍩 Pie Chart (Proporsi)"], horizontal=True)
                        fig = None
                        
                        if jenis_grafik == "📊 Bar Chart (Perbandingan)":
                            if len(chart_df.columns) == 1:
                                y_axis_name = chart_df.columns[0]
                                fig = px.bar(chart_data_clean, x=x_axis_name, y=y_axis_name, text_auto=True, color=y_axis_name)
                            else:
                                chart_melted = chart_data_clean.melt(id_vars=x_axis_name, var_name='Kategori', value_name='Jumlah')
                                fig = px.bar(chart_melted, x=x_axis_name, y='Jumlah', color='Kategori', text_auto=True, barmode='group')

                        elif jenis_grafik == "📈 Line Chart (Tren Waktu)":
                            if len(chart_df.columns) == 1:
                                y_axis_name = chart_df.columns[0]
                                fig = px.line(chart_data_clean, x=x_axis_name, y=y_axis_name, markers=True)
                            else:
                                chart_melted = chart_data_clean.melt(id_vars=x_axis_name, var_name='Kategori', value_name='Jumlah')
                                fig = px.line(chart_melted, x=x_axis_name, y='Jumlah', color='Kategori', markers=True)

                        elif jenis_grafik == "🍩 Pie Chart (Proporsi)":
                            if len(chart_df.columns) == 1:
                                y_axis_name = chart_df.columns[0]
                                fig = px.pie(chart_data_clean, names=x_axis_name, values=y_axis_name, hole=0.4)
                            else:
                                st.warning("⚠️ Pie Chart hanya untuk data 1 kolom.")

                        if fig: st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.warning("Data tidak cukup untuk membuat grafik.")

                except Exception as e:
                    st.error(f"Gagal memproses data: {e}")
            else:
                st.info("👈 Silakan pilih minimal satu 'Baris (Rows)' di menu pengaturan.")

# --- 12. ROUTING UTAMA ---
if st.session_state.page == 'landing':
    show_landing_page()

# Routing Teknisi
elif st.session_state.page == 'teknisi_menu_pilihan':
    show_teknisi_menu_pilihan()
elif st.session_state.page == 'teknisi_ioan_detail':
    show_teknisi_detail("IOAN", 3, 6)
elif st.session_state.page == 'teknisi_psb_detail':
    show_teknisi_detail("PSB", 6, 9) 
elif st.session_state.page == 'teknisi_b2b_detail':
    show_teknisi_detail("B2B", 0, 3) 

# Routing PSB
elif st.session_state.page == 'psb_menu_pilihan':
    show_psb_menu_pilihan()

elif st.session_state.page == 'psb_utama':
    show_dashboard(
        "KPI IMBAL JASA PROVISIONING SA TANDES", TAB_NAME_PSB, MAIN_SPREADSHEET_ID, 
        range_khusus="A7:F15", kolom_kunci="ACHIEVEMENT", back_to='psb_menu'
    )

elif st.session_state.page == 'psb_pivot_interaktif':
    show_interactive_pivot()

# --- [UPDATE] Routing IOAN ---
elif st.session_state.page == 'ioan_menu_pilihan':
    show_ioan_menu_pilihan() # Menampilkan menu pilihan

elif st.session_state.page == 'ioan':
    # Dashboard Lama (A1:K29)
    show_dashboard("Performansi SLA Imbal Jasa IOAN", TAB_NAME_IOAN, MAIN_SPREADSHEET_ID, range_khusus="A1:K29", kolom_kunci="SCORE", back_to='ioan_menu')

elif st.session_state.page == 'ioan_tambahan':
    # Dashboard Kedua (M9:Q25)
    show_dashboard("Performansi MSA-WSA IOAN", TAB_NAME_IOAN, MAIN_SPREADSHEET_ID, range_khusus="M9:Q25", kolom_kunci="ACHIEVEMENT", back_to='ioan_menu')

elif st.session_state.page == 'ioan_baru_lagi':
    # Dashboard Ketiga (T9:Y21) -> INI YANG BARU
    show_dashboard("PI LATEN", TAB_NAME_IOAN, MAIN_SPREADSHEET_ID, range_khusus="T9:Y21", kolom_kunci="ACHIEVEMENT", back_to='ioan_menu')

# Routing B2B
elif st.session_state.page == 'b2b':
    show_dashboard("Performansi B2B", TAB_NAME_B2B, MAIN_SPREADSHEET_ID, kolom_kunci="SCORE")









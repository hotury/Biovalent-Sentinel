# =============================================================================
#  BIOVALENT SENTINEL v2.0
#  Tarımsal Biyoteknoloji & Genetik Karar Destek Sistemi
#  "Decoding the Bonds of Life"
#
#  KURULUM:
#      pip install streamlit pandas numpy biopython plotly openpyxl
#      streamlit run app.py
#
#  Google Colab:
#      !pip install streamlit pandas numpy biopython plotly openpyxl pyngrok -q
#      !streamlit run app.py &
#      from pyngrok import ngrok; print(ngrok.connect(8501))
# =============================================================================

# ─────────────────────────────────────────────────────────────────────────────
# §0  IMPORTS
# ─────────────────────────────────────────────────────────────────────────────
import re
import math
import itertools
import traceback
from datetime import datetime
from typing import List, Dict, Tuple, Optional

import streamlit as st
import pandas as pd
import numpy as np

try:
    from Bio.Seq import Seq
    _BIO_OK = True
except ImportError:
    _BIO_OK = False

try:
    import plotly.express as px
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    _PLT_OK = True
except ImportError:
    _PLT_OK = False

# ─────────────────────────────────────────────────────────────────────────────
# §1  SAYFA KONFİGÜRASYONU  (her zaman ilk Streamlit çağrısı)
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Biovalent Sentinel v2.0",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# §2  GLOBAL RENK PALETİ & CSS
# ─────────────────────────────────────────────────────────────────────────────
# Koyu Yeşil / Altın / Gri kurumsal palet
PAL = {
    "bg"       : "#0e1a0e",   # Ana arka plan
    "panel"    : "#142014",   # Kart / panel arka planı
    "border"   : "#1f3a1f",   # Kenar çizgileri
    "green_hi" : "#4ade80",   # Neon yeşil vurgu
    "green_mid": "#22c55e",   # Orta yeşil
    "green_dim": "#166534",   # Koyu yeşil
    "gold"     : "#fbbf24",   # Altın vurgu
    "gold_dim" : "#92400e",   # Koyu altın
    "grey_hi"  : "#d1fae5",   # Açık gri-yeşil metin
    "grey_mid" : "#6b7280",   # Orta gri
    "grey_dim" : "#374151",   # Koyu gri
    "red"      : "#f87171",   # Risk / uyarı
    "amber"    : "#fcd34d",   # Orta uyarı
    "white"    : "#f0fdf4",   # Beyaz
}

# Plotly tema renkleri
PLOTLY_COLORS = [
    PAL["green_hi"], PAL["gold"], "#60a5fa", "#c084fc",
    "#f97316", "#34d399", "#fb7185", "#a3e635",
]

CUSTOM_CSS = f"""
<style>
  /* ── Root ── */
  html, body, [data-testid="stAppViewContainer"] {{
      background-color: {PAL["bg"]};
      color: {PAL["grey_hi"]};
      font-family: 'Inter', 'Segoe UI', sans-serif;
  }}
  /* ── Sidebar ── */
  [data-testid="stSidebar"] {{
      background: linear-gradient(180deg, #0a1a0a 0%, #0f2210 100%);
      border-right: 1px solid {PAL["border"]};
  }}
  /* ── Başlıklar ── */
  h1 {{ color: {PAL["green_hi"]} !important; letter-spacing: -0.5px; }}
  h2 {{ color: {PAL["gold"]} !important; }}
  h3 {{ color: {PAL["green_mid"]} !important; }}
  /* ── Metrik kartları ── */
  [data-testid="metric-container"] {{
      background: linear-gradient(135deg, {PAL["panel"]} 0%, {PAL["bg"]} 100%);
      border: 1px solid {PAL["border"]};
      border-radius: 10px;
      padding: 14px !important;
  }}
  [data-testid="metric-container"] label {{
      color: {PAL["gold"]} !important;
      font-size: 0.78rem;
  }}
  [data-testid="metric-container"] [data-testid="stMetricValue"] {{
      color: {PAL["green_hi"]} !important;
      font-weight: 700;
  }}
  /* ── Butonlar ── */
  .stButton > button {{
      background: linear-gradient(135deg, {PAL["green_dim"]} 0%, #14532d 100%);
      color: {PAL["green_hi"]};
      border: 1px solid {PAL["green_mid"]};
      border-radius: 8px;
      font-weight: 700;
      padding: 0.45rem 1.3rem;
      transition: all 0.2s ease;
  }}
  .stButton > button:hover {{
      background: linear-gradient(135deg, {PAL["green_mid"]} 0%, {PAL["green_dim"]} 100%);
      color: {PAL["white"]};
      transform: translateY(-1px);
      box-shadow: 0 4px 18px rgba(74,222,128,0.30);
  }}
  /* ── Inputlar ── */
  .stTextArea textarea, .stTextInput input {{
      background-color: {PAL["panel"]} !important;
      color: {PAL["grey_hi"]} !important;
      border: 1px solid {PAL["border"]} !important;
      border-radius: 8px !important;
  }}
  /* ── Selectbox / Multiselect ── */
  .stSelectbox > div, .stMultiSelect > div {{
      background-color: {PAL["panel"]} !important;
  }}
  /* ── Tab başlıkları ── */
  [data-baseweb="tab-list"] {{
      background-color: {PAL["panel"]} !important;
      border-radius: 10px;
      padding: 4px;
  }}
  [data-baseweb="tab"] {{
      color: {PAL["grey_mid"]} !important;
      font-weight: 600;
  }}
  [aria-selected="true"] {{
      color: {PAL["green_hi"]} !important;
      background-color: {PAL["green_dim"]} !important;
      border-radius: 8px;
  }}
  /* ── Dataframe ── */
  [data-testid="stDataFrame"] {{
      border: 1px solid {PAL["border"]};
      border-radius: 8px;
  }}
  /* ── Expander ── */
  .streamlit-expanderHeader {{
      background-color: {PAL["panel"]} !important;
      color: {PAL["gold"]} !important;
      border-radius: 8px !important;
  }}
  /* ── Alert (info/success/warning/error) ── */
  .stAlert {{ border-radius: 8px !important; border-left-width: 4px !important; }}
  /* ── Divider ── */
  hr {{ border-color: {PAL["border"]} !important; }}
  /* ── Özel kartlar ── */
  .bv-card {{
      background: linear-gradient(135deg, {PAL["panel"]} 0%, {PAL["bg"]} 100%);
      border: 1px solid {PAL["border"]};
      border-radius: 12px;
      padding: 1.2rem 1.4rem;
      margin-bottom: 0.9rem;
  }}
  .bv-hero {{
      background: linear-gradient(135deg, {PAL["panel"]} 0%, #0a1f0a 50%, {PAL["bg"]} 100%);
      border: 1px solid {PAL["border"]};
      border-radius: 16px;
      padding: 1.8rem 2.2rem;
      margin-bottom: 1.2rem;
      text-align: center;
  }}
  .badge-green  {{ background:{PAL["green_dim"]};color:{PAL["green_hi"]};
                   padding:2px 9px;border-radius:20px;font-size:0.76rem;font-weight:700; }}
  .badge-gold   {{ background:{PAL["gold_dim"]};color:{PAL["gold"]};
                   padding:2px 9px;border-radius:20px;font-size:0.76rem;font-weight:700; }}
  .badge-red    {{ background:#450a0a;color:{PAL["red"]};
                   padding:2px 9px;border-radius:20px;font-size:0.76rem;font-weight:700; }}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# §3  SABITLER
# ─────────────────────────────────────────────────────────────────────────────
VER    = "2.0.0"
FIRMA  = "Biovalent"
SLOGAN = "Decoding the Bonds of Life"
GUVEN  = 0.95

# Demo DNA dizisi (NBS-LRR P-loop içerir)
DEMO_DNA = (
    "ATGGGCGTTGGCAAAACTACCATGCTTGCAGCTGATTTGCGTCAGAAGATGGCTGCAGAGCTGAAAGAT"
    "CGCTTTGCGATGGTGGATGGCGTGGGCGAAGTGGACTCTTTTGGCGACTTCCTCAAAACACTCGCAGAG"
    "GAGATCATTGGCGTCGTCAAAGATAGTAAACTCTATTTGTTGCTTCTTTTAAGTGGCAGGACTTGGCAT"
    "GTTGGGCGGCGTACTTGGCATTTCAATGGGCGGACAAGAAGTTCCTCATACCGAGAGAGAGTGGGCGTT"
    "GGCAAAACTACCGTATGGGCGGCAAGAAGTTCCTTGAGGGGGTGGCAAAACCATGGCTGGCAGACTTGC"
    "TGGCAAGAAGTGGCAGAAGTGGGAGCAGCTACAGCAGCAGCAGCAGCAGCAGCAGCAGCAGCAGCAGCAG"
)

# ─────────────────────────────────────────────────────────────────────────────
# §4  DEMO VERİSETİ  (≥20 satır, biyolojik olarak gerçekçi)
# ─────────────────────────────────────────────────────────────────────────────

@st.cache_data
def demo_veri() -> pd.DataFrame:
    """
    Domates ve biber ağırlıklı, 25 satırlık kapsamlı demo envanter.
    Sütunlar:
        hat_id, hat_adi, tur, meyve_rengi, verim_t_ha, raf_omru_gun,
        hasat_gunu, brix, fusarium_I, tmv_Tm2a, nematod_Mi12, rin_gen,
        pto_gen, fusarium_cM, tmv_cM, nematod_cM, rin_cM,
        etiketler
    """
    rows = [
        # ── DOMATES (Solanum lycopersicum) ──
        dict(hat_id="BIO-TOM-001", hat_adi="Crimson Shield F6",  tur="Solanum lycopersicum",
             meyve_rengi="Koyu Kırmızı",  verim_t_ha=18.5, raf_omru_gun=14, hasat_gunu=72,
             brix=5.2,
             fusarium_I=1,  tmv_Tm2a=1,  nematod_Mi12=0, rin_gen=0, pto_gen=1,
             fusarium_cM=45.0, tmv_cM=22.0, nematod_cM=33.0, rin_cM=12.0,
             etiketler="fusarium direnci,tmv direnci,virüs direnci,orta verim"),
        dict(hat_id="BIO-TOM-002", hat_adi="GoldenYield HV-9",   tur="Solanum lycopersicum",
             meyve_rengi="Parlak Sarı",   verim_t_ha=22.3, raf_omru_gun=11, hasat_gunu=68,
             brix=4.8,
             fusarium_I=0,  tmv_Tm2a=1,  nematod_Mi12=0, rin_gen=0, pto_gen=0,
             fusarium_cM=45.0, tmv_cM=22.0, nematod_cM=33.0, rin_cM=12.0,
             etiketler="sarı meyve,yüksek verim,ticari hat"),
        dict(hat_id="BIO-TOM-003", hat_adi="LongLife Premium",   tur="Solanum lycopersicum",
             meyve_rengi="Kırmızı",       verim_t_ha=16.8, raf_omru_gun=24, hasat_gunu=78,
             brix=5.8,
             fusarium_I=0,  tmv_Tm2a=0,  nematod_Mi12=1, rin_gen=1, pto_gen=0,
             fusarium_cM=45.0, tmv_cM=22.0, nematod_cM=33.0, rin_cM=12.0,
             etiketler="uzun raf ömrü,nematod direnci,ihracat"),
        dict(hat_id="BIO-TOM-004", hat_adi="SunGold Cherry",     tur="Solanum lycopersicum",
             meyve_rengi="Turuncu-Sarı",  verim_t_ha=21.0, raf_omru_gun=10, hasat_gunu=62,
             brix=8.2,
             fusarium_I=0,  tmv_Tm2a=0,  nematod_Mi12=0, rin_gen=0, pto_gen=0,
             fusarium_cM=45.0, tmv_cM=22.0, nematod_cM=33.0, rin_cM=12.0,
             etiketler="sarı meyve,cherry,yüksek brix,gourmet"),
        dict(hat_id="BIO-TOM-005", hat_adi="Titan Robust F4",    tur="Solanum lycopersicum",
             meyve_rengi="Koyu Kırmızı",  verim_t_ha=17.2, raf_omru_gun=16, hasat_gunu=80,
             brix=4.5,
             fusarium_I=1,  tmv_Tm2a=0,  nematod_Mi12=1, rin_gen=0, pto_gen=0,
             fusarium_cM=45.0, tmv_cM=22.0, nematod_cM=33.0, rin_cM=12.0,
             etiketler="fusarium direnci,nematod direnci,ağır toprak"),
        dict(hat_id="BIO-TOM-006", hat_adi="Sunrise Export",     tur="Solanum lycopersicum",
             meyve_rengi="Sarı-Turuncu",  verim_t_ha=19.6, raf_omru_gun=20, hasat_gunu=74,
             brix=5.0,
             fusarium_I=0,  tmv_Tm2a=1,  nematod_Mi12=0, rin_gen=1, pto_gen=0,
             fusarium_cM=45.0, tmv_cM=22.0, nematod_cM=33.0, rin_cM=12.0,
             etiketler="sarı meyve,uzun raf ömrü,tmv direnci,ihracat"),
        dict(hat_id="BIO-TOM-007", hat_adi="MiniSweet Pink",     tur="Solanum lycopersicum",
             meyve_rengi="Pembe",         verim_t_ha=14.4, raf_omru_gun=9,  hasat_gunu=60,
             brix=9.1,
             fusarium_I=0,  tmv_Tm2a=0,  nematod_Mi12=0, rin_gen=0, pto_gen=0,
             fusarium_cM=45.0, tmv_cM=22.0, nematod_cM=33.0, rin_cM=12.0,
             etiketler="pembe,cherry,yüksek brix,gurme"),
        dict(hat_id="BIO-TOM-008", hat_adi="IronShield Plus",    tur="Solanum lycopersicum",
             meyve_rengi="Kırmızı",       verim_t_ha=16.0, raf_omru_gun=18, hasat_gunu=76,
             brix=4.7,
             fusarium_I=1,  tmv_Tm2a=1,  nematod_Mi12=1, rin_gen=0, pto_gen=1,
             fusarium_cM=45.0, tmv_cM=22.0, nematod_cM=33.0, rin_cM=12.0,
             etiketler="fusarium direnci,tmv direnci,nematod direnci,çok dirençli"),
        dict(hat_id="BIO-TOM-009", hat_adi="Quantum Beefsteak",  tur="Solanum lycopersicum",
             meyve_rengi="Kırmızı",       verim_t_ha=20.1, raf_omru_gun=12, hasat_gunu=84,
             brix=4.2,
             fusarium_I=1,  tmv_Tm2a=0,  nematod_Mi12=0, rin_gen=0, pto_gen=0,
             fusarium_cM=45.0, tmv_cM=22.0, nematod_cM=33.0, rin_cM=12.0,
             etiketler="yüksek verim,büyük meyve,endüstriyel"),
        dict(hat_id="BIO-TOM-010", hat_adi="Arctic White F3",    tur="Solanum lycopersicum",
             meyve_rengi="Beyaz",         verim_t_ha=12.5, raf_omru_gun=13, hasat_gunu=70,
             brix=6.5,
             fusarium_I=0,  tmv_Tm2a=0,  nematod_Mi12=0, rin_gen=1, pto_gen=0,
             fusarium_cM=45.0, tmv_cM=22.0, nematod_cM=33.0, rin_cM=12.0,
             etiketler="beyaz meyve,uzun raf ömrü,özel pazar"),
        dict(hat_id="BIO-TOM-011", hat_adi="BioShield Triple",   tur="Solanum lycopersicum",
             meyve_rengi="Kırmızı",       verim_t_ha=15.3, raf_omru_gun=15, hasat_gunu=73,
             brix=5.1,
             fusarium_I=1,  tmv_Tm2a=1,  nematod_Mi12=1, rin_gen=1, pto_gen=1,
             fusarium_cM=45.0, tmv_cM=22.0, nematod_cM=33.0, rin_cM=12.0,
             etiketler="tam direnç paketi,uzun raf ömrü,organik"),
        dict(hat_id="BIO-TOM-012", hat_adi="Volcano Dark",       tur="Solanum lycopersicum",
             meyve_rengi="Siyah-Mor",     verim_t_ha=11.8, raf_omru_gun=11, hasat_gunu=78,
             brix=7.3,
             fusarium_I=0,  tmv_Tm2a=0,  nematod_Mi12=0, rin_gen=0, pto_gen=0,
             fusarium_cM=45.0, tmv_cM=22.0, nematod_cM=33.0, rin_cM=12.0,
             etiketler="siyah meyve,antosiyanin,özel pazar,gurme"),
        # ── BİBER (Capsicum annuum) ──
        dict(hat_id="BIO-CAP-001", hat_adi="RedBlaze L4 F5",     tur="Capsicum annuum",
             meyve_rengi="Parlak Kırmızı",verim_t_ha=15.5, raf_omru_gun=18, hasat_gunu=85,
             brix=6.1,
             fusarium_I=0,  tmv_Tm2a=1,  nematod_Mi12=0, rin_gen=0, pto_gen=0,
             fusarium_cM=18.0, tmv_cM=18.0, nematod_cM=28.0, rin_cM=9.0,
             etiketler="kırmızı meyve,tmv direnci,pvy direnci,virüs direnci"),
        dict(hat_id="BIO-CAP-002", hat_adi="YellowBell Export",  tur="Capsicum annuum",
             meyve_rengi="Sarı",          verim_t_ha=13.8, raf_omru_gun=14, hasat_gunu=90,
             brix=5.5,
             fusarium_I=0,  tmv_Tm2a=0,  nematod_Mi12=0, rin_gen=0, pto_gen=0,
             fusarium_cM=18.0, tmv_cM=18.0, nematod_cM=28.0, rin_cM=9.0,
             etiketler="sarı meyve,dolmalık biber,ihracat"),
        dict(hat_id="BIO-CAP-003", hat_adi="Spicy Supreme",      tur="Capsicum annuum",
             meyve_rengi="Kırmızı-Turuncu",verim_t_ha=16.2, raf_omru_gun=12, hasat_gunu=78,
             brix=7.2,
             fusarium_I=0,  tmv_Tm2a=1,  nematod_Mi12=0, rin_gen=0, pto_gen=0,
             fusarium_cM=18.0, tmv_cM=18.0, nematod_cM=28.0, rin_cM=9.0,
             etiketler="acı biber,yüksek brix,yüksek verim,gourmet"),
        dict(hat_id="BIO-CAP-004", hat_adi="Purple Beauty",      tur="Capsicum annuum",
             meyve_rengi="Mor",           verim_t_ha=12.0, raf_omru_gun=13, hasat_gunu=88,
             brix=6.8,
             fusarium_I=0,  tmv_Tm2a=0,  nematod_Mi12=0, rin_gen=0, pto_gen=0,
             fusarium_cM=18.0, tmv_cM=18.0, nematod_cM=28.0, rin_cM=9.0,
             etiketler="mor meyve,özel pazar,dolmalık"),
        dict(hat_id="BIO-CAP-005", hat_adi="FireFighter TMV",    tur="Capsicum annuum",
             meyve_rengi="Turuncu",       verim_t_ha=14.7, raf_omru_gun=16, hasat_gunu=82,
             brix=5.9,
             fusarium_I=0,  tmv_Tm2a=1,  nematod_Mi12=1, rin_gen=0, pto_gen=0,
             fusarium_cM=18.0, tmv_cM=18.0, nematod_cM=28.0, rin_cM=9.0,
             etiketler="tmv direnci,nematod direnci,virüs direnci,ihracat"),
        dict(hat_id="BIO-CAP-006", hat_adi="SuperSweet Block",   tur="Capsicum annuum",
             meyve_rengi="Kırmızı",       verim_t_ha=17.0, raf_omru_gun=15, hasat_gunu=80,
             brix=8.0,
             fusarium_I=0,  tmv_Tm2a=0,  nematod_Mi12=0, rin_gen=0, pto_gen=0,
             fusarium_cM=18.0, tmv_cM=18.0, nematod_cM=28.0, rin_cM=9.0,
             etiketler="yüksek brix,yüksek verim,sanayi"),
        # ── KAVUN (Cucumis melo) ──
        dict(hat_id="BIO-MEL-001", hat_adi="Honeygold F1",       tur="Cucumis melo",
             meyve_rengi="Sarı-Altın",    verim_t_ha=24.0, raf_omru_gun=16, hasat_gunu=82,
             brix=14.5,
             fusarium_I=1,  tmv_Tm2a=0,  nematod_Mi12=0, rin_gen=0, pto_gen=0,
             fusarium_cM=30.0, tmv_cM=15.0, nematod_cM=42.0, rin_cM=20.0,
             etiketler="kavun,yüksek brix,fusarium direnci,ihracat"),
        dict(hat_id="BIO-MEL-002", hat_adi="Cantaloup Elite",    tur="Cucumis melo",
             meyve_rengi="Turuncu",       verim_t_ha=21.5, raf_omru_gun=14, hasat_gunu=78,
             brix=13.2,
             fusarium_I=0,  tmv_Tm2a=1,  nematod_Mi12=0, rin_gen=0, pto_gen=0,
             fusarium_cM=30.0, tmv_cM=15.0, nematod_cM=42.0, rin_cM=20.0,
             etiketler="kavun,kantalup,tmv direnci,özel pazar"),
        dict(hat_id="BIO-MEL-003", hat_adi="EarlyDawn PM",       tur="Cucumis melo",
             meyve_rengi="Beyaz-Sarı",    verim_t_ha=19.8, raf_omru_gun=18, hasat_gunu=72,
             brix=12.8,
             fusarium_I=0,  tmv_Tm2a=0,  nematod_Mi12=1, rin_gen=1, pto_gen=0,
             fusarium_cM=30.0, tmv_cM=15.0, nematod_cM=42.0, rin_cM=20.0,
             etiketler="kavun,erken olgunlaşma,nematod direnci,uzun raf ömrü"),
        # ── KARPUZ (Citrullus lanatus) ──
        dict(hat_id="BIO-WAT-001", hat_adi="Crimson Giant F2",   tur="Citrullus lanatus",
             meyve_rengi="Kırmızı",       verim_t_ha=35.0, raf_omru_gun=21, hasat_gunu=88,
             brix=11.5,
             fusarium_I=1,  tmv_Tm2a=0,  nematod_Mi12=0, rin_gen=0, pto_gen=0,
             fusarium_cM=38.0, tmv_cM=25.0, nematod_cM=50.0, rin_cM=18.0,
             etiketler="karpuz,yüksek verim,fusarium direnci,endüstriyel"),
        dict(hat_id="BIO-WAT-002", hat_adi="Seedless Wonder",    tur="Citrullus lanatus",
             meyve_rengi="Kırmızı",       verim_t_ha=28.5, raf_omru_gun=19, hasat_gunu=84,
             brix=12.2,
             fusarium_I=0,  tmv_Tm2a=0,  nematod_Mi12=0, rin_gen=0, pto_gen=0,
             fusarium_cM=38.0, tmv_cM=25.0, nematod_cM=50.0, rin_cM=18.0,
             etiketler="karpuz,tohumsuz,özel pazar,ihracat"),
        dict(hat_id="BIO-WAT-003", hat_adi="YellowFlesh Mini",   tur="Citrullus lanatus",
             meyve_rengi="Sarı Et",       verim_t_ha=22.0, raf_omru_gun=17, hasat_gunu=80,
             brix=13.0,
             fusarium_I=0,  tmv_Tm2a=0,  nematod_Mi12=1, rin_gen=0, pto_gen=0,
             fusarium_cM=38.0, tmv_cM=25.0, nematod_cM=50.0, rin_cM=18.0,
             etiketler="karpuz,sarı et,nematod direnci,gourmet"),
    ]
    return pd.DataFrame(rows)

# ─────────────────────────────────────────────────────────────────────────────
# §5  GENETİK MOTOR (hesap sınıfları — Streamlit bağımsız)
# ─────────────────────────────────────────────────────────────────────────────

# ── §5.1  Matchmaker ─────────────────────────────────────────────────────────

GEN_SUTUNLARI = ["fusarium_I", "tmv_Tm2a", "nematod_Mi12", "rin_gen", "pto_gen"]
GEN_ETIKETLER = {
    "fusarium_I"  : "Fusarium Direnci (I)",
    "tmv_Tm2a"    : "TMV Direnci (Tm-2a)",
    "nematod_Mi12": "Nematod Direnci (Mi-1.2)",
    "rin_gen"     : "Uzun Raf Ömrü (rin)",
    "pto_gen"     : "Pseudomonas Direnci (Pto)",
    "yüksek_verim": "Yüksek Verim (≥18 t/ha)",
    "uzun_raf"    : "Uzun Raf Ömrü (≥18 gün)",
    "yüksek_brix" : "Yüksek Brix (≥7°)",
}


def mendel_f2_p(anne_val: int, baba_val: int) -> float:
    """
    İki ebeveynin tek-gen değerinden F2 dominant fenotip olasılığını döndürür.
    0 = resesif homozigot (aa), 1 = dominant (AA veya Aa varsayımı)
    """
    if anne_val == 1 and baba_val == 1:
        return 1.00   # AA x AA → tümü
    elif anne_val == 1 or baba_val == 1:
        return 0.75   # Aa x aa → 3:1
    else:
        return 0.00   # aa x aa → hiç


def matchmaker_skoru(
    anne: pd.Series,
    baba: pd.Series,
    hedef_genler: List[str],
    hedef_fenotip: List[str],
) -> Dict:
    """
    Anne × Baba çifti için 100 üzerinden bileşik uyum skoru hesaplar.
    """
    # 1. Gen uyum skoru (max 50 puan)
    gen_p_toplam = 0.0
    gen_detay    = {}
    for g in hedef_genler:
        if g not in anne.index:
            continue
        p = mendel_f2_p(int(anne[g]), int(baba[g]))
        gen_p_toplam += p
        gen_detay[GEN_ETIKETLER.get(g, g)] = round(p * 100, 1)
    gen_skoru = (gen_p_toplam / max(len(hedef_genler), 1)) * 50

    # 2. Fenotip uyum skoru (max 30 puan)
    feno_skoru = 0.0
    if "yüksek_verim" in hedef_fenotip:
        avg_v = (anne["verim_t_ha"] + baba["verim_t_ha"]) / 2
        feno_skoru += min(avg_v / 25, 1.0) * 15
    if "uzun_raf" in hedef_fenotip:
        avg_r = (anne["raf_omru_gun"] + baba["raf_omru_gun"]) / 2
        feno_skoru += min(avg_r / 30, 1.0) * 10
    if "yüksek_brix" in hedef_fenotip:
        avg_b = (anne["brix"] + baba["brix"]) / 2
        feno_skoru += min(avg_b / 10, 1.0) * 5
    if not hedef_fenotip:
        feno_skoru = 15   # Fenotip hedefi yoksa nötr

    # 3. Tür uyumu (max 20 puan)
    tur_skoru = 20.0 if anne["tur"] == baba["tur"] else 0.0

    toplam = min(gen_skoru + feno_skoru + tur_skoru, 100.0)
    return {
        "anne_id"       : anne["hat_id"],
        "anne_adi"      : anne["hat_adi"],
        "baba_id"       : baba["hat_id"],
        "baba_adi"      : baba["hat_adi"],
        "tur"           : anne["tur"],
        "skor"          : round(toplam, 1),
        "gen_skoru"     : round(gen_skoru, 1),
        "feno_skoru"    : round(feno_skoru, 1),
        "tur_skoru"     : round(tur_skoru, 1),
        "gen_detay"     : gen_detay,
    }


def en_iyi_eslesme(
    df: pd.DataFrame,
    hedef_genler: List[str],
    hedef_fenotip: List[str],
    tür_filtre: str = "Tümü",
    top_n: int = 10,
) -> pd.DataFrame:
    """Tüm (anne, baba) permütasyonlarını değerlendirip en iyi N'i döndürür."""
    hatlar = df if tür_filtre == "Tümü" else df[df["tur"] == tür_filtre]
    if len(hatlar) < 2:
        return pd.DataFrame()
    sonuclar = []
    for i, j in itertools.permutations(range(len(hatlar)), 2):
        anne = hatlar.iloc[i]
        baba = hatlar.iloc[j]
        if anne["hat_id"] == baba["hat_id"]:
            continue
        s = matchmaker_skoru(anne, baba, hedef_genler, hedef_fenotip)
        sonuclar.append(s)
    if not sonuclar:
        return pd.DataFrame()
    res = pd.DataFrame(sonuclar).drop_duplicates(
        subset=["anne_id", "baba_id"]
    ).sort_values("skor", ascending=False).head(top_n).reset_index(drop=True)
    res.index += 1
    return res


# ── §5.2  Risk Engine ────────────────────────────────────────────────────────

def haldane_r(cm: float) -> float:
    """Haldane harita fonksiyonu: r = 0.5*(1 - e^(-2d/100))"""
    return 0.5 * (1 - math.exp(-2 * cm / 100))


def linkage_drag_analiz(cm_a: float, cm_b: float) -> Dict:
    """
    İki genin cM pozisyonundan Linkage Drag riskini hesaplar.
    cm_a, cm_b: Aynı referans noktasına göre cM konumları
    """
    mesafe = abs(cm_a - cm_b)
    r      = haldane_r(mesafe)
    surukleme_riski = 1 - r   # Birlikte kalıtılma olasılığı

    if mesafe < 5:
        seviye, aciklama = "KRİTİK", "Genler neredeyse her zaman birlikte kalıtılır."
    elif mesafe < 15:
        seviye, aciklama = "YÜKSEK", "Linkage drag yüksek risk taşıyor; geniş populasyon gerekli."
    elif mesafe < 30:
        seviye, aciklama = "ORTA", "Makul ayrışma olasılığı; MAS ile yönetilebilir."
    else:
        seviye, aciklama = "DÜŞÜK", "Genler büyük ölçüde bağımsız ayrışır."

    # Rekombinan bitki sayısı (%95 güven)
    if r > 0:
        gerekli_bitki = math.ceil(math.log(1 - GUVEN) / math.log(1 - r))
    else:
        gerekli_bitki = 999_999

    return {
        "mesafe_cM"      : round(mesafe, 2),
        "rekomb_p"       : round(r, 4),
        "surukleme_riski": round(surukleme_riski * 100, 1),
        "seviye"         : seviye,
        "aciklama"       : aciklama,
        "gerekli_bitki"  : gerekli_bitki,
    }


def f_nesil_sim(anne_val: int, baba_val: int, nesil: int = 4) -> pd.DataFrame:
    """
    F1 → F(nesil) arasında dominant fenotip sabitlenme (homozigot) olasılığını döndürür.

    Formül: Her nesilde heterozigot oran yarıya iner (selfing varsayımı).
    p_dominant(n) = 1 - (1/2)^(n-1) * p_het_F1 * (3/4)
    (Basitleştirilmiş yaklaşım — bağımsız ayrışma varsayımı)
    """
    rows = []
    for n in range(1, nesil + 1):
        if anne_val == 1 and baba_val == 1:
            # Her iki ebeveyn dominant → F1 ve ötesi sabitlenir
            p_dom  = 1.0
            p_homo = 1.0
        elif anne_val == 1 or baba_val == 1:
            # Heterozigot F1
            p_het_n = (0.5) ** (n - 1)   # F1=0.50, F2=0.25, F3=0.125...
            p_dom   = 1 - p_het_n * 0.25 if n > 1 else 0.75
            p_homo  = 1 - p_het_n
        else:
            # Her iki resesif → hedef fenotip hiç görülmez
            p_dom  = 0.0
            p_homo = 0.0
        rows.append({
            "Nesil"                 : f"F{n}",
            "Dominant Fenotip (%)"  : round(p_dom * 100, 2),
            "Homozigot Oran (%)"    : round(p_homo * 100, 2),
        })
    return pd.DataFrame(rows)


# ── §5.3  Proteomik Motor ────────────────────────────────────────────────────

KODON_TABLOSU: Dict[str, str] = {
    'TTT':'F','TTC':'F','TTA':'L','TTG':'L','CTT':'L','CTC':'L','CTA':'L','CTG':'L',
    'ATT':'I','ATC':'I','ATA':'I','ATG':'M','GTT':'V','GTC':'V','GTA':'V','GTG':'V',
    'TCT':'S','TCC':'S','TCA':'S','TCG':'S','CCT':'P','CCC':'P','CCA':'P','CCG':'P',
    'ACT':'T','ACC':'T','ACA':'T','ACG':'T','GCT':'A','GCC':'A','GCA':'A','GCG':'A',
    'TAT':'Y','TAC':'Y','TAA':'*','TAG':'*','CAT':'H','CAC':'H','CAA':'Q','CAG':'Q',
    'AAT':'N','AAC':'N','AAA':'K','AAG':'K','GAT':'D','GAC':'D','GAA':'E','GAG':'E',
    'TGT':'C','TGC':'C','TGA':'*','TGG':'W','CGT':'R','CGC':'R','CGA':'R','CGG':'R',
    'AGT':'S','AGC':'S','AGA':'R','AGG':'R','GGT':'G','GGC':'G','GGA':'G','GGG':'G',
}

# 15 ticari/bilimsel motif kütüphanesi
MOTIF_KUTUPHANE: List[Dict] = [
    {"isim":"NBS P-loop (Kinaz-1a)",   "motif":"GVGKTT",    "sinif":"NBS-LRR Direnç",
     "islev":"Nükleotid bağlanma — NBS-LRR R-gen çekirdeği.",
     "tarla":"Geniş spektrumlu patojen direnci."},
    {"isim":"NBS Kinaz-2 (RNBS-A)",    "motif":"ILVDDE",    "sinif":"NBS-LRR Direnç",
     "islev":"RNBS-A bölgesi; NBS etkinleştirme kaskadı.",
     "tarla":"R-gen aktivasyonu — hipersensitivite yanıtı."},
    {"isim":"LRR Tekrar Birimi",        "motif":"LXXLXLXX",  "sinif":"NBS-LRR Direnç",
     "islev":"Lösin tekrarlı bölge; protein-protein etkileşim yüzeyi.",
     "tarla":"Effektör tanıma spektrumunu belirler."},
    {"isim":"TIR Domaini (TIR-NBS)",    "motif":"FLHFAD",    "sinif":"TIR-NBS-LRR",
     "islev":"Toll/IL-1 reseptör domaini; sinyal iletimi.",
     "tarla":"Dikotil bitkilerinde geniş dayanıklılık sınıfı."},
    {"isim":"Kinaz DFG Motifi",         "motif":"DFG",       "sinif":"Serin/Treonin Kinaz",
     "islev":"ATP bağlanma ve substrat fosforilasyonu.",
     "tarla":"Savunma sinyal kaskadı aktivasyonu."},
    {"isim":"Kinaz VAIK Motifi",        "motif":"VAIK",      "sinif":"Protein Kinaz",
     "islev":"Kinaz-2 bölgesi; katalitik aktivite.",
     "tarla":"Biyotik/abiyotik stres sinyal iletimi."},
    {"isim":"WRKY Transkripsiyon Faktörü","motif":"WRKYGQK", "sinif":"TF — WRKY",
     "islev":"W-box (TTGAC) DNA bağlanma; savunma geni ifadesi.",
     "tarla":"Sistemik edinilmiş direnç (SAR) mekanizması."},
    {"isim":"MYB DNA Bağlanma (R2R3)",  "motif":"GRTWHTE",   "sinif":"TF — MYB",
     "islev":"R2R3-MYB; pigment ve olgunlaşma geni düzenleme.",
     "tarla":"Meyve rengi, antosiyanin birikimi, olgunlaşma."},
    {"isim":"MADS-Box Domaini",         "motif":"MGRNGKVEHI","sinif":"TF — MADS",
     "islev":"MADS kutu; çiçeklenme ve meyve gelişimi.",
     "tarla":"Olgunlaşma zamanı, meyve kalitesi (rin geni ailesi)."},
    {"isim":"AP2/ERF Domaini",          "motif":"RAYDAWLKL", "sinif":"TF — ERF",
     "islev":"Etilen yanıt faktörü; stres & olgunlaşma.",
     "tarla":"Stres toleransı, hasat zamanlaması."},
    {"isim":"PR-1 Sinyal Peptidi",      "motif":"MKKLLAL",   "sinif":"PR Proteini",
     "islev":"Salisilik asit yolunda salgılanan savunma proteini.",
     "tarla":"SAR markörü — PR-1 gen ifadesi."},
    {"isim":"PR-5 (Osmotin/Taumatin)", "motif":"CCQCSPLDS", "sinif":"PR Proteini",
     "islev":"Membran permeabilizasyonu; antifungal aktivite.",
     "tarla":"Küf/fungal patojenlere karşı direnç."},
    {"isim":"ABC Taşıyıcı (LSGGQ)",    "motif":"LSGGQ",     "sinif":"Taşıyıcı Protein",
     "islev":"ATP bağlama kaseti; membran molekül taşınımı.",
     "tarla":"Fitotoksin atımı, ilaç direnci benzeri mekanizma."},
    {"isim":"SOD Katalitik Merkez",     "motif":"HVHAQY",    "sinif":"Antioksidan Enzim",
     "islev":"Süperoksit dismutaz; ROS temizleme.",
     "tarla":"Kuraklık, ısı ve oksidatif stres toleransı."},
    {"isim":"HSP90 EEVD Terminali",     "motif":"EEVD",      "sinif":"Chaperone",
     "islev":"Isı şoku proteini 90; protein katlanma yönetimi.",
     "tarla":"Yüksek sıcaklık stres koruması."},
]

# Hidrofobik amino asitler (Kyte-Doolittle pozitif)
HIDROFOBIK = set("VILMFWP")


def dna_cevir(dna_str: str) -> str:
    """DNA → Amino asit (en uzun ORF — 3 çerçeve)."""
    dna = "".join(c for c in dna_str.upper().strip()
                  if c in "ACGTUNRYSWKMBDHV")
    en_uzun = ""
    for f in range(3):
        aa_list = []
        for i in range(f, len(dna) - 2, 3):
            kodon = dna[i:i+3]
            if len(kodon) < 3:
                break
            h = KODON_TABLOSU.get(kodon, "X")
            if h == "*":
                break
            aa_list.append(h)
        peptid = "".join(aa_list)
        if len(peptid) > len(en_uzun):
            en_uzun = peptid
    return en_uzun


def biopython_cevir(dna_str: str) -> str:
    """Biopython kullanılabilirse onunla çevir, yoksa dahili tabloyu kullan."""
    if _BIO_OK:
        try:
            dna = "".join(c for c in dna_str.upper() if c in "ACGTUNRYSWKMBDHV")
            dna = dna[:len(dna) - len(dna) % 3]
            return str(Seq(dna).translate(to_stop=True))
        except Exception:
            pass
    return dna_cevir(dna_str)


def motif_tara(aa: str) -> List[Dict]:
    """Amino asit dizisinde MOTIF_KUTUPHANE'yi tarar."""
    bulunan = []
    for m in MOTIF_KUTUPHANE:
        pat = m["motif"].replace("X", ".").replace("x", ".")
        try:
            hits = list(re.finditer(pat, aa, re.IGNORECASE))
        except re.error:
            hits = []
        if hits:
            bulunan.append({**m, "konumlar": [h.start() for h in hits], "adet": len(hits)})
    return bulunan


def hidrofobik_analiz(aa: str) -> Dict:
    """Lösin yüzdesi ve genel hidrofobiklik oranını hesaplar."""
    if not aa:
        return {}
    leucine_pct  = aa.count("L") / len(aa) * 100
    hidrofob_pct = sum(1 for c in aa if c in HIDROFOBIK) / len(aa) * 100
    return {
        "leucine_pct" : round(leucine_pct, 1),
        "hidrofob_pct": round(hidrofob_pct, 1),
    }


def akilli_tahmin(motifler: List[Dict], aa: str) -> Optional[str]:
    """
    Motif eşleşmesi yoksa hidrofobiklik/lösin oranına göre çıkarım yapar.
    Eşik: leucine ≥ 8% VE hidrofob ≥ 35% → savunma proteini benzerliği.
    """
    if motifler:
        return None   # Motif zaten bulundu
    if not aa or len(aa) < 20:
        return None
    h = hidrofobik_analiz(aa)
    if h["leucine_pct"] >= 8.0 and h["hidrofob_pct"] >= 35.0:
        return (
            f"Tam motif eşleşmesi bulunamadı. Ancak bu proteindeki "
            f"**%{h['hidrofob_pct']} hidrofobik amino asit** oranı ve "
            f"**%{h['leucine_pct']} lösin (L)** yüzdesi yüksek bulundu. "
            f"Bu bileşim, NBS-LRR veya LRR tekrar bölgelerine sahip "
            f"**R-Gen (Direnç) proteini** yapısına benzemektedir. "
            f"Yapısal doğrulama için AlphaFold / InterPro analizi önerilir."
        )
    elif h["hidrofob_pct"] >= 45.0:
        return (
            f"Tam motif eşleşmesi bulunamadı. Yüksek hidrofobiklik (**%{h['hidrofob_pct']}**) "
            f"bu dizinin bir **membran proteini veya taşıyıcı** olduğuna işaret edebilir. "
            f"Dizi uzunluğu ve bağlam bilgisi ile değerlendirin."
        )
    return None


# ── §5.4  Genetic Detective (Akrabalık Analizi) ──────────────────────────────

def jaccard_benzerlik(s1: set, s2: set) -> float:
    """Jaccard benzerlik skoru: |A∩B| / |A∪B|"""
    if not s1 and not s2:
        return 1.0
    if not s1 or not s2:
        return 0.0
    return len(s1 & s2) / len(s1 | s2)


def ozellik_seti(satir: pd.Series) -> set:
    """Bir hattın genetik özelliklerini ikili set olarak döndürür."""
    ozellikler = set()
    for g in GEN_SUTUNLARI:
        if g in satir.index and satir[g] == 1:
            ozellikler.add(g)
    # Fenotipik etiketleri de ekle
    if "etiketler" in satir.index and isinstance(satir["etiketler"], str):
        for e in satir["etiketler"].split(","):
            ozellikler.add(e.strip().lower())
    return ozellikler


def akrabalik_matrisi(df: pd.DataFrame) -> pd.DataFrame:
    """Tüm hat çiftleri için Jaccard benzerlik matrisi oluşturur."""
    ids    = df["hat_id"].tolist()
    setler = [ozellik_seti(df.iloc[i]) for i in range(len(df))]
    n      = len(ids)
    mat    = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            mat[i, j] = jaccard_benzerlik(setler[i], setler[j])
    return pd.DataFrame(mat, index=ids, columns=ids)


# ─────────────────────────────────────────────────────────────────────────────
# §6  GRAFİK YARDIMCILARI (Plotly)
# ─────────────────────────────────────────────────────────────────────────────

def plotly_layout(title: str = "") -> Dict:
    """Standart koyu-yeşil Plotly layout şablonu."""
    return dict(
        title       = dict(text=title, font=dict(color=PAL["gold"], size=16)),
        paper_bgcolor = PAL["bg"],
        plot_bgcolor  = PAL["panel"],
        font          = dict(color=PAL["grey_hi"], family="Inter, Segoe UI, sans-serif"),
        xaxis         = dict(gridcolor=PAL["border"], zerolinecolor=PAL["border"]),
        yaxis         = dict(gridcolor=PAL["border"], zerolinecolor=PAL["border"]),
        legend        = dict(bgcolor=PAL["panel"], bordercolor=PAL["border"]),
        margin        = dict(l=60, r=30, t=60, b=60),
    )


def fig_matchmaker_bar(df_res: pd.DataFrame) -> "go.Figure":
    """Matchmaker sonuçları için yatay bar grafiği."""
    fig = go.Figure()
    etiketler = [f"{r['anne_adi'][:12]} × {r['baba_adi'][:12]}"
                 for _, r in df_res.iterrows()]
    fig.add_trace(go.Bar(
        y=etiketler, x=df_res["skor"], orientation="h",
        marker=dict(
            color=df_res["skor"],
            colorscale=[[0, PAL["green_dim"]], [0.5, PAL["green_mid"]], [1, PAL["green_hi"]]],
            showscale=True,
            colorbar=dict(title="Skor", tickfont=dict(color=PAL["grey_hi"])),
        ),
        text=[f"{s:.1f}" for s in df_res["skor"]],
        textposition="outside",
        textfont=dict(color=PAL["gold"]),
        hovertemplate="%{y}<br>Skor: %{x:.1f}<extra></extra>",
    ))
    layout = plotly_layout("🏆 Matchmaker — Eşleşme Skorları")
    layout["yaxis"]["autorange"] = "reversed"
    layout["height"] = max(350, len(df_res) * 42)
    fig.update_layout(**layout)
    return fig


def fig_f_nesil(df_sim: pd.DataFrame, gen_adi: str) -> "go.Figure":
    """F1-F4 nesil simülasyon çizgi grafiği."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_sim["Nesil"], y=df_sim["Dominant Fenotip (%)"],
        name="Dominant Fenotip (%)",
        line=dict(color=PAL["green_hi"], width=2.5),
        mode="lines+markers",
        marker=dict(size=9, color=PAL["green_hi"]),
        fill="tozeroy", fillcolor="rgba(74,222,128,0.08)",
        hovertemplate="%{x}: %{y:.1f}%<extra>Dominant</extra>",
    ))
    fig.add_trace(go.Scatter(
        x=df_sim["Nesil"], y=df_sim["Homozigot Oran (%)"],
        name="Homozigot Oran (%)",
        line=dict(color=PAL["gold"], width=2.5, dash="dot"),
        mode="lines+markers",
        marker=dict(size=9, color=PAL["gold"]),
        hovertemplate="%{x}: %{y:.1f}%<extra>Homozigot</extra>",
    ))
    layout = plotly_layout(f"⏱️ F1→F4 Sabitlenme Simülasyonu — {gen_adi}")
    layout["yaxis"]["range"] = [0, 105]
    layout["height"] = 380
    fig.update_layout(**layout)
    return fig


def fig_risk_gauge(risk_pct: float, baslik: str = "Linkage Drag Riski") -> "go.Figure":
    """Risk seviyesini gösteren gösterge (gauge) grafiği."""
    renk = PAL["red"] if risk_pct > 70 else PAL["amber"] if risk_pct > 40 else PAL["green_mid"]
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=risk_pct,
        title=dict(text=baslik, font=dict(color=PAL["gold"], size=14)),
        number=dict(suffix="%", font=dict(color=renk, size=28)),
        gauge=dict(
            axis      = dict(range=[0, 100], tickcolor=PAL["grey_hi"]),
            bar       = dict(color=renk),
            bgcolor   = PAL["panel"],
            bordercolor = PAL["border"],
            steps     = [
                dict(range=[0, 40],  color=PAL["green_dim"]),
                dict(range=[40, 70], color=PAL["gold_dim"]),
                dict(range=[70, 100],color="#450a0a"),
            ],
            threshold = dict(line=dict(color=PAL["red"], width=3), value=70),
        ),
    ))
    fig.update_layout(paper_bgcolor=PAL["bg"], font=dict(color=PAL["grey_hi"]),
                      height=280, margin=dict(l=30, r=30, t=50, b=20))
    return fig


def fig_genetik_harita(df: pd.DataFrame) -> "go.Figure":
    """
    Genlerin cM pozisyonlarını interaktif scatter plot ile görselleştirir.
    Her gen: yatay eksen = cM, dikey eksen = fiktif kromozom grubu.
    """
    gen_kolon_cM = {
        "fusarium_I"  : ("fusarium_cM",   "Fusarium I",   "Chr 11", 0),
        "tmv_Tm2a"    : ("tmv_cM",         "TMV Tm-2a",    "Chr 9",  1),
        "nematod_Mi12": ("nematod_cM",     "Mi-1.2",       "Chr 6",  2),
        "rin_gen"      : ("rin_cM",         "rin",          "Chr 5",  3),
    }
    fig = go.Figure()
    # Her tür için farklı renk
    tur_renk = {
        "Solanum lycopersicum": PAL["green_hi"],
        "Capsicum annuum"     : PAL["gold"],
        "Cucumis melo"        : "#60a5fa",
        "Citrullus lanatus"   : "#c084fc",
    }

    for gen_kolon, (cm_kolon, gen_adi, krom, y_pos) in gen_kolon_cM.items():
        if cm_kolon not in df.columns:
            continue
        # Sadece bu geni taşıyan hatlar
        alt = df[df[gen_kolon] == 1].copy()
        if alt.empty:
            continue
        for tur, grup in alt.groupby("tur"):
            cm_vals = grup[cm_kolon].values
            fig.add_trace(go.Scatter(
                x=[cm_vals.mean()],
                y=[y_pos + np.random.uniform(-0.15, 0.15)],
                mode="markers+text",
                name=f"{gen_adi} ({tur.split()[0]})",
                marker=dict(
                    size=14,
                    color=tur_renk.get(tur, PAL["grey_mid"]),
                    symbol="diamond",
                    line=dict(color=PAL["border"], width=1),
                ),
                text=[gen_adi],
                textposition="top center",
                textfont=dict(size=9, color=PAL["grey_hi"]),
                hovertemplate=(
                    f"<b>{gen_adi}</b><br>"
                    f"Tür: {tur}<br>"
                    f"cM: {cm_vals.mean():.1f}<br>"
                    f"Hat sayısı: {len(grup)}<extra></extra>"
                ),
            ))

    # Kromozom çubukları (arka plan çizgisi)
    for i, (_, (_, gen_adi, krom, y_pos)) in enumerate(gen_kolon_cM.items()):
        fig.add_shape(
            type="line", x0=0, x1=100, y0=y_pos, y1=y_pos,
            line=dict(color=PAL["border"], width=2, dash="dot"),
        )
        fig.add_annotation(
            x=-2, y=y_pos, text=krom, showarrow=False,
            font=dict(color=PAL["gold"], size=11), xanchor="right",
        )

    # Tehlike bölgesi (< 10 cM arası)
    fig.add_vrect(
        x0=0, x1=10, fillcolor="rgba(248,113,113,0.07)",
        annotation_text="⚠ Yakın Bağlantı Bölgesi (<10 cM)",
        annotation_font_color=PAL["red"],
        line_width=0,
    )

    layout = plotly_layout("🗺️ Dinamik Genetik Harita — Kromozom cM Konumları")
    layout["xaxis"] = dict(
        title="Genetik Mesafe (centiMorgan)",
        gridcolor=PAL["border"],
        range=[-5, 105],
        tickfont=dict(color=PAL["grey_hi"]),
    )
    layout["yaxis"] = dict(
        tickvals=list(range(len(gen_kolon_cM))),
        ticktext=[f"Chr {i+1}" for i in range(len(gen_kolon_cM))],
        gridcolor=PAL["border"],
        tickfont=dict(color=PAL["grey_hi"]),
    )
    layout["height"]      = 380
    layout["showlegend"]  = True
    layout["legend"]["title"] = dict(text="Gen · Tür", font=dict(color=PAL["gold"]))
    fig.update_layout(**layout)
    return fig


def fig_heatmap(mat: pd.DataFrame) -> "go.Figure":
    """Akrabalık (Jaccard benzerlik) ısı haritası."""
    # Kısa ID etiketleri
    ids_kisa = [i[:12] for i in mat.index.tolist()]
    fig = go.Figure(go.Heatmap(
        z=mat.values,
        x=ids_kisa,
        y=ids_kisa,
        colorscale=[
            [0.0, PAL["bg"]],
            [0.3, PAL["green_dim"]],
            [0.7, PAL["green_mid"]],
            [1.0, PAL["green_hi"]],
        ],
        zmin=0, zmax=1,
        colorbar=dict(
            title="Jaccard<br>Benzerliği",
            tickfont=dict(color=PAL["grey_hi"]),
            titlefont=dict(color=PAL["gold"]),
        ),
        hovertemplate="Hat-1: %{y}<br>Hat-2: %{x}<br>Benzerlik: %{z:.3f}<extra></extra>",
    ))
    layout = plotly_layout("🔥 Genetik Akrabalık Isı Haritası (Jaccard Benzerliği)")
    layout["xaxis"]["tickangle"] = -45
    layout["xaxis"]["tickfont"]  = dict(size=9, color=PAL["grey_hi"])
    layout["yaxis"]["tickfont"]  = dict(size=9, color=PAL["grey_hi"])
    n = len(mat)
    layout["height"] = max(400, n * 30 + 120)
    fig.update_layout(**layout)
    return fig


def fig_proteomic_bar(motifler: List[Dict]) -> "go.Figure":
    """Bulunan motifleri ve adet bilgisini gösteren bar grafiği."""
    if not motifler:
        return None
    isimsler = [m["isim"][:30] for m in motifler]
    adetler  = [m["adet"] for m in motifler]
    siniflar = [m["sinif"] for m in motifler]
    renk_map = {
        "NBS-LRR Direnç"    : PAL["green_hi"],
        "TIR-NBS-LRR"       : PAL["green_mid"],
        "Serin/Treonin Kinaz": PAL["gold"],
        "Protein Kinaz"     : PAL["amber"],
        "TF — WRKY"         : "#60a5fa",
        "TF — MYB"          : "#c084fc",
        "TF — MADS"         : "#f97316",
        "TF — ERF"          : "#34d399",
        "PR Proteini"       : "#fb7185",
        "Taşıyıcı Protein"  : PAL["grey_mid"],
        "Antioksidan Enzim" : "#a3e635",
        "Chaperone"         : "#fbbf24",
    }
    renkler = [renk_map.get(s, PAL["grey_mid"]) for s in siniflar]
    fig = go.Figure(go.Bar(
        y=isimsler, x=adetler, orientation="h",
        marker=dict(color=renkler, line=dict(color=PAL["border"], width=0.5)),
        text=[f"{a}×" for a in adetler],
        textposition="outside",
        textfont=dict(color=PAL["gold"]),
        hovertemplate="%{y}<br>Eşleşme sayısı: %{x}<extra></extra>",
    ))
    layout = plotly_layout("🔬 Tespit Edilen Protein Motifleri")
    layout["yaxis"]["autorange"] = "reversed"
    layout["height"] = max(300, len(motifler) * 45)
    fig.update_layout(**layout)
    return fig


# ─────────────────────────────────────────────────────────────────────────────
# §7  SIDEBAR (Veri Yükleme + Navigasyon)
# ─────────────────────────────────────────────────────────────────────────────

def sidebar_render() -> pd.DataFrame:
    """Sidebar'ı render eder, veri çerçevesini döndürür."""
    with st.sidebar:
        # Logo & başlık
        st.markdown(f"""
        <div style="text-align:center;padding:1rem 0 0.5rem">
          <div style="font-size:2.4rem">🧬</div>
          <div style="color:{PAL['green_hi']};font-weight:800;font-size:1.18rem;
                      letter-spacing:1.5px">BIOVALENT</div>
          <div style="color:{PAL['grey_mid']};font-size:0.70rem;letter-spacing:3px;
                      margin-top:2px">SENTINEL v{VER}</div>
          <div style="color:{PAL['gold']};font-size:0.72rem;
                      margin-top:6px;font-style:italic">
            {SLOGAN}
          </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")
        st.markdown(f"### 📁 Veri Yükleme")
        st.caption("Excel (.xlsx) veya CSV dosyası yükleyin. Yüklemezseniz demo veri kullanılır.")

        dosya = st.file_uploader(
            "Hat Envanteri",
            type=["xlsx", "csv"],
            help="Gerekli sütunlar: hat_id, hat_adi, tur, verim_t_ha, raf_omru_gun, "
                 "hasat_gunu, brix, fusarium_I, tmv_Tm2a, nematod_Mi12, rin_gen, pto_gen, "
                 "fusarium_cM, tmv_cM, nematod_cM, rin_cM, etiketler",
        )

        df = None
        if dosya is not None:
            try:
                if dosya.name.endswith(".csv"):
                    df = pd.read_csv(dosya)
                else:
                    df = pd.read_excel(dosya)
                st.success(f"✅ {len(df)} hat yüklendi: **{dosya.name}**", icon="✅")
            except Exception as exc:
                st.error(f"Dosya okunamadı: {exc}", icon="❌")
                df = None

        if df is None:
            df = demo_veri()
            st.info("📊 Demo veri seti kullanılıyor (25 hat).", icon="ℹ️")

        st.markdown("---")

        # Özet metrikleri
        st.markdown(f"**📋 Envanter Özeti**")
        c1, c2 = st.columns(2)
        c1.metric("Toplam Hat", len(df))
        c2.metric("Tür Sayısı", df["tur"].nunique() if "tur" in df.columns else "—")

        if "verim_t_ha" in df.columns:
            st.metric("Ort. Verim (t/ha)", f"{df['verim_t_ha'].mean():.1f}")
        if "raf_omru_gun" in df.columns:
            st.metric("Ort. Raf Ömrü (gün)", f"{df['raf_omru_gun'].mean():.0f}")

        st.markdown("---")
        st.markdown(f"""
        <div style="color:{PAL['grey_mid']};font-size:0.73rem;line-height:1.7">
          <b style="color:{PAL['green_mid']}">Bilimsel Kaynaklar</b><br>
          Jones et al. (1993) — <i>I</i> geni<br>
          Pelham (1966) — <i>Tm-2a</i><br>
          Martin et al. (1993) — <i>Pto</i><br>
          Giovannoni (2004) — <i>rin</i><br>
          Rossi et al. (1998) — <i>Mi-1.2</i><br>
          Haldane (1919) — Harita Fonksiyonu
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")
        st.markdown(f"""
        <div style="color:{PAL['grey_mid']};font-size:0.70rem;text-align:center">
          © {datetime.now().year} {FIRMA}<br>
          Bağımsız SaaS Platformu
        </div>
        """, unsafe_allow_html=True)

    return df


# ─────────────────────────────────────────────────────────────────────────────
# §8  SEKMELERİ RENDER ET
# ─────────────────────────────────────────────────────────────────────────────

# ── §8.1  Matchmaker ─────────────────────────────────────────────────────────

def sekme_matchmaker(df: pd.DataFrame) -> None:
    st.markdown("## 🧬 Matchmaker — Eşleştirme Motoru")
    st.markdown(
        "Hedef özellikleri seçin; sistem envanterdeki hatları tarayıp "
        "**Anne × Baba** çaprazlama adaylarını F2 Mendel olasılıkları ve "
        "fenotip uyumuyla 100 üzerinden puanlar."
    )

    with st.expander("📖 Skor Hesaplama Metodolojisi", expanded=False):
        st.markdown("""
        | Bileşen | Ağırlık | Açıklama |
        |---|---|---|
        | **Gen Uyumu** | %50 | Her hedef gen için F2 dominant fenotip olasılığı (Mendel) |
        | **Fenotipik Uyum** | %30 | Verim, raf ömrü ve brix normalize ortalaması |
        | **Tür Uyumu** | %20 | Aynı tür çiftlere tam puan, türlerarası sıfır |

        F2 olasılık kuralları: AA×AA → %100, Aa×aa → %75, aa×aa → %0
        """)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("**🎯 Hastalık Direnci Hedefleri**")
        h_fusarium  = st.checkbox("🛡️ Fusarium Direnci (I geni)",   value=True)
        h_tmv       = st.checkbox("🦠 TMV Direnci (Tm-2a)",          value=True)
        h_nematod   = st.checkbox("🪱 Nematod Direnci (Mi-1.2)",     value=False)
        h_pto       = st.checkbox("🔬 Pseudomonas Direnci (Pto)",    value=False)
        h_rin       = st.checkbox("⏳ Uzun Raf Ömrü — rin geni",      value=False)

    with col2:
        st.markdown("**📈 Fenotipik Hedefler**")
        h_yverim = st.checkbox("📦 Yüksek Verim (≥18 t/ha)",  value=True)
        h_yraf   = st.checkbox("🗓️ Uzun Raf Ömrü (≥18 gün)", value=False)
        h_ybrix  = st.checkbox("🍬 Yüksek Brix (≥7°)",        value=False)

    with col3:
        st.markdown("**⚙️ Filtreler**")
        tür_seç = st.selectbox(
            "Tür Filtresi",
            ["Tümü"] + sorted(df["tur"].unique().tolist()) if "tur" in df.columns else ["Tümü"],
        )
        top_n = st.slider("Kaç Sonuç Göster?", 3, 20, 8)

    hedef_genler: List[str] = []
    if h_fusarium: hedef_genler.append("fusarium_I")
    if h_tmv:      hedef_genler.append("tmv_Tm2a")
    if h_nematod:  hedef_genler.append("nematod_Mi12")
    if h_pto:      hedef_genler.append("pto_gen")
    if h_rin:      hedef_genler.append("rin_gen")

    hedef_fenotip: List[str] = []
    if h_yverim: hedef_fenotip.append("yüksek_verim")
    if h_yraf:   hedef_fenotip.append("uzun_raf")
    if h_ybrix:  hedef_fenotip.append("yüksek_brix")

    if st.button("🚀 Eşleştirme Analizini Başlat", key="mm_btn"):
        if not hedef_genler and not hedef_fenotip:
            st.warning("Lütfen en az bir hedef özellik seçin.", icon="⚠️")
            return
        try:
            with st.spinner("Genetik uyum analizi yapılıyor..."):
                res = en_iyi_eslesme(df, hedef_genler, hedef_fenotip, tür_seç, top_n)

            if res.empty:
                st.error("Uyumlu çift bulunamadı. Filtreleri genişletin.", icon="❌")
                return

            st.success(f"✅ {len(res)} eşleşme adayı bulundu.", icon="✅")

            # KPI satırı
            best = res.iloc[0]
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("🥇 En Yüksek Skor", f"{best['skor']:.1f}/100")
            m2.metric("Gen Uyum Skoru", f"{best['gen_skoru']:.1f}/50")
            m3.metric("Fenotip Skoru",   f"{best['feno_skoru']:.1f}/30")
            m4.metric("Tür Skoru",       f"{best['tur_skoru']:.1f}/20")

            # Bar grafiği
            if _PLT_OK:
                st.plotly_chart(fig_matchmaker_bar(res), use_container_width=True)

            # Sonuç tablosu
            st.markdown("### 📋 Eşleşme Sonuçları")
            gorsel_df = res[["anne_id","anne_adi","baba_id","baba_adi","tur","skor",
                             "gen_skoru","feno_skoru","tur_skoru"]].copy()
            gorsel_df.columns = ["Anne ID","Anne Adı","Baba ID","Baba Adı","Tür",
                                 "Skor","Gen Skoru","Fenotip Skoru","Tür Skoru"]
            st.dataframe(
                gorsel_df.style.background_gradient(subset=["Skor"],
                    cmap="Greens").format({"Skor": "{:.1f}","Gen Skoru":"{:.1f}",
                    "Fenotip Skoru":"{:.1f}","Tür Skoru":"{:.1f}"}),
                use_container_width=True,
            )

            # En iyi çift detayı
            st.markdown("---")
            st.markdown(f"### 🥇 En İyi Çift: `{best['anne_adi']}` × `{best['baba_adi']}`")
            with st.expander("Gen Bazında Detaylı Analiz", expanded=True):
                if best["gen_detay"]:
                    det_df = pd.DataFrame(
                        list(best["gen_detay"].items()),
                        columns=["Gen / Özellik", "F2 Başarı Olasılığı (%)"]
                    )
                    st.dataframe(det_df, use_container_width=True)
                else:
                    st.info("Gen hedefi seçilmedi; sadece fenotip skoru kullanıldı.")

        except Exception as exc:
            st.error(f"Analiz hatası: {exc}", icon="❌")
            st.code(traceback.format_exc())


# ── §8.2  Risk Engine & Simulation ───────────────────────────────────────────

def sekme_risk(df: pd.DataFrame) -> None:
    st.markdown("## ⚠️ Risk Engine & Simülasyon")
    st.markdown(
        "**Linkage Drag Analizi:** Seçilen iki genin cM mesafesine göre "
        "birlikte kalıtılma riskini hesaplar. "
        "**F4 Simülasyonu:** F1'den F4'e dominantlık ve homozigotluk eğrisini çizer."
    )

    with st.expander("📖 Bilimsel Temel", expanded=False):
        st.markdown("""
        **Haldane Harita Fonksiyonu:** `r = 0.5 × (1 − e^(−2d/100))`

        - `d` = centiMorgan (cM) cinsinden genetik mesafe
        - `r` = Rekombinasyon frekansı (0-0.5 arası)

        **Bitki Sayısı:** `n = ⌈log(0.05)/log(1−r)⌉` (%95 güven)

        **F-Nesil Sabitlenme (selfing):** Her nesil heterozigot oran yarıya iner.
        `Homozigot% = (1 − (1/2)^(n−1)) × 100`

        | cM | Risk | Yorum |
        |---|---|---|
        | <5 | 🔴 KRİTİK | Neredeyse her zaman birlikte kalıtılır |
        | 5–15 | 🟠 YÜKSEK | Geniş populasyon + MAS gerekli |
        | 15–30 | 🟡 ORTA | Yönetilebilir; MAS önerilir |
        | >30 | 🟢 DÜŞÜK | Büyük ölçüde bağımsız ayrışır |
        """)

    col_sol, col_sag = st.columns(2)

    with col_sol:
        st.markdown("### 🔗 Linkage Drag Analizi")
        gen_seçenekler = {
            "fusarium_I"  : ("Fusarium I geni",    "fusarium_cM"),
            "tmv_Tm2a"    : ("TMV Tm-2a geni",     "tmv_cM"),
            "nematod_Mi12": ("Mi-1.2 (Nematod)",   "nematod_cM"),
            "rin_gen"     : ("rin geni",            "rin_cM"),
        }
        gen_a_key = st.selectbox(
            "Gen A (Hedef Gen)",
            list(gen_seçenekler.keys()),
            format_func=lambda x: gen_seçenekler[x][0],
            key="risk_a",
        )
        gen_b_key = st.selectbox(
            "Gen B (Potansiyel Drag Geni)",
            [k for k in gen_seçenekler if k != gen_a_key],
            format_func=lambda x: gen_seçenekler[x][0],
            key="risk_b",
        )
        cm_a = st.number_input("Gen A cM Pozisyonu", 0.0, 200.0,
                               float(df[gen_seçenekler[gen_a_key][1]].mean())
                               if gen_seçenekler[gen_a_key][1] in df.columns else 45.0,
                               step=0.5, key="cm_a")
        cm_b = st.number_input("Gen B cM Pozisyonu", 0.0, 200.0,
                               float(df[gen_seçenekler[gen_b_key][1]].mean())
                               if gen_seçenekler[gen_b_key][1] in df.columns else 22.0,
                               step=0.5, key="cm_b")

        if st.button("⚡ Linkage Analizini Çalıştır", key="risk_btn"):
            try:
                sonuc = linkage_drag_analiz(cm_a, cm_b)
                sev_renk = {"KRİTİK": "error", "YÜKSEK": "error",
                            "ORTA": "warning", "DÜŞÜK": "success"}
                sev_fn   = {"KRİTİK": st.error, "YÜKSEK": st.error,
                            "ORTA": st.warning, "DÜŞÜK": st.success}

                sev_fn[sonuc["seviye"]](
                    f"**Risk Seviyesi: {sonuc['seviye']}** — {sonuc['aciklama']}"
                )

                r1, r2 = st.columns(2)
                r1.metric("Genetik Mesafe", f"{sonuc['mesafe_cM']:.1f} cM")
                r2.metric("Rekombinasyon p", f"{sonuc['rekomb_p']*100:.2f}%")
                r3, r4 = st.columns(2)
                r3.metric("Sürüklenme Riski", f"%{sonuc['surukleme_riski']}")
                r4.metric("Gerekli Bitki (95%)", f"{sonuc['gerekli_bitki']:,}")

                if _PLT_OK:
                    st.plotly_chart(
                        fig_risk_gauge(sonuc["surukleme_riski"], "Linkage Drag Riski"),
                        use_container_width=True,
                    )
                # Session'a kaydet (simülasyon için)
                st.session_state["risk_gen_a_key"] = gen_a_key
                st.session_state["risk_gen_a_val"] = int(df[gen_a_key].max())
                st.session_state["risk_gen_b_key"] = gen_b_key
                st.session_state["risk_gen_b_val"] = int(df[gen_b_key].min())

            except Exception as exc:
                st.error(f"Linkage analiz hatası: {exc}", icon="❌")

    with col_sag:
        st.markdown("### ⏱️ F1 → F4 Nesil Simülasyonu")
        sim_gen_key = st.selectbox(
            "Simüle Edilecek Gen",
            list(gen_seçenekler.keys()),
            format_func=lambda x: gen_seçenekler[x][0],
            key="sim_gen",
        )
        anne_val_sim = st.select_slider(
            "Anne Genotip Değeri",
            options=[0, 1],
            value=1,
            format_func=lambda x: "Dominant (1)" if x == 1 else "Resesif (0)",
            key="anne_sim",
        )
        baba_val_sim = st.select_slider(
            "Baba Genotip Değeri",
            options=[0, 1],
            value=0,
            format_func=lambda x: "Dominant (1)" if x == 1 else "Resesif (0)",
            key="baba_sim",
        )
        nesil_n = st.slider("Kaç Nesil Simüle Edilsin?", 2, 6, 4, key="nesil_n")

        if st.button("▶️ Simülasyonu Başlat", key="sim_btn"):
            try:
                df_sim = f_nesil_sim(anne_val_sim, baba_val_sim, nesil_n)
                if _PLT_OK:
                    gen_adi = gen_seçenekler[sim_gen_key][0]
                    st.plotly_chart(fig_f_nesil(df_sim, gen_adi), use_container_width=True)

                st.dataframe(df_sim, use_container_width=True)

                # Yorum
                son_nesil = df_sim.iloc[-1]
                if son_nesil["Homozigot Oran (%)"] >= 90:
                    st.success(
                        f"✅ F{nesil_n} itibarıyla homozigotluk **%{son_nesil['Homozigot Oran (%)']:.1f}**'e ulaştı. "
                        f"Hat, bu nesilde ticari kullanıma hazır sayılabilir.",
                        icon="✅"
                    )
                elif son_nesil["Homozigot Oran (%)"] >= 60:
                    st.warning(
                        f"⚠️ F{nesil_n} sonunda homozigotluk **%{son_nesil['Homozigot Oran (%)']:.1f}**. "
                        f"Daha fazla nesil veya markör destekli seçim (MAS) önerilir.",
                        icon="⚠️"
                    )
                else:
                    st.error(
                        f"❌ F{nesil_n} sonunda homozigotluk hâlâ **%{son_nesil['Homozigot Oran (%)']:.1f}**. "
                        f"Backcross stratejisi veya piramitleme gerekli.",
                        icon="❌"
                    )

            except Exception as exc:
                st.error(f"Simülasyon hatası: {exc}", icon="❌")


# ── §8.3  Genetic Map ─────────────────────────────────────────────────────────

def sekme_genetic_map(df: pd.DataFrame) -> None:
    st.markdown("## 🗺️ Genetic Map — Dinamik Genetik Harita")
    st.markdown(
        "Veri setindeki genlerin kromozom üzerindeki **cM konumlarını** interaktif "
        "olarak görselleştirir. Tehlikeli yakınlıkları (linkage drag riski) "
        "kırmızı bölge ile vurgular."
    )

    with st.expander("ℹ️ Harita Hakkında", expanded=False):
        st.markdown("""
        - **X ekseni:** centiMorgan (cM) — 0 = sentromer
        - **Yatay çizgiler:** Farklı kromozom grupları
        - **Kırmızı bölge:** <10 cM → Yüksek linkage drag riski
        - **Semboller:** Gen pozisyonunu taşıyan hat ortalaması
        - Her renk farklı bir bitki türünü temsil eder
        """)

    if not _PLT_OK:
        st.error("Plotly kurulu değil. pip install plotly", icon="❌")
        return

    try:
        gerekli = ["fusarium_cM", "tmv_cM", "nematod_cM", "rin_cM"]
        eksik   = [k for k in gerekli if k not in df.columns]
        if eksik:
            st.warning(f"cM sütunları eksik: {eksik}. Demo verisi ile gösteriliyor.", icon="⚠️")
            df_harita = demo_veri()
        else:
            df_harita = df

        st.plotly_chart(fig_genetik_harita(df_harita), use_container_width=True)

        # Yakın gen uyarıları
        st.markdown("### ⚠️ Kritik Yakınlık Uyarıları")
        gen_cM_ort = {
            "Fusarium I"   : df_harita["fusarium_cM"].mean() if "fusarium_cM" in df_harita else 45,
            "TMV Tm-2a"    : df_harita["tmv_cM"].mean()      if "tmv_cM"      in df_harita else 22,
            "Mi-1.2"       : df_harita["nematod_cM"].mean()  if "nematod_cM"  in df_harita else 33,
            "rin"          : df_harita["rin_cM"].mean()       if "rin_cM"      in df_harita else 12,
        }
        uyari_sayisi = 0
        for (ga, va), (gb, vb) in itertools.combinations(gen_cM_ort.items(), 2):
            mesafe = abs(va - vb)
            if mesafe < 20:
                renk = "🔴" if mesafe < 10 else "🟡"
                st.warning(
                    f"{renk} **{ga}** ↔ **{gb}**: {mesafe:.1f} cM — "
                    f"{'KRİTİK linkage drag riski!' if mesafe < 10 else 'Orta risk — takip edin.'}",
                    icon="⚠️"
                )
                uyari_sayisi += 1

        if uyari_sayisi == 0:
            st.success("✅ Analiz edilen gen çiftleri arasında kritik yakınlık tespit edilmedi.", icon="✅")

        # Tablo
        st.markdown("### 📐 Gen Konumları Tablosu")
        tablo_verisi = [
            {"Gen": g, "Ortalama cM": round(v, 1),
             "Risk (<10 cM)": "⚠️ Evet" if any(abs(v-v2) < 10 for g2, v2 in gen_cM_ort.items() if g2 != g) else "✅ Hayır"}
            for g, v in gen_cM_ort.items()
        ]
        st.dataframe(pd.DataFrame(tablo_verisi), use_container_width=True)

    except Exception as exc:
        st.error(f"Genetik harita hatası: {exc}", icon="❌")
        st.code(traceback.format_exc())


# ── §8.4  Proteomic Insights ──────────────────────────────────────────────────

def sekme_proteomik(df: pd.DataFrame) -> None:
    st.markdown("## 🧪 Proteomic Insights — Protein Analizi & Akıllı Tahmin")
    st.markdown(
        "DNA dizisini amino aside çevirir, **15 ticari/bilimsel motif** ile tarar. "
        "Eşleşme bulunamazsa hidrofobiklik ve lösin analizi ile **akıllı tahmin** üretir."
    )

    col1, col2 = st.columns([3, 2])

    with col1:
        kaynak = st.radio(
            "DNA Kaynağı",
            ["Demo Dizi (NBS-LRR)", "Elle Gir"],
            horizontal=True,
        )
        if kaynak == "Demo Dizi (NBS-LRR)":
            dna_input = DEMO_DNA
            st.code(DEMO_DNA[:100] + "...", language="text")
        else:
            dna_input = st.text_area(
                "DNA Dizisi (FASTA veya düz nükleotid)",
                height=140,
                placeholder=">Bilinmeyen_Gen\nATGGGCGTTGGCAAAACTACCATGCTTGCAGCT...",
            )

    with col2:
        st.markdown("**⚙️ Analiz Ayarları**")
        leucine_esik    = st.slider("Lösin Eşiği (%)",    1, 20, 8,  key="leu_thr")
        hidrofob_esik   = st.slider("Hidrofobiklik Eşiği (%)", 10, 60, 35, key="hyd_thr")
        min_uzunluk     = st.number_input("Minimum AA Uzunluğu", 10, 500, 20, step=5)

    if st.button("🔬 Proteomik Analizi Başlat", key="prot_btn"):
        if not dna_input or len(dna_input.strip()) < 30:
            st.error("Lütfen en az 30 nükleotid içeren bir dizi girin.", icon="❌")
            return
        try:
            with st.spinner("DNA çevirisi ve motif taraması yapılıyor..."):
                aa = biopython_cevir(dna_input)

            if not aa or len(aa) < min_uzunluk:
                st.error(
                    f"Çeviri sonucu çok kısa ({len(aa)} AA). "
                    f"DNA dizisi veya minimum uzunluk eşiğini kontrol edin.",
                    icon="❌"
                )
                return

            motifler = motif_tara(aa)
            h_anal   = hidrofobik_analiz(aa)

            # KPI satırı
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("DNA Uzunluğu",    f"{len(dna_input.replace(chr(10),''))} bp")
            m2.metric("AA Uzunluğu",     f"{len(aa)} aa")
            m3.metric("Bulunan Motif",   f"{len(motifler)}")
            m4.metric("Lösin (%)",       f"{h_anal.get('leucine_pct','?')}")

            st.markdown("---")
            col_a, col_b = st.columns(2)

            with col_a:
                # Amino asit dizisi
                st.markdown("#### 🔤 Amino Asit Dizisi")
                st.code(aa if len(aa) <= 200 else aa[:200] + "...", language="text")

                # Hidrofobik analiz
                st.markdown("#### 💧 Hidrofobik Analiz")
                hd1, hd2 = st.columns(2)
                hd1.metric("Hidrofobiklik", f"%{h_anal.get('hidrofob_pct','?')}")
                hd2.metric("Lösin (L)",     f"%{h_anal.get('leucine_pct','?')}")

                # Eşik karşılaştırması
                if h_anal.get("leucine_pct", 0) >= leucine_esik:
                    st.success(f"✅ Lösin eşiği aşıldı: %{h_anal['leucine_pct']} ≥ %{leucine_esik}", icon="✅")
                else:
                    st.info(f"ℹ️ Lösin: %{h_anal.get('leucine_pct','?')} < %{leucine_esik} eşiği", icon="ℹ️")

                if h_anal.get("hidrofob_pct", 0) >= hidrofob_esik:
                    st.success(f"✅ Hidrofobiklik eşiği aşıldı: %{h_anal['hidrofob_pct']} ≥ %{hidrofob_esik}", icon="✅")
                else:
                    st.info(f"ℹ️ Hidrofobiklik: %{h_anal.get('hidrofob_pct','?')} < %{hidrofob_esik} eşiği", icon="ℹ️")

            with col_b:
                # Protein sınıflandırma
                st.markdown("#### 🏷️ Protein Sınıfı")
                if motifler:
                    sinif_sayim: Dict[str, int] = {}
                    for m in motifler:
                        sinif_sayim[m["sinif"]] = sinif_sayim.get(m["sinif"], 0) + 1
                    dominant_sinif = max(sinif_sayim, key=sinif_sayim.get)
                    st.success(f"**{dominant_sinif}**", icon="🔬")

                    for sinif, sayi in sinif_sayim.items():
                        st.markdown(
                            f'<span class="badge-green">{sinif}</span> '
                            f'<span class="badge-gold">{sayi} eşleşme</span>',
                            unsafe_allow_html=True,
                        )
                        st.markdown("")
                else:
                    st.warning("Bilinen motif bulunamadı.", icon="⚠️")

                # Akıllı tahmin (özelleştirilmiş eşiklerle)
                tahmin = None
                if not motifler and len(aa) >= 20:
                    l_pct = h_anal.get("leucine_pct", 0)
                    h_pct = h_anal.get("hidrofob_pct", 0)
                    if l_pct >= leucine_esik and h_pct >= hidrofob_esik:
                        tahmin = (
                            f"Tam motif eşleşmesi bulunamadı. Ancak bu proteindeki "
                            f"**%{h_pct} hidrofobik amino asit** oranı ve "
                            f"**%{l_pct} lösin (L)** yüzdesi yüksek bulundu. "
                            f"Bu bileşim, NBS-LRR veya LRR tekrar bölgelerine sahip "
                            f"**R-Gen (Direnç) proteini** yapısına benzemektedir. "
                            f"Kesin sonuç için AlphaFold / InterPro analizi önerilir."
                        )
                    elif h_pct >= 45:
                        tahmin = (
                            f"Tam motif eşleşmesi bulunamadı. Yüksek hidrofobiklik "
                            f"(**%{h_pct}**) bu dizinin bir membran proteini veya "
                            f"taşıyıcı protein olduğuna işaret edebilir."
                        )

                if tahmin:
                    st.markdown("#### 🤖 Akıllı Tahmin")
                    st.info(tahmin, icon="🤖")

            st.markdown("---")

            # Motif detayları
            if motifler:
                st.markdown("### 🔬 Tespit Edilen Motifler")
                if _PLT_OK:
                    bar_fig = fig_proteomic_bar(motifler)
                    if bar_fig:
                        st.plotly_chart(bar_fig, use_container_width=True)

                for m in motifler:
                    pozisyonlar = ", ".join(str(k) for k in m.get("konumlar", []))
                    with st.expander(
                        f"**{m['isim']}** — `{m['motif']}` | {m['sinif']} | {m['adet']}×",
                        expanded=False,
                    ):
                        mc1, mc2 = st.columns(2)
                        with mc1:
                            st.markdown(f"**Sınıf:** {m['sinif']}")
                            st.markdown(f"**Motif:** `{m['motif']}`")
                            st.markdown(f"**Konum(lar):** {pozisyonlar}")
                            st.markdown(f"**Eşleşme Sayısı:** {m['adet']}")
                        with mc2:
                            st.markdown(f"**Biyolojik İşlev:** {m['islev']}")
                            st.success(f"🌾 **Tarla Etkisi:** {m['tarla']}", icon="🌿")
            else:
                if not tahmin:
                    st.info(
                        "Bu dizi için bilinen motif bulunamadı ve akıllı tahmin eşikleri "
                        "de karşılanmadı. Dizi yapısal bir protein veya bilinmeyen işlevli "
                        "bir gen ürünü olabilir. AlphaFold / InterPro analizi önerilir.",
                        icon="ℹ️"
                    )

        except Exception as exc:
            st.error(f"Proteomik analiz hatası: {exc}", icon="❌")
            st.code(traceback.format_exc())


# ── §8.5  Genetic Detective ───────────────────────────────────────────────────

def sekme_detective(df: pd.DataFrame) -> None:
    st.markdown("## 🕵️ Genetic Detective — Akrabalık & Benzerlik Analizi")
    st.markdown(
        "Envanterdeki hatların genetik özellik profillerinden "
        "**Jaccard benzerlik matrisi** hesaplar ve interaktif ısı haritası çizer. "
        "Yüksek benzerlik = Yüksek akrabalık → Genetik daralma riski."
    )

    with st.expander("📖 Metodoloji", expanded=False):
        st.markdown("""
        **Jaccard Benzerliği:** `|A ∩ B| / |A ∪ B|`

        Her hat için ikili özellik seti oluşturulur:
        - Genetik markörler (fusarium_I, tmv_Tm2a, nematod_Mi12, rin_gen, pto_gen)
        - Fenotipik etiketler (etiketler sütunundan ayrıştırılır)

        **Renk Yorumu:**
        - 🟢 Koyu Yeşil → Yüksek benzerlik (akraba hatlar)
        - ⬛ Koyu → Düşük benzerlik (genetik çeşitlilik var)

        Köşegen (her hattın kendisiyle karşılaştırması) her zaman 1.0'dır.
        """)

    if not _PLT_OK:
        st.error("Plotly kurulu değil. pip install plotly", icon="❌")
        return

    col_filtre, col_ayar = st.columns(2)
    with col_filtre:
        tür_f = st.selectbox(
            "Tür Filtresi (Isı haritası için)",
            ["Tümü"] + sorted(df["tur"].unique().tolist()) if "tur" in df.columns else ["Tümü"],
            key="det_tur",
        )
    with col_ayar:
        esik = st.slider("Akrabalık Uyarı Eşiği", 0.30, 0.90, 0.65, step=0.05, key="det_esik")

    if st.button("🔥 Akrabalık Analizini Başlat", key="det_btn"):
        try:
            df_f = df if tür_f == "Tümü" else df[df["tur"] == tür_f]
            if len(df_f) < 2:
                st.warning("Isı haritası için en az 2 hat gereklidir.", icon="⚠️")
                return

            with st.spinner("Jaccard benzerlik matrisi hesaplanıyor..."):
                mat = akrabalik_matrisi(df_f)

            # KPI
            np_mat = mat.values.copy()
            np.fill_diagonal(np_mat, np.nan)
            ortalama_benzerlik = float(np.nanmean(np_mat))
            max_benzerlik      = float(np.nanmax(np_mat))

            m1, m2, m3 = st.columns(3)
            m1.metric("Ortalama Benzerlik",   f"{ortalama_benzerlik:.3f}")
            m2.metric("Maksimum Benzerlik",   f"{max_benzerlik:.3f}")
            m3.metric("Hat Sayısı (Analiz)",  len(df_f))

            # Isı haritası
            st.plotly_chart(fig_heatmap(mat), use_container_width=True)

            # Yüksek akrabalık uyarıları
            st.markdown(f"### ⚠️ Yüksek Akrabalık Uyarıları (>{esik:.2f})")
            uyari_listesi = []
            ids = mat.index.tolist()
            for i in range(len(ids)):
                for j in range(i + 1, len(ids)):
                    val = mat.iloc[i, j]
                    if val >= esik:
                        uyari_listesi.append({
                            "Hat-1": ids[i],
                            "Hat-2": ids[j],
                            "Benzerlik": round(val, 4),
                            "Risk": "🔴 Yüksek" if val >= 0.80 else "🟡 Orta",
                        })

            if uyari_listesi:
                uyari_df = pd.DataFrame(uyari_listesi).sort_values(
                    "Benzerlik", ascending=False
                ).reset_index(drop=True)
                uyari_df.index += 1
                st.dataframe(
                    uyari_df.style.background_gradient(
                        subset=["Benzerlik"], cmap="RdYlGn_r"
                    ),
                    use_container_width=True,
                )
                st.warning(
                    f"⚠️ {len(uyari_listesi)} yüksek akrabalık çifti tespit edildi. "
                    f"Bu hatları aynı çaprazlamada kullanmaktan kaçının "
                    f"(genetik daralma riski).",
                    icon="⚠️"
                )
            else:
                st.success(
                    f"✅ {esik:.2f} eşiğinin üzerinde akrabalık tespit edilmedi. "
                    f"Envanteriniz genetik çeşitlilik açısından sağlıklı görünüyor.",
                    icon="✅"
                )

            # Tam matris tablosu
            with st.expander("📊 Tam Benzerlik Matrisi", expanded=False):
                st.dataframe(
                    mat.style.background_gradient(cmap="Greens").format("{:.3f}"),
                    use_container_width=True,
                )

        except Exception as exc:
            st.error(f"Akrabalık analizi hatası: {exc}", icon="❌")
            st.code(traceback.format_exc())


# ─────────────────────────────────────────────────────────────────────────────
# §9  DASHBOARD (Ana Sayfa)
# ─────────────────────────────────────────────────────────────────────────────

def dashboard_hero(df: pd.DataFrame) -> None:
    """Uygulama ana ekranının üst kısmı."""
    st.markdown(f"""
    <div class="bv-hero">
      <div style="font-size:2.8rem;margin-bottom:0.3rem">🧬</div>
      <h1 style="margin:0;font-size:2.4rem">Biovalent Sentinel</h1>
      <p style="color:{PAL['gold']};font-size:1.05rem;margin:0.2rem 0 0.5rem;
                letter-spacing:1.5px;font-weight:600">
        DECODING THE BONDS OF LIFE
      </p>
      <p style="color:{PAL['grey_mid']};font-size:0.82rem;margin:0">
        v{VER} · Tarımsal Biyoteknoloji & Genetik Karar Destek SaaS Platformu
      </p>
    </div>
    """, unsafe_allow_html=True)

    # Envanter KPI'ları
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("🌱 Hat Sayısı",       len(df))
    c2.metric("🔬 Tür Sayısı",       df["tur"].nunique() if "tur" in df.columns else "—")
    if "verim_t_ha" in df.columns:
        c3.metric("📦 Ort. Verim (t/ha)", f"{df['verim_t_ha'].mean():.1f}")
    if "raf_omru_gun" in df.columns:
        c4.metric("🗓️ Ort. Raf Ömrü",     f"{df['raf_omru_gun'].mean():.0f} gün")
    if "brix" in df.columns:
        c5.metric("🍬 Ort. Brix",          f"{df['brix'].mean():.1f}°")


# ─────────────────────────────────────────────────────────────────────────────
# §10  ANA FONKSİYON
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    # Sidebar ve veri
    df = sidebar_render()

    # Hero banner
    dashboard_hero(df)

    st.markdown("---")

    # Ana sekmeler
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🧬 Matchmaker",
        "⚠️ Risk Engine",
        "🗺️ Genetic Map",
        "🧪 Proteomic Insights",
        "🕵️ Genetic Detective",
    ])

    with tab1:
        try:
            sekme_matchmaker(df)
        except Exception as exc:
            st.error(f"Matchmaker modül hatası: {exc}", icon="❌")

    with tab2:
        try:
            sekme_risk(df)
        except Exception as exc:
            st.error(f"Risk Engine modül hatası: {exc}", icon="❌")

    with tab3:
        try:
            sekme_genetic_map(df)
        except Exception as exc:
            st.error(f"Genetic Map modül hatası: {exc}", icon="❌")

    with tab4:
        try:
            sekme_proteomik(df)
        except Exception as exc:
            st.error(f"Proteomik modül hatası: {exc}", icon="❌")

    with tab5:
        try:
            sekme_detective(df)
        except Exception as exc:
            st.error(f"Genetic Detective modül hatası: {exc}", icon="❌")


# ─────────────────────────────────────────────────────────────────────────────
# §11  GİRİŞ NOKTASI
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    main()

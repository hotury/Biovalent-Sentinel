# ==============================================================================
#  BIOVALENT SENTINEL v3.0
#  Otonom Küresel Genetik Zekâ & Karar Destek Platformu
#  "Decoding the Bonds of Life — Autonomously"
#
#  KURULUM:
#    pip install streamlit pandas numpy biopython plotly requests openpyxl
#    streamlit run app.py
#
#  Google Colab:
#    !pip install streamlit pandas numpy biopython plotly requests openpyxl pyngrok -q
#    !streamlit run app.py &
#    from pyngrok import ngrok; print(ngrok.connect(8501))
#
#  Güvenlik Notu:
#    NCBI API erişimi için Entrez.email zorunludur.
#    Tüm dış API çağrıları try-except ile korunmuştur.
#    API başarısız olursa sistem Heuristic moduna otomatik geçer.
# ==============================================================================

# ─────────────────────────────────────────────────────────────────────────────
# §0  IMPORTS
# ─────────────────────────────────────────────────────────────────────────────
import re
import io
import math
import time
import json
import hashlib
import itertools
import traceback
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import requests
import numpy as np
import pandas as pd
import streamlit as st

import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

try:
    from Bio import Entrez, SeqIO
    from Bio.Seq import Seq
    from Bio.Blast import NCBIWWW, NCBIXML
    Entrez.email = "info@biovalentsentinel.com"   # NCBI zorunlu e-posta
    _BIO_OK = True
except ImportError:
    _BIO_OK = False

# ─────────────────────────────────────────────────────────────────────────────
# §1  SAYFA AYARI  (her zaman ilk Streamlit çağrısı olmalıdır)
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Biovalent Sentinel v3.0",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help"    : "https://biovalentsentinel.com/docs",
        "Report a bug": "https://biovalentsentinel.com/support",
        "About"       : "Biovalent Sentinel v3.0 — Decoding the Bonds of Life",
    },
)

# ─────────────────────────────────────────────────────────────────────────────
# §2  RENK PALETİ & KURUMSAL CSS
# ─────────────────────────────────────────────────────────────────────────────
PAL = {
    "bg"      : "#070d07",
    "panel"   : "#0d1f0d",
    "panel2"  : "#112311",
    "border"  : "#1a3a1a",
    "g_hi"    : "#4ade80",   # Neon yeşil
    "g_mid"   : "#22c55e",   # Orta yeşil
    "g_dim"   : "#14532d",   # Koyu yeşil
    "gold"    : "#fbbf24",   # Altın
    "gold_d"  : "#78350f",   # Koyu altın
    "txt"     : "#d1fae5",   # Ana metin
    "txt_dim" : "#6b7280",   # Soluk metin
    "red"     : "#f87171",   # Tehlike
    "red_d"   : "#450a0a",   # Koyu tehlike
    "amber"   : "#fcd34d",   # Uyarı
    "blue"    : "#60a5fa",   # Bilgi
    "purple"  : "#c084fc",   # Özel
    "teal"    : "#2dd4bf",   # Turkuaz
    "white"   : "#f0fdf4",
    "alpha_g" : "rgba(74,222,128,0.10)",
    "alpha_r" : "rgba(248,113,113,0.08)",
    "alpha_y" : "rgba(251,191,36,0.10)",
}

PLOTLY_BG = "rgba(0,0,0,0)"    # Şeffaf grafik arka planı

CSS = f"""
<style>
/* ── Temel ── */
html, body, [data-testid="stAppViewContainer"] {{
    background-color: {PAL["bg"]};
    color: {PAL["txt"]};
    font-family: 'Inter', 'Segoe UI', 'SF Pro Display', sans-serif;
}}
/* ── Sidebar ── */
[data-testid="stSidebar"] {{
    background: linear-gradient(180deg, #050d05 0%, #091509 100%);
    border-right: 1px solid {PAL["border"]};
}}
/* ── Başlıklar ── */
h1 {{ color: {PAL["g_hi"]} !important; letter-spacing: -.6px; }}
h2 {{ color: {PAL["gold"]} !important; }}
h3 {{ color: {PAL["g_mid"]} !important; }}
h4 {{ color: {PAL["txt"]} !important; }}
/* ── Metrik kartları ── */
[data-testid="metric-container"] {{
    background: linear-gradient(145deg, {PAL["panel"]} 0%, {PAL["bg"]} 100%);
    border: 1px solid {PAL["border"]};
    border-radius: 12px;
    padding: 14px 16px !important;
    transition: border-color .2s;
}}
[data-testid="metric-container"]:hover {{
    border-color: {PAL["g_dim"]};
}}
[data-testid="metric-container"] label {{
    color: {PAL["gold"]} !important;
    font-size: .76rem;
    font-weight: 600;
    letter-spacing: .5px;
}}
[data-testid="metric-container"] [data-testid="stMetricValue"] {{
    color: {PAL["g_hi"]} !important;
    font-weight: 800;
    font-size: 1.6rem;
}}
[data-testid="metric-container"] [data-testid="stMetricDelta"] {{
    color: {PAL["amber"]} !important;
}}
/* ── Butonlar ── */
.stButton > button {{
    background: linear-gradient(135deg, {PAL["g_dim"]} 0%, #0f3d1a 100%);
    color: {PAL["g_hi"]};
    border: 1px solid {PAL["g_mid"]};
    border-radius: 9px;
    font-weight: 700;
    font-size: .92rem;
    padding: .45rem 1.3rem;
    transition: all .22s ease;
    letter-spacing: .3px;
}}
.stButton > button:hover {{
    background: linear-gradient(135deg, {PAL["g_mid"]} 0%, {PAL["g_dim"]} 100%);
    color: {PAL["white"]};
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(74,222,128,.30);
    border-color: {PAL["g_hi"]};
}}
.stButton > button:active {{
    transform: translateY(0);
}}
/* ── Input alanları ── */
.stTextArea textarea, .stTextInput input,
.stNumberInput input {{
    background-color: {PAL["panel"]} !important;
    color: {PAL["txt"]} !important;
    border: 1px solid {PAL["border"]} !important;
    border-radius: 8px !important;
    font-family: 'JetBrains Mono', 'Fira Code', monospace !important;
}}
.stTextArea textarea:focus, .stTextInput input:focus {{
    border-color: {PAL["g_dim"]} !important;
    box-shadow: 0 0 0 2px rgba(34,197,94,.15) !important;
}}
/* ── Select / Multiselect ── */
.stSelectbox > div > div,
.stMultiSelect > div > div {{
    background-color: {PAL["panel"]} !important;
    border: 1px solid {PAL["border"]} !important;
    border-radius: 8px !important;
}}
/* ── Tab başlıkları ── */
[data-baseweb="tab-list"] {{
    background-color: {PAL["panel"]} !important;
    border-radius: 12px;
    padding: 5px;
    gap: 4px;
}}
[data-baseweb="tab"] {{
    color: {PAL["txt_dim"]} !important;
    font-weight: 600;
    border-radius: 8px !important;
    padding: .35rem .9rem !important;
    transition: all .18s;
}}
[aria-selected="true"] {{
    color: {PAL["g_hi"]} !important;
    background-color: {PAL["g_dim"]} !important;
}}
/* ── Dataframe ── */
[data-testid="stDataFrame"] {{
    border: 1px solid {PAL["border"]};
    border-radius: 10px;
    overflow: hidden;
}}
/* ── Expander ── */
.streamlit-expanderHeader {{
    background-color: {PAL["panel2"]} !important;
    color: {PAL["gold"]} !important;
    border-radius: 8px !important;
    font-weight: 600;
}}
.streamlit-expanderContent {{
    border: 1px solid {PAL["border"]};
    border-top: none;
    border-radius: 0 0 8px 8px;
    background-color: {PAL["panel"]} !important;
    padding: 1rem !important;
}}
/* ── Alert / info / warning / error / success ── */
.stAlert {{
    border-radius: 10px !important;
    border-left-width: 4px !important;
    font-size: .92rem;
}}
/* ── Divider ── */
hr {{ border-color: {PAL["border"]} !important; opacity: .6; }}
/* ── Spinner ── */
[data-testid="stSpinner"] > div {{
    border-top-color: {PAL["g_hi"]} !important;
}}
/* ── Özel kart ── */
.bv-card {{
    background: linear-gradient(145deg, {PAL["panel"]} 0%, {PAL["bg"]} 100%);
    border: 1px solid {PAL["border"]};
    border-radius: 14px;
    padding: 1.2rem 1.5rem;
    margin-bottom: .9rem;
    transition: border-color .2s;
}}
.bv-card:hover {{ border-color: {PAL["g_dim"]}; }}
/* ── Hero banner ── */
.bv-hero {{
    background: linear-gradient(135deg, {PAL["panel"]} 0%, #091809 40%, {PAL["bg"]} 100%);
    border: 1px solid {PAL["border"]};
    border-radius: 18px;
    padding: 2rem 2.8rem;
    margin-bottom: 1.4rem;
    text-align: center;
    position: relative;
    overflow: hidden;
}}
/* ── Etiket pilleri ── */
.tag-green  {{ display:inline-block; background:{PAL["g_dim"]}; color:{PAL["g_hi"]};
               border:1px solid {PAL["g_mid"]}; border-radius:20px;
               padding:2px 10px; margin:2px; font-size:.75rem; font-weight:700; }}
.tag-gold   {{ display:inline-block; background:{PAL["gold_d"]}; color:{PAL["gold"]};
               border:1px solid {PAL["gold"]}; border-radius:20px;
               padding:2px 10px; margin:2px; font-size:.75rem; font-weight:700; }}
.tag-red    {{ display:inline-block; background:{PAL["red_d"]}; color:{PAL["red"]};
               border:1px solid {PAL["red"]}; border-radius:20px;
               padding:2px 10px; margin:2px; font-size:.75rem; font-weight:700; }}
.tag-blue   {{ display:inline-block; background:#1e3a5f; color:{PAL["blue"]};
               border:1px solid {PAL["blue"]}; border-radius:20px;
               padding:2px 10px; margin:2px; font-size:.75rem; font-weight:700; }}
/* ── Kod blokları ── */
code, pre {{ background:{PAL["panel2"]} !important; color:{PAL["g_hi"]} !important;
             font-family:'JetBrains Mono','Fira Code',monospace !important; }}
/* ── Scrollbar ── */
::-webkit-scrollbar {{ width:6px; height:6px; }}
::-webkit-scrollbar-track {{ background:{PAL["bg"]}; }}
::-webkit-scrollbar-thumb {{ background:{PAL["g_dim"]}; border-radius:3px; }}
::-webkit-scrollbar-thumb:hover {{ background:{PAL["g_mid"]}; }}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# §3  GLOBAL SABİTLER
# ─────────────────────────────────────────────────────────────────────────────
VER    = "3.0.0"
SLOGAN = "Decoding the Bonds of Life — Autonomously"
GUVEN  = 0.95    # İstatistiksel güven seviyesi

# ── Kodon çeviri tablosu ─────────────────────────────────────────────────────
KODON: Dict[str, str] = {
    "TTT":"F","TTC":"F","TTA":"L","TTG":"L","CTT":"L","CTC":"L","CTA":"L","CTG":"L",
    "ATT":"I","ATC":"I","ATA":"I","ATG":"M","GTT":"V","GTC":"V","GTA":"V","GTG":"V",
    "TCT":"S","TCC":"S","TCA":"S","TCG":"S","CCT":"P","CCC":"P","CCA":"P","CCG":"P",
    "ACT":"T","ACC":"T","ACA":"T","ACG":"T","GCT":"A","GCC":"A","GCA":"A","GCG":"A",
    "TAT":"Y","TAC":"Y","TAA":"*","TAG":"*","CAT":"H","CAC":"H","CAA":"Q","CAG":"Q",
    "AAT":"N","AAC":"N","AAA":"K","AAG":"K","GAT":"D","GAC":"D","GAA":"E","GAG":"E",
    "TGT":"C","TGC":"C","TGA":"*","TGG":"W","CGT":"R","CGC":"R","CGA":"R","CGG":"R",
    "AGT":"S","AGC":"S","AGA":"R","AGG":"R","GGT":"G","GGC":"G","GGA":"G","GGG":"G",
}

# ── 20 Biyolojik Motif Kütüphanesi ───────────────────────────────────────────
MOTIF_BANK: List[Dict] = [
    {"ad":"NBS P-loop",         "motif":"GVGKTT",    "sinif":"NBS-LRR",
     "islev":"Nükleotid bağlanma — R-gen çekirdeği.",
     "tarla":"Geniş spektrumlu patojen direnci."},
    {"ad":"NBS RNBS-A",         "motif":"ILVDDE",    "sinif":"NBS-LRR",
     "islev":"RNBS-A bölgesi; NBS etkinleştirme kaskadı.",
     "tarla":"Hipersensitivite yanıtı (HR) tetikler."},
    {"ad":"LRR Tekrar",         "motif":"LXXLXLXX",  "sinif":"NBS-LRR",
     "islev":"Lösin tekrarlı bölge — effektör tanıma yüzeyi.",
     "tarla":"Irk spektrumunu ve direnç genişliğini belirler."},
    {"ad":"TIR Domaini",        "motif":"FLHFAD",    "sinif":"TIR-NBS",
     "islev":"Toll/IL-1 homoloji domaini; sinyal iletimi.",
     "tarla":"Dikotil TIR-NBS-LRR sınıfı direnç genleri."},
    {"ad":"Coiled-Coil",        "motif":"LRRLEEL",   "sinif":"CC-NBS",
     "islev":"Protein etkileşim yüzeyi; CC-NBS-LRR alt sınıfı.",
     "tarla":"CC-NBS-LRR sınıfı monokotil direnç."},
    {"ad":"Kinaz DFG",          "motif":"DFG",       "sinif":"Protein Kinaz",
     "islev":"ATP bağlanma ve substrat fosforilasyonu.",
     "tarla":"Savunma sinyal kaskadı aktivasyonu."},
    {"ad":"Kinaz VAIK",         "motif":"VAIK",      "sinif":"Protein Kinaz",
     "islev":"Kinaz-2 bölgesi; katalitik aktivite.",
     "tarla":"Biyotik/abiyotik stres sinyal iletimi."},
    {"ad":"WRKY Domaini",       "motif":"WRKYGQK",   "sinif":"TF-WRKY",
     "islev":"W-box (TTGAC) DNA bağlanma; savunma gen ifadesi.",
     "tarla":"Sistemik edinilmiş direnç (SAR) mekanizması."},
    {"ad":"MYB R2R3",           "motif":"GRTWHTE",   "sinif":"TF-MYB",
     "islev":"R2R3-MYB; pigment ve olgunlaşma düzenleme.",
     "tarla":"Meyve rengi, antosiyanin birikimi."},
    {"ad":"MADS-Box",           "motif":"MGRNGKVEHI","sinif":"TF-MADS",
     "islev":"Meyve gelişimi ve olgunlaşma regulasyonu.",
     "tarla":"Raf ömrü kontrolü (rin/nor bölgesi)."},
    {"ad":"AP2/ERF",            "motif":"RAYDAWLKL", "sinif":"TF-ERF",
     "islev":"Etilen yanıt faktörü; stres ve olgunlaşma.",
     "tarla":"Hasat zamanlaması ve stres toleransı."},
    {"ad":"Zinc Finger C2H2",   "motif":"CXXCXXXXHXXXH","sinif":"Zinc Finger",
     "islev":"C2H2 tipi çinko parmak; transkripsiyon düzenleme.",
     "tarla":"Stres ve gelişim gen ifadesi kontrolü."},
    {"ad":"Zinc Finger C3H",    "motif":"CXXXCXXH",  "sinif":"Zinc Finger",
     "islev":"C3H tipi; RNA işleme ve stres yanıtı.",
     "tarla":"Çevre adaptasyon mekanizmaları."},
    {"ad":"PR-1 Sinyal Peptidi","motif":"MKKLLAL",   "sinif":"PR Proteini",
     "islev":"Salisilik asit yolunda salgılanan savunma proteini.",
     "tarla":"SAR biyogöstergesi — PR-1 gen ifadesi."},
    {"ad":"PR-5 Osmotin",       "motif":"CCQCSPLDS", "sinif":"PR Proteini",
     "islev":"Antifungal aktivite; hücre zarı permeabilizasyonu.",
     "tarla":"Küf ve fungal patojen direnci."},
    {"ad":"PR-3 Kitinaz",       "motif":"FYGLNHD",   "sinif":"PR Proteini",
     "islev":"Kitin yıkımı — fungal hücre duvarını hedefler.",
     "tarla":"Mantar patojen direnci."},
    {"ad":"ABC Taşıyıcı",       "motif":"LSGGQ",     "sinif":"Taşıyıcı",
     "islev":"ATP bağlama kaseti; membran taşınımı.",
     "tarla":"Fitotoksin atımı ve ilaç direnci."},
    {"ad":"SOD Merkez",         "motif":"HVHAQY",    "sinif":"Antioksidan",
     "islev":"Süperoksit dismutaz; reaktif oksijen temizleme.",
     "tarla":"Kuraklık ve ısı stresi toleransı."},
    {"ad":"HSP90 EEVD",         "motif":"EEVD",      "sinif":"Chaperone",
     "islev":"Isı şoku proteini 90; protein katlanma yönetimi.",
     "tarla":"Yüksek sıcaklık stres koruması."},
    {"ad":"Antifroz Tip-I",     "motif":"DTASDAAAA", "sinif":"Antifroz",
     "islev":"Buz kristali büyümesini engeller.",
     "tarla":"Donma toleransı; soğuğa dayanıklılık."},
]

# ── Amino asit grupları ───────────────────────────────────────────────────────
AA_HIDROFOBIK = set("VILMFWPA")
AA_NEGATIF    = set("DE")
AA_POZITIF    = set("KRH")

# ── pKa tablosu (izoelektrik nokta hesabı) ───────────────────────────────────
PKA = {"D":3.86, "E":4.07, "C":8.18, "Y":10.46,
       "H":6.04, "K":10.53, "R":12.48,
       "N_term":8.00, "C_term":3.10}

# ── Referans Domates Genomu (ITAG 4.0) ───────────────────────────────────────
TOMATO_GENOME: Dict[str, List[Dict]] = {
    "Chr01": [
        {"gen":"Cf-1", "cm":5.2,  "sinif":"NBS-LRR",   "islev":"Cladosporium fulvum ırk 1 direnci"},
        {"gen":"I-2",  "cm":48.7, "sinif":"NBS-LRR",   "islev":"Fusarium oxysporum ırk 2 direnci"},
    ],
    "Chr02": [
        {"gen":"Tm-1",  "cm":2.1,  "sinif":"Kinaz",     "islev":"TMV ırk 0,1,2 direnci"},
        {"gen":"Ph-3",  "cm":62.0, "sinif":"NBS-LRR",   "islev":"Phytophthora infestans direnci"},
    ],
    "Chr03": [
        {"gen":"Pto",   "cm":18.5, "sinif":"Kinaz",     "islev":"Pseudomonas syringae direnci"},
        {"gen":"Prf",   "cm":19.8, "sinif":"NBS-LRR",   "islev":"Pto aktivatör NBS-LRR geni"},
    ],
    "Chr04": [
        {"gen":"sw-5",  "cm":44.1, "sinif":"NBS-LRR",   "islev":"TSWV (Tospovirüs) direnci"},
    ],
    "Chr05": [
        {"gen":"rin",   "cm":21.0, "sinif":"MADS TF",   "islev":"Olgunlaşma inhibitörü — uzun raf ömrü"},
        {"gen":"nor",   "cm":26.5, "sinif":"TF",         "islev":"rin ile sinerjik olgunlaşma kontrolü"},
    ],
    "Chr06": [
        {"gen":"Mi-1.2","cm":33.1, "sinif":"NBS-LRR",   "islev":"Nematod + yaprak biti direnci"},
    ],
    "Chr07": [
        {"gen":"Cf-4",  "cm":12.3, "sinif":"LRR-RLP",   "islev":"Cladosporium ırk 4 direnci"},
        {"gen":"Cf-9",  "cm":14.8, "sinif":"LRR-RLP",   "islev":"Cladosporium ırk 9 direnci"},
    ],
    "Chr08": [
        {"gen":"Ty-1",  "cm":55.2, "sinif":"RdRP",      "islev":"TYLCV (Sarı yaprak kıvırcıklığı) direnci"},
    ],
    "Chr09": [
        {"gen":"Tm-2a", "cm":22.4, "sinif":"NBS-LRR",   "islev":"TMV ırk 1,2,3 — geniş spektrum"},
        {"gen":"Cf-2",  "cm":36.0, "sinif":"LRR-RLP",   "islev":"Cladosporium ırk 2,5 direnci"},
    ],
    "Chr11": [
        {"gen":"I",     "cm":45.0, "sinif":"NBS-LRR",   "islev":"Fusarium oxysporum ırk 1,2 direnci"},
        {"gen":"Ve1",   "cm":72.0, "sinif":"LRR-RLP",   "islev":"Verticillium solgunluğu direnci"},
    ],
    "Chr12": [
        {"gen":"y",     "cm":5.0,  "sinif":"TF (MYB)",  "islev":"Meyve rengi — Y sarı, y kırmızı"},
    ],
}

# ── Gen sutunları (ikili özellik vektörü için) ────────────────────────────────
GEN_KOLONLARI = [
    "fusarium_I","tmv","nematod","rin","pto","ty1","sw5","mi12",
    "kok_guclu","soguk_dayanikli","kuraklık_toleransi"
]

# ─────────────────────────────────────────────────────────────────────────────
# §4  DEMO VERİSETİ  (24 hat — biyolojik olarak tutarlı)
# ─────────────────────────────────────────────────────────────────────────────

@st.cache_data(show_spinner=False)
def demo_df() -> pd.DataFrame:
    """24 hatlık, biyolojik olarak gerçekçi demo envanter."""
    rows = [
        # ── DOMATES ──────────────────────────────────────────────────────────
        dict(hat_id="BIO-TOM-001", hat_adi="Crimson Shield F6",
             tur="Solanum lycopersicum",
             meyve_rengi="Koyu Kırmızı", verim=18.5, raf=14, hasat=72, brix=5.2,
             fusarium_I=1, tmv=1, nematod=0, rin=0, pto=1, ty1=0, sw5=0, mi12=1,
             fusarium_cM=45.0, tmv_cM=22.4, nematod_cM=33.1, rin_cM=21.0,
             kok_guclu=1, soguk_dayanikli=0, kuraklık_toleransi=0,
             etiketler="fusarium,tmv,pseudomonas,nematod"),
        dict(hat_id="BIO-TOM-002", hat_adi="GoldenYield HV-9",
             tur="Solanum lycopersicum",
             meyve_rengi="Parlak Sarı", verim=22.3, raf=11, hasat=68, brix=4.8,
             fusarium_I=0, tmv=1, nematod=0, rin=0, pto=0, ty1=0, sw5=0, mi12=0,
             fusarium_cM=45.0, tmv_cM=22.4, nematod_cM=33.1, rin_cM=21.0,
             kok_guclu=0, soguk_dayanikli=0, kuraklık_toleransi=1,
             etiketler="sarı meyve,yüksek verim,ticari"),
        dict(hat_id="BIO-TOM-003", hat_adi="LongLife Premium",
             tur="Solanum lycopersicum",
             meyve_rengi="Kırmızı", verim=16.8, raf=24, hasat=78, brix=5.8,
             fusarium_I=0, tmv=0, nematod=1, rin=1, pto=0, ty1=0, sw5=0, mi12=1,
             fusarium_cM=45.0, tmv_cM=22.4, nematod_cM=33.1, rin_cM=21.0,
             kok_guclu=1, soguk_dayanikli=0, kuraklık_toleransi=0,
             etiketler="uzun raf ömrü,nematod,ihracat"),
        dict(hat_id="BIO-TOM-004", hat_adi="SunGold Cherry",
             tur="Solanum lycopersicum",
             meyve_rengi="Turuncu-Sarı", verim=21.0, raf=10, hasat=62, brix=8.2,
             fusarium_I=0, tmv=0, nematod=0, rin=0, pto=0, ty1=0, sw5=0, mi12=0,
             fusarium_cM=45.0, tmv_cM=22.4, nematod_cM=33.1, rin_cM=21.0,
             kok_guclu=0, soguk_dayanikli=0, kuraklık_toleransi=1,
             etiketler="sarı,cherry,yüksek brix,gurme"),
        dict(hat_id="BIO-TOM-005", hat_adi="Titan Robust F4",
             tur="Solanum lycopersicum",
             meyve_rengi="Koyu Kırmızı", verim=17.2, raf=16, hasat=80, brix=4.5,
             fusarium_I=1, tmv=0, nematod=1, rin=0, pto=0, ty1=1, sw5=0, mi12=1,
             fusarium_cM=45.0, tmv_cM=22.4, nematod_cM=33.1, rin_cM=21.0,
             kok_guclu=1, soguk_dayanikli=1, kuraklık_toleransi=0,
             etiketler="fusarium,nematod,tylcv,soğuğa dayanıklı"),
        dict(hat_id="BIO-TOM-006", hat_adi="Sunrise Export",
             tur="Solanum lycopersicum",
             meyve_rengi="Sarı-Turuncu", verim=19.6, raf=20, hasat=74, brix=5.0,
             fusarium_I=0, tmv=1, nematod=0, rin=1, pto=0, ty1=0, sw5=0, mi12=0,
             fusarium_cM=45.0, tmv_cM=22.4, nematod_cM=33.1, rin_cM=21.0,
             kok_guclu=1, soguk_dayanikli=0, kuraklık_toleransi=0,
             etiketler="sarı,uzun raf,tmv,ihracat"),
        dict(hat_id="BIO-TOM-007", hat_adi="IronShield Plus",
             tur="Solanum lycopersicum",
             meyve_rengi="Kırmızı", verim=16.0, raf=18, hasat=76, brix=4.7,
             fusarium_I=1, tmv=1, nematod=1, rin=0, pto=1, ty1=1, sw5=1, mi12=1,
             fusarium_cM=45.0, tmv_cM=22.4, nematod_cM=33.1, rin_cM=21.0,
             kok_guclu=1, soguk_dayanikli=1, kuraklık_toleransi=1,
             etiketler="tam direnç,organik,sertifika"),
        dict(hat_id="BIO-TOM-008", hat_adi="Quantum Beefsteak",
             tur="Solanum lycopersicum",
             meyve_rengi="Kırmızı", verim=20.1, raf=12, hasat=84, brix=4.2,
             fusarium_I=1, tmv=0, nematod=0, rin=0, pto=0, ty1=0, sw5=0, mi12=0,
             fusarium_cM=45.0, tmv_cM=22.4, nematod_cM=33.1, rin_cM=21.0,
             kok_guclu=0, soguk_dayanikli=0, kuraklık_toleransi=0,
             etiketler="yüksek verim,büyük meyve,endüstriyel"),
        dict(hat_id="BIO-TOM-009", hat_adi="Arctic White F3",
             tur="Solanum lycopersicum",
             meyve_rengi="Beyaz", verim=12.5, raf=13, hasat=70, brix=6.5,
             fusarium_I=0, tmv=0, nematod=0, rin=1, pto=0, ty1=0, sw5=0, mi12=0,
             fusarium_cM=45.0, tmv_cM=22.4, nematod_cM=33.1, rin_cM=21.0,
             kok_guclu=0, soguk_dayanikli=1, kuraklık_toleransi=0,
             etiketler="beyaz meyve,uzun raf,özel pazar"),
        dict(hat_id="BIO-TOM-010", hat_adi="BioShield Triple",
             tur="Solanum lycopersicum",
             meyve_rengi="Kırmızı", verim=15.3, raf=15, hasat=73, brix=5.1,
             fusarium_I=1, tmv=1, nematod=1, rin=1, pto=1, ty1=0, sw5=0, mi12=1,
             fusarium_cM=45.0, tmv_cM=22.4, nematod_cM=33.1, rin_cM=21.0,
             kok_guclu=1, soguk_dayanikli=0, kuraklık_toleransi=1,
             etiketler="tam direnç,uzun raf,organik"),
        dict(hat_id="BIO-TOM-011", hat_adi="FastTrack F5",
             tur="Solanum lycopersicum",
             meyve_rengi="Kırmızı", verim=23.5, raf=9, hasat=60, brix=4.0,
             fusarium_I=1, tmv=0, nematod=0, rin=0, pto=0, ty1=1, sw5=0, mi12=0,
             fusarium_cM=45.0, tmv_cM=22.4, nematod_cM=33.1, rin_cM=21.0,
             kok_guclu=0, soguk_dayanikli=0, kuraklık_toleransi=1,
             etiketler="erken hasat,yüksek verim,fusarium,tylcv"),
        dict(hat_id="BIO-TOM-012", hat_adi="Volcano Dark",
             tur="Solanum lycopersicum",
             meyve_rengi="Siyah-Mor", verim=11.8, raf=11, hasat=78, brix=7.3,
             fusarium_I=0, tmv=0, nematod=0, rin=0, pto=0, ty1=0, sw5=0, mi12=0,
             fusarium_cM=45.0, tmv_cM=22.4, nematod_cM=33.1, rin_cM=21.0,
             kok_guclu=0, soguk_dayanikli=0, kuraklık_toleransi=0,
             etiketler="siyah meyve,antosiyanin,gurme"),
        # ── BİBER ──────────────────────────────────────────────────────────
        dict(hat_id="BIO-CAP-001", hat_adi="RedBlaze L4 F5",
             tur="Capsicum annuum",
             meyve_rengi="Parlak Kırmızı", verim=15.5, raf=18, hasat=85, brix=6.1,
             fusarium_I=0, tmv=1, nematod=0, rin=0, pto=0, ty1=0, sw5=0, mi12=0,
             fusarium_cM=18.0, tmv_cM=18.0, nematod_cM=28.0, rin_cM=9.0,
             kok_guclu=1, soguk_dayanikli=0, kuraklık_toleransi=0,
             etiketler="tmv,pvy,kırmızı biber"),
        dict(hat_id="BIO-CAP-002", hat_adi="YellowBell Export",
             tur="Capsicum annuum",
             meyve_rengi="Sarı", verim=13.8, raf=14, hasat=90, brix=5.5,
             fusarium_I=0, tmv=0, nematod=0, rin=0, pto=0, ty1=0, sw5=0, mi12=0,
             fusarium_cM=18.0, tmv_cM=18.0, nematod_cM=28.0, rin_cM=9.0,
             kok_guclu=0, soguk_dayanikli=0, kuraklık_toleransi=0,
             etiketler="sarı,dolmalık,ihracat"),
        dict(hat_id="BIO-CAP-003", hat_adi="Spicy Supreme",
             tur="Capsicum annuum",
             meyve_rengi="Turuncu", verim=16.2, raf=12, hasat=78, brix=7.2,
             fusarium_I=0, tmv=1, nematod=1, rin=0, pto=0, ty1=0, sw5=0, mi12=0,
             fusarium_cM=18.0, tmv_cM=18.0, nematod_cM=28.0, rin_cM=9.0,
             kok_guclu=1, soguk_dayanikli=0, kuraklık_toleransi=1,
             etiketler="acı,yüksek brix,tmv,nematod"),
        dict(hat_id="BIO-CAP-004", hat_adi="FireFighter TMV",
             tur="Capsicum annuum",
             meyve_rengi="Turuncu", verim=14.7, raf=16, hasat=82, brix=5.9,
             fusarium_I=0, tmv=1, nematod=1, rin=0, pto=0, ty1=0, sw5=0, mi12=0,
             fusarium_cM=18.0, tmv_cM=18.0, nematod_cM=28.0, rin_cM=9.0,
             kok_guclu=1, soguk_dayanikli=1, kuraklık_toleransi=0,
             etiketler="tmv,nematod,ihracat,soğuk"),
        dict(hat_id="BIO-CAP-005", hat_adi="SuperSweet Block",
             tur="Capsicum annuum",
             meyve_rengi="Kırmızı", verim=17.0, raf=15, hasat=80, brix=8.0,
             fusarium_I=0, tmv=0, nematod=0, rin=0, pto=0, ty1=0, sw5=0, mi12=0,
             fusarium_cM=18.0, tmv_cM=18.0, nematod_cM=28.0, rin_cM=9.0,
             kok_guclu=0, soguk_dayanikli=0, kuraklık_toleransi=1,
             etiketler="yüksek brix,yüksek verim,sanayi"),
        # ── KAVUN ──────────────────────────────────────────────────────────
        dict(hat_id="BIO-MEL-001", hat_adi="Honeygold F1",
             tur="Cucumis melo",
             meyve_rengi="Sarı-Altın", verim=24.0, raf=16, hasat=82, brix=14.5,
             fusarium_I=1, tmv=0, nematod=0, rin=0, pto=0, ty1=0, sw5=0, mi12=0,
             fusarium_cM=30.0, tmv_cM=15.0, nematod_cM=42.0, rin_cM=20.0,
             kok_guclu=1, soguk_dayanikli=0, kuraklık_toleransi=1,
             etiketler="kavun,fusarium,ihracat,yüksek brix"),
        dict(hat_id="BIO-MEL-002", hat_adi="Cantaloup Elite",
             tur="Cucumis melo",
             meyve_rengi="Turuncu", verim=21.5, raf=14, hasat=78, brix=13.2,
             fusarium_I=0, tmv=1, nematod=0, rin=0, pto=0, ty1=0, sw5=0, mi12=0,
             fusarium_cM=30.0, tmv_cM=15.0, nematod_cM=42.0, rin_cM=20.0,
             kok_guclu=0, soguk_dayanikli=0, kuraklık_toleransi=1,
             etiketler="kavun,tmv,kantalup"),
        dict(hat_id="BIO-MEL-003", hat_adi="EarlyDawn PM",
             tur="Cucumis melo",
             meyve_rengi="Beyaz-Sarı", verim=19.8, raf=18, hasat=72, brix=12.8,
             fusarium_I=0, tmv=0, nematod=1, rin=1, pto=0, ty1=0, sw5=0, mi12=0,
             fusarium_cM=30.0, tmv_cM=15.0, nematod_cM=42.0, rin_cM=20.0,
             kok_guclu=1, soguk_dayanikli=1, kuraklık_toleransi=0,
             etiketler="kavun,nematod,uzun raf,erken"),
        # ── KARPUZ ─────────────────────────────────────────────────────────
        dict(hat_id="BIO-WAT-001", hat_adi="Crimson Giant F2",
             tur="Citrullus lanatus",
             meyve_rengi="Kırmızı", verim=35.0, raf=21, hasat=88, brix=11.5,
             fusarium_I=1, tmv=0, nematod=0, rin=0, pto=0, ty1=0, sw5=0, mi12=0,
             fusarium_cM=38.0, tmv_cM=25.0, nematod_cM=50.0, rin_cM=18.0,
             kok_guclu=1, soguk_dayanikli=0, kuraklık_toleransi=1,
             etiketler="karpuz,fusarium,yüksek verim"),
        dict(hat_id="BIO-WAT-002", hat_adi="Seedless Wonder",
             tur="Citrullus lanatus",
             meyve_rengi="Kırmızı", verim=28.5, raf=19, hasat=84, brix=12.2,
             fusarium_I=0, tmv=0, nematod=0, rin=0, pto=0, ty1=0, sw5=0, mi12=0,
             fusarium_cM=38.0, tmv_cM=25.0, nematod_cM=50.0, rin_cM=18.0,
             kok_guclu=0, soguk_dayanikli=0, kuraklık_toleransi=0,
             etiketler="karpuz,tohumsuz,ihracat"),
        dict(hat_id="BIO-WAT-003", hat_adi="YellowFlesh Mini",
             tur="Citrullus lanatus",
             meyve_rengi="Sarı Et", verim=22.0, raf=17, hasat=80, brix=13.0,
             fusarium_I=0, tmv=0, nematod=1, rin=0, pto=0, ty1=0, sw5=0, mi12=0,
             fusarium_cM=38.0, tmv_cM=25.0, nematod_cM=50.0, rin_cM=18.0,
             kok_guclu=1, soguk_dayanikli=0, kuraklık_toleransi=1,
             etiketler="karpuz,sarı et,nematod,gurme"),
    ]
    return pd.DataFrame(rows)

# ─────────────────────────────────────────────────────────────────────────────
# §5  BİYOENFORMATİK MOTOR KATMANI
# ─────────────────────────────────────────────────────────────────────────────

# ── §5.1  DNA → Protein ──────────────────────────────────────────────────────

def dna_temizle(dna_str: str) -> str:
    """FASTA başlıkları ve geçersiz karakterleri kaldırır."""
    satirlar = dna_str.strip().splitlines()
    temiz = "".join(
        s.strip() for s in satirlar if not s.strip().startswith(">")
    )
    return "".join(c for c in temiz.upper() if c in "ACGTUNRYSWKMBDHV")


def dna_cevir(dna_str: str) -> str:
    """
    DNA → Amino asit çevirisi.
    Önce Biopython dener (kurulu ise); yoksa dahili kodon tablosunu kullanır.
    En uzun ORF seçilir (3 okuma çerçevesi).
    """
    dna = dna_temizle(dna_str)
    if _BIO_OK:
        try:
            trim = dna[: len(dna) - len(dna) % 3]
            return str(Seq(trim).translate(to_stop=True))
        except Exception:
            pass
    # Dahili çeviri
    en_uzun = ""
    for f in range(3):
        aa_list: List[str] = []
        for i in range(f, len(dna) - 2, 3):
            h = KODON.get(dna[i : i + 3], "X")
            if h == "*":
                break
            aa_list.append(h)
        peptid = "".join(aa_list)
        if len(peptid) > len(en_uzun):
            en_uzun = peptid
    return en_uzun


# ── §5.2  Protein Biyofizik ──────────────────────────────────────────────────

def izoelektrik_nokta(aa: str) -> float:
    """Henderson-Hasselbalch yaklaşımıyla tahmini pI hesabı."""
    if not aa:
        return 7.0
    adim, pH = 1.0, 7.0
    for _ in range(25):
        q = 1.0 / (1 + 10 ** (pH - PKA["N_term"]))
        q -= 1.0 / (1 + 10 ** (PKA["C_term"] - pH))
        for aa_c, pka_v in [("D", PKA["D"]), ("E", PKA["E"]),
                             ("C", PKA["C"]), ("Y", PKA["Y"])]:
            q -= aa.count(aa_c) / (1 + 10 ** (pka_v - pH))
        for aa_c, pka_v in [("H", PKA["H"]), ("K", PKA["K"]), ("R", PKA["R"])]:
            q += aa.count(aa_c) / (1 + 10 ** (pH - pka_v))
        if abs(q) < 0.01:
            break
        pH += adim if q > 0 else -adim
        adim *= 0.5
    return round(pH, 2)


def biyofizik(aa: str) -> Dict:
    """Amino asit dizisi için kapsamlı biyofiziksel profil."""
    if not aa:
        return {}
    n = len(aa)
    aa_mw = {
        "A": 89, "R": 174, "N": 132, "D": 133, "C": 121, "E": 147, "Q": 146,
        "G": 75, "H": 155, "I": 131, "L": 131, "K": 146, "M": 149, "F": 165,
        "P": 115, "S": 105, "T": 119, "W": 204, "Y": 181, "V": 117,
    }
    return {
        "uzunluk"  : n,
        "leu_pct"  : round(aa.count("L") / n * 100, 1),
        "hid_pct"  : round(sum(1 for c in aa if c in AA_HIDROFOBIK) / n * 100, 1),
        "neg_pct"  : round(sum(1 for c in aa if c in AA_NEGATIF) / n * 100, 1),
        "pos_pct"  : round(sum(1 for c in aa if c in AA_POZITIF) / n * 100, 1),
        "pi"       : izoelektrik_nokta(aa),
        "mw_kDa"   : round(sum(aa_mw.get(c, 111) for c in aa) / 1000, 1),
    }


# ── §5.3  Motif Tarama & Akıllı Yorumlayıcı ──────────────────────────────────

def motif_tara(aa: str) -> List[Dict]:
    """20 motif bankasını amino asit dizisinde tarar."""
    bulunan: List[Dict] = []
    for m in MOTIF_BANK:
        pat = m["motif"].replace("X", ".").replace("x", ".")
        try:
            hits = list(re.finditer(pat, aa, re.IGNORECASE))
        except re.error:
            hits = []
        if hits:
            bulunan.append({
                **m,
                "konumlar": [h.start() for h in hits],
                "adet"    : len(hits),
            })
    return bulunan


def akilli_yorum(motifler: List[Dict], bio_profil: Dict) -> Dict:
    """
    Motif bulgularını ve biyofiziksel profili sentezleyen Heuristic yorumlayıcı.

    Döner:
        sinif     : Tahmini protein sınıfı
        ihtimal   : 0–100 güven skoru
        aciklama  : Kullanıcıya sunulacak analiz metni
        mod       : "motif" | "heuristic"
    """
    leu = bio_profil.get("leu_pct", 0)
    hid = bio_profil.get("hid_pct", 0)
    pi  = bio_profil.get("pi", 7.0)
    neg = bio_profil.get("neg_pct", 0)

    if motifler:
        # ── Motif tabanlı yorum ───────────────────────────────────────────
        sinif_say: Dict[str, int] = {}
        for m in motifler:
            sinif_say[m["sinif"]] = sinif_say.get(m["sinif"], 0) + m["adet"]
        dominant = max(sinif_say, key=sinif_say.get)
        ihtimal  = min(len(motifler) * 16 + 40, 96)
        aciklama = (
            f"**{len(motifler)} resmi motif** tespit edildi. "
            f"Baskın sınıf: **{dominant}** ({sinif_say[dominant]} eşleşme). "
            f"Bu dizi büyük olasılıkla bir **{dominant}** proteinidir. "
            f"Tahmini güven: **%{ihtimal}**."
        )
        return {"sinif": dominant, "ihtimal": ihtimal,
                "aciklama": aciklama, "mod": "motif"}

    # ── Heuristic mod (motif bulunamadı) ─────────────────────────────────
    if leu >= 12 and hid >= 35:
        ihtimal = round(min(leu * 2.5 + hid * 0.8, 88), 1)
        return {
            "sinif"   : "NBS-LRR / R-Gen Proteini (Heuristic)",
            "ihtimal" : ihtimal,
            "aciklama": (
                f"Resmi motif eşleşmesi **bulunamadı** — sistem Heuristic moduna geçti.\n\n"
                f"Ancak bu proteindeki **Lösin (L) oranı %{leu}** ve "
                f"**Hidrofobiklik %{hid}** değerleri, NBS-LRR R-gen ailesi proteinlerinin "
                f"lösin tekrar bölgesi (LRR domain) örüntüsüyle **doğrudan uyumludur**. "
                f"Bu dizi büyük olasılıkla bir **bağışıklık/savunma proteini** veya "
                f"**R-gen ürünü**dür. "
                f"Kesin doğrulama için AlphaFold veya InterPro analizi önerilir. "
                f"Tahmini güven: **%{ihtimal}**."
            ),
            "mod": "heuristic",
        }
    elif hid >= 45:
        ihtimal = round(min(hid * 1.6, 82), 1)
        return {
            "sinif"   : "Membran / Taşıyıcı Protein (Heuristic)",
            "ihtimal" : ihtimal,
            "aciklama": (
                f"Resmi motif eşleşmesi **bulunamadı** — sistem Heuristic moduna geçti.\n\n"
                f"Yüksek hidrofobiklik (**%{hid}**) membran-içi α-heliks bölgelerle "
                f"uyumludur. Bu dizi muhtemelen bir **iyon kanalı, ABC taşıyıcı** veya "
                f"**transmembran reseptör kinaz** segmentidir. "
                f"Tahmini güven: **%{ihtimal}**."
            ),
            "mod": "heuristic",
        }
    elif pi < 5.5 and neg >= 14:
        ihtimal = round(min(neg * 3.2 + 25, 74), 1)
        return {
            "sinif"   : "Asidik / Transkripsiyon Düzenleyici (Heuristic)",
            "ihtimal" : ihtimal,
            "aciklama": (
                f"Resmi motif eşleşmesi **bulunamadı** — sistem Heuristic moduna geçti.\n\n"
                f"İzoelektrik nokta **{pi}** (asidik) ve negatif yük yüzdesi **%{neg}**, "
                f"**WRKY, ERF veya MYB** ailesinden bir **transkripsiyon faktörü** olduğuna "
                f"işaret etmektedir. Tahmini güven: **%{ihtimal}**."
            ),
            "mod": "heuristic",
        }
    elif pi > 9.5:
        ihtimal = round(min((pi - 9) * 11 + 38, 77), 1)
        return {
            "sinif"   : "Bazik / DNA-Bağlayan Protein (Heuristic)",
            "ihtimal" : ihtimal,
            "aciklama": (
                f"Resmi motif eşleşmesi **bulunamadı** — sistem Heuristic moduna geçti.\n\n"
                f"Yüksek izoelektrik nokta (**{pi}**) DNA ve RNA'ya yüksek afinite ile "
                f"bağlanan proteinlerde (histon, ribosomal, Zinc Finger TF) sıktır. "
                f"Tahmini güven: **%{ihtimal}**."
            ),
            "mod": "heuristic",
        }
    else:
        return {
            "sinif"   : "Yapısal / Bilinmeyen Fonksiyonlu Protein",
            "ihtimal" : 28.0,
            "aciklama": (
                "Resmi motif eşleşmesi **bulunamadı** ve Heuristic eşikler de aşılmadı. "
                "Bu dizi yapısal bir protein, enzimatik bir protein veya "
                "bilgi tabanımızın dışında kalan yeni bir işlev taşıyıcısı olabilir. "
                "**AlphaFold2, ESMFold veya InterPro** ile yapısal analiz önerilir."
            ),
            "mod": "heuristic",
        }


# ── §5.4  ESMFold API ────────────────────────────────────────────────────────

def esmfold_katla(aa_dizi: str, timeout: int = 60) -> Tuple[Optional[str], str]:
    """
    Meta'nın ESMFold REST API'sine dizi gönderir.
    Döner: (pdb_str | None, durum_mesajı)

    API: https://api.esmatlas.com/foldSequence/v1/pdb/
    - Maksimum 400 AA — uzun diziler kısaltılır.
    - Timeout: 60 sn (varsayılan).
    - Hata durumunda None ve açıklama mesajı döner (uygulama çökmez).
    """
    dizi = aa_dizi[:400].strip()
    if len(dizi) < 10:
        return None, "Dizi çok kısa (minimum 10 AA)."
    try:
        resp = requests.post(
            "https://api.esmatlas.com/foldSequence/v1/pdb/",
            data=dizi,
            headers={"Content-Type": "text/plain"},
            timeout=timeout,
        )
        if resp.status_code == 200 and resp.text.strip().startswith("ATOM"):
            return resp.text, "Başarılı"
        else:
            return None, (
                f"ESMFold API yanıt kodu: {resp.status_code}. "
                "Sunucu meşgul olabilir — birkaç dakika sonra tekrar deneyin."
            )
    except requests.Timeout:
        return None, (
            f"ESMFold API {timeout} saniyede yanıt vermedi. "
            "Daha kısa bir dizi deneyin (<200 AA) veya daha sonra tekrar deneyin."
        )
    except requests.ConnectionError:
        return None, (
            "ESMFold sunucusuna bağlanılamadı. "
            "İnternet bağlantınızı veya sunucu durumunu kontrol edin: "
            "https://api.esmatlas.com"
        )
    except Exception as exc:
        return None, f"Beklenmeyen hata: {str(exc)[:200]}"


def pdb_3d_html(pdb_str: str, stil: str = "cartoon", renk: str = "spectrum") -> str:
    """
    3Dmol.js CDN kullanarak interaktif 3D protein görselleştirmesi.
    st.components.v1.html ile gösterilir.
    PDB verisi JavaScript string içine güvenle gömülür.
    """
    pdb_escaped = (
        pdb_str
        .replace("\\", "\\\\")
        .replace("`", "\\`")
        .replace("$", "\\$")
    )
    return f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <script src="https://cdnjs.cloudflare.com/ajax/libs/jquery/3.6.0/jquery.min.js"></script>
  <script src="https://3dmol.org/build/3Dmol-min.js" crossorigin="anonymous"></script>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ background: {PAL["bg"]}; overflow: hidden; }}
    #viewer {{ width: 100%; height: 480px; position: relative; }}
    #controls {{
      position: absolute; bottom: 10px; left: 50%; transform: translateX(-50%);
      display: flex; gap: 8px; z-index: 10;
    }}
    .ctrl-btn {{
      background: rgba(20,83,45,.85); color: #4ade80;
      border: 1px solid #22c55e; border-radius: 6px;
      padding: 4px 12px; font-size: 12px; font-family: Inter, sans-serif;
      cursor: pointer; font-weight: 600; transition: all .15s;
    }}
    .ctrl-btn:hover {{ background: rgba(34,197,94,.3); }}
  </style>
</head>
<body>
  <div style="position:relative;">
    <div id="viewer"></div>
    <div id="controls">
      <button class="ctrl-btn" onclick="toggleSpin()">⏸ / ▶</button>
      <button class="ctrl-btn" onclick="setStyle('cartoon')">Cartoon</button>
      <button class="ctrl-btn" onclick="setStyle('stick')">Stick</button>
      <button class="ctrl-btn" onclick="setStyle('sphere')">Sphere</button>
      <button class="ctrl-btn" onclick="setStyle('line')">Line</button>
    </div>
  </div>
  <script>
    var viewer = $3Dmol.createViewer("viewer", {{
      backgroundColor: "{PAL["bg"]}", antialias: true
    }});
    var pdbData = `{pdb_escaped}`;
    viewer.addModel(pdbData, "pdb");
    viewer.setStyle({{}}, {{ "{stil}": {{ "color": "{renk}" }} }});
    viewer.zoomTo();
    viewer.render();
    var spinning = true;
    viewer.spin(true);
    function toggleSpin() {{
      spinning = !spinning;
      viewer.spin(spinning);
    }}
    function setStyle(s) {{
      viewer.setStyle({{}}, {{ [s]: {{ "color": "{renk}" }} }});
      viewer.render();
    }}
  </script>
</body>
</html>"""


# ── §5.5  NCBI API Çağrıları ─────────────────────────────────────────────────

def ncbi_gen_ara(sorgu: str, db: str = "gene", max_n: int = 8) -> Tuple[List[Dict], str]:
    """
    NCBI Gene veya Nucleotide veritabanında arama yapar.
    Döner: (sonuçlar_listesi, durum_mesajı)
    Biopython yoksa veya hata olursa boş liste + açıklama döner.
    """
    if not _BIO_OK:
        return [], "Biopython kurulu değil. `pip install biopython` ile kurun."
    try:
        Entrez.email = "info@biovalentsentinel.com"
        handle  = Entrez.esearch(db=db, term=sorgu, retmax=max_n)
        record  = Entrez.read(handle)
        handle.close()
        ids = record.get("IdList", [])
        if not ids:
            return [], f"'{sorgu}' için NCBI {db} veritabanında sonuç bulunamadı."
        sonuclar: List[Dict] = []
        for uid in ids[:max_n]:
            try:
                h2  = Entrez.efetch(db=db, id=uid, rettype="gb", retmode="text")
                txt = h2.read()
                h2.close()
                if isinstance(txt, bytes):
                    txt = txt.decode("utf-8", errors="ignore")
                # Accession ve tanım
                acc  = next(
                    (l.split()[1] for l in txt.splitlines() if l.startswith("ACCESSION")),
                    uid,
                )
                defi = next(
                    (l.replace("DEFINITION", "").strip()
                     for l in txt.splitlines() if l.startswith("DEFINITION")),
                    "(Tanım alınamadı)",
                )
                org  = next(
                    (l.replace("ORGANISM", "").strip()
                     for l in txt.splitlines() if "ORGANISM" in l),
                    "Bilinmiyor",
                )
                sonuclar.append({
                    "uid"    : uid,
                    "acc"    : acc,
                    "tanim"  : defi[:200],
                    "org"    : org[:80],
                    "kaynak" : f"NCBI {db.upper()} — {acc}",
                })
            except Exception as exc:
                sonuclar.append({
                    "uid"   : uid,
                    "acc"   : uid,
                    "tanim" : f"(Detay alınamadı: {str(exc)[:80]})",
                    "org"   : "—",
                    "kaynak": f"NCBI {db.upper()} UID:{uid}",
                })
        return sonuclar, f"✅ {len(sonuclar)} kayıt bulundu."
    except Exception as exc:
        return [], f"NCBI API hatası: {str(exc)[:200]}"


# ── §5.6  Haldane Linkage & F-Nesil ──────────────────────────────────────────

def haldane_r(cm: float) -> float:
    """Haldane harita fonksiyonu: r = 0.5 × (1 − e^(−2d/100))"""
    return 0.5 * (1.0 - math.exp(-2.0 * cm / 100.0))


def linkage_analiz(cm_a: float, cm_b: float) -> Dict:
    """
    İki genin cM mesafesinden Linkage Drag risk analizi.
    %95 güven ile rekombinan bireyi yakalamak için gereken bitki sayısını hesaplar.
    """
    mesafe    = abs(cm_a - cm_b)
    r         = haldane_r(mesafe)
    surukleme = (1.0 - r) * 100.0
    if r > 0:
        gerekli = math.ceil(math.log(1.0 - GUVEN) / math.log(1.0 - r))
    else:
        gerekli = 999_999

    if mesafe < 5:
        seviye, simge, renk_css = "KRİTİK 🔴", "🔴", PAL["red"]
    elif mesafe < 10:
        seviye, simge, renk_css = "YÜKSEK 🟠", "🟠", PAL["amber"]
    elif mesafe < 20:
        seviye, simge, renk_css = "ORTA 🟡",  "🟡", PAL["gold"]
    else:
        seviye, simge, renk_css = "DÜŞÜK 🟢", "🟢", PAL["g_hi"]

    return {
        "mesafe_cM"  : round(mesafe, 2),
        "r"          : round(r, 5),
        "surukleme"  : round(surukleme, 1),
        "seviye"     : seviye,
        "simge"      : simge,
        "renk"       : renk_css,
        "gerekli"    : gerekli,
    }


def otonom_linkage_tara(df: pd.DataFrame) -> List[Dict]:
    """
    Envanterdeki tüm cM sütun çiftleri arasında linkage analizi yapar.
    10 cM veya altındaki mesafeleri 'Kırmızı Alarm' olarak döndürür.
    """
    cm_kolonlar = [c for c in df.columns if c.endswith("_cM")]
    alarmlar: List[Dict] = []
    for i in range(len(cm_kolonlar)):
        for j in range(i + 1, len(cm_kolonlar)):
            ka, kb = cm_kolonlar[i], cm_kolonlar[j]
            for tur, grp in df.groupby("tur") if "tur" in df.columns else [("Tümü", df)]:
                cm_a = grp[ka].mean()
                cm_b = grp[kb].mean()
                r    = linkage_analiz(cm_a, cm_b)
                if r["mesafe_cM"] <= 20:   # Tüm riskli çiftleri döndür
                    alarmlar.append({
                        "tur"       : tur,
                        "gen_a"     : ka.replace("_cM", ""),
                        "gen_b"     : kb.replace("_cM", ""),
                        "cm_a"      : round(cm_a, 1),
                        "cm_b"      : round(cm_b, 1),
                        **r,
                    })
    alarmlar.sort(key=lambda x: x["mesafe_cM"])
    return alarmlar


def f_nesil_sim(anne_dom: int, baba_dom: int, n_nesil: int = 4) -> pd.DataFrame:
    """
    F1 → F{n_nesil} selfing sabitlenme simülasyonu.
    Her nesilde heterozigot oran yarıya iner (selfing varsayımı).
    """
    rows: List[Dict] = []
    for g in range(1, n_nesil + 1):
        p_het = 0.5 ** (g - 1)
        if anne_dom == 1 and baba_dom == 1:
            p_dom = 1.0
            p_hom = 1.0
        elif anne_dom == 1 or baba_dom == 1:
            p_dom = 1.0 - p_het * 0.25 if g > 1 else 0.75
            p_hom = 1.0 - p_het
        else:
            p_dom = 0.0
            p_hom = 0.0
        rows.append({
            "Nesil"                : f"F{g}",
            "Dominant Fenotip (%)": round(p_dom * 100, 2),
            "Homozigot Oran (%)"  : round(p_hom * 100, 2),
        })
    return pd.DataFrame(rows)


# ── §5.7  Jaccard Akrabalık & Ebeveyn Tahmini ────────────────────────────────

def ozellik_seti(satir: pd.Series) -> set:
    """Bir hattın ikili gen + fenotipik etiket setini döndürür."""
    s: set = set()
    for g in GEN_KOLONLARI:
        if g in satir.index and satir[g] == 1:
            s.add(g)
    if "etiketler" in satir.index and isinstance(satir["etiketler"], str):
        for e in satir["etiketler"].split(","):
            s.add(e.strip().lower())
    return s


def jaccard(a: set, b: set) -> float:
    """Jaccard benzerlik skoru: |A ∩ B| / |A ∪ B|"""
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def akrabalik_mat(df: pd.DataFrame) -> pd.DataFrame:
    """Tüm hat çiftleri için tam Jaccard benzerlik matrisi."""
    ids    = df["hat_id"].tolist()
    setler = [ozellik_seti(df.iloc[i]) for i in range(len(df))]
    n      = len(ids)
    mat    = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            mat[i, j] = jaccard(setler[i], setler[j])
    return pd.DataFrame(mat, index=ids, columns=ids)


def ebeveyn_tahmin(df: pd.DataFrame, hedef_id: str) -> List[Dict]:
    """
    Olasılıklı ebeveyn tahmini.

    Algoritma:
    1. Hedef hattın özellik seti belirlenir.
    2. Diğer tüm hatlar için Jaccard skoru hesaplanır.
    3. En yüksek skorlu iki hat Anne ve Baba adayı olarak seçilir.
       Anne ve Baba, birbirinden maksimum farklı olacak şekilde seçilir
       (genetik çeşitlilik prensibi).
    4. Olasılıklar normalize edilir ve her özelliğin hangi ebeveynden
       geldiği tahmin edilir.

    Döner: [{"hat_id", "hat_adi", "rol", "olasilik", "ortak_ozellikler"}, ...]
    """
    if hedef_id not in df["hat_id"].values:
        return []

    hedef_satir = df[df["hat_id"] == hedef_id].iloc[0]
    hedef_set   = ozellik_seti(hedef_satir)
    diger       = df[df["hat_id"] != hedef_id].reset_index(drop=True)

    # Tüm adaylar için Jaccard skoru
    skorlar = []
    for i in range(len(diger)):
        s = ozellik_seti(diger.iloc[i])
        j = jaccard(hedef_set, s)
        ortak = hedef_set & s
        skorlar.append({
            "hat_id"         : diger.iloc[i]["hat_id"],
            "hat_adi"        : diger.iloc[i]["hat_adi"],
            "skor"           : j,
            "ortak_ozellik"  : len(ortak),
            "ortak_listesi"  : list(ortak)[:8],
        })
    skorlar.sort(key=lambda x: x["skor"], reverse=True)

    if len(skorlar) < 2:
        return skorlar[:2] if skorlar else []

    # Anne: en yüksek benzerlik
    anne = skorlar[0]
    anne_set = ozellik_seti(df[df["hat_id"] == anne["hat_id"]].iloc[0])

    # Baba: Anne'den en farklı, ama yine de hedefe yakın
    baba_adaylari = sorted(
        skorlar[1:8],
        key=lambda x: -jaccard(
            ozellik_seti(df[df["hat_id"] == x["hat_id"]].iloc[0]),
            hedef_set,
        ) + jaccard(
            ozellik_seti(df[df["hat_id"] == x["hat_id"]].iloc[0]),
            anne_set,
        )
    )
    baba = baba_adaylari[0] if baba_adaylari else skorlar[1]

    # Normalize olasılıklar
    toplam = anne["skor"] + baba["skor"]
    anne_p = round(anne["skor"] / toplam * 100, 1) if toplam > 0 else 50.0
    baba_p = round(100.0 - anne_p, 1)

    return [
        {**anne, "rol": "♀ Anne Adayı", "olasilik": anne_p},
        {**baba, "rol": "♂ Baba Adayı", "olasilik": baba_p},
    ]


# ── §5.8  Kapsamlı Genetik Portre Yorumlayıcısı ──────────────────────────────

def genetik_portre(satir: pd.Series, ebeveynler: List[Dict]) -> str:
    """
    Bir hattın tüm genetik, fenotipik ve soy bilgisini
    doğal dil paragraflarına dönüştüren sentez motoru.
    Yalnızca mevcut veriyi yorumlar; hiçbir şey uydurmaz.
    """
    ad    = satir.get("hat_adi", satir.get("hat_id", "?"))
    tur   = satir.get("tur", "?")
    verim = float(satir.get("verim", 0))
    raf   = int(satir.get("raf", 0))
    hasat = int(satir.get("hasat", 0))
    brix  = float(satir.get("brix", 0))
    renk  = satir.get("meyve_rengi", "?")
    kok   = int(satir.get("kok_guclu", 0))
    soguk = int(satir.get("soguk_dayanikli", 0))
    kurak = int(satir.get("kuraklık_toleransi", 0))

    # ── Direnç genlerini çöz ──────────────────────────────────────────────
    gen_aciklamalari = {
        "fusarium_I": ("Fusarium solgunluğu (I — ırk 1,2)", "high"),
        "tmv"       : ("Tütün mozaik virüsü (Tm-2a)", "high"),
        "nematod"   : ("Kök-ur nematodları (Mi-1.2)", "high"),
        "rin"       : ("Olgunlaşma kontrolü — uzun raf ömrü (rin)", "medium"),
        "pto"       : ("Pseudomonas syringae (Pto kinaz)", "high"),
        "ty1"       : ("TYLCV — Sarı yaprak kıvırcıklığı (Ty-1)", "high"),
        "sw5"       : ("TSWV — Solgunluk leke virüsü (sw-5)", "high"),
        "mi12"      : ("Nematod + yaprak biti (Mi-1.2 yedek)", "medium"),
    }
    direncli   = [v[0] for k, v in gen_aciklamalari.items() if satir.get(k, 0) == 1]
    hassas     = [v[0] for k, v in gen_aciklamalari.items() if satir.get(k, 0) == 0]
    yuksek_deg = [v[0] for k, v in gen_aciklamalari.items()
                  if satir.get(k, 0) == 1 and v[1] == "high"]

    # ── Verim yorumu ──────────────────────────────────────────────────────
    if verim >= 22:
        verim_y = f"yüksek verimli ({verim} t/ha — ticari üst sınır)"
    elif verim >= 16:
        verim_y = f"orta-yüksek verimli ({verim} t/ha)"
    elif verim >= 12:
        verim_y = f"orta verimli ({verim} t/ha)"
    else:
        verim_y = f"düşük verimli ({verim} t/ha — özel segment)"

    # ── Raf ömrü yorumu ───────────────────────────────────────────────────
    if raf >= 20:
        raf_y = f"çok uzun raf ömrü ({raf} gün — ihracat ideal)"
    elif raf >= 14:
        raf_y = f"orta-uzun raf ömrü ({raf} gün)"
    elif raf >= 9:
        raf_y = f"orta raf ömrü ({raf} gün)"
    else:
        raf_y = f"kısa raf ömrü ({raf} gün — yerel tüketim)"

    # ── Hasat yorumu ──────────────────────────────────────────────────────
    if hasat <= 65:
        hasat_y = f"erken hasat çeşidi ({hasat} gün)"
    elif hasat <= 78:
        hasat_y = f"orta mevsim çeşidi ({hasat} gün)"
    else:
        hasat_y = f"geç hasat çeşidi ({hasat} gün)"

    # ── İklim yorumu ──────────────────────────────────────────────────────
    iklim_parcalari: List[str] = []
    if soguk:
        iklim_parcalari.append("soğuğa orta dayanıklı")
    else:
        iklim_parcalari.append("soğuğa **zayıf** dayanıklı — düşük sıcaklıklardan kaçının")
    if kurak:
        iklim_parcalari.append("kuraklığa toleranslı")
    if kok:
        iklim_parcalari.append("güçlü kök sistemi (stres koşullarında avantajlı)")

    # ── Ticari değerlendirme ──────────────────────────────────────────────
    puan = 0
    puan += 2 if verim >= 20 else 1 if verim >= 15 else 0
    puan += 2 if raf >= 18 else 1 if raf >= 12 else 0
    puan += 3 if len(direncli) >= 4 else 1 if len(direncli) >= 2 else 0
    puan += 1 if brix >= 7 else 0
    puan += 1 if hasat <= 70 else 0
    puan += 1 if kurak else 0

    if puan >= 8:
        ticari_y = "🌟 **Yüksek Ticari Potansiyel** — İhracat ve organik sertifikasyon için öncelikli aday."
    elif puan >= 5:
        ticari_y = "📈 **Orta-Yüksek Ticari Değer** — Yerel pazar ve örtüaltı üretim için uygundur."
    elif puan >= 3:
        ticari_y = "📊 **Orta Ticari Değer** — Niş pazar (gourmet, organik) için değerlendirilebilir."
    else:
        ticari_y = "🔬 **Islah Materyali Olarak Değerli** — Ticari potansiyeli sınırlı; ancak gen kaynağı olarak faydalıdır."

    # ── Ebeveyn bölümü ────────────────────────────────────────────────────
    eb_bolum = ""
    if ebeveynler and len(ebeveynler) >= 2:
        e0, e1  = ebeveynler[0], ebeveynler[1]
        ortak0  = ", ".join(e0.get("ortak_listesi", [])[:5])
        ortak1  = ", ".join(e1.get("ortak_listesi", [])[:5])
        eb_bolum = f"""
---
**🧬 Olasılıklı Soy Ağacı Analizi**

Bu hat, özelliklerinin tahminen **%{e0["olasilik"]}**'ini **{e0["hat_adi"]}** 
(`{e0["hat_id"]}`) ve **%{e1["olasilik"]}**'ini **{e1["hat_adi"]}** 
(`{e1["hat_id"]}`) adlı hatlardan almış olabilir.

- **Anne adayı** ({e0["hat_id"]}) ile paylaşılan özellikler: `{ortak0 or "—"}`
- **Baba adayı** ({e1["hat_id"]}) ile paylaşılan özellikler: `{ortak1 or "—"}`

*Bu tahmin Jaccard genetik benzerlik analizi ile üretilmiştir.  
Kesin soy doğrulaması için SNP çip verisi veya SSR markör paneli gereklidir.*"""

    # ── Tam metin ─────────────────────────────────────────────────────────
    metin = f"""## 🧬 {ad} — Kapsamlı Genetik Portre
**Tür:** *{tur}*

---

### 🍅 Meyve & Fenoloji
- **Meyve rengi:** {renk} &nbsp;|&nbsp; **Brix:** {brix}° &nbsp;|&nbsp; **{hasat_y}**

### 📦 Verim & Pazar
- **{verim_y}** — {raf_y}

### 🌦️ Morfoloji & İklim Uyumu
- {" · ".join(iklim_parcalari) if iklim_parcalari else "—"}

---

### 🛡️ Hastalık Direnci (Kanıtlanmış Genler)
- ✅ **Dirençli ({len(direncli)} gen):** {", ".join(direncli) if direncli else "*(direnç geni bulunamadı)*"}
- ⚠️ **Hassas:** {", ".join(hassas[:4]) if hassas else "*(tüm hastalıklara dirençli)*"}{"..." if len(hassas) > 4 else ""}

---

### 💼 Ticari Değerlendirme
{ticari_y}
{eb_bolum}

---
*Biovalent Sentinel v{VER} — Otomatik Genetik Portre  ·  {datetime.now().strftime("%Y-%m-%d %H:%M")}*
"""
    return metin.strip()


# ─────────────────────────────────────────────────────────────────────────────
# §6  GRAFİK FONKSİYONLARI (Plotly — şeffaf arka plan)
# ─────────────────────────────────────────────────────────────────────────────

def _lay(title: str = "", h: int = 380) -> Dict:
    """Standart şeffaf Plotly layout şablonu."""
    return dict(
        title        = dict(text=title, font=dict(color=PAL["gold"], size=15)),
        paper_bgcolor= PLOTLY_BG,
        plot_bgcolor = "rgba(13,31,13,0.6)",
        font         = dict(color=PAL["txt"], family="Inter,Segoe UI,sans-serif"),
        xaxis        = dict(gridcolor=PAL["border"], zerolinecolor=PAL["border"],
                            tickfont=dict(color=PAL["txt_dim"])),
        yaxis        = dict(gridcolor=PAL["border"], zerolinecolor=PAL["border"],
                            tickfont=dict(color=PAL["txt_dim"])),
        legend       = dict(bgcolor="rgba(13,31,13,.85)", bordercolor=PAL["border"],
                            borderwidth=1),
        margin       = dict(l=55, r=25, t=55, b=50),
        height       = h,
        hoverlabel   = dict(bgcolor=PAL["panel"], bordercolor=PAL["border"],
                            font=dict(color=PAL["txt"])),
    )


def fig_genom(tur: str = "Solanum lycopersicum") -> go.Figure:
    """ITAG 4.0 referans domates genomu interaktif haritası."""
    fig   = go.Figure()
    krom_y = {k: i for i, k in enumerate(TOMATO_GENOME.keys())}
    sinif_renk = {
        "NBS-LRR" : PAL["g_hi"],  "LRR-RLP": PAL["g_mid"],
        "TIR-NBS" : "#34d399",    "Kinaz"   : PAL["gold"],
        "MADS TF" : PAL["blue"],  "TF"      : PAL["purple"],
        "RdRP"    : PAL["amber"], "TF (MYB)": PAL["red"],
    }
    eklendi: set = set()

    for krom, genler in TOMATO_GENOME.items():
        y = krom_y[krom]
        fig.add_shape(
            type="line", x0=0, x1=110, y0=y, y1=y,
            line=dict(color=PAL["border"], width=2.5),
        )
        fig.add_annotation(
            x=-2, y=y, text=krom, showarrow=False,
            font=dict(color=PAL["gold"], size=10), xanchor="right",
        )
        for g in genler:
            renk          = sinif_renk.get(g["sinif"], PAL["txt_dim"])
            goster_legend = g["sinif"] not in eklendi
            if goster_legend:
                eklendi.add(g["sinif"])
            fig.add_trace(go.Scatter(
                x=[g["cm"]], y=[y + 0.05],
                mode="markers+text",
                name=g["sinif"],
                legendgroup=g["sinif"],
                showlegend=goster_legend,
                marker=dict(size=14, color=renk, symbol="diamond",
                            line=dict(color=PAL["border"], width=1)),
                text=[g["gen"]],
                textposition="top center",
                textfont=dict(size=9, color=PAL["white"]),
                hovertemplate=(
                    f"<b>{g['gen']}</b><br>"
                    f"Sınıf: {g['sinif']}<br>"
                    f"Konum: {g['cm']} cM<br>"
                    f"İşlev: {g['islev']}<extra></extra>"
                ),
            ))

    fig.add_vrect(
        x0=0, x1=10,
        fillcolor=PAL["alpha_r"],
        annotation_text="⚠ Linkage Tehlike (<10 cM)",
        annotation_font_color=PAL["red"],
        annotation_position="top left",
        line_width=0,
    )
    layout = _lay(f"🧬 Referans Genom Haritası — {tur} (ITAG 4.0)", h=500)
    layout["xaxis"]["title"] = "Genetik Konum (centiMorgan)"
    layout["xaxis"]["range"] = [-5, 115]
    layout["yaxis"]["tickvals"] = list(krom_y.values())
    layout["yaxis"]["ticktext"] = list(krom_y.keys())
    layout["showlegend"] = True
    layout["legend"]["title"] = dict(text="Protein Sınıfı",
                                     font=dict(color=PAL["gold"]))
    fig.update_layout(**layout)
    return fig


def fig_f_nesil(df_sim: pd.DataFrame, gen_adi: str) -> go.Figure:
    """F1 → Fn sabitlenme çizgi grafiği."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_sim["Nesil"], y=df_sim["Dominant Fenotip (%)"],
        name="Dominant Fenotip", mode="lines+markers",
        line=dict(color=PAL["g_hi"], width=2.8),
        marker=dict(size=10, color=PAL["g_hi"],
                    line=dict(color=PAL["bg"], width=2)),
        fill="tozeroy", fillcolor="rgba(74,222,128,0.07)",
        hovertemplate="%{x}: %{y:.2f}%<extra>Dominant</extra>",
    ))
    fig.add_trace(go.Scatter(
        x=df_sim["Nesil"], y=df_sim["Homozigot Oran (%)"],
        name="Homozigot Oran", mode="lines+markers",
        line=dict(color=PAL["gold"], width=2.8, dash="dot"),
        marker=dict(size=10, color=PAL["gold"],
                    line=dict(color=PAL["bg"], width=2)),
        hovertemplate="%{x}: %{y:.2f}%<extra>Homozigot</extra>",
    ))
    fig.add_hline(y=90, line_dash="dash", line_color=PAL["g_dim"],
                  annotation_text="90% Eşik (Ticari Hazır)",
                  annotation_font_color=PAL["g_dim"])
    layout = _lay(f"⏱️ F1 → F{len(df_sim)} Sabitlenme Simülasyonu — {gen_adi}", h=370)
    layout["yaxis"]["range"] = [-2, 105]
    layout["yaxis"]["title"] = "Oran (%)"
    fig.update_layout(**layout)
    return fig


def fig_risk_gauge(risk_pct: float, baslik: str = "") -> go.Figure:
    """Linkage drag riskini gösteren gösterge (gauge) grafiği."""
    clr = PAL["red"] if risk_pct > 70 else PAL["amber"] if risk_pct > 40 else PAL["g_mid"]
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=risk_pct,
        title=dict(text=baslik or "Linkage Drag Riski",
                   font=dict(color=PAL["gold"], size=13)),
        number=dict(suffix="%", font=dict(color=clr, size=28)),
        gauge=dict(
            axis=dict(range=[0, 100], tickcolor=PAL["txt"],
                      tickfont=dict(color=PAL["txt_dim"])),
            bar=dict(color=clr, thickness=0.25),
            bgcolor=PLOTLY_BG,
            bordercolor=PAL["border"],
            steps=[
                dict(range=[0, 40],  color="rgba(20,83,45,.4)"),
                dict(range=[40, 70], color="rgba(120,53,15,.4)"),
                dict(range=[70, 100],color="rgba(69,10,10,.4)"),
            ],
            threshold=dict(line=dict(color=PAL["red"], width=3), value=70),
        ),
    ))
    fig.update_layout(
        paper_bgcolor=PLOTLY_BG,
        font=dict(color=PAL["txt"]),
        height=270,
        margin=dict(l=30, r=30, t=50, b=15),
    )
    return fig


def fig_heatmap(mat: pd.DataFrame) -> go.Figure:
    """Jaccard akrabalık ısı haritası."""
    ids_k = [i[:12] for i in mat.index]
    fig = go.Figure(go.Heatmap(
        z=mat.values, x=ids_k, y=ids_k,
        colorscale=[
            [0.0, PAL["bg"]],
            [0.3, PAL["g_dim"]],
            [0.7, PAL["g_mid"]],
            [1.0, PAL["g_hi"]],
        ],
        zmin=0, zmax=1,
        colorbar=dict(
            title="Jaccard",
            tickfont=dict(color=PAL["txt"]),
            titlefont=dict(color=PAL["gold"]),
        ),
        hovertemplate=(
            "Hat-1: %{y}<br>"
            "Hat-2: %{x}<br>"
            "Benzerlik: %{z:.3f}<extra></extra>"
        ),
    ))
    layout = _lay(
        "🔥 Genetik Akrabalık Isı Haritası (Jaccard)",
        h=max(440, len(mat) * 26 + 120),
    )
    layout["xaxis"]["tickangle"] = -40
    layout["xaxis"]["tickfont"]["size"] = 8
    layout["yaxis"]["tickfont"]["size"] = 8
    fig.update_layout(**layout)
    return fig


def fig_motif_bar(motifler: List[Dict]) -> Optional[go.Figure]:
    """Bulunan motifleri ve eşleşme sayılarını gösteren yatay bar grafiği."""
    if not motifler:
        return None
    sinif_renk = {
        "NBS-LRR"    : PAL["g_hi"],  "TIR-NBS": "#34d399",
        "CC-NBS"     : "#a7f3d0",    "Protein Kinaz": PAL["gold"],
        "TF-WRKY"    : PAL["blue"],  "TF-MYB"  : PAL["purple"],
        "TF-MADS"    : PAL["amber"], "TF-ERF"  : "#f97316",
        "Zinc Finger": "#c084fc",    "PR Proteini"  : "#fb7185",
        "Taşıyıcı"   : PAL["txt_dim"],"Antioksidan"  : "#a3e635",
        "Chaperone"  : "#fbbf24",    "Antifroz": PAL["teal"],
    }
    renkler = [sinif_renk.get(m["sinif"], PAL["txt_dim"]) for m in motifler]
    fig = go.Figure(go.Bar(
        y=[m["ad"][:30] for m in motifler],
        x=[m["adet"] for m in motifler],
        orientation="h",
        marker=dict(color=renkler, line=dict(color=PAL["border"], width=0.5)),
        text=[f"{m['adet']}×" for m in motifler],
        textposition="outside",
        textfont=dict(color=PAL["gold"]),
        hovertemplate="%{y}<br>Eşleşme: %{x}<extra></extra>",
    ))
    layout = _lay("🔬 Tespit Edilen Protein Motifleri",
                  h=max(300, len(motifler) * 46))
    layout["yaxis"]["autorange"] = "reversed"
    fig.update_layout(**layout)
    return fig


def fig_verim_scatter(df: pd.DataFrame) -> go.Figure:
    """Envanter verim × raf ömrü scatter matrisi."""
    tur_renk = {
        "Solanum lycopersicum": PAL["g_hi"],
        "Capsicum annuum"     : PAL["gold"],
        "Cucumis melo"        : PAL["blue"],
        "Citrullus lanatus"   : PAL["purple"],
    }
    fig = go.Figure()
    for tur, grp in df.groupby("tur") if "tur" in df.columns else [("Tümü", df)]:
        fig.add_trace(go.Scatter(
            x=grp["verim"], y=grp["raf"],
            mode="markers+text",
            name=tur,
            marker=dict(size=12, color=tur_renk.get(tur, PAL["txt_dim"]),
                        line=dict(color=PAL["border"], width=1)),
            text=grp["hat_id"].str[:9],
            textposition="top center",
            textfont=dict(size=8, color=PAL["txt_dim"]),
            hovertemplate=(
                "<b>%{text}</b><br>"
                "Verim: %{x} t/ha<br>"
                "Raf: %{y} gün<extra></extra>"
            ),
        ))
    layout = _lay("📊 Envanter: Verim × Raf Ömrü", h=380)
    layout["xaxis"]["title"] = "Verim (t/ha)"
    layout["yaxis"]["title"] = "Raf Ömrü (gün)"
    fig.update_layout(**layout)
    return fig


def fig_linkage_scatter(alarmlar: List[Dict]) -> go.Figure:
    """Linkage alarm listesini risk düzeyine göre scatter ile görselleştirir."""
    if not alarmlar:
        return go.Figure()
    df_a = pd.DataFrame(alarmlar)
    renk_map = {"KRİTİK 🔴": PAL["red"], "YÜKSEK 🟠": PAL["amber"],
                "ORTA 🟡": PAL["gold"], "DÜŞÜK 🟢": PAL["g_hi"]}
    fig = go.Figure()
    for seviye, grp in df_a.groupby("seviye"):
        fig.add_trace(go.Scatter(
            x=grp["mesafe_cM"],
            y=grp["surukleme"],
            mode="markers",
            name=seviye,
            marker=dict(size=14, color=renk_map.get(seviye, PAL["txt_dim"]),
                        symbol="diamond",
                        line=dict(color=PAL["border"], width=1)),
            hovertemplate=(
                "<b>%{customdata[0]} ↔ %{customdata[1]}</b><br>"
                "Mesafe: %{x:.1f} cM<br>"
                "Sürüklenme: %{y:.1f}%<br>"
                "Risk: %{customdata[2]}<br>"
                "Gerekli Bitki: %{customdata[3]:,}<extra></extra>"
            ),
            customdata=list(zip(
                grp["gen_a"], grp["gen_b"], grp["seviye"], grp["gerekli"]
            )),
        ))
    fig.add_vrect(x0=0, x1=10, fillcolor=PAL["alpha_r"],
                  line_width=0,
                  annotation_text="⚠ Kırmızı Alarm Bölgesi",
                  annotation_font_color=PAL["red"])
    layout = _lay("⚠️ Linkage Drag Risk Haritası", h=380)
    layout["xaxis"]["title"] = "Genetik Mesafe (cM)"
    layout["yaxis"]["title"] = "Sürüklenme Riski (%)"
    fig.update_layout(**layout)
    return fig


# ─────────────────────────────────────────────────────────────────────────────
# §7  SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────

def sidebar_yukle() -> pd.DataFrame:
    """Sidebar render + veri yükleme. DataFrame döndürür."""
    with st.sidebar:
        # ── Logo ──────────────────────────────────────────────────────────
        st.markdown(f"""
        <div style="text-align:center;padding:1.1rem 0 .6rem">
          <div style="font-size:2.4rem">🧬</div>
          <div style="color:{PAL['g_hi']};font-weight:900;font-size:1.18rem;
                      letter-spacing:2px;margin-top:4px">BIOVALENT</div>
          <div style="color:{PAL['txt_dim']};font-size:.68rem;letter-spacing:3px;
                      margin-top:3px;text-transform:uppercase">Sentinel v{VER}</div>
          <div style="color:{PAL['gold']};font-size:.71rem;margin-top:6px;
                      font-style:italic;opacity:.85">{SLOGAN}</div>
        </div>""", unsafe_allow_html=True)

        st.markdown("---")

        # ── Veri Yükleme ──────────────────────────────────────────────────
        st.markdown(f"### 📁 Veri Kaynağı")
        dosya = st.file_uploader(
            "Excel (.xlsx) veya CSV yükle",
            type=["xlsx", "csv"],
            help=(
                "Beklenen sütunlar: hat_id, hat_adi, tur, meyve_rengi, verim, raf, hasat, "
                "brix, fusarium_I, tmv, nematod, rin, pto, ty1, sw5, mi12, "
                "fusarium_cM, tmv_cM, nematod_cM, rin_cM, "
                "kok_guclu, soguk_dayanikli, kuraklık_toleransi, etiketler"
            ),
        )

        df: Optional[pd.DataFrame] = None
        if dosya is not None:
            try:
                if dosya.name.endswith(".csv"):
                    df = pd.read_csv(dosya)
                else:
                    df = pd.read_excel(dosya)
                st.success(f"✅ {len(df)} hat başarıyla yüklendi.", icon="✅")
            except Exception as exc:
                st.error(f"Dosya okunamadı: {exc}", icon="❌")
                df = None

        if df is None:
            df = demo_df()
            st.info("📊 Demo veri seti kullanılıyor (24 hat, 4 tür).", icon="ℹ️")

        st.markdown("---")

        # ── Envanter özeti ────────────────────────────────────────────────
        st.markdown("**📋 Envanter Özeti**")
        kc1, kc2 = st.columns(2)
        kc1.metric("Hat #", len(df))
        kc2.metric("Tür #", df["tur"].nunique() if "tur" in df.columns else "—")
        if "verim" in df.columns:
            st.metric("Ort. Verim", f"{df['verim'].mean():.1f} t/ha")
        if "raf" in df.columns:
            st.metric("Ort. Raf Ömrü", f"{df['raf'].mean():.0f} gün")

        st.markdown("---")

        # ── API durumu ────────────────────────────────────────────────────
        st.markdown("**🌐 API Durumu**")
        st.markdown(
            f"- NCBI Entrez: {'<span class=\"tag-green\">Aktif</span>' if _BIO_OK else '<span class=\"tag-red\">⚠ Biopython Eksik</span>'}\n"
            f"- ESMFold: <span class='tag-blue'>İstek Bazlı</span>\n"
             "- Heuristic Modu: <span class='tag-green'>Hazır</span>",
            unsafe_allow_html=True,
        )
        if not _BIO_OK:
            st.warning("`pip install biopython` komutu ile NCBI erişimini etkinleştirin.", icon="⚠️")

        st.markdown("---")

        # ── Kaynaklar ────────────────────────────────────────────────────
        st.markdown(f"""
        <div style="color:{PAL['txt_dim']};font-size:.71rem;line-height:1.8">
          <b style="color:{PAL['g_mid']}">Veri Kaynakları</b><br>
          NCBI Entrez / Gene / Nucleotide<br>
          ESMFold API — Meta Research<br>
          ITAG 4.0 — Domates Referans Genomu<br>
          Haldane (1919) Harita Fonksiyonu<br>
          Tomato Genome Consortium (2012)
        </div>""", unsafe_allow_html=True)

        st.markdown("---")
        st.markdown(f"""
        <div style="color:{PAL['txt_dim']};font-size:.68rem;text-align:center;
                    line-height:1.6">
          © {datetime.now().year} Biovalent<br>
          Bağımsız AgTech SaaS Platformu<br>
          <span style="color:{PAL['border']}">info@biovalentsentinel.com</span>
        </div>""", unsafe_allow_html=True)

    return df


# ─────────────────────────────────────────────────────────────────────────────
# §8  SEKMELERİ RENDER ET
# ─────────────────────────────────────────────────────────────────────────────

# ── §8.1  Genome Browser & NCBI Arama (Tab 1) ────────────────────────────────

def sekme_genome_ncbi(df: pd.DataFrame) -> None:
    st.markdown("## 🗺️ Genome Browser & Global NCBI Arama")
    st.markdown(
        "Referans domates genomunda kritik direnç gen konumlarını görselleştirir "
        "ve NCBI veritabanlarında gerçek zamanlı gen araması yapar."
    )

    col_harita, col_ncbi = st.columns([3, 2], gap="large")

    with col_harita:
        st.markdown("### Referans Domates Genomu")
        st.caption("Kaynak: ITAG 4.0 — *Solanum lycopersicum* kritik gen konumları")
        try:
            st.plotly_chart(fig_genom(), use_container_width=True)
        except Exception as exc:
            st.error(f"Harita yüklenemedi: {exc}", icon="❌")

        # Otomatik Linkage uyarıları
        st.markdown("#### ⚠️ Referans Genomdaki Kritik Yakınlıklar")
        tum_genler: List[Dict] = []
        for krom, genler in TOMATO_GENOME.items():
            for g in genler:
                tum_genler.append({"krom": krom, **g})
        uyari_sayisi = 0
        for i in range(len(tum_genler)):
            for j in range(i + 1, len(tum_genler)):
                ga, gb = tum_genler[i], tum_genler[j]
                if ga["krom"] == gb["krom"]:
                    r = linkage_analiz(ga["cm"], gb["cm"])
                    if r["mesafe_cM"] < 15:
                        st.warning(
                            f"{r['simge']} **{ga['gen']}** ↔ **{gb['gen']}** "
                            f"({ga['krom']}): **{r['mesafe_cM']:.1f} cM** — {r['seviye']}",
                            icon="⚠️",
                        )
                        uyari_sayisi += 1
        if uyari_sayisi == 0:
            st.success(
                "Referans genomda kritik bağlantı tespit edilmedi.", icon="✅"
            )

        # Verim scatter
        st.markdown("#### 📊 Envanter: Verim × Raf Ömrü")
        try:
            st.plotly_chart(fig_verim_scatter(df), use_container_width=True)
        except Exception as exc:
            st.error(f"Grafik hatası: {exc}", icon="❌")

    with col_ncbi:
        st.markdown("### 🌐 NCBI Küresel Arama")
        sorgu  = st.text_input(
            "Hastalık, gen adı veya bitki türü",
            placeholder="örn: Fusarium resistance tomato NBS-LRR",
            key="ncbi_q",
        )
        db_sec = st.radio("Veritabanı", ["nucleotide", "gene"], horizontal=True,
                          key="ncbi_db")
        max_n  = st.slider("Maksimum sonuç", 2, 12, 6, key="ncbi_n")

        if st.button("🔍 NCBI'da Ara", key="ncbi_btn"):
            if not sorgu.strip():
                st.warning("Lütfen bir arama terimi girin.", icon="⚠️")
            else:
                with st.spinner(
                    "🌐 Küresel veritabanları taranıyor... "
                    "(Bu işlem 15–60 saniye sürebilir)"
                ):
                    try:
                        sonuclar, mesaj = ncbi_gen_ara(sorgu, db_sec, max_n)
                        if not sonuclar:
                            st.warning(mesaj, icon="ℹ️")
                        else:
                            st.success(mesaj, icon="✅")
                            for s in sonuclar:
                                with st.expander(
                                    f"📄 {s['acc']} — {s['org'][:40]}",
                                    expanded=False,
                                ):
                                    st.markdown(f"**Tanım:** {s['tanim']}")
                                    st.caption(f"Kaynak: {s['kaynak']}")
                    except Exception as exc:
                        st.error(
                            f"NCBI araması sırasında beklenmeyen bir hata oluştu: {exc}. "
                            "Sistem Heuristic modunda çalışmaya devam ediyor.",
                            icon="❌",
                        )

        st.markdown("---")
        st.markdown("### 📋 Envanter Hızlı Görünüm")
        try:
            cols_goster = [
                c for c in ["hat_id","hat_adi","tur","meyve_rengi","verim","raf","hasat"]
                if c in df.columns
            ]
            st.dataframe(
                df[cols_goster].rename(columns={
                    "hat_id": "ID", "hat_adi": "Adı", "tur": "Tür",
                    "meyve_rengi": "Renk", "verim": "Verim",
                    "raf": "Raf (gün)", "hasat": "Hasat (gün)",
                }),
                use_container_width=True,
                height=280,
            )
        except Exception as exc:
            st.error(f"Tablo hatası: {exc}", icon="❌")


# ── §8.2  Proteomik & ESMFold 3D (Tab 2) ─────────────────────────────────────

def sekme_proteomik(df: pd.DataFrame) -> None:
    st.markdown("## 🧪 Proteomik Analiz & Canlı 3D Protein Katlanması")
    st.markdown(
        "DNA dizisini amino aside çevirir, **20 biyolojik motif** ile tarar, "
        "biyofiziksel profil çıkarır ve **ESMFold API** ile 3D yapı oluşturur. "
        "Motif bulunamazsa **Heuristic Yorumlayıcı** devreye girer."
    )

    # Demo NBS-LRR dizisi
    DEMO_DNA = (
        "ATGGGCGTTGGCAAAACTACCATGCTTGCAGCTGATTTGCGTCAGAAGATGGCTGCAGAGCTGAAAGAT"
        "CGCTTTGCGATGGTGGATGGCGTGGGCGAAGTGGACTCTTTTGGCGACTTCCTCAAAACACTCGCAGAG"
        "GAGATCATTGGCGTCGTCAAAGATAGTAAACTCTATTTGTTGCTTCTTTTAAGTGGCAGGACTTGGCAT"
        "GTTGGGCGGCGTACTTGGCATTTCAATGGGCGGACAAGAAGTTCCTCATACCGAGAGAGAGTGGGCGTT"
        "GGCAAAACTACCGTATGGGCGGCAAGAAGTTCCTTGAGGGGGTGGCAAAACCATGGCTGGCAGACTTGC"
    )

    col_giris, col_sonuc = st.columns([2, 3], gap="large")

    with col_giris:
        st.markdown("### DNA Girişi")
        kaynak = st.radio(
            "Dizi Kaynağı",
            ["Demo Dizi (NBS-LRR)", "Elle Gir"],
            key="prot_kaynak", horizontal=True,
        )
        if kaynak == "Demo Dizi (NBS-LRR)":
            dna_in = DEMO_DNA
            st.code(DEMO_DNA[:80] + "...", language="text")
        else:
            dna_in = st.text_area(
                "DNA Dizisi (FASTA veya düz nükleotid)",
                placeholder=">Gen_Adi\nATGGGCGTTGGCAAAACTACC...",
                height=140, key="prot_dna",
            )

        st.markdown("**⚙️ Analiz Parametreleri**")
        leu_esik = st.slider("Lösin Eşiği (%)", 5, 20, 12, key="leu_t",
                             help="Heuristic: Bu eşiğin üzerindeki lösin oranı R-gen işaret eder.")
        hid_esik = st.slider("Hidrofobiklik Eşiği (%)", 15, 60, 35, key="hid_t",
                             help="Heuristic: Yüksek hidrofobiklik membran proteini işaret eder.")
        goster_3d = st.checkbox(
            "🔵 ESMFold 3D Yapı Oluştur (internet + ~30-60 sn)",
            value=False, key="goster_3d",
            help="Meta'nın ESMFold API'si üzerinden gerçek 3D katlanma yapar.",
        )
        mol_stil = st.selectbox(
            "3D Görünüm Stili",
            ["cartoon", "stick", "sphere", "line"],
            key="mol_stil",
        )

        analiz_btn = st.button("🔬 Analizi Başlat", key="prot_btn",
                               use_container_width=True)

    with col_sonuc:
        if analiz_btn:
            if not dna_in or len(dna_in.strip()) < 30:
                st.error("Lütfen en az 30 nükleotid içeren bir dizi girin.", icon="❌")
                return
            try:
                with st.spinner("DNA çeviriliyor ve 20 motif taranıyor..."):
                    aa = dna_cevir(dna_in)

                if not aa or len(aa) < 12:
                    st.error(
                        f"Çeviri sonucu çok kısa ({len(aa)} AA). "
                        "Farklı bir dizi veya daha uzun bir giriş deneyin.",
                        icon="❌",
                    )
                    return

                bio   = biyofizik(aa)
                motif = motif_tara(aa)
                yorum = akilli_yorum(motif, bio)

                # ── KPI ───────────────────────────────────────────────────
                k1, k2, k3, k4 = st.columns(4)
                k1.metric("DNA bp",    len(dna_temizle(dna_in)))
                k2.metric("AA Uzunluk", f"{bio['uzunluk']} aa")
                k3.metric("pI",         bio["pi"])
                k4.metric("MW",         f"{bio['mw_kDa']} kDa")
                b1, b2, b3, b4 = st.columns(4)
                b1.metric("Hidrofobiklik", f"%{bio['hid_pct']}")
                b2.metric("Lösin (L)",     f"%{bio['leu_pct']}")
                b3.metric("Negatif Yük",   f"%{bio['neg_pct']}")
                b4.metric("Motif #",       len(motif))

                st.markdown("---")

                # ── Protein sınıfı ────────────────────────────────────────
                clr = (PAL["g_hi"] if yorum["ihtimal"] > 70
                       else PAL["amber"] if yorum["ihtimal"] > 45
                       else PAL["red"])
                st.markdown(
                    f"### 🏷️ `{yorum['sinif']}`  "
                    f"<span style='color:{clr};font-weight:800'>"
                    f"%{yorum['ihtimal']} güven</span>"
                    f"  <span class='tag-{'blue' if yorum['mod']=='heuristic' else 'green'}'>"
                    f"{'🤖 Heuristic' if yorum['mod']=='heuristic' else '✅ Motif'}</span>",
                    unsafe_allow_html=True,
                )
                if yorum["mod"] == "heuristic":
                    st.warning(yorum["aciklama"], icon="🤖")
                else:
                    st.success(yorum["aciklama"], icon="✅")

                # ── AA dizisi ─────────────────────────────────────────────
                with st.expander("🔤 Amino Asit Dizisi", expanded=False):
                    st.code(
                        aa[:300] + ("..." if len(aa) > 300 else ""),
                        language="text",
                    )

                # ── Motif grafiği + detayları ─────────────────────────────
                if motif:
                    fig_m = fig_motif_bar(motif)
                    if fig_m:
                        st.plotly_chart(fig_m, use_container_width=True)
                    for m in motif:
                        konum_str = ", ".join(str(k) for k in m["konumlar"])
                        with st.expander(
                            f"**{m['ad']}** — `{m['motif']}` | {m['sinif']} | {m['adet']}×",
                            expanded=False,
                        ):
                            mc1, mc2 = st.columns(2)
                            mc1.markdown(f"**Konum(lar):** {konum_str}")
                            mc1.markdown(f"**İşlev:** {m['islev']}")
                            mc2.success(f"🌾 {m['tarla']}", icon="🌿")
                else:
                    st.info(
                        "20 motif bankasında eşleşme bulunamadı. "
                        "Yukarıdaki Heuristic analizi sonuçlarını inceleyin.",
                        icon="🔎",
                    )

                # ── ESMFold 3D ────────────────────────────────────────────
                if goster_3d:
                    st.markdown("---")
                    st.markdown("### 🔵 ESMFold — Canlı 3D Protein Yapısı")
                    st.caption("Meta Research ESMFold API · api.esmatlas.com")
                    with st.spinner(
                        "🧬 ESMFold sunucusuna dizi gönderiliyor... "
                        "Bu işlem 30–90 saniye sürebilir."
                    ):
                        try:
                            pdb_str, durum = esmfold_katla(aa[:400])
                        except Exception as exc:
                            pdb_str = None
                            durum   = f"Beklenmeyen hata: {str(exc)[:150]}"

                    if pdb_str:
                        st.success(
                            "✅ 3D yapı başarıyla katlandı! "
                            "Grafiği döndürmek için sürükleyin.",
                            icon="✅",
                        )
                        try:
                            import streamlit.components.v1 as components
                            html_kodu = pdb_3d_html(pdb_str, stil=mol_stil)
                            components.html(html_kodu, height=510, scrolling=False)
                        except Exception as exc:
                            st.warning(
                                f"3D görselleştirici yüklenemedi: {exc}. "
                                "Ham PDB verisi aşağıdadır.",
                                icon="⚠️",
                            )
                        with st.expander("📄 Ham PDB Verisi (ilk 2000 karakter)",
                                         expanded=False):
                            st.text(pdb_str[:2000])
                    else:
                        st.warning(
                            f"ESMFold 3D yapı oluşturulamadı: {durum}\n\n"
                            "Sistem Heuristic modunda çalışmaya devam ediyor.",
                            icon="⚠️",
                        )

            except Exception as exc:
                st.error(
                    f"Proteomik analiz sırasında hata oluştu: {exc}. "
                    "Sistem Heuristic moduna geçti.",
                    icon="❌",
                )
                st.code(traceback.format_exc())


# ── §8.3  Otonom Risk Engine (Tab 3) ─────────────────────────────────────────

def sekme_risk(df: pd.DataFrame) -> None:
    st.markdown("## ⚠️ Otonom Risk Engine — Linkage Drag Algılayıcı")
    st.markdown(
        "Sistem envanterdeki **tüm gen çiftlerini** otomatik olarak tarar. "
        "10 cM veya altındaki mesafeleri **Kırmızı Alarm** olarak listeler "
        "ve bu bağı kırmak için gereken **popülasyon büyüklüğünü** hesaplar."
    )

    with st.expander("📖 Bilimsel Temel (Haldane Harita Fonksiyonu)", expanded=False):
        st.markdown(r"""
**Haldane:** $r = 0.5 \times (1 - e^{-2d/100})$

| cM | Risk | Anlam |
|---|---|---|
| < 5 | 🔴 KRİTİK | Her nesilde birlikte kalır |
| 5–10 | 🟠 YÜKSEK | Geniş popülasyon şart |
| 10–20 | 🟡 ORTA | MAS ile yönetilebilir |
| > 20 | 🟢 DÜŞÜK | Bağımsız ayrışır |

**Bitki Sayısı:** $n = \lceil \log(0.05) / \log(1-r) \rceil$ (%95 güven)
        """)

    col_oto, col_manuel = st.columns([3, 2], gap="large")

    with col_oto:
        st.markdown("### 🔴 Otonom Alarm Taraması")
        if st.button("🚨 Tüm Envanteri Otomatik Tara", key="oto_tara",
                     use_container_width=True):
            try:
                with st.spinner(
                    "🔍 Envanterdeki tüm gen çiftleri linkage açısından "
                    "taranıyor..."
                ):
                    alarmlar = otonom_linkage_tara(df)

                kritik = [a for a in alarmlar if a["mesafe_cM"] <= 10]
                orta   = [a for a in alarmlar if 10 < a["mesafe_cM"] <= 20]

                m1, m2, m3 = st.columns(3)
                m1.metric("Kırmızı Alarm (≤10 cM)", len(kritik), delta=None)
                m2.metric("Orta Risk (10–20 cM)", len(orta))
                m3.metric("Toplam Kontrol Edilen", len(alarmlar))

                if kritik:
                    st.error(
                        f"🔴 **{len(kritik)} Kırmızı Alarm!** "
                        f"Aşağıdaki gen çiftleri kritik Linkage Drag riski taşıyor.",
                        icon="🚨",
                    )
                    for a in kritik:
                        gerekli_k = f"{a['gerekli']:,}" if a["gerekli"] < 999_999 else ">1.000.000"
                        st.error(
                            f"**{a['gen_a'].upper()} ↔ {a['gen_b'].upper()}** "
                            f"({a.get('tur', '')})  —  **{a['mesafe_cM']} cM**  |  "
                            f"Sürüklenme riski: **%{a['surukleme']}**  |  "
                            f"Bu bağı kırmak için: **{gerekli_k} bitki** gereklidir.",
                            icon="🔴",
                        )

                if alarmlar:
                    try:
                        st.plotly_chart(
                            fig_linkage_scatter(alarmlar),
                            use_container_width=True,
                        )
                    except Exception as exc:
                        st.warning(f"Grafik yüklenemedi: {exc}", icon="⚠️")

                    alarm_df = pd.DataFrame([{
                        "Gen A"       : a["gen_a"].upper(),
                        "Gen B"       : a["gen_b"].upper(),
                        "Tür"         : a.get("tur", "—"),
                        "Mesafe (cM)" : a["mesafe_cM"],
                        "Sürüklenme %" : a["surukleme"],
                        "Risk"         : a["seviye"],
                        "Gerekli Bitki": a["gerekli"] if a["gerekli"] < 999_999 else ">1M",
                    } for a in alarmlar])
                    st.dataframe(
                        alarm_df.style.map(
                            lambda v: "color:#f87171;font-weight:700"
                            if isinstance(v, str) and "KRİTİK" in v else "",
                        ),
                        use_container_width=True,
                    )
                else:
                    st.success(
                        "✅ Envanterde 20 cM altında bağlantı tespit edilmedi. "
                        "Genetik haritanız risk açısından temiz görünüyor.",
                        icon="✅",
                    )
            except Exception as exc:
                st.error(
                    f"Otonom tarama hatası: {exc}. "
                    "Manuel analiz bölümünü kullanın.",
                    icon="❌",
                )

    with col_manuel:
        st.markdown("### ⚙️ Manuel Linkage Analizi")
        gen_opts = {
            "Fusarium I (Chr11, 45 cM)"   : 45.0,
            "TMV Tm-2a (Chr9, 22.4 cM)"   : 22.4,
            "Nematod Mi-1.2 (Chr6, 33 cM)": 33.1,
            "rin olgunlaşma (Chr5, 21 cM)" : 21.0,
            "Pto kinaz (Chr3, 18.5 cM)"    : 18.5,
            "Prf NBS-LRR (Chr3, 19.8 cM)"  : 19.8,
            "TYLCV Ty-1 (Chr8, 55.2 cM)"   : 55.2,
        }
        gen_a_lbl = st.selectbox(
            "Gen A", list(gen_opts.keys()), key="man_ga"
        )
        gen_b_lbl = st.selectbox(
            "Gen B",
            [k for k in gen_opts if k != gen_a_lbl],
            key="man_gb",
        )
        cm_a = gen_opts[gen_a_lbl]
        cm_b = gen_opts[gen_b_lbl]
        st.info(f"Gen A: **{cm_a} cM**  |  Gen B: **{cm_b} cM**", icon="📍")

        if st.button("⚡ Manuel Analiz Et", key="man_btn",
                     use_container_width=True):
            try:
                r = linkage_analiz(cm_a, cm_b)
                gerekli_k = f"{r['gerekli']:,}" if r["gerekli"] < 999_999 else ">1.000.000"

                fn_map = {
                    "KRİTİK 🔴": st.error,
                    "YÜKSEK 🟠": st.error,
                    "ORTA 🟡"  : st.warning,
                    "DÜŞÜK 🟢" : st.success,
                }
                fn_map.get(r["seviye"], st.info)(
                    f"{r['simge']} **Risk: {r['seviye']}** — "
                    f"Mesafe: **{r['mesafe_cM']} cM** — "
                    f"Rekombinasyon p: **{r['r']:.5f}**",
                )
                rc1, rc2 = st.columns(2)
                rc1.metric("Sürüklenme Riski", f"%{r['surukleme']}")
                rc2.metric("Gerekli Bitki (95%)", gerekli_k)
                st.plotly_chart(
                    fig_risk_gauge(r["surukleme"]),
                    use_container_width=True,
                )
            except Exception as exc:
                st.error(f"Analiz hatası: {exc}", icon="❌")

        st.markdown("---")
        st.markdown("### ⏱️ F1 → F4 Selfing Simülasyonu")
        anne_v = st.select_slider(
            "Anne Genotipi", [0, 1], value=1, key="anne_v",
            format_func=lambda x: "Dominant (1)" if x else "Resesif (0)",
        )
        baba_v = st.select_slider(
            "Baba Genotipi", [0, 1], value=0, key="baba_v",
            format_func=lambda x: "Dominant (1)" if x else "Resesif (0)",
        )
        n_nesil = st.slider("Nesil Sayısı", 2, 6, 4, key="n_nesil")
        gen_adi = st.text_input("Gen Adı (grafik başlığı)", value="Hedef Gen", key="g_adi")

        if st.button("▶️ Simüle Et", key="sim_btn", use_container_width=True):
            try:
                df_sim = f_nesil_sim(anne_v, baba_v, n_nesil)
                st.plotly_chart(fig_f_nesil(df_sim, gen_adi), use_container_width=True)
                st.dataframe(df_sim, use_container_width=True)
                son = df_sim.iloc[-1]
                if son["Homozigot Oran (%)"] >= 90:
                    st.success(
                        f"✅ F{n_nesil} itibarıyla homozigotluk **%{son['Homozigot Oran (%)']:.1f}**. "
                        f"Hat ticari kullanıma hazır.",
                        icon="✅",
                    )
                elif son["Homozigot Oran (%)"] >= 60:
                    st.warning(
                        f"⚠️ F{n_nesil} homozigotluk: **%{son['Homozigot Oran (%)']:.1f}**. "
                        f"Ek nesil veya MAS (Markör Destekli Seçim) önerilir.",
                        icon="⚠️",
                    )
                else:
                    st.error(
                        f"❌ F{n_nesil} homozigotluk: **%{son['Homozigot Oran (%)']:.1f}**. "
                        f"Backcross veya piramitleme stratejisi gereklidir.",
                        icon="❌",
                    )
            except Exception as exc:
                st.error(f"Simülasyon hatası: {exc}", icon="❌")


# ── §8.4  Genetic Detective & Portre (Tab 4) ─────────────────────────────────

def sekme_detective(df: pd.DataFrame) -> None:
    st.markdown("## 🕵️ Genetic Detective — Ebeveyn Tahmini & Genetik Portre")

    alt_t1, alt_t2 = st.tabs(["🔥 Akrabalık Isı Haritası", "🧬 Genetik Portre"])

    # ── Isı haritası ──────────────────────────────────────────────────────────
    with alt_t1:
        st.markdown(
            "Envanterdeki tüm hat çiftleri için **Jaccard genetik benzerlik matrisi** "
            "hesaplar. Yüksek değer = Yüksek akrabalık → Genetik daralma riski."
        )
        tur_f = st.selectbox(
            "Tür Filtresi",
            ["Tümü"] + sorted(df["tur"].unique().tolist()) if "tur" in df.columns else ["Tümü"],
            key="det_tur",
        )
        esik  = st.slider("Akrabalık Uyarı Eşiği", 0.30, 0.90, 0.65, step=0.05, key="det_e")

        if st.button("🔥 Akrabalık Analizini Başlat", key="det_btn",
                     use_container_width=True):
            try:
                df_f = df if tur_f == "Tümü" else df[df["tur"] == tur_f]
                if len(df_f) < 2:
                    st.warning("En az 2 hat gereklidir.", icon="⚠️")
                    return
                with st.spinner("Jaccard benzerlik matrisi hesaplanıyor..."):
                    mat = akrabalik_mat(df_f)

                np_m = mat.values.copy()
                np.fill_diagonal(np_m, np.nan)
                ort  = float(np.nanmean(np_m))
                maks = float(np.nanmax(np_m))

                m1, m2, m3 = st.columns(3)
                m1.metric("Ort. Benzerlik", f"{ort:.3f}")
                m2.metric("Maks. Benzerlik", f"{maks:.3f}")
                m3.metric("Analiz Edilen Hat", len(df_f))

                st.plotly_chart(fig_heatmap(mat), use_container_width=True)

                # Yüksek akrabalık uyarıları
                st.markdown(f"### ⚠️ Yüksek Akrabalık Çiftleri (> {esik:.2f})")
                ids     = mat.index.tolist()
                uyarilar: List[Dict] = []
                for i in range(len(ids)):
                    for j in range(i + 1, len(ids)):
                        v = mat.iloc[i, j]
                        if v >= esik:
                            uyarilar.append({
                                "Hat-1"      : ids[i],
                                "Hat-2"      : ids[j],
                                "Benzerlik"  : round(v, 4),
                                "Risk"       : "🔴 Yüksek" if v >= 0.80 else "🟡 Orta",
                            })
                if uyarilar:
                    u_df = (
                        pd.DataFrame(uyarilar)
                        .sort_values("Benzerlik", ascending=False)
                        .reset_index(drop=True)
                    )
                    u_df.index += 1
                    st.dataframe(
                        u_df.style.background_gradient(
                            subset=["Benzerlik"], cmap="RdYlGn_r"
                        ),
                        use_container_width=True,
                    )
                    st.warning(
                        f"⚠️ **{len(uyarilar)} yüksek akrabalık çifti** tespit edildi. "
                        "Bu hatları aynı çaprazlamada kullanmaktan kaçının — "
                        "**genetik daralma (genetic bottleneck)** riski taşırlar.",
                        icon="⚠️",
                    )
                else:
                    st.success(
                        f"✅ **{esik:.2f}** eşiğinin üzerinde akrabalık tespit edilmedi. "
                        "Envanteriniz genetik çeşitlilik açısından sağlıklı.",
                        icon="✅",
                    )

            except Exception as exc:
                st.error(f"Akrabalık analizi hatası: {exc}", icon="❌")
                st.code(traceback.format_exc())

    # ── Genetik Portre ────────────────────────────────────────────────────────
    with alt_t2:
        st.markdown(
            "Bir hat seçin; sistem **tüm genetik ve fenotipik verileri** sentezleyerek "
            "doğal dil paragraflarında **kapsamlı bir portre** oluşturur. "
            "Olasılıklı **ebeveyn tahmini** ve **Mendel sabitlenme simülasyonu** dahildir."
        )
        hat_ids = df["hat_id"].tolist() if "hat_id" in df.columns else []
        if not hat_ids:
            st.warning("Envanterde hat_id sütunu bulunamadı.", icon="⚠️")
            return

        secim = st.selectbox("Analiz Edilecek Hat", hat_ids, key="portre_hat")
        inc_eb = st.checkbox("Ebeveyn Tahmini Dahil Et (Jaccard)", value=True, key="inc_eb")
        inc_sim = st.checkbox("Mendel F4 Simülasyonu Dahil Et", value=True, key="inc_sim")

        if st.button("🧬 Genetik Portre Oluştur", key="portre_btn",
                     use_container_width=True):
            try:
                satir = df[df["hat_id"] == secim].iloc[0]
                ebeveynler: List[Dict] = []

                if inc_eb:
                    with st.spinner(
                        "🔍 Jaccard benzerlik analizi ile ebeveyn tahmini "
                        "yapılıyor..."
                    ):
                        try:
                            ebeveynler = ebeveyn_tahmin(df, secim)
                        except Exception as exc:
                            st.warning(
                                f"Ebeveyn tahmini sırasında hata: {exc}. "
                                "Portre ebeveyn bilgisi olmadan oluşturulacak.",
                                icon="⚠️",
                            )

                # Ebeveyn kartları
                if ebeveynler and len(ebeveynler) >= 2:
                    e0, e1 = ebeveynler[0], ebeveynler[1]
                    pc1, pc2 = st.columns(2)
                    with pc1:
                        st.markdown(f"""
                        <div class="bv-card">
                          <span class="tag-green">♀ Anne Adayı — %{e0["olasilik"]}</span>
                          <h4 style="margin:.5rem 0 .2rem">{e0["hat_adi"]}</h4>
                          <small style="color:{PAL["txt_dim"]}">{e0["hat_id"]}</small><br>
                          <small>Ortak özellik: <b>{e0["ortak_ozellik"]}</b></small>
                        </div>""", unsafe_allow_html=True)
                    with pc2:
                        st.markdown(f"""
                        <div class="bv-card">
                          <span class="tag-gold">♂ Baba Adayı — %{e1["olasilik"]}</span>
                          <h4 style="margin:.5rem 0 .2rem">{e1["hat_adi"]}</h4>
                          <small style="color:{PAL["txt_dim"]}">{e1["hat_id"]}</small><br>
                          <small>Ortak özellik: <b>{e1["ortak_ozellik"]}</b></small>
                        </div>""", unsafe_allow_html=True)

                # Mendel simülasyonu
                if inc_sim and ebeveynler and len(ebeveynler) >= 2:
                    for gen_k in ["fusarium_I", "tmv", "nematod"]:
                        if gen_k in df.columns:
                            anne_h = df[df["hat_id"] == ebeveynler[0]["hat_id"]]
                            baba_h = df[df["hat_id"] == ebeveynler[1]["hat_id"]]
                            if len(anne_h) > 0 and len(baba_h) > 0:
                                av = int(anne_h.iloc[0].get(gen_k, 0))
                                bv = int(baba_h.iloc[0].get(gen_k, 0))
                                if av != bv:
                                    etk = {
                                        "fusarium_I": "Fusarium I",
                                        "tmv"       : "TMV Tm-2a",
                                        "nematod"   : "Nematod Mi-1.2",
                                    }
                                    df_sim = f_nesil_sim(av, bv, 4)
                                    st.plotly_chart(
                                        fig_f_nesil(df_sim, etk[gen_k]),
                                        use_container_width=True,
                                    )
                                    break

                st.markdown("---")

                # Kapsamlı portre metni
                st.markdown("### 📋 Kapsamlı Genetik Portre")
                yorum = genetik_portre(satir, ebeveynler)
                st.markdown(yorum)

                with st.expander("📊 Ham Veri Satırı", expanded=False):
                    st.dataframe(
                        pd.DataFrame([satir.to_dict()]),
                        use_container_width=True,
                    )

            except Exception as exc:
                st.error(f"Portre oluşturma hatası: {exc}", icon="❌")
                st.code(traceback.format_exc())


# ── §8.5  Matchmaker & F4 Simülasyonu (Tab 5) ────────────────────────────────

def sekme_matchmaker(df: pd.DataFrame) -> None:
    st.markdown("## 🧬 Matchmaker & Otonom F4 Simülasyonu")
    st.markdown(
        "Hedef özellikleri seçin; sistem en uyumlu **Anne × Baba** çiftlerini "
        "Mendel olasılıklarıyla 100 üzerinden puanlar ve "
        "**F1 → F4 sabitlenme eğrisini** otonom olarak çizer."
    )

    col_giris, col_sonuc = st.columns([2, 3], gap="large")

    with col_giris:
        st.markdown("### 🎯 Hedef Özellikler")
        h_fus  = st.checkbox("🛡️ Fusarium Direnci (I)", value=True, key="h_f")
        h_tmv  = st.checkbox("🦠 TMV Direnci (Tm-2a)",   value=True, key="h_t")
        h_nem  = st.checkbox("🪱 Nematod (Mi-1.2)",       value=False, key="h_n")
        h_pto  = st.checkbox("🔬 Pseudomonas (Pto)",      value=False, key="h_p")
        h_rin  = st.checkbox("⏳ Uzun Raf Ömrü (rin)",    value=False, key="h_r")
        h_ty1  = st.checkbox("🌿 TYLCV (Ty-1)",           value=False, key="h_ty")
        h_sw5  = st.checkbox("💨 TSWV (sw-5)",            value=False, key="h_sw")

        st.markdown("### 📈 Fenotip Hedefleri")
        h_yv   = st.checkbox("📦 Yüksek Verim (≥18 t/ha)",  value=True, key="h_yv")
        h_yr   = st.checkbox("🗓️ Uzun Raf (≥18 gün)",       value=False, key="h_yr")
        h_yb   = st.checkbox("🍬 Yüksek Brix (≥7°)",        value=False, key="h_yb")

        st.markdown("### ⚙️ Filtreler")
        tur_f = st.selectbox(
            "Tür Filtresi",
            ["Tümü"] + sorted(df["tur"].unique().tolist()) if "tur" in df.columns else ["Tümü"],
            key="mm_tur",
        )
        top_n = st.slider("Gösterilecek Sonuç Sayısı", 3, 15, 8, key="mm_n")

        basla_btn = st.button(
            "🚀 Eşleştirme Analizini Başlat",
            key="mm_btn", use_container_width=True,
        )

    with col_sonuc:
        if basla_btn:
            # ── Hedef listelerini oluştur ──────────────────────────────────
            hedef_genler: List[str] = []
            if h_fus : hedef_genler.append("fusarium_I")
            if h_tmv : hedef_genler.append("tmv")
            if h_nem : hedef_genler.append("nematod")
            if h_pto : hedef_genler.append("pto")
            if h_rin : hedef_genler.append("rin")
            if h_ty1 : hedef_genler.append("ty1")
            if h_sw5 : hedef_genler.append("sw5")

            hedef_feno: List[str] = []
            if h_yv : hedef_feno.append("yuksek_verim")
            if h_yr : hedef_feno.append("uzun_raf")
            if h_yb : hedef_feno.append("yuksek_brix")

            if not hedef_genler and not hedef_feno:
                st.warning("En az bir hedef özellik seçin.", icon="⚠️")
                return

            try:
                df_f = df if tur_f == "Tümü" else df[df["tur"] == tur_f]
                if len(df_f) < 2:
                    st.warning("Tür filtresini genişletin (en az 2 hat).", icon="⚠️")
                    return

                with st.spinner("Tüm hat kombinasyonları değerlendiriliyor..."):
                    # ── Eşleştirme motoru ──────────────────────────────────
                    sonuclar: List[Dict] = []
                    for i, j in itertools.permutations(range(len(df_f)), 2):
                        anne = df_f.iloc[i]
                        baba = df_f.iloc[j]
                        if anne["hat_id"] == baba["hat_id"]:
                            continue

                        # Gen uyum skoru (max 50)
                        gen_toplam = 0.0
                        gen_detay: Dict[str, float] = {}
                        for g in hedef_genler:
                            if g in anne.index and g in baba.index:
                                a_d = int(anne[g])
                                b_d = int(baba[g])
                                p_f2 = 1.0 if (a_d == 1 and b_d == 1) else \
                                       0.75 if (a_d == 1 or b_d == 1) else 0.0
                                gen_toplam += p_f2
                                gen_detay[g] = round(p_f2 * 100, 1)
                        gen_sk = (gen_toplam / max(len(hedef_genler), 1)) * 50 if hedef_genler else 25

                        # Fenotip uyum skoru (max 30)
                        feno_sk = 0.0
                        if "yuksek_verim" in hedef_feno:
                            avg_v = (anne.get("verim", 0) + baba.get("verim", 0)) / 2
                            feno_sk += min(avg_v / 25, 1.0) * 15
                        if "uzun_raf" in hedef_feno:
                            avg_r = (anne.get("raf", 0) + baba.get("raf", 0)) / 2
                            feno_sk += min(avg_r / 30, 1.0) * 10
                        if "yuksek_brix" in hedef_feno:
                            avg_b = (anne.get("brix", 0) + baba.get("brix", 0)) / 2
                            feno_sk += min(avg_b / 10, 1.0) * 5
                        if not hedef_feno:
                            feno_sk = 15

                        # Tür uyumu (max 20)
                        tur_sk = 20.0 if anne.get("tur") == baba.get("tur") else 0.0

                        skor = min(gen_sk + feno_sk + tur_sk, 100.0)

                        sonuclar.append({
                            "anne_id"  : anne["hat_id"],
                            "anne_adi" : anne["hat_adi"],
                            "baba_id"  : baba["hat_id"],
                            "baba_adi" : baba["hat_adi"],
                            "tur"      : anne.get("tur", "—"),
                            "skor"     : round(skor, 1),
                            "gen_sk"   : round(gen_sk, 1),
                            "feno_sk"  : round(feno_sk, 1),
                            "tur_sk"   : round(tur_sk, 1),
                            "gen_detay": gen_detay,
                        })

                # ── Deduplicate (A×B == B×A) ve sırala ────────────────────
                seen: set = set()
                uniq: List[Dict] = []
                for s in sorted(sonuclar, key=lambda x: x["skor"], reverse=True):
                    key = frozenset([s["anne_id"], s["baba_id"]])
                    if key not in seen:
                        seen.add(key)
                        uniq.append(s)
                uniq = uniq[:top_n]

                if not uniq:
                    st.error("Uyumlu çift bulunamadı.", icon="❌")
                    return

                best = uniq[0]
                st.success(f"✅ **{len(uniq)} en iyi eşleşme** listelendi.", icon="✅")

                m1, m2, m3, m4 = st.columns(4)
                m1.metric("🥇 En Yüksek Skor", f"{best['skor']:.1f}/100")
                m2.metric("Gen Uyum Skoru",    f"{best['gen_sk']:.1f}/50")
                m3.metric("Fenotip Skoru",     f"{best['feno_sk']:.1f}/30")
                m4.metric("Tür Skoru",         f"{best['tur_sk']:.1f}/20")

                # ── Skor bar grafiği ───────────────────────────────────────
                try:
                    res_df   = pd.DataFrame(uniq)
                    etiketler = [
                        f"{r['anne_adi'][:10]}×{r['baba_adi'][:10]}"
                        for _, r in res_df.iterrows()
                    ]
                    fig_bar = go.Figure(go.Bar(
                        y=etiketler,
                        x=res_df["skor"],
                        orientation="h",
                        marker=dict(
                            color=res_df["skor"],
                            colorscale=[
                                [0, PAL["g_dim"]],
                                [0.5, PAL["g_mid"]],
                                [1, PAL["g_hi"]],
                            ],
                            showscale=True,
                            colorbar=dict(title="Skor",
                                          tickfont=dict(color=PAL["txt"])),
                        ),
                        text=[f"{s:.1f}" for s in res_df["skor"]],
                        textposition="outside",
                        textfont=dict(color=PAL["gold"]),
                        hovertemplate="%{y}<br>Skor: %{x:.1f}<extra></extra>",
                    ))
                    layout_bar = _lay("🏆 Eşleşme Skorları", h=max(350, len(uniq) * 46))
                    layout_bar["yaxis"]["autorange"] = "reversed"
                    fig_bar.update_layout(**layout_bar)
                    st.plotly_chart(fig_bar, use_container_width=True)
                except Exception as exc:
                    st.warning(f"Bar grafiği yüklenemedi: {exc}", icon="⚠️")

                # ── Sonuç tablosu ──────────────────────────────────────────
                goster_df = pd.DataFrame([{
                    "Anne": r["anne_adi"], "Baba": r["baba_adi"],
                    "Tür": r["tur"], "Skor": r["skor"],
                    "Gen": r["gen_sk"], "Fenotip": r["feno_sk"],
                } for r in uniq])
                st.dataframe(
                    goster_df.style.background_gradient(
                        subset=["Skor"], cmap="Greens"
                    ).format({"Skor": "{:.1f}", "Gen": "{:.1f}", "Fenotip": "{:.1f}"}),
                    use_container_width=True,
                )

                # ── En iyi çift için F4 simülasyonu ────────────────────────
                st.markdown("---")
                st.markdown(
                    f"### 🥇 En İyi Çift: `{best['anne_adi']}` × `{best['baba_adi']}`"
                )
                if best["gen_detay"] and hedef_genler:
                    # İlk anlamlı gen için simüle et
                    sim_gen = hedef_genler[0]
                    if sim_gen in df_f.columns:
                        anne_row = df_f[df_f["hat_id"] == best["anne_id"]]
                        baba_row = df_f[df_f["hat_id"] == best["baba_id"]]
                        if len(anne_row) > 0 and len(baba_row) > 0:
                            av = int(anne_row.iloc[0].get(sim_gen, 0))
                            bv = int(baba_row.iloc[0].get(sim_gen, 0))
                            try:
                                df_sim = f_nesil_sim(av, bv, 4)
                                st.plotly_chart(
                                    fig_f_nesil(
                                        df_sim,
                                        f"{sim_gen.upper()} geni — "
                                        f"{best['anne_adi'][:12]} × {best['baba_adi'][:12]}",
                                    ),
                                    use_container_width=True,
                                )
                            except Exception as exc:
                                st.warning(f"Simülasyon grafiği: {exc}", icon="⚠️")

                with st.expander("🔬 En İyi Çift Gen Uyum Detayı", expanded=False):
                    if best["gen_detay"]:
                        det_df = pd.DataFrame(
                            list(best["gen_detay"].items()),
                            columns=["Gen", "F2 Başarı Olasılığı (%)"],
                        )
                        st.dataframe(det_df, use_container_width=True)
                    else:
                        st.info("Gen hedefi seçilmedi; fenotip skoru kullanıldı.")

            except Exception as exc:
                st.error(
                    f"Matchmaker analizi sırasında hata: {exc}. "
                    "Hedefleri veya tür filtresini değiştirip tekrar deneyin.",
                    icon="❌",
                )
                st.code(traceback.format_exc())


# ─────────────────────────────────────────────────────────────────────────────
# §9  HERO BANNER & ANA YAPI
# ─────────────────────────────────────────────────────────────────────────────

def hero_banner(df: pd.DataFrame) -> None:
    """Ana ekranın üst kısmındaki hero banner ve KPI satırı."""
    st.markdown(f"""
    <div class="bv-hero">
      <div style="font-size:2.9rem;margin-bottom:.35rem">🧬</div>
      <h1 style="margin:0;font-size:2.45rem;letter-spacing:-.8px">
        Biovalent Sentinel
      </h1>
      <p style="color:{PAL['gold']};font-size:1.05rem;margin:.25rem 0 .55rem;
                letter-spacing:1.8px;font-weight:700;opacity:.9">
        DECODING THE BONDS OF LIFE — AUTONOMOUSLY
      </p>
      <p style="color:{PAL['txt_dim']};font-size:.82rem;margin:0">
        v{VER} &nbsp;·&nbsp; NCBI &nbsp;·&nbsp; ESMFold &nbsp;·&nbsp;
        Mendel &nbsp;·&nbsp; Jaccard &nbsp;·&nbsp; ITAG 4.0
      </p>
    </div>""", unsafe_allow_html=True)

    cols = st.columns(5)
    cols[0].metric("🌱 Hat Sayısı", len(df))
    cols[1].metric("🔬 Tür Sayısı",
                   df["tur"].nunique() if "tur" in df.columns else "—")
    if "verim" in df.columns:
        cols[2].metric("📦 Ort. Verim", f"{df['verim'].mean():.1f} t/ha")
    if "raf" in df.columns:
        cols[3].metric("🗓️ Ort. Raf Ömrü", f"{df['raf'].mean():.0f} gün")
    cols[4].metric(
        "🌐 NCBI",
        "Bağlı" if _BIO_OK else "⚠️ Eksik",
        delta="Heuristic Aktif" if not _BIO_OK else None,
    )


def main() -> None:
    """Ana uygulama akışı."""
    # 1. Sidebar + veri yükle
    df = sidebar_yukle()

    # 2. Hero banner
    hero_banner(df)
    st.markdown("---")

    # 3. Ana sekmeler
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🗺️  Genome & NCBI",
        "🧪  Proteomik & 3D",
        "⚠️  Risk Engine",
        "🕵️  Genetic Detective",
        "🧬  Matchmaker",
    ])

    with tab1:
        try:
            sekme_genome_ncbi(df)
        except Exception as exc:
            st.error(f"Genome & NCBI modülü hatası: {exc}", icon="❌")
            st.code(traceback.format_exc())

    with tab2:
        try:
            sekme_proteomik(df)
        except Exception as exc:
            st.error(f"Proteomik modülü hatası: {exc}. Sistem Heuristic modunda.", icon="❌")
            st.code(traceback.format_exc())

    with tab3:
        try:
            sekme_risk(df)
        except Exception as exc:
            st.error(f"Risk Engine modülü hatası: {exc}", icon="❌")
            st.code(traceback.format_exc())

    with tab4:
        try:
            sekme_detective(df)
        except Exception as exc:
            st.error(f"Genetic Detective modülü hatası: {exc}", icon="❌")
            st.code(traceback.format_exc())

    with tab5:
        try:
            sekme_matchmaker(df)
        except Exception as exc:
            st.error(f"Matchmaker modülü hatası: {exc}", icon="❌")
            st.code(traceback.format_exc())


# ─────────────────────────────────────────────────────────────────────────────
# §10  GİRİŞ NOKTASI
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    main()

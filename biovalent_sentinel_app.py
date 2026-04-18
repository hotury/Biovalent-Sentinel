# ==============================================================================
#  BIOVALENT SENTINEL v4.0
#  Genetik Istihbarat Merkezi - Kuresel Bitki Islahi Karar Destek Sistemi
#  "Decoding the Bonds of Life - Intelligence at Scale"
#
#  KURULUM:
#    pip install streamlit pandas numpy biopython plotly requests openpyxl reportlab
#    streamlit run app.py
#
#  Python 3.11+ uyumlu. Tum API cagrılari try-except ile korunmustur.
# ==============================================================================

# -----------------------------------------------------------------------------
# §0  IMPORTS
# -----------------------------------------------------------------------------
import re
import io
import csv
import math
import time
import json
import base64
import hashlib
import difflib
import textwrap
import itertools
import traceback
import threading
import concurrent.futures
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union

import requests
import numpy as np
import pandas as pd
import streamlit as st

import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# -- Biopython -----------------------------------------------------------------
try:
    from Bio import Entrez, SeqIO
    from Bio.Seq import Seq
    from Bio.Blast import NCBIWWW, NCBIXML
    from Bio.SeqRecord import SeqRecord
    Entrez.email = "info@biovalentsentinel.com"
    _BIO_OK = True
except ImportError:
    _BIO_OK = False

# -- ReportLab (PDF) -----------------------------------------------------------
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.lib import colors
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table,
        TableStyle, HRFlowable, KeepTogether
    )
    _PDF_OK = True
except ImportError:
    _PDF_OK = False

# -----------------------------------------------------------------------------
# §1  SAYFA AYARI  (her zaman ilk Streamlit cagrisi olmalidir)
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Biovalent Sentinel v4.0",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help"    : "https://biovalentsentinel.com/docs",
        "Report a bug": "https://biovalentsentinel.com/support",
        "About"       : "Biovalent Sentinel v4.0 - Genetic Intelligence at Scale",
    },
)
def yerel_3d_koordinat_olustur(aa_dizisi):
    """API olmadan proteinin hidrofobiklik ve açılarına göre koordinat üretir."""
    n = len(aa_dizisi)
    # Fiziksel parametreler (basit sarmal yapı)
    t = np.linspace(0, n/5, n)
    # Hidrofobiklik haritası (Gerçek amino asit özelliklerine göre itme/çekme)
    h_map = [1.5 if a in "LIVFMCW" else 0.8 for a in aa_dizisi]
    
    x = np.cumsum(np.cos(t) * h_map)
    y = np.cumsum(np.sin(t) * h_map)
    z = np.linspace(0, n * 0.2, n)
    
    return pd.DataFrame({'x': x, 'y': y, 'z': z, 'aa': list(aa_dizisi)})
# -----------------------------------------------------------------------------
# §2  RENK PALETi & CSS
# -----------------------------------------------------------------------------
PAL = {
    "bg"     : "#070d07",
    "panel"  : "#0d1f0d",
    "panel2" : "#112311",
    "border" : "#1a3a1a",
    "g_hi"   : "#4ade80",
    "g_mid"  : "#22c55e",
    "g_dim"  : "#14532d",
    "gold"   : "#fbbf24",
    "gold_d" : "#78350f",
    "txt"    : "#d1fae5",
    "txt_dim": "#6b7280",
    "red"    : "#f87171",
    "red_d"  : "#450a0a",
    "amber"  : "#fcd34d",
    "blue"   : "#60a5fa",
    "purple" : "#c084fc",
    "teal"   : "#2dd4bf",
    "white"  : "#f0fdf4",
    "alpha_g": "rgba(74,222,128,0.10)",
    "alpha_r": "rgba(248,113,113,0.08)",
}
PLOTLY_BG = "rgba(0,0,0,0)"

# CSS: f-string yerine .format() kullaniyoruz — tum {} cakismalarindan kaciniriz
_CSS_TEMPLATE = """
<style>
html,body,[data-testid="stAppViewContainer"]{{
  background:{bg};color:{txt};
  font-family:'Inter','Segoe UI','SF Pro Display',sans-serif;
}}
[data-testid="stSidebar"]{{
  background:linear-gradient(180deg,#050d05 0%,#091509 100%);
  border-right:1px solid {border};
}}
h1{{color:{g_hi}!important;letter-spacing:-.6px;}}
h2{{color:{gold}!important;}}
h3{{color:{g_mid}!important;}}
h4{{color:{txt}!important;}}
[data-testid="metric-container"]{{
  background:linear-gradient(145deg,{panel} 0%,{bg} 100%);
  border:1px solid {border};border-radius:12px;padding:14px 16px!important;
}}
[data-testid="metric-container"] label{{color:{gold}!important;font-size:.76rem;font-weight:600;}}
[data-testid="metric-container"] [data-testid="stMetricValue"]{{
  color:{g_hi}!important;font-weight:800;
}}
.stButton>button{{
  background:linear-gradient(135deg,{g_dim} 0%,#0f3d1a 100%);
  color:{g_hi};border:1px solid {g_mid};border-radius:9px;
  font-weight:700;font-size:.92rem;padding:.45rem 1.3rem;transition:all .22s ease;
}}
.stButton>button:hover{{
  background:linear-gradient(135deg,{g_mid} 0%,{g_dim} 100%);
  color:{white};transform:translateY(-2px);
  box-shadow:0 6px 20px rgba(74,222,128,.30);
}}
.stTextArea textarea,.stTextInput input,.stNumberInput input{{
  background-color:{panel}!important;color:{txt}!important;
  border:1px solid {border}!important;border-radius:8px!important;
}}
.stSelectbox>div>div,.stMultiSelect>div>div{{
  background-color:{panel}!important;border:1px solid {border}!important;border-radius:8px!important;
}}
[data-baseweb="tab-list"]{{
  background-color:{panel}!important;border-radius:12px;padding:5px;gap:4px;
}}
[data-baseweb="tab"]{{
  color:{txt_dim}!important;font-weight:600;border-radius:8px!important;padding:.35rem .9rem!important;
}}
[aria-selected="true"]{{color:{g_hi}!important;background-color:{g_dim}!important;}}
[data-testid="stDataFrame"]{{border:1px solid {border};border-radius:10px;overflow:hidden;}}
.streamlit-expanderHeader{{
  background-color:{panel2}!important;color:{gold}!important;
  border-radius:8px!important;font-weight:600;
}}
.stAlert{{border-radius:10px!important;border-left-width:4px!important;font-size:.92rem;}}
hr{{border-color:{border}!important;opacity:.6;}}
.bv-card{{
  background:linear-gradient(145deg,{panel} 0%,{bg} 100%);
  border:1px solid {border};border-radius:14px;
  padding:1.2rem 1.5rem;margin-bottom:.9rem;
}}
.bv-hero{{
  background:linear-gradient(135deg,{panel} 0%,#091809 40%,{bg} 100%);
  border:1px solid {border};border-radius:18px;
  padding:2rem 2.8rem;margin-bottom:1.4rem;text-align:center;
}}
.tag-green{{display:inline-block;background:{g_dim};color:{g_hi};
  border:1px solid {g_mid};border-radius:20px;padding:2px 10px;margin:2px;
  font-size:.75rem;font-weight:700;}}
.tag-gold{{display:inline-block;background:{gold_d};color:{gold};
  border:1px solid {gold};border-radius:20px;padding:2px 10px;margin:2px;
  font-size:.75rem;font-weight:700;}}
.tag-red{{display:inline-block;background:{red_d};color:{red};
  border:1px solid {red};border-radius:20px;padding:2px 10px;margin:2px;
  font-size:.75rem;font-weight:700;}}
.tag-blue{{display:inline-block;background:#1e3a5f;color:{blue};
  border:1px solid {blue};border-radius:20px;padding:2px 10px;margin:2px;
  font-size:.75rem;font-weight:700;}}
.tag-amber{{display:inline-block;background:#3d2a00;color:{amber};
  border:1px solid {amber};border-radius:20px;padding:2px 10px;margin:2px;
  font-size:.75rem;font-weight:700;}}
.fuzzy-bar{{
  height:8px;border-radius:4px;
  background:linear-gradient(90deg,{g_dim},{g_hi});
}}
</style>
"""

CSS = _CSS_TEMPLATE.format(**PAL)
st.markdown(CSS, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# §3  GLOBAL SABiTLER
# -----------------------------------------------------------------------------
VER    = "4.0.0"
SLOGAN = "Decoding the Bonds of Life - Intelligence at Scale"
GUVEN  = 0.95
ENTREZ_EMAIL = "info@biovalentsentinel.com"

# Kodon tablosu
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

# 20 Yerel Motif Bankasi
MOTIF_BANK: List[Dict] = [
    {"ad":"NBS P-loop",        "motif":"GVGKTT",     "sinif":"NBS-LRR",
     "islev":"Nukleotid baglanma - R-gen cekirde.",   "tarla":"Genis spektrumlu patoj. direnci."},
    {"ad":"NBS RNBS-A",        "motif":"ILVDDE",     "sinif":"NBS-LRR",
     "islev":"RNBS-A; NBS etkinlestirme.",            "tarla":"Hipersensitivite yaniti (HR)."},
    {"ad":"LRR Tekrar",        "motif":"LXXLXLXX",   "sinif":"NBS-LRR",
     "islev":"Losin tekrarlı bolge.",                 "tirla":"Irk spektrumunu belirler."},
    {"ad":"TIR Domaini",       "motif":"FLHFAD",     "sinif":"TIR-NBS",
     "islev":"Toll/IL-1 homoloji domaini.",           "tarla":"Dikotil TIR-NBS-LRR direnci."},
    {"ad":"Coiled-Coil",       "motif":"LRRLEEL",    "sinif":"CC-NBS",
     "islev":"Protein etkilesim yuzeyi.",             "tarla":"CC-NBS-LRR monokotil direnc."},
    {"ad":"Kinaz DFG",         "motif":"DFG",        "sinif":"Protein Kinaz",
     "islev":"ATP baglanma ve fosforilasyon.",        "tarla":"Savunma sinyal kaskadi."},
    {"ad":"Kinaz VAIK",        "motif":"VAIK",       "sinif":"Protein Kinaz",
     "islev":"Kinaz-2; katalitik aktivite.",          "tarla":"Biyotik/abiyotik stres sinyali."},
    {"ad":"WRKY Domaini",      "motif":"WRKYGQK",    "sinif":"TF-WRKY",
     "islev":"W-box DNA baglanma.",                   "tarla":"Sistemik edinilmis direnc (SAR)."},
    {"ad":"MYB R2R3",          "motif":"GRTWHTE",    "sinif":"TF-MYB",
     "islev":"Pigment ve olgunlasma duzenleme.",      "tarla":"Meyve rengi, antosiyanin."},
    {"ad":"MADS-Box",          "motif":"MGRNGKVEHI", "sinif":"TF-MADS",
     "islev":"Meyve gelisimi ve olgunlasma.",         "tarla":"Raf omru kontrolu."},
    {"ad":"AP2/ERF",           "motif":"RAYDAWLKL",  "sinif":"TF-ERF",
     "islev":"Etilen yanit faktoru.",                 "tarla":"Hasat ve stres toleransi."},
    {"ad":"Zinc Finger C2H2",  "motif":"CXXCXXXXHXXXH","sinif":"Zinc Finger",
     "islev":"C2H2 transkripsiyon duzenleme.",        "tarla":"Stres ve gelisim genleri."},
    {"ad":"Zinc Finger C3H",   "motif":"CXXXCXXH",   "sinif":"Zinc Finger",
     "islev":"C3H RNA isleme.",                       "tarla":"Cevre adaptasyon mekanizmalari."},
    {"ad":"PR-1 Peptidi",      "motif":"MKKLLAL",    "sinif":"PR Proteini",
     "islev":"Salisilik asit yolunda savunma.",       "tarla":"SAR biyogostergesi."},
    {"ad":"PR-5 Osmotin",      "motif":"CCQCSPLDS",  "sinif":"PR Proteini",
     "islev":"Antifungal aktivite.",                  "tarla":"Kuf ve fungal patoj. direnci."},
    {"ad":"PR-3 Kitinaz",      "motif":"FYGLNHD",    "sinif":"PR Proteini",
     "islev":"Kitin yikimi.",                         "tarla":"Mantar patoj. direnci."},
    {"ad":"ABC Tasiyici",      "motif":"LSGGQ",      "sinif":"Tasiyici",
     "islev":"ATP baglama kaseti.",                   "tarla":"Fitotoksin atimi."},
    {"ad":"SOD Merkez",        "motif":"HVHAQY",     "sinif":"Antioksidan",
     "islev":"Superoksit dismutaz; ROS temizleme.",   "tarla":"Kuraklık/isi stresi toleransi."},
    {"ad":"HSP90 EEVD",        "motif":"EEVD",       "sinif":"Chaperone",
     "islev":"Isi soku; protein katlanma.",           "tarla":"Yuksek sicaklik korumasi."},
    {"ad":"Antifroz Tip-I",    "motif":"DTASDAAAA",  "sinif":"Antifroz",
     "islev":"Buz kristali engelleme.",               "tarla":"Donma toleransi."},
]

# Amino asit gruplari
AA_HIDROFOBIK = set("VILMFWPA")
AA_NEGATIF    = set("DE")
AA_POZITIF    = set("KRH")

# pKa tablosu
PKA = {
    "D":3.86, "E":4.07, "C":8.18, "Y":10.46,
    "H":6.04, "K":10.53, "R":12.48,
    "N_term":8.00, "C_term":3.10,
}

# Referans Domates Genomu (ITAG 4.0)
TOMATO_GENOME: Dict[str, List[Dict]] = {
    "Chr01": [
        {"gen":"Cf-1", "cm":5.2,  "sinif":"NBS-LRR", "islev":"Cladosporium irk 1 direnci"},
        {"gen":"I-2",  "cm":48.7, "sinif":"NBS-LRR", "islev":"Fusarium oxysporum irk 2 direnci"},
    ],
    "Chr02": [
        {"gen":"Tm-1",  "cm":2.1,  "sinif":"Kinaz",   "islev":"TMV irk 0,1,2 direnci"},
        {"gen":"Ph-3",  "cm":62.0, "sinif":"NBS-LRR", "islev":"Phytophthora infestans direnci"},
    ],
    "Chr03": [
        {"gen":"Pto",   "cm":18.5, "sinif":"Kinaz",   "islev":"Pseudomonas syringae direnci"},
        {"gen":"Prf",   "cm":19.8, "sinif":"NBS-LRR", "islev":"Pto aktivator NBS-LRR geni"},
    ],
    "Chr04": [
        {"gen":"sw-5",  "cm":44.1, "sinif":"NBS-LRR", "islev":"TSWV (Tospoviruus) direnci"},
    ],
    "Chr05": [
        {"gen":"rin",   "cm":21.0, "sinif":"MADS TF", "islev":"Olgunlasma inhibitoru - uzun raf omru"},
        {"gen":"nor",   "cm":26.5, "sinif":"TF",       "islev":"rin ile sinerjik olgunlasma kontrolu"},
    ],
    "Chr06": [
        {"gen":"Mi-1.2","cm":33.1, "sinif":"NBS-LRR", "islev":"Nematod + yaprak biti direnci"},
    ],
    "Chr07": [
        {"gen":"Cf-4",  "cm":12.3, "sinif":"LRR-RLP", "islev":"Cladosporium irk 4 direnci"},
        {"gen":"Cf-9",  "cm":14.8, "sinif":"LRR-RLP", "islev":"Cladosporium irk 9 direnci"},
    ],
    "Chr08": [
        {"gen":"Ty-1",  "cm":55.2, "sinif":"RdRP",    "islev":"TYLCV (Sari yaprak kivirc.) direnci"},
    ],
    "Chr09": [
        {"gen":"Tm-2a", "cm":22.4, "sinif":"NBS-LRR", "islev":"TMV irk 1,2,3 - genis spektrum"},
        {"gen":"Cf-2",  "cm":36.0, "sinif":"LRR-RLP", "islev":"Cladosporium irk 2,5 direnci"},
    ],
    "Chr11": [
        {"gen":"I",     "cm":45.0, "sinif":"NBS-LRR", "islev":"Fusarium oxysporum irk 1,2 direnci"},
        {"gen":"Ve1",   "cm":72.0, "sinif":"LRR-RLP", "islev":"Verticillium solgunlugu direnci"},
    ],
    "Chr12": [
        {"gen":"y",     "cm":5.0,  "sinif":"TF (MYB)", "islev":"Meyve rengi - Y sari, y kirmizi"},
    ],
}

GEN_KOLONLARI = [
    "fusarium_I", "tmv", "nematod", "rin", "pto", "ty1",
    "sw5", "mi12", "kok_guclu", "soguk_dayanikli", "kuraklık_toleransi",
]

# -----------------------------------------------------------------------------
# §4  DEMO VERiSETi
# -----------------------------------------------------------------------------

@st.cache_data(show_spinner=False)
def demo_df() -> pd.DataFrame:
    rows = [
        dict(hat_id="BIO-TOM-001", hat_adi="Crimson Shield F6",
             tur="Solanum lycopersicum",
             meyve_rengi="Koyu Kirmizi", verim=18.5, raf=14, hasat=72, brix=5.2,
             fusarium_I=1, tmv=1, nematod=0, rin=0, pto=1, ty1=0, sw5=0, mi12=1,
             fusarium_cM=45.0, tmv_cM=22.4, nematod_cM=33.1, rin_cM=21.0,
             kok_guclu=1, soguk_dayanikli=0, kuraklık_toleransi=0,
             etiketler="fusarium,tmv,pseudomonas,nematod"),
        dict(hat_id="BIO-TOM-002", hat_adi="GoldenYield HV-9",
             tur="Solanum lycopersicum",
             meyve_rengi="Parlak Sari", verim=22.3, raf=11, hasat=68, brix=4.8,
             fusarium_I=0, tmv=1, nematod=0, rin=0, pto=0, ty1=0, sw5=0, mi12=0,
             fusarium_cM=45.0, tmv_cM=22.4, nematod_cM=33.1, rin_cM=21.0,
             kok_guclu=0, soguk_dayanikli=0, kuraklık_toleransi=1,
             etiketler="sari meyve,yuksek verim,ticari"),
        dict(hat_id="BIO-TOM-003", hat_adi="LongLife Premium",
             tur="Solanum lycopersicum",
             meyve_rengi="Kirmizi", verim=16.8, raf=24, hasat=78, brix=5.8,
             fusarium_I=0, tmv=0, nematod=1, rin=1, pto=0, ty1=0, sw5=0, mi12=1,
             fusarium_cM=45.0, tmv_cM=22.4, nematod_cM=33.1, rin_cM=21.0,
             kok_guclu=1, soguk_dayanikli=0, kuraklık_toleransi=0,
             etiketler="uzun raf omru,nematod,ihracat"),
        dict(hat_id="BIO-TOM-004", hat_adi="SunGold Cherry",
             tur="Solanum lycopersicum",
             meyve_rengi="Turuncu-Sari", verim=21.0, raf=10, hasat=62, brix=8.2,
             fusarium_I=0, tmv=0, nematod=0, rin=0, pto=0, ty1=0, sw5=0, mi12=0,
             fusarium_cM=45.0, tmv_cM=22.4, nematod_cM=33.1, rin_cM=21.0,
             kok_guclu=0, soguk_dayanikli=0, kuraklık_toleransi=1,
             etiketler="sari,cherry,yuksek brix,gurme"),
        dict(hat_id="BIO-TOM-005", hat_adi="Titan Robust F4",
             tur="Solanum lycopersicum",
             meyve_rengi="Koyu Kirmizi", verim=17.2, raf=16, hasat=80, brix=4.5,
             fusarium_I=1, tmv=0, nematod=1, rin=0, pto=0, ty1=1, sw5=0, mi12=1,
             fusarium_cM=45.0, tmv_cM=22.4, nematod_cM=33.1, rin_cM=21.0,
             kok_guclu=1, soguk_dayanikli=1, kuraklık_toleransi=0,
             etiketler="fusarium,nematod,tylcv,soguga dayanikli"),
        dict(hat_id="BIO-TOM-006", hat_adi="Sunrise Export",
             tur="Solanum lycopersicum",
             meyve_rengi="Sari-Turuncu", verim=19.6, raf=20, hasat=74, brix=5.0,
             fusarium_I=0, tmv=1, nematod=0, rin=1, pto=0, ty1=0, sw5=0, mi12=0,
             fusarium_cM=45.0, tmv_cM=22.4, nematod_cM=33.1, rin_cM=21.0,
             kok_guclu=1, soguk_dayanikli=0, kuraklık_toleransi=0,
             etiketler="sari,uzun raf,tmv,ihracat"),
        dict(hat_id="BIO-TOM-007", hat_adi="IronShield Plus",
             tur="Solanum lycopersicum",
             meyve_rengi="Kirmizi", verim=16.0, raf=18, hasat=76, brix=4.7,
             fusarium_I=1, tmv=1, nematod=1, rin=0, pto=1, ty1=1, sw5=1, mi12=1,
             fusarium_cM=45.0, tmv_cM=22.4, nematod_cM=33.1, rin_cM=21.0,
             kok_guclu=1, soguk_dayanikli=1, kuraklık_toleransi=1,
             etiketler="tam direnc,organik,sertifika"),
        dict(hat_id="BIO-TOM-008", hat_adi="Quantum Beefsteak",
             tur="Solanum lycopersicum",
             meyve_rengi="Kirmizi", verim=20.1, raf=12, hasat=84, brix=4.2,
             fusarium_I=1, tmv=0, nematod=0, rin=0, pto=0, ty1=0, sw5=0, mi12=0,
             fusarium_cM=45.0, tmv_cM=22.4, nematod_cM=33.1, rin_cM=21.0,
             kok_guclu=0, soguk_dayanikli=0, kuraklık_toleransi=0,
             etiketler="yuksek verim,buyuk meyve,endustriyel"),
        dict(hat_id="BIO-TOM-009", hat_adi="BioShield Triple",
             tur="Solanum lycopersicum",
             meyve_rengi="Kirmizi", verim=15.3, raf=15, hasat=73, brix=5.1,
             fusarium_I=1, tmv=1, nematod=1, rin=1, pto=1, ty1=0, sw5=0, mi12=1,
             fusarium_cM=45.0, tmv_cM=22.4, nematod_cM=33.1, rin_cM=21.0,
             kok_guclu=1, soguk_dayanikli=0, kuraklık_toleransi=1,
             etiketler="tam direnc,uzun raf,organik"),
        dict(hat_id="BIO-CAP-001", hat_adi="RedBlaze L4 F5",
             tur="Capsicum annuum",
             meyve_rengi="Parlak Kirmizi", verim=15.5, raf=18, hasat=85, brix=6.1,
             fusarium_I=0, tmv=1, nematod=0, rin=0, pto=0, ty1=0, sw5=0, mi12=0,
             fusarium_cM=18.0, tmv_cM=18.0, nematod_cM=28.0, rin_cM=9.0,
             kok_guclu=1, soguk_dayanikli=0, kuraklık_toleransi=0,
             etiketler="tmv,pvy,kirmizi biber"),
        dict(hat_id="BIO-CAP-002", hat_adi="YellowBell Export",
             tur="Capsicum annuum",
             meyve_rengi="Sari", verim=13.8, raf=14, hasat=90, brix=5.5,
             fusarium_I=0, tmv=0, nematod=0, rin=0, pto=0, ty1=0, sw5=0, mi12=0,
             fusarium_cM=18.0, tmv_cM=18.0, nematod_cM=28.0, rin_cM=9.0,
             kok_guclu=0, soguk_dayanikli=0, kuraklık_toleransi=0,
             etiketler="sari,dolmalik,ihracat"),
        dict(hat_id="BIO-CAP-003", hat_adi="Spicy Supreme",
             tur="Capsicum annuum",
             meyve_rengi="Turuncu", verim=16.2, raf=12, hasat=78, brix=7.2,
             fusarium_I=0, tmv=1, nematod=1, rin=0, pto=0, ty1=0, sw5=0, mi12=0,
             fusarium_cM=18.0, tmv_cM=18.0, nematod_cM=28.0, rin_cM=9.0,
             kok_guclu=1, soguk_dayanikli=0, kuraklık_toleransi=1,
             etiketler="aci,yuksek brix,tmv,nematod"),
        dict(hat_id="BIO-MEL-001", hat_adi="Honeygold F1",
             tur="Cucumis melo",
             meyve_rengi="Sari-Altin", verim=24.0, raf=16, hasat=82, brix=14.5,
             fusarium_I=1, tmv=0, nematod=0, rin=0, pto=0, ty1=0, sw5=0, mi12=0,
             fusarium_cM=30.0, tmv_cM=15.0, nematod_cM=42.0, rin_cM=20.0,
             kok_guclu=1, soguk_dayanikli=0, kuraklık_toleransi=1,
             etiketler="kavun,fusarium,ihracat,yuksek brix"),
        dict(hat_id="BIO-WAT-001", hat_adi="Crimson Giant F2",
             tur="Citrullus lanatus",
             meyve_rengi="Kirmizi", verim=35.0, raf=21, hasat=88, brix=11.5,
             fusarium_I=1, tmv=0, nematod=0, rin=0, pto=0, ty1=0, sw5=0, mi12=0,
             fusarium_cM=38.0, tmv_cM=25.0, nematod_cM=50.0, rin_cM=18.0,
             kok_guclu=1, soguk_dayanikli=0, kuraklık_toleransi=1,
             etiketler="karpuz,fusarium,yuksek verim"),
    ]
    return pd.DataFrame(rows)

# -----------------------------------------------------------------------------
# §5  TEMEL BiYOENFORMATiK MOTOR
# -----------------------------------------------------------------------------

def dna_temizle(s: str) -> str:
    lines = s.strip().splitlines()
    temiz = "".join(l.strip() for l in lines if not l.strip().startswith(">"))
    return "".join(c for c in temiz.upper() if c in "ACGTUNRYSWKMBDHV")


def dna_cevir(dna_str: str) -> str:
    dna = dna_temizle(dna_str)
    if _BIO_OK:
        try:
            trim = dna[: len(dna) - len(dna) % 3]
            return str(Seq(trim).translate(to_stop=True))
        except Exception:
            pass
    en_uzun = ""
    for f in range(3):
        aa_list: List[str] = []
        for i in range(f, len(dna) - 2, 3):
            h = KODON.get(dna[i:i+3], "X")
            if h == "*":
                break
            aa_list.append(h)
        p = "".join(aa_list)
        if len(p) > len(en_uzun):
            en_uzun = p
    return en_uzun


def izoelektrik_nokta(aa: str) -> float:
    if not aa:
        return 7.0
    adim, pH = 1.0, 7.0
    for _ in range(25):
        q  =  1.0 / (1 + 10 ** (pH - PKA["N_term"]))
        q -= 1.0 / (1 + 10 ** (PKA["C_term"] - pH))
        for aa_c, pka_v in [("D",PKA["D"]),("E",PKA["E"]),("C",PKA["C"]),("Y",PKA["Y"])]:
            q -= aa.count(aa_c) / (1 + 10 ** (pka_v - pH))
        for aa_c, pka_v in [("H",PKA["H"]),("K",PKA["K"]),("R",PKA["R"])]:
            q += aa.count(aa_c) / (1 + 10 ** (pH - pka_v))
        if abs(q) < 0.01:
            break
        pH += adim if q > 0 else -adim
        adim *= 0.5
    return round(pH, 2)


def biyofizik(aa: str) -> Dict:
    if not aa:
        return {}
    n = len(aa)
    aa_mw = {
        "A":89,"R":174,"N":132,"D":133,"C":121,"E":147,"Q":146,"G":75,"H":155,
        "I":131,"L":131,"K":146,"M":149,"F":165,"P":115,"S":105,"T":119,"W":204,"Y":181,"V":117,
    }
    return {
        "uzunluk": n,
        "leu_pct": round(aa.count("L") / n * 100, 1),
        "hid_pct": round(sum(1 for c in aa if c in AA_HIDROFOBIK) / n * 100, 1),
        "neg_pct": round(sum(1 for c in aa if c in AA_NEGATIF) / n * 100, 1),
        "pos_pct": round(sum(1 for c in aa if c in AA_POZITIF) / n * 100, 1),
        "pi"     : izoelektrik_nokta(aa),
        "mw_kDa" : round(sum(aa_mw.get(c, 111) for c in aa) / 1000, 1),
    }


def haldane_r(cm: float) -> float:
    return 0.5 * (1.0 - math.exp(-2.0 * cm / 100.0))


def linkage_analiz(cm_a: float, cm_b: float) -> Dict:
    mesafe    = abs(cm_a - cm_b)
    r         = haldane_r(mesafe)
    surukleme = (1.0 - r) * 100.0
    gerekli   = math.ceil(math.log(1.0 - GUVEN) / math.log(1.0 - r)) if r > 0 else 999_999
    if mesafe < 5:
        seviye, simge = "KRITIK", "kirmizi"
    elif mesafe < 10:
        seviye, simge = "YUKSEK", "turuncu"
    elif mesafe < 20:
        seviye, simge = "ORTA", "sari"
    else:
        seviye, simge = "DUSUK", "yesil"
    return {
        "mesafe_cM": round(mesafe, 2),
        "r"        : round(r, 5),
        "surukleme": round(surukleme, 1),
        "seviye"   : seviye,
        "simge"    : simge,
        "gerekli"  : gerekli,
    }


def ozellik_seti(satir: pd.Series) -> set:
    s: set = set()
    for g in GEN_KOLONLARI:
        if g in satir.index and satir[g] == 1:
            s.add(g)
    if "etiketler" in satir.index and isinstance(satir["etiketler"], str):
        for e in satir["etiketler"].split(","):
            s.add(e.strip().lower())
    return s


def jaccard(a: set, b: set) -> float:
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def f_nesil_sim(anne_dom: int, baba_dom: int, n_nesil: int = 4) -> pd.DataFrame:
    rows: List[Dict] = []
    for g in range(1, n_nesil + 1):
        p_het = 0.5 ** (g - 1)
        if anne_dom == 1 and baba_dom == 1:
            p_dom, p_hom = 1.0, 1.0
        elif anne_dom == 1 or baba_dom == 1:
            p_dom = 1.0 - p_het * 0.25 if g > 1 else 0.75
            p_hom = 1.0 - p_het
        else:
            p_dom, p_hom = 0.0, 0.0
        rows.append({
            "Nesil"                : "F" + str(g),
            "Dominant Fenotip (%)": round(p_dom * 100, 2),
            "Homozigot Oran (%)"  : round(p_hom * 100, 2),
        })
    return pd.DataFrame(rows)

# -----------------------------------------------------------------------------
# §6  M1 - KURESEL MOTiF ENTEGRASYoNU (InterPro/Pfam + Fuzzy Matching)
# -----------------------------------------------------------------------------

def _fuzzy_skor(hedef: str, aday: str) -> float:
    if not hedef or not aday:
        return 0.0
    m = difflib.SequenceMatcher(None, hedef.upper(), aday.upper())
    base = m.ratio()
    wildcard_bonus = hedef.upper().count("X") * 0.02
    return round(min(base + wildcard_bonus, 1.0), 4)


def motif_tara_yerel(aa: str) -> List[Dict]:
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
                "konumlar"    : [h.start() for h in hits],
                "adet"        : len(hits),
                "eslesme_tipi": "Tam",
                "fuzzy_skor"  : 1.0,
                "kaynak"      : "Yerel Bank",
            })
    return bulunan


def motif_fuzzy_tara(aa: str, esik: float = 0.72) -> List[Dict]:
    tam_eslesmeler = {m["ad"] for m in motif_tara_yerel(aa)}
    fuzzy_sonuclar: List[Dict] = []
    for m in MOTIF_BANK:
        if m["ad"] in tam_eslesmeler:
            continue
        motif_len = len(m["motif"].replace("X","").replace("x",""))
        pencere   = max(motif_len, 6)
        en_iyi    = 0.0
        en_iyi_pos = -1
        for i in range(len(aa) - pencere + 1):
            skor = _fuzzy_skor(m["motif"], aa[i:i+pencere])
            if skor > en_iyi:
                en_iyi     = skor
                en_iyi_pos = i
        if en_iyi >= esik:
            fuzzy_sonuclar.append({
                **m,
                "konumlar"    : [en_iyi_pos],
                "adet"        : 1,
                "eslesme_tipi": "Fuzzy (" + str(int(en_iyi * 100)) + "%)",
                "fuzzy_skor"  : en_iyi,
                "kaynak"      : "Fuzzy Matching",
            })
    return fuzzy_sonuclar


def interpro_sorgula(aa_dizi: str, timeout: int = 30) -> List[Dict]:
    if not aa_dizi or len(aa_dizi) < 20:
        return []
    try:
        resp = requests.post(
            "https://www.ebi.ac.uk/Tools/hmmer/search/hmmscan",
            data={"seqdb":"pfam","seq":">query\n" + aa_dizi[:400],"output":"json"},
            headers={"Accept":"application/json"},
            timeout=timeout,
        )
        if resp.status_code != 200:
            return []
        data = resp.json()
        hits = data.get("results",{}).get("hits",[]) or data.get("hits",[])
        sonuclar: List[Dict] = []
        for hit in hits[:8]:
            doms = hit.get("domains", [{}])
            dom  = doms[0] if doms else {}
            sonuclar.append({
                "acc"          : hit.get("acc","?"),
                "ad"           : hit.get("name", hit.get("acc","?")),
                "sinif"        : "InterPro/Pfam",
                "e_value"      : float(hit.get("evalue", hit.get("e_value",99))),
                "konum"        : [dom.get("alisqfrom",0), dom.get("alisqto",0)],
                "tanim"        : hit.get("desc",""),
                "kaynak"       : "InterPro API",
                "fuzzy_skor"   : 1.0,
                "eslesme_tipi" : "API",
                "konumlar"     : [dom.get("alisqfrom",0)],
                "adet"         : 1,
                "islev"        : hit.get("desc",""),
                "tarla"        : "API sonucu - detay icin InterPro sitesini inceleyin.",
            })
        return sonuclar
    except Exception:
        return []


def pfam_sorgula(aa_dizi: str, timeout: int = 35) -> List[Dict]:
    if not aa_dizi or len(aa_dizi) < 20:
        return []
    try:
        resp = requests.post(
            "https://pfam.xfam.org/search/sequence",
            data={"seq": aa_dizi[:400], "output":"json"},
            headers={"Accept":"application/json"},
            timeout=timeout,
        )
        if resp.status_code != 200:
            return []
        data = resp.json()
        sonuclar: List[Dict] = []
        for hit in (data.get("hits",{}).get("hits",[]))[:8]:
            sonuclar.append({
                "acc"          : hit.get("id","?"),
                "ad"           : hit.get("name","?"),
                "sinif"        : "Pfam Domain",
                "e_value"      : float(hit.get("evalue",99)),
                "konum"        : [hit.get("from",0), hit.get("to",0)],
                "tanim"        : hit.get("desc",""),
                "kaynak"       : "Pfam API",
                "fuzzy_skor"   : 1.0,
                "eslesme_tipi" : "API",
                "konumlar"     : [hit.get("from",0)],
                "adet"         : 1,
                "islev"        : hit.get("desc",""),
                "tarla"        : "Pfam API sonucu.",
            })
        return sonuclar
    except Exception:
        return []


def tam_motif_analizi(
    aa: str,
    fuzzy_esik: float = 0.72,
    interpro_aktif: bool = False,
) -> Dict:
    yerel = motif_tara_yerel(aa)
    fuzzy = motif_fuzzy_tara(aa, esik=fuzzy_esik)
    api_r: List[Dict] = []

    if interpro_aktif:
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
            f1 = ex.submit(interpro_sorgula, aa)
            f2 = ex.submit(pfam_sorgula, aa)
            try:
                api_r += f1.result(timeout=40)
            except Exception:
                pass
            try:
                api_r += f2.result(timeout=40)
            except Exception:
                pass

    tumu = yerel + fuzzy + api_r
    sinif_sayim: Dict[str, int] = {}
    for m in tumu:
        s = m.get("sinif","?")
        sinif_sayim[s] = sinif_sayim.get(s, 0) + m.get("adet", 1)
    ozet_sinif = max(sinif_sayim, key=sinif_sayim.get) if sinif_sayim else "Bilinmiyor"

    return {
        "yerel"      : yerel,
        "fuzzy"      : fuzzy,
        "api"        : api_r,
        "ozet_sinif" : ozet_sinif,
        "toplam"     : len(tumu),
        "sinif_sayim": sinif_sayim,
    }


def akilli_yorum(motif_sonuclari: Dict, bio_profil: Dict) -> Dict:
    tum_motifler = (
        motif_sonuclari.get("yerel", [])
        + motif_sonuclari.get("fuzzy", [])
        + motif_sonuclari.get("api", [])
    )
    leu = bio_profil.get("leu_pct", 0)
    hid = bio_profil.get("hid_pct", 0)
    pi  = bio_profil.get("pi", 7.0)
    neg = bio_profil.get("neg_pct", 0)

    if tum_motifler:
        ozet = motif_sonuclari.get("ozet_sinif","?")
        n    = len(tum_motifler)
        gv   = min(n * 15 + 40, 96)
        fuzzy_var = any(m.get("eslesme_tipi","").startswith("Fuzzy") for m in tum_motifler)
        aciklama = (
            str(n) + " motif tespit edildi "
            "(Tam: " + str(len(motif_sonuclari.get("yerel",[]))) + ", "
            "Fuzzy: " + str(len(motif_sonuclari.get("fuzzy",[]))) + ", "
            "API: " + str(len(motif_sonuclari.get("api",[]))) + "). "
            "Baskin sinif: " + ozet + ". "
            + ("Fuzzy eslesmeler yapisal benzerlige isaret ediyor. " if fuzzy_var else "")
            + "Guven: %" + str(gv) + "."
        )
        return {"sinif":ozet,"ihtimal":gv,"aciklama":aciklama,"mod":"motif"}

    if leu >= 12 and hid >= 35:
        iht = round(min(leu*2.5 + hid*0.8, 88), 1)
        aciklama = (
            "Resmi motif bulunamadi - Heuristic mod aktif. "
            "Losin %" + str(leu) + " ve Hidrofobiklik %" + str(hid) + " "
            "degerlerinin yuksekligi LRR R-gen yapisiyla uyumludur. "
            "Guven: %" + str(iht) + "."
        )
        return {"sinif":"NBS-LRR / R-Gen Proteini (Heuristic)",
                "ihtimal":iht, "aciklama":aciklama, "mod":"heuristic"}

    if hid >= 45:
        iht = round(min(hid*1.6, 82), 1)
        return {
            "sinif"   : "Membran / Tasiyici Protein (Heuristic)",
            "ihtimal" : iht,
            "aciklama": "Yuksek hidrofobiklik %" + str(hid) + " - membran proteini olabilir. Guven: %" + str(iht) + ".",
            "mod"     : "heuristic",
        }

    if pi < 5.5 and neg >= 14:
        iht = round(min(neg*3.2+25, 74), 1)
        return {
            "sinif"   : "Asidik / Transkripsiyon Duzenleyici (Heuristic)",
            "ihtimal" : iht,
            "aciklama": "pI=" + str(pi) + " ve negatif yuk %" + str(neg) + " - TF olabilir. Guven: %" + str(iht) + ".",
            "mod"     : "heuristic",
        }

    if pi > 9.5:
        iht = round(min((pi-9)*11+38, 77), 1)
        return {
            "sinif"   : "Bazik / DNA-Baglayan Protein (Heuristic)",
            "ihtimal" : iht,
            "aciklama": "Yuksek pI=" + str(pi) + " - DNA-baglayan protein. Guven: %" + str(iht) + ".",
            "mod"     : "heuristic",
        }

    return {
        "sinif"   : "Yapisal / Bilinmiyor",
        "ihtimal" : 28.0,
        "aciklama": "Hicbir esik asilmadi. AlphaFold / InterPro analizi onerilir.",
        "mod"     : "heuristic",
    }

# -----------------------------------------------------------------------------
# §7  M2 - BULK UPLOAD  (FASTA / VCF / CSV)
# -----------------------------------------------------------------------------

def parse_fasta(raw: str) -> List[Dict]:
    kayitlar: List[Dict] = []
    mevcut_id   = None
    mevcut_desc = ""
    satirlar: List[str] = []
    for satir in raw.strip().splitlines():
        satir = satir.strip()
        if satir.startswith(">"):
            if mevcut_id is not None:
                kayitlar.append({"id":mevcut_id,"desc":mevcut_desc,"seq":"".join(satirlar)})
            parcalar    = satir[1:].split(None, 1)
            mevcut_id   = parcalar[0] if parcalar else "seq"
            mevcut_desc = parcalar[1] if len(parcalar) > 1 else ""
            satirlar    = []
        elif satir and not satir.startswith(";"):
            satirlar.append(satir.upper())
    if mevcut_id is not None:
        kayitlar.append({"id":mevcut_id,"desc":mevcut_desc,"seq":"".join(satirlar)})
    return kayitlar


def parse_vcf(raw: str) -> pd.DataFrame:
    satirlar = [s for s in raw.strip().splitlines() if not s.startswith("##")]
    if not satirlar:
        return pd.DataFrame()
    baslik: List[str] = []
    veri: List[List[str]] = []
    for s in satirlar:
        if s.startswith("#CHROM") or s.startswith("#chrom"):
            baslik = s.lstrip("#").split("\t")
        elif not s.startswith("#") and s.strip():
            veri.append(s.split("\t"))
    if not baslik:
        baslik = ["CHROM","POS","ID","REF","ALT","QUAL","FILTER","INFO"]
    try:
        df = pd.DataFrame(veri, columns=baslik[:len(veri[0])] if veri else baslik)
        for col in ["POS","QUAL"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        return df
    except Exception:
        return pd.DataFrame()


def vcf_varyant_analiz(df_vcf: pd.DataFrame) -> Dict:
    if df_vcf.empty:
        return {"toplam":0,"snp":0,"indel":0,"kromozomlar":[],"ort_qual":0}
    toplam = len(df_vcf)
    snp = indel = 0
    ref_col = next((c for c in df_vcf.columns if c.upper() in ("REF","REFERENCE")), None)
    alt_col = next((c for c in df_vcf.columns if c.upper() in ("ALT","ALTERNATE")), None)
    if ref_col and alt_col:
        for _, row in df_vcf.iterrows():
            ref = str(row.get(ref_col,"")).strip()
            alt = str(row.get(alt_col,"")).strip()
            if len(ref) == 1 and len(alt) == 1 and ref != "." and alt != ".":
                snp += 1
            else:
                indel += 1
    chr_col = next((c for c in df_vcf.columns if c.upper() in ("CHROM","CHR","#CHROM")), None)
    kromozomlar = sorted(df_vcf[chr_col].unique().tolist()) if chr_col else []
    qual_col = next((c for c in df_vcf.columns if c.upper() == "QUAL"), None)
    ort_qual = 0.0
    if qual_col:
        q = pd.to_numeric(df_vcf[qual_col], errors="coerce").dropna()
        ort_qual = round(q.mean(), 2) if not q.empty else 0.0
    return {"toplam":toplam,"snp":snp,"indel":indel,
            "kromozomlar":kromozomlar,"ort_qual":ort_qual}

# -----------------------------------------------------------------------------
# §8  M3 - HiBRiT PROTEiN YAPI TAHMiNi
# -----------------------------------------------------------------------------

def esmfold_katla(aa_dizi: str, timeout: int = 60) -> Tuple[Optional[str], str]:
    dizi = aa_dizi[:400].strip()
    if len(dizi) < 10:
        return None, "Dizi cok kisa (min 10 AA)."
    try:
        resp = requests.post(
            "https://api.esmatlas.com/foldSequence/v1/pdb/",
            data=dizi,
            headers={"Content-Type": "text/plain"},
            timeout=timeout,
        )
        if resp.status_code == 200 and resp.text.strip().startswith("ATOM"):
            return resp.text, "ESMFold - Basarili"
        return None, "ESMFold HTTP " + str(resp.status_code)
    except requests.exceptions.Timeout:
        return None, "ESMFold timeout - AlphaFold'a geciliyor"
    except requests.exceptions.ConnectionError:
        return None, "ESMFold baglanti hatasi - AlphaFold'a geciliyor"
    except Exception as exc:
        return None, "ESMFold hata: " + str(exc)[:100]


def alphafold_ara(aa_dizi: str, timeout: int = 30) -> Tuple[Optional[str], str]:
    if not aa_dizi or len(aa_dizi) < 20:
        return None, "Dizi cok kisa."
    try:
        uniprot_resp = requests.get(
            "https://rest.uniprot.org/uniprotkb/search",
            params={
                "query" : "sequence_length:[" + str(max(len(aa_dizi)-10,1)) + " TO " + str(len(aa_dizi)+10) + "]",
                "format": "json",
                "fields": "accession,sequence",
                "size"  : "1",
            },
            timeout=timeout,
        )
        if uniprot_resp.status_code != 200:
            return None, "UniProt HTTP " + str(uniprot_resp.status_code)
        data    = uniprot_resp.json()
        results = data.get("results", [])
        if not results:
            return None, "UniProt'ta eslesen protein bulunamadi."
        uniprot_id = results[0].get("primaryAccession","")
        if not uniprot_id:
            return None, "UniProt ID alinamadi."
        af_resp = requests.get(
            "https://alphafold.ebi.ac.uk/api/prediction/" + uniprot_id,
            timeout=timeout,
        )
        if af_resp.status_code == 200:
            af_data = af_resp.json()
            pdb_url = af_data[0].get("pdbUrl","") if af_data else ""
            if pdb_url:
                pdb_content = requests.get(pdb_url, timeout=timeout).text
                return pdb_content, "AlphaFold - " + uniprot_id
        return None, "AlphaFold kaydi bulunamadi (UniProt: " + uniprot_id + ")"
    except requests.exceptions.Timeout:
        return None, "AlphaFold timeout"
    except requests.exceptions.ConnectionError:
        return None, "AlphaFold baglanti hatasi"
    except Exception as exc:
        return None, "AlphaFold hata: " + str(exc)[:100]


def ikincil_yapi_tahmin(aa: str) -> Dict:
    if not aa:
        return {"helix_pct":0,"beta_pct":0,"coil_pct":0,"yorum":"Dizi bos"}
    helix_favori = set("AELM")
    beta_favori  = set("VIYTW")
    n  = max(len(aa), 1)
    h  = round(sum(1 for c in aa if c in helix_favori) / n * 100, 1)
    b  = round(sum(1 for c in aa if c in beta_favori)  / n * 100, 1)
    co = round(100.0 - h - b, 1)
    if h > 35:
        yorum = "alfa-heliks baskin (" + str(h) + "%) - membran veya baglayici protein."
    elif b > 25:
        yorum = "beta-zincir baskin (" + str(b) + "%) - NBS-LRR veya immunoglobulin benzeri."
    else:
        yorum = "Kirpimli/duzensiz yapi agirlikli (" + str(co) + "%) - esnek baglayici protein."
    return {"helix_pct":h,"beta_pct":b,"coil_pct":co,"yorum":yorum}


def hibrit_protein_analiz(aa: str, deneme_esmfold: bool = True) -> Dict:
    pdb_str = None
    kaynak  = "Yerel Tahmin"
    durum   = ""
    if deneme_esmfold:
        pdb_str, durum = esmfold_katla(aa)
        if pdb_str:
            kaynak = "ESMFold (Meta)"
        else:
            pdb_str, durum2 = alphafold_ara(aa)
            if pdb_str:
                kaynak = "AlphaFold (EBI) - " + durum2
                durum  = durum2
            else:
                durum = "ESMFold: " + durum + " | AlphaFold: " + durum2 + " -> Yerel tahmine gecildi"
    else:
        durum = "3D API devre disi - Yerel tahmin kullanildi"
    ikincil = ikincil_yapi_tahmin(aa)
    return {"pdb":pdb_str,"kaynak":kaynak,"ikincil":ikincil,"durum":durum}


def pdb_3d_html(pdb_str: str, stil: str = "cartoon", renk: str = "spectrum") -> str:
    """
    3Dmol.js CDN ile interaktif 3D protein gorsellestirmesi.
    HTML, f-string yerine string.replace() ile olusturulur - syntax hatasi riski yok.
    """
    pdb_e = (
        pdb_str
        .replace("\\", "\\\\")
        .replace("`", "\\`")
        .replace("$", "\\$")
    )
    # Stil ve renk degerleri guvenli sekilde yerlestirilir
    html = (
        "<!DOCTYPE html>\n"
        "<html><head><meta charset=\"utf-8\">\n"
        "<script src=\"https://cdnjs.cloudflare.com/ajax/libs/jquery/3.6.0/jquery.min.js\"></script>\n"
        "<script src=\"https://3dmol.org/build/3Dmol-min.js\" crossorigin=\"anonymous\"></script>\n"
        "<style>\n"
        "* { box-sizing: border-box; margin: 0; padding: 0; }\n"
        "body { background: #070d07; overflow: hidden; }\n"
        "#viewer { width: 100%; height: 480px; position: relative; }\n"
        "#ctrl {\n"
        "  position: absolute; bottom: 10px; left: 50%; transform: translateX(-50%);\n"
        "  display: flex; gap: 8px; z-index: 10;\n"
        "}\n"
        ".cb {\n"
        "  background: rgba(20,83,45,.85); color: #4ade80;\n"
        "  border: 1px solid #22c55e; border-radius: 6px;\n"
        "  padding: 4px 12px; font-size: 12px; cursor: pointer;\n"
        "  font-weight: 600; transition: all .15s;\n"
        "}\n"
        ".cb:hover { background: rgba(34,197,94,.3); }\n"
        "</style></head>\n"
        "<body>\n"
        "<div style=\"position:relative\">\n"
        "  <div id=\"viewer\"></div>\n"
        "  <div id=\"ctrl\">\n"
        "    <button class=\"cb\" onclick=\"toggleSpin()\">Dur / Calistir</button>\n"
        "    <button class=\"cb\" onclick=\"setStyle('cartoon')\">Cartoon</button>\n"
        "    <button class=\"cb\" onclick=\"setStyle('stick')\">Stick</button>\n"
        "    <button class=\"cb\" onclick=\"setStyle('sphere')\">Sphere</button>\n"
        "  </div>\n"
        "</div>\n"
        "<script>\n"
        "var v = $3Dmol.createViewer('viewer', {backgroundColor: '#070d07', antialias: true});\n"
        "var pdbData = `__PDB_DATA__`;\n"
        "v.addModel(pdbData, 'pdb');\n"
        "v.setStyle({}, {__STIL__: {color: '__RENK__'}});\n"
        "v.zoomTo();\n"
        "v.render();\n"
        "var sp = true;\n"
        "v.spin(true);\n"
        "function toggleSpin() { sp = !sp; v.spin(sp); }\n"
        "function setStyle(s) { v.setStyle({}, {[s]: {color: '__RENK__'}}); v.render(); }\n"
        "</script></body></html>"
    )
    html = html.replace("__PDB_DATA__", pdb_e)
    html = html.replace("__STIL__", stil)
    html = html.replace("__RENK__", renk)
    return html

# -----------------------------------------------------------------------------
# §9  M4 - TiCARi KARAR MOTORU v2.0
# -----------------------------------------------------------------------------

def nesil_kaybi_tahmini(
    hedef_gen_sayisi: int,
    baslangic_frekans: float = 0.5,
    min_frekans: float = 0.95,
    max_nesil: int = 10,
) -> pd.DataFrame:
    rows: List[Dict] = []
    for g in range(1, max_nesil + 1):
        p_het   = 0.5 ** (g - 1)
        p_hom   = 1.0 - p_het
        p_hedef = p_hom ** hedef_gen_sayisi
        if p_hedef > 0:
            n_bitki = math.ceil(math.log(1 - GUVEN) / math.log(1 - p_hedef))
        else:
            n_bitki = 999_999
        if p_hom >= min_frekans:
            tavsiye = "Ticari Hazir"
        elif p_hom >= 0.75:
            tavsiye = "MAS ile ileri"
        else:
            tavsiye = "Devam et"
        rows.append({
            "Nesil"                  : "F" + str(g),
            "Homozigot Oran (%)"     : round(p_hom * 100, 2),
            "Hedef Genotip (%)"      : round(p_hedef * 100, 4),
            "Secim Havuzu (bitki)"   : min(n_bitki, 999_999),
            "Durum"                  : tavsiye,
        })
        if p_hom >= min_frekans:
            break
    return pd.DataFrame(rows)


def pazar_uygunluk_skoru(
    verim         : float,
    raf_gun       : int,
    brix          : float,
    n_direnc_geni : int,
    hasat_gun     : int,
    hedef_pazar   : str = "ihracat",
) -> Dict:
    pazar_agirlik = {
        "ihracat" : {"verim":20,"raf":30,"brix":15,"direnc":25,"erken":10},
        "yerel"   : {"verim":30,"raf":15,"brix":20,"direnc":20,"erken":15},
        "organik" : {"verim":15,"raf":20,"brix":20,"direnc":35,"erken":10},
        "sanayi"  : {"verim":40,"raf":10,"brix":10,"direnc":20,"erken":20},
    }
    agirlik = pazar_agirlik.get(hedef_pazar, pazar_agirlik["yerel"])
    v_puan = min(verim / 25,   1.0) * agirlik["verim"]
    r_puan = min(raf_gun / 28, 1.0) * agirlik["raf"]
    b_puan = min(brix / 12,    1.0) * agirlik["brix"]
    d_puan = min(n_direnc_geni / 5, 1.0) * agirlik["direnc"]
    e_puan = (1.0 if hasat_gun <= 70 else 0.5 if hasat_gun <= 80 else 0.0) * agirlik["erken"]
    toplam = round(v_puan + r_puan + b_puan + d_puan + e_puan, 1)

    if toplam >= 80:
        kategori = "A - Premium Ticari Potansiyel"
        aciklama = "Bu cesit dogrudan ticari uretime hazir. Ihracat sertifikasyonu onceliklendirilmeli."
    elif toplam >= 65:
        kategori = "B - Yuksek Degerli Islah Materyali"
        aciklama = "1-2 nesil ek iyilestirme ile ticari uretime hazir hale gelebilir."
    elif toplam >= 50:
        kategori = "C - Orta Ticari Deger"
        aciklama = "Nis pazar veya organik segment icin degerlendirilebilir."
    else:
        kategori = "D - Islah / Arastirma Materyali"
        aciklama = "Dogrudan ticari degil; gen kaynagi veya caprazlama materyali olarak faydali."

    return {
        "toplam"     : toplam,
        "kategori"   : kategori,
        "aciklama"   : aciklama,
        "detay"      : {
            "verim_p" :round(v_puan,1), "raf_p"   :round(r_puan,1),
            "brix_p"  :round(b_puan,1), "direnc_p":round(d_puan,1),
            "erken_p" :round(e_puan,1),
        },
        "hedef_pazar": hedef_pazar,
    }


def otonom_linkage_tara(df: pd.DataFrame) -> List[Dict]:
    cm_kolonlar = [c for c in df.columns if c.endswith("_cM")]
    alarmlar: List[Dict] = []
    for i in range(len(cm_kolonlar)):
        for j in range(i + 1, len(cm_kolonlar)):
            ka, kb = cm_kolonlar[i], cm_kolonlar[j]
            gruplama = df.groupby("tur") if "tur" in df.columns else [("Tumu", df)]
            for tur, grp in gruplama:
                cm_a = grp[ka].mean()
                cm_b = grp[kb].mean()
                r    = linkage_analiz(cm_a, cm_b)
                if r["mesafe_cM"] <= 20:
                    alarmlar.append({
                        "tur"   : tur,
                        "gen_a" : ka.replace("_cM",""),
                        "gen_b" : kb.replace("_cM",""),
                        "cm_a"  : round(cm_a, 1),
                        "cm_b"  : round(cm_b, 1),
                        **r,
                    })
    alarmlar.sort(key=lambda x: x["mesafe_cM"])
    return alarmlar

# -----------------------------------------------------------------------------
# §10  M5 - GENERATIVE REPORTING (PDF)
# -----------------------------------------------------------------------------

def pdf_uret(
    baslik   : str,
    icerik_md: str,
    tablo_df : Optional[pd.DataFrame] = None,
    firma_adi: str = "Biovalent Sentinel",
) -> Optional[bytes]:
    if not _PDF_OK:
        return None
    buf    = io.BytesIO()
    doc    = SimpleDocTemplate(buf, pagesize=A4,
                               leftMargin=2*cm, rightMargin=2*cm,
                               topMargin=2.5*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()
    baslik_s = ParagraphStyle("Baslik", parent=styles["Title"],
                               fontSize=18, textColor=colors.HexColor("#14532d"),
                               spaceAfter=10, fontName="Helvetica-Bold")
    h2_s     = ParagraphStyle("H2",     parent=styles["Heading2"],
                               fontSize=12, textColor=colors.HexColor("#78350f"),
                               spaceBefore=10, spaceAfter=5, fontName="Helvetica-Bold")
    normal_s = ParagraphStyle("Normal2",parent=styles["Normal"],
                               fontSize=9, leading=13, spaceAfter=4,
                               textColor=colors.HexColor("#1a1a1a"))
    meta_s   = ParagraphStyle("Meta",   parent=styles["Normal"],
                               fontSize=7.5, textColor=colors.grey, spaceAfter=6)
    elements = []
    elements.append(Paragraph(baslik, baslik_s))
    elements.append(Paragraph(
        firma_adi + " | " + datetime.now().strftime("%d.%m.%Y %H:%M") + " | v" + VER,
        meta_s,
    ))
    elements.append(HRFlowable(width="100%", thickness=1,
                                color=colors.HexColor("#14532d"), spaceAfter=6))
    for satir in icerik_md.splitlines():
        satir = satir.strip()
        if not satir or satir == "---":
            elements.append(Spacer(1, 5))
            continue
        if satir.startswith("# "):
            elements.append(Paragraph(satir[2:], baslik_s))
        elif satir.startswith("## "):
            elements.append(Paragraph(satir[3:], h2_s))
        elif satir.startswith("- "):
            metin = satir[2:].replace("**","<b>",1).replace("**","</b>",1)
            elements.append(Paragraph("- " + metin, normal_s))
        else:
            metin = satir.replace("**","<b>",1).replace("**","</b>",1)
            elements.append(Paragraph(metin, normal_s))
    if tablo_df is not None and not tablo_df.empty:
        elements.append(Spacer(1, 10))
        elements.append(Paragraph("Detay Tablosu", h2_s))
        cols   = list(tablo_df.columns)
        t_data = [cols] + tablo_df.head(40).values.tolist()
        tablo  = Table(t_data, repeatRows=1, hAlign="LEFT")
        tablo.setStyle(TableStyle([
            ("BACKGROUND",    (0,0), (-1,0),  colors.HexColor("#14532d")),
            ("TEXTCOLOR",     (0,0), (-1,0),  colors.white),
            ("FONTNAME",      (0,0), (-1,0),  "Helvetica-Bold"),
            ("FONTSIZE",      (0,0), (-1,-1), 7.5),
            ("ROWBACKGROUNDS",(0,1), (-1,-1), [colors.white, colors.HexColor("#f0fdf4")]),
            ("GRID",          (0,0), (-1,-1), 0.4, colors.HexColor("#1a3a1a")),
            ("TOPPADDING",    (0,0), (-1,-1), 3),
            ("BOTTOMPADDING", (0,0), (-1,-1), 3),
        ]))
        elements.append(KeepTogether(tablo))
    elements.append(Spacer(1, 14))
    elements.append(HRFlowable(width="100%", thickness=0.4,
                                color=colors.grey, spaceAfter=3))
    elements.append(Paragraph(
        "Bu rapor " + firma_adi + " tarafindan otomatik uretilmistir. "
        "Bilimsel karar verme sureclerinde uzman gorusu ile desteklenmelidir.",
        meta_s,
    ))
    try:
        doc.build(elements)
        return buf.getvalue()
    except Exception:
        return None


def pdf_indirme_butonu(
    icerik_md: str,
    baslik   : str = "Biovalent Raporu",
    tablo_df : Optional[pd.DataFrame] = None,
    dosya_adi: str = "biovalent_rapor.pdf",
) -> None:
    if _PDF_OK:
        pdf_bytes = pdf_uret(baslik, icerik_md, tablo_df)
        if pdf_bytes:
            st.download_button(
                label              = "PDF indir",
                data               = pdf_bytes,
                file_name          = dosya_adi,
                mime               = "application/pdf",
                use_container_width= True,
            )
        else:
            st.warning("PDF olusturulamadi. Markdown olarak indirebilirsiniz.", icon="warning")
    else:
        st.info("PDF icin 'pip install reportlab' gereklidir.", icon="info")
    st.download_button(
        label              = "Markdown indir",
        data               = icerik_md.encode("utf-8"),
        file_name          = dosya_adi.replace(".pdf",".md"),
        mime               = "text/markdown",
        use_container_width= True,
    )

# -----------------------------------------------------------------------------
# §11  PLOTLY GRAFiK YARDIMCILARI
# -----------------------------------------------------------------------------

def _lay(title: str = "", h: int = 380) -> Dict:
    return dict(
        title        = dict(text=title, font=dict(color=PAL["gold"], size=15)),
        paper_bgcolor= PLOTLY_BG,
        plot_bgcolor = "rgba(13,31,13,0.6)",
        font         = dict(color=PAL["txt"], family="Inter,Segoe UI,sans-serif"),
        xaxis        = dict(gridcolor=PAL["border"], zerolinecolor=PAL["border"],
                            tickfont=dict(color=PAL["txt_dim"])),
        yaxis        = dict(gridcolor=PAL["border"], zerolinecolor=PAL["border"],
                            tickfont=dict(color=PAL["txt_dim"])),
        legend       = dict(bgcolor="rgba(13,31,13,.85)", bordercolor=PAL["border"], borderwidth=1),
        margin       = dict(l=55, r=25, t=55, b=50),
        height       = h,
        hoverlabel   = dict(bgcolor=PAL["panel"], bordercolor=PAL["border"],
                            font=dict(color=PAL["txt"])),
    )


def fig_f_nesil(df_sim: pd.DataFrame, gen_adi: str) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_sim["Nesil"], y=df_sim["Dominant Fenotip (%)"],
        name="Dominant Fenotip", mode="lines+markers",
        line=dict(color=PAL["g_hi"], width=2.8),
        marker=dict(size=10, color=PAL["g_hi"], line=dict(color=PAL["bg"], width=2)),
        fill="tozeroy", fillcolor="rgba(74,222,128,0.07)",
        hovertemplate="%{x}: %{y:.2f}%<extra>Dominant</extra>",
    ))
    fig.add_trace(go.Scatter(
        x=df_sim["Nesil"], y=df_sim["Homozigot Oran (%)"],
        name="Homozigot Oran", mode="lines+markers",
        line=dict(color=PAL["gold"], width=2.8, dash="dot"),
        marker=dict(size=10, color=PAL["gold"]),
        hovertemplate="%{x}: %{y:.2f}%<extra>Homozigot</extra>",
    ))
    fig.add_hline(
        y=90, line_dash="dash", line_color=PAL["g_dim"],
        annotation_text="90% Esik (Ticari Hazir)",
        annotation_font_color=PAL["g_dim"],
    )
    layout = _lay("Sabitleme Simulasyonu - " + gen_adi, h=370)
    layout["yaxis"]["range"] = [-2, 105]
    layout["yaxis"]["title"] = "Oran (%)"
    fig.update_layout(**layout)
    return fig


def fig_pazar_radar(pazar: Dict) -> go.Figure:
    detay    = pazar.get("detay", {})
    kat      = ["Verim", "Raf Omru", "Brix/Kalite", "Direnc Geni", "Erken Hasat"]
    degerler = [
        detay.get("verim_p",  0),
        detay.get("raf_p",    0),
        detay.get("brix_p",   0),
        detay.get("direnc_p", 0),
        detay.get("erken_p",  0),
    ]
    fig = go.Figure(go.Scatterpolar(
        r     = degerler + [degerler[0]],
        theta = kat + [kat[0]],
        fill  = "toself",
        fillcolor = "rgba(74,222,128,0.15)",
        line  = dict(color=PAL["g_hi"], width=2),
        name  = "Puan",
    ))
    fig.update_layout(
        polar=dict(
            bgcolor     = "rgba(13,31,13,0.6)",
            radialaxis  = dict(visible=True, range=[0,30], gridcolor=PAL["border"],
                               tickfont=dict(color=PAL["txt_dim"])),
            angularaxis = dict(gridcolor=PAL["border"], tickfont=dict(color=PAL["gold"])),
        ),
        paper_bgcolor= PLOTLY_BG,
        height       = 320,
        showlegend   = False,
        title        = dict(
            text = "Pazar Uygunluk Radar - " + pazar.get("hedef_pazar","?").title(),
            font = dict(color=PAL["gold"], size=13),
        ),
        margin=dict(l=30, r=30, t=50, b=20),
    )
    return fig


def fig_motif_bar(motifler: List[Dict]) -> Optional[go.Figure]:
    if not motifler:
        return None
    sinif_renk = {
        "NBS-LRR"       : PAL["g_hi"],   "TIR-NBS"    : "#34d399",
        "CC-NBS"        : "#a7f3d0",     "Protein Kinaz": PAL["gold"],
        "TF-WRKY"       : PAL["blue"],   "TF-MYB"     : PAL["purple"],
        "TF-MADS"       : PAL["amber"],  "TF-ERF"     : "#f97316",
        "Zinc Finger"   : "#c084fc",     "PR Proteini": "#fb7185",
        "Tasiyici"      : PAL["txt_dim"],"Antioksidan": "#a3e635",
        "Chaperone"     : "#fbbf24",     "Antifroz"   : PAL["teal"],
        "InterPro/Pfam" : PAL["blue"],   "Pfam Domain": PAL["blue"],
    }
    renkler = [sinif_renk.get(m.get("sinif","?"), PAL["txt_dim"]) for m in motifler]
    fig = go.Figure(go.Bar(
        y   = [m.get("ad","?")[:30] for m in motifler],
        x   = [m.get("fuzzy_skor", 1.0) * 100 for m in motifler],
        orientation  = "h",
        marker       = dict(color=renkler, line=dict(color=PAL["border"], width=0.5)),
        text         = [m.get("eslesme_tipi","?") for m in motifler],
        textposition = "outside",
        textfont     = dict(color=PAL["gold"]),
        hovertemplate= "%{y}<br>Skor: %{x:.1f}%<extra></extra>",
    ))
    layout = _lay("Motif Analizi - Tam & Fuzzy Eslesmeler", h=max(300, len(motifler)*46))
    layout["yaxis"]["autorange"] = "reversed"
    layout["xaxis"]["range"]     = [0, 115]
    layout["xaxis"]["title"]     = "Eslesme Skoru (%)"
    fig.update_layout(**layout)
    return fig


def fig_heatmap(mat: pd.DataFrame) -> go.Figure:
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
            title     = "Jaccard",
            tickfont  = dict(color=PAL["txt"]),
            titlefont = dict(color=PAL["gold"]),
        ),
        hovertemplate="Hat-1:%{y}<br>Hat-2:%{x}<br>Benzerlik:%{z:.3f}<extra></extra>",
    ))
    layout = _lay("Genetik Akrabalik Isi Haritasi", h=max(440, len(mat)*26+120))
    layout["xaxis"]["tickangle"]        = -40
    layout["xaxis"]["tickfont"]["size"] = 8
    layout["yaxis"]["tickfont"]["size"] = 8
    fig.update_layout(**layout)
    return fig


def fig_vcf_dist(df_vcf: pd.DataFrame) -> go.Figure:
    qual_col = next((c for c in df_vcf.columns if c.upper()=="QUAL"), None)
    if not qual_col or df_vcf.empty:
        return go.Figure()
    q = pd.to_numeric(df_vcf[qual_col], errors="coerce").dropna()
    fig = go.Figure(go.Histogram(
        x      = q,
        nbinsx = 30,
        marker = dict(color=PAL["g_mid"], line=dict(color=PAL["border"], width=0.5)),
        hovertemplate="QUAL: %{x:.0f}<br>Sayi: %{y}<extra></extra>",
    ))
    layout = _lay("VCF Varyant Kalite Dagilimi (QUAL Score)", h=320)
    layout["xaxis"]["title"] = "QUAL Score"
    layout["yaxis"]["title"] = "Varyant Sayisi"
    fig.update_layout(**layout)
    return fig


def fig_nesil_kaybi(df_nesil: pd.DataFrame) -> go.Figure:
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Scatter(
        x=df_nesil["Nesil"], y=df_nesil["Homozigot Oran (%)"],
        name="Homozigot Oran", mode="lines+markers",
        line=dict(color=PAL["g_hi"], width=2.5),
        fill="tozeroy", fillcolor="rgba(74,222,128,0.07)",
    ), secondary_y=False)
    fig.add_trace(go.Scatter(
        x=df_nesil["Nesil"], y=df_nesil["Hedef Genotip (%)"],
        name="Hedef Genotip %", mode="lines+markers",
        line=dict(color=PAL["gold"], width=2.5, dash="dot"),
    ), secondary_y=False)
    fig.add_trace(go.Bar(
        x=df_nesil["Nesil"],
        y=df_nesil["Secim Havuzu (bitki)"].clip(upper=5000),
        name="Secim Havuzu (bitki, max 5K)",
        marker=dict(color="rgba(96,165,250,0.3)", line=dict(color=PAL["border"])),
        opacity=0.6,
    ), secondary_y=True)
    fig.add_hline(
        y=90, line_dash="dash", line_color=PAL["g_dim"],
        annotation_text="90% Esik", annotation_font_color=PAL["g_dim"],
    )
    fig.update_layout(
        paper_bgcolor= PLOTLY_BG,
        plot_bgcolor = "rgba(13,31,13,0.6)",
        font         = dict(color=PAL["txt"]),
        height       = 380,
        title        = dict(
            text = "Nesil Kaybi Tahmini & Secim Havuzu",
            font = dict(color=PAL["gold"], size=14),
        ),
        legend = dict(bgcolor="rgba(13,31,13,.85)", bordercolor=PAL["border"]),
        margin = dict(l=55, r=55, t=55, b=50),
    )
    fig.update_yaxes(title_text="Oran (%)", secondary_y=False,
                     gridcolor=PAL["border"], tickfont=dict(color=PAL["txt_dim"]))
    fig.update_yaxes(title_text="Secim Havuzu (bitki)", secondary_y=True,
                     tickfont=dict(color=PAL["blue"]))
    fig.update_xaxes(gridcolor=PAL["border"], tickfont=dict(color=PAL["txt_dim"]))
    return fig

# -----------------------------------------------------------------------------
# §12  SIDEBAR
# -----------------------------------------------------------------------------

def sidebar_yukle() -> pd.DataFrame:
    with st.sidebar:
        st.markdown(
            "<div style='text-align:center;padding:1.1rem 0 .6rem'>"
            "<div style='font-size:2.4rem'>&#x1F9EC;</div>"
            "<div style='color:#4ade80;font-weight:900;font-size:1.18rem;letter-spacing:2px'>"
            "BIOVALENT</div>"
            "<div style='color:#6b7280;font-size:.68rem;letter-spacing:3px;text-transform:uppercase'>"
            "Sentinel v" + VER + "</div>"
            "<div style='color:#fbbf24;font-size:.71rem;margin-top:6px;font-style:italic;opacity:.85'>"
            + SLOGAN + "</div>"
            "</div>",
            unsafe_allow_html=True,
        )

        st.markdown("---")
        st.markdown("### Veri Kaynagi")
        dosya = st.file_uploader(
            "Excel / CSV yukle",
            type=["xlsx","csv"],
            help=(
                "Beklenen sutunlar: hat_id, hat_adi, tur, verim, raf, hasat, brix, "
                "fusarium_I, tmv, nematod, rin, pto, ty1, sw5, mi12, "
                "*_cM, kok_guclu, soguk_dayanikli, kuralik_toleransi, etiketler"
            ),
        )
        df: Optional[pd.DataFrame] = None
        if dosya:
            try:
                df = pd.read_csv(dosya) if dosya.name.endswith(".csv") else pd.read_excel(dosya)
                st.success(str(len(df)) + " hat yuklendi.", icon="check")
            except Exception as exc:
                st.error("Okuma hatasi: " + str(exc), icon="x")
                df = None
        if df is None:
            df = demo_df()
            st.info("Demo veri seti aktif (" + str(len(demo_df())) + " hat).", icon="ℹ️")

        st.markdown("---")
        st.markdown("**Envanter**")
        kc1, kc2 = st.columns(2)
        kc1.metric("Hat #", len(df))
        kc2.metric("Tur #", df["tur"].nunique() if "tur" in df.columns else "?")
        if "verim" in df.columns:
            st.metric("Ort. Verim", str(round(df["verim"].mean(),1)) + " t/ha")

        st.markdown("---")
        st.markdown("**Servis Durumu**")
        ncbi_tag = "Aktif" if _BIO_OK else "Eksik (pip install biopython)"
        pdf_tag  = "Aktif" if _PDF_OK else "Eksik (pip install reportlab)"
        st.markdown(
            "- NCBI: " + ncbi_tag + "\n"
            "- PDF: " + pdf_tag + "\n"
            "- InterPro: Istek bazli\n"
            "- ESMFold: Istek bazli"
        )

        st.markdown("---")
        st.markdown(
            "<div style='color:#6b7280;font-size:.68rem;text-align:center;line-height:1.6'>"
            "&#169; " + str(datetime.now().year) + " Biovalent AgTech<br>"
            "Bagimsiz SaaS Platformu"
            "</div>",
            unsafe_allow_html=True,
        )
    return df

# -----------------------------------------------------------------------------
# §13  SEKME 1 - PROTEOMiK & MOTiF
# -----------------------------------------------------------------------------

def sekme_proteomik(df: pd.DataFrame) -> None:
    st.markdown("## Kuresel Motif Entegrasyonu & Protein Analizi")
    st.markdown(
        "DNA dizisini amino aside cevirir, **20 yerel motif + Fuzzy Matching** ile tarar. "
        "Isteğe bagli **InterPro/Pfam API** ve "
        "**ESMFold -> AlphaFold -> Yerel Tahmin** hibrit zinciri 3D yapi sunar."
    )

    DEMO_DNA = (
        "ATGGGCGTTGGCAAAACTACCATGCTTGCAGCTGATTTGCGTCAGAAGATGGCTGCAGAGCTGAAAGAT"
        "CGCTTTGCGATGGTGGATGGCGTGGGCGAAGTGGACTCTTTTGGCGACTTCCTCAAAACACTCGCAGAG"
        "GAGATCATTGGCGTCGTCAAAGATAGTAAACTCTATTTGTTGCTTCTTTTAAGTGGCAGGACTTGGCAT"
        "GTTGGGCGGCGTACTTGGCATTTCAATGGGCGGACAAGAAGTTCCTCATACCGAGAGAGAGTGGGCGTT"
    )

    col_giris, col_sonuc = st.columns([2, 3], gap="large")

    with col_giris:
        st.markdown("### DNA Girisi")
        kaynak = st.radio(
            "Kaynak",
            ["Demo Dizi (NBS-LRR)", "Elle Gir"],
            horizontal=True,
            key="p_src",
        )
        if kaynak == "Demo Dizi (NBS-LRR)":
            dna_in = DEMO_DNA
            st.code(DEMO_DNA[:80] + "...", language="text")
        else:
            dna_in = st.text_area(
                "DNA Dizisi (FASTA veya duz nukleotid)",
                placeholder=">GenAdi\nATGGGC...",
                height=130,
                key="p_dna",
            )

        st.markdown("**Analiz Parametreleri**")
        fuzzy_esik    = st.slider("Fuzzy Esik", 0.50, 0.95, 0.72, step=0.02, key="fzq",
                                  help="Dusuk deger daha toleransli; daha fazla benzer eslesme bulur")
        interpro_akif = st.checkbox("InterPro/Pfam API (yavas, ~30 sn)", value=False, key="ip_ak")
        goster_3d     = st.checkbox("3D Yapi (ESMFold -> AlphaFold fallback)", value=False, key="g3d")
        mol_stil      = st.selectbox("3D Stil", ["cartoon","stick","sphere","line"], key="mol_s")
        analiz_btn    = st.button("Analizi Baslat", key="p_btn", use_container_width=True)

    with col_sonuc:
        if analiz_btn:
            if not dna_in or len(dna_in.strip()) < 30:
                st.error("En az 30 nukleotid girin.", icon="x")
                return
       # --- 3D & ANALİZ PANELLERİ ---
        with tab_3d:
            st.subheader("3D Protein Yapısı - Yerel Fizik Motoru")
            
            # Hata veren 1617. satırın düzeltilmiş hali burada:
            if st.button("🧬 3D Yapıyı Simüle Et", use_container_width=True, key="local_3d_sim_key"):
                if aa:
                    try:
                        with st.spinner("Protein katlanma geometrisi hesaplanıyor..."):
                            # Koordinatları hesapla (82. satırdaki fonksiyon)
                            df_coords = yerel_3d_koordinat_olustur(aa)
                            
                            # Plotly ile Çizim
                            fig_3d = go.Figure(data=[go.Scatter3d(
                                x=df_coords['x'],
                                y=df_coords['y'],
                                z=df_coords['z'],
                                mode='lines+markers',
                                line=dict(color='#10b981', width=6),
                                marker=dict(
                                    size=5,
                                    color=df_coords['z'],
                                    colorscale='Viridis',
                                    opacity=0.9
                                ),
                                text=df_coords['aa'],
                                hoverinfo='text'
                            )])
                            
                            fig_3d.update_layout(
                                height=600,
                                margin=dict(l=0, r=0, b=0, t=0),
                                scene=dict(
                                    xaxis=dict(title='X (Å)', gridcolor='gray'),
                                    yaxis=dict(title='Y (Å)', gridcolor='gray'),
                                    zaxis=dict(title='Z (Å)', gridcolor='gray'),
                                    bgcolor="black"
                                ),
                                template="plotly_dark"
                            )
                            
                            st.plotly_chart(fig_3d, use_container_width=True)
                            st.success("✅ Yerel motor ile 3D yapı başarıyla oluşturuldu.")
                    except Exception as e:
                        st.error(f"3D Modelleme sırasında bir hata oluştu: {str(e)}")
                else:
                    st.warning("Analiz edilecek bir amino asit dizisi bulunamadı.")

        with tab_analiz:
            st.subheader("Gelişmiş Hat Analizi")
            if 'df' in locals() and len(df) > 1:
                st.write("### Genetik Benzerlik Isı Haritası (Jaccard)")
                if len(df) <= 30:
                    try:
                        ids = df["hat_id"].tolist()
                        mat_data = [
                            [jaccard(ozellik_seti(df.iloc[i]), ozellik_seti(df.iloc[j])) 
                             for j in range(len(df))] 
                            for i in range(len(df))
                        ]
                        mat = pd.DataFrame(mat_data, index=ids, columns=ids)
                        st.plotly_chart(fig_heatmap(mat), use_container_width=True)
                    except Exception as exc:
                        st.error(f"Isı haritası oluşturulurken bir hata oluştu: {exc}")
                else:
                    st.info("Isı haritası performansı korumak için en fazla 30 hat ile çalışır.")
            else:
                st.info("Karşılaştırmalı analiz için en az 2 hat gereklidir.")

# -----------------------------------------------------------------------------
# §14  SEKME 2 - BULK UPLOAD
# -----------------------------------------------------------------------------

def sekme_bulk_upload(df: pd.DataFrame) -> None:
    st.markdown("## Toplu Dosya Yukleme - FASTA / VCF / CSV")
    st.markdown(
        "`.fasta` dosyalarindan toplu protein analizi, `.vcf` dosyalarindan "
        "konum tabanli varyant analizi ve ozel `.csv` envanter yuklemesi."
    )

    alt1, alt2, alt3 = st.tabs(["FASTA Toplu Analiz", "VCF Varyant Analizi", "CSV Envanter"])

    # ---- FASTA ---------------------------------------------------------------
    with alt1:
        st.markdown("### Toplu FASTA Protein Analizi")
        fasta_mod = st.radio("Giris Modu", ["Dosya Yukle","Metin Yapistir"], horizontal=True, key="fa_mod")
        fasta_raw = ""
        if fasta_mod == "Dosya Yukle":
            fa_dosya = st.file_uploader("FASTA Dosyasi", type=["fasta","fa","fna","faa","txt"], key="fa_d")
            if fa_dosya:
                try:
                    fasta_raw = fa_dosya.read().decode("utf-8", errors="ignore")
                    st.success(fa_dosya.name + " yuklendi (" + str(len(fasta_raw)) + " karakter).")
                except Exception as exc:
                    st.error("Okuma hatasi: " + str(exc))
        else:
            fasta_raw = st.text_area(
                "FASTA Icerigi",
                height=180,
                placeholder=">Gene1 Fusarium resistance\nATGGGCGTT...\n>Gene2 TMV resistance\nATGCTTGCA...",
                key="fa_txt",
            )

        fuzzy_fasta = st.slider("Fuzzy Esik (FASTA)", 0.50, 0.95, 0.70, step=0.02, key="fa_fz")

        if st.button("Toplu Analizi Baslat", key="fa_btn", use_container_width=True):
            if not fasta_raw.strip():
                st.warning("FASTA verisi bos.")
                return
            try:
                with st.spinner("FASTA dosyasi ayristiriliyor..."):
                    kayitlar = parse_fasta(fasta_raw)
                if not kayitlar:
                    st.error("Gecerli FASTA kaydi bulunamadi.")
                    return
                st.success(str(len(kayitlar)) + " sekans bulundu.")
                sonuc_listesi: List[Dict] = []
                progress = st.progress(0, text="Analiz ediliyor...")

                def _analiz_tek(kayit: Dict) -> Dict:
                    seq     = kayit["seq"]
                    dna_kar = sum(1 for c in seq if c in "ACGTUN")
                    aa      = dna_cevir(seq) if dna_kar / max(len(seq),1) > 0.80 else seq
                    if not aa or len(aa) < 10:
                        return {**kayit, "aa":aa, "bio":{}, "motif_sonuc":{},
                                "yorum":{"sinif":"Dizi cok kisa","ihtimal":0,"mod":"hata","aciklama":""}}
                    bio_p = biyofizik(aa)
                    mot_s = tam_motif_analizi(aa, fuzzy_esik=fuzzy_fasta, interpro_aktif=False)
                    yor   = akilli_yorum(mot_s, bio_p)
                    return {**kayit, "aa":(aa[:40]+"..." if len(aa)>40 else aa),
                            "bio":bio_p, "motif_sonuc":mot_s, "yorum":yor}

                with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
                    futures = {ex.submit(_analiz_tek, k): i for i,k in enumerate(kayitlar)}
                    for n_tam, future in enumerate(concurrent.futures.as_completed(futures)):
                        try:
                            sonuc_listesi.append(future.result())
                        except Exception:
                            pass
                        progress.progress(
                            (n_tam+1)/len(kayitlar),
                            text="Analiz: " + str(n_tam+1) + "/" + str(len(kayitlar)),
                        )
                progress.empty()

                ozet_rows = [{
                    "ID"            : s.get("id","?"),
                    "Tanim"         : s.get("desc","?")[:40],
                    "AA Uzunluk"    : s.get("bio",{}).get("uzunluk",0),
                    "Protein Sinifi": s.get("yorum",{}).get("sinif","?")[:35],
                    "Guven (%)"     : s.get("yorum",{}).get("ihtimal",0),
                    "Mod"           : s.get("yorum",{}).get("mod","?"),
                    "Motif Toplam"  : s.get("motif_sonuc",{}).get("toplam",0),
                    "pI"            : s.get("bio",{}).get("pi",0),
                    "MW (kDa)"      : s.get("bio",{}).get("mw_kDa",0),
                } for s in sonuc_listesi]

                ozet_df = pd.DataFrame(ozet_rows)
                st.dataframe(
                    ozet_df.style.background_gradient(subset=["Guven (%)"], cmap="Greens"),
                    use_container_width=True,
                )
                rapor_md = "# FASTA Toplu Analiz Raporu\n\n" + str(len(kayitlar)) + " sekans analiz edildi.\n\n---\n\n"
                for s in sonuc_listesi:
                    rapor_md += (
                        "## " + s.get("id","?") + "\n"
                        "- Sinif: " + s.get("yorum",{}).get("sinif","?") + "\n"
                        "- Guven: %" + str(s.get("yorum",{}).get("ihtimal",0)) + "\n"
                        "- pI: " + str(s.get("bio",{}).get("pi","?")) + "\n"
                        "- MW: " + str(s.get("bio",{}).get("mw_kDa","?")) + " kDa\n\n"
                    )
                pdf_indirme_butonu(rapor_md, "FASTA Toplu Analiz", ozet_df, "fasta_analiz.pdf")

            except Exception as exc:
                st.error("FASTA analiz hatasi: " + str(exc))
                st.code(traceback.format_exc())

    # ---- VCF -----------------------------------------------------------------
    with alt2:
        st.markdown("### VCF Varyant Analizi")
        vcf_mod = st.radio("VCF Giris", ["Dosya Yukle","Metin Yapistir"], horizontal=True, key="vcf_mod")
        vcf_raw = ""
        if vcf_mod == "Dosya Yukle":
            vcf_dosya = st.file_uploader("VCF Dosyasi", type=["vcf","txt"], key="vcf_d")
            if vcf_dosya:
                try:
                    vcf_raw = vcf_dosya.read().decode("utf-8", errors="ignore")
                    st.success(vcf_dosya.name + " yuklendi.")
                except Exception as exc:
                    st.error("Okuma hatasi: " + str(exc))
        else:
            vcf_raw = st.text_area(
                "VCF Icerigi",
                height=160,
                placeholder=(
                    "##fileformat=VCFv4.1\n"
                    "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\n"
                    "Chr01\t5200\t.\tA\tG\t55.0\tPASS\t.\n"
                ),
                key="vcf_txt",
            )

        if st.button("VCF Analiz Et", key="vcf_btn", use_container_width=True):
            if not vcf_raw.strip():
                st.warning("VCF verisi bos.")
                return
            try:
                with st.spinner("VCF ayristiriliyor..."):
                    df_vcf = parse_vcf(vcf_raw)
                if df_vcf.empty:
                    st.error("Gecerli VCF verisi bulunamadi.")
                    return
                analiz = vcf_varyant_analiz(df_vcf)
                m1,m2,m3,m4,m5 = st.columns(5)
                m1.metric("Toplam Varyant", analiz["toplam"])
                m2.metric("SNP",            analiz["snp"])
                m3.metric("INDEL",          analiz["indel"])
                m4.metric("Kromozom #",     len(analiz["kromozomlar"]))
                m5.metric("Ort. QUAL",      analiz["ort_qual"])
                if analiz["kromozomlar"]:
                    st.info("Kromozomlar: " + ", ".join(str(c) for c in analiz["kromozomlar"][:10]))
                try:
                    fig_q = fig_vcf_dist(df_vcf)
                    if fig_q.data:
                        st.plotly_chart(fig_q, use_container_width=True)
                except Exception:
                    pass
                with st.expander("VCF Ham Veri", expanded=False):
                    st.dataframe(df_vcf.head(50), use_container_width=True)

                # Koordinat eslestirme
                st.markdown("### Referans Genom Koordinat Eslestirmesi")
                pos_col = next((c for c in df_vcf.columns if c.upper()=="POS"), None)
                chr_col = next((c for c in df_vcf.columns if c.upper() in ("CHROM","CHR","#CHROM")), None)
                eslesme_rows: List[Dict] = []
                if pos_col and chr_col:
                    for _, var_row in df_vcf.head(20).iterrows():
                        chrom_val = str(var_row.get(chr_col,"")).replace("chr","Chr").strip()
                        pos_val   = float(var_row.get(pos_col,0) or 0)
                        if chrom_val in TOMATO_GENOME:
                            for gen in TOMATO_GENOME[chrom_val]:
                                gen_cm_pos = gen["cm"] * 1_000_000
                                mesafe     = abs(pos_val - gen_cm_pos)
                                if mesafe < 5_000_000:
                                    eslesme_rows.append({
                                        "Pozisyon"   : int(pos_val),
                                        "Kromozom"   : chrom_val,
                                        "Yakin Gen"  : gen["gen"],
                                        "Gen Islevi" : gen["islev"][:60],
                                        "cM Konumu"  : gen["cm"],
                                        "Mesafe (bp)": int(mesafe),
                                    })
                if eslesme_rows:
                    eslm_df = pd.DataFrame(eslesme_rows).sort_values("Mesafe (bp)")
                    st.dataframe(eslm_df, use_container_width=True)
                    st.success(str(len(eslesme_rows)) + " varyant yakin gen ile eslesti.")
                else:
                    st.info("Referans genlerle koordinat eslesmesi bulunamadi.")

                rapor_md = (
                    "# VCF Varyant Analiz Raporu\n\n"
                    "- Toplam Varyant: " + str(analiz["toplam"]) + "\n"
                    "- SNP: " + str(analiz["snp"]) + " | INDEL: " + str(analiz["indel"]) + "\n"
                    "- Ort. QUAL: " + str(analiz["ort_qual"]) + "\n"
                )
                pdf_indirme_butonu(rapor_md, "VCF Varyant Analiz", df_vcf.head(40), "vcf_analiz.pdf")

            except Exception as exc:
                st.error("VCF analiz hatasi: " + str(exc))
                st.code(traceback.format_exc())

    # ---- CSV Envanter --------------------------------------------------------
    with alt3:
        st.markdown("### CSV Envanter Yukleme")
        st.info(
            "Kendi hat envanterinizi sidebar'daki 'Veri Kaynagi' bolumunden yukleyebilirsiniz. "
            "Sistem otomatik olarak demo verisi yerine yüklenen dosyayi kullanir.",
        )
        with st.expander("Beklenen Sutun Formati", expanded=True):
            ornek = pd.DataFrame({
                "hat_id"    : ["BIO-001","BIO-002"],
                "hat_adi"   : ["Hat A","Hat B"],
                "tur"       : ["Solanum lycopersicum","Capsicum annuum"],
                "verim"     : [18.5, 14.2],
                "raf"       : [14, 18],
                "hasat"     : [72, 85],
                "brix"      : [5.2, 6.1],
                "fusarium_I": [1, 0],
                "tmv"       : [1, 1],
                "nematod"   : [0, 0],
                "fusarium_cM": [45.0, 18.0],
                "tmv_cM"    : [22.4, 18.0],
                "etiketler" : ["fusarium,tmv","tmv,kirmizi"],
            })
            st.dataframe(ornek, use_container_width=True)

# -----------------------------------------------------------------------------
# §15  SEKME 3 - MATCHMAKER
# -----------------------------------------------------------------------------

def _standardize_trait(s: pd.Series, min_v: float, max_v: float) -> pd.Series:
    rng = max_v - min_v
    if rng == 0:
        return pd.Series(0.5, index=s.index)
    return ((s.fillna(min_v) - min_v) / rng).clip(0, 1)


def sekme_matchmaker(df: pd.DataFrame) -> None:
    st.markdown("## Sanal Eslestirme & Ebeveyn Optimizasyonu")
    st.markdown(
        "GBLUP mantığina dayali **Kantitatif Secim Indeksi** kullanarak, "
        "hedeflenen ozelliklere gore en yuksek genetik deger (EBV) tasiyan hatlari "
        "tamamlayici sekilde eslestirir. Icce evlenme (inbreeding) riskini minimize eder."
    )

    col_settings, col_results = st.columns([1, 2], gap="large")

    with col_settings:
        st.markdown("### Hedef Ozellikler & Agirliklar")
        hedef_verim = st.slider("Verim Agirligi",     0.0, 1.0, 0.30, step=0.05, key="w_verim")
        hedef_brix  = st.slider("Brix Agirligi",      0.0, 1.0, 0.20, step=0.05, key="w_brix")
        hedef_raf   = st.slider("Raf Omru Agirligi",  0.0, 1.0, 0.20, step=0.05, key="w_raf")
        st.markdown("**Direnc Agirliklari**")
        hedef_fus   = st.slider("Fusarium",            0.0, 1.0, 0.10, step=0.05, key="w_fus")
        hedef_tmv   = st.slider("TMV",                 0.0, 1.0, 0.05, step=0.05, key="w_tmv")
        hedef_nem   = st.slider("Nematod",             0.0, 1.0, 0.05, step=0.05, key="w_nem")
        hedef_kurak = st.slider("Kuraklık Toleransi", 0.0, 1.0, 0.10, step=0.05, key="w_kurak")

        agirliklar = {
            "verim"              : hedef_verim,
            "brix"               : hedef_brix,
            "raf"                : hedef_raf,
            "fusarium_I"         : hedef_fus,
            "tmv"                : hedef_tmv,
            "nematod"            : hedef_nem,
            "kuraklık_toleransi" : hedef_kurak,
        }
        inbreeding_penalty = st.slider(
            "Icce Evlenme Cezasi",
            0.0, 0.5, 0.25, step=0.05, key="penalty",
            help="Yuksek deger, genetik olarak cok benzer hatlarin eslesmesini engeller.",
        )
        top_n  = st.number_input("Gosterilecek En Iyi Cift Sayisi",
                                  min_value=5, max_value=50, value=10)
        run_btn = st.button("Eslestirmeyi Hesapla", use_container_width=True, key="mm_btn")

    with col_results:
        if run_btn:
            if len(df) < 2:
                st.warning("Eslestirme icin en az 2 hat gereklidir.")
                return

            with st.spinner("Kantitatif secim indeksi hesaplaniyor..."):
                df_calc = df.copy()
                if "verim"  in df.columns: df_calc["verim_z"] = _standardize_trait(df["verim"],  10.0, 30.0)
                if "brix"   in df.columns: df_calc["brix_z"]  = _standardize_trait(df["brix"],    3.0, 12.0)
                if "raf"    in df.columns: df_calc["raf_z"]   = _standardize_trait(df["raf"],     5.0, 30.0)

                toplam_agirlik = sum(agirliklar.values()) or 1.0
                df_calc["EBV"] = 0.0
                for trait, w in agirliklar.items():
                    col_z = trait + "_z" if (trait + "_z") in df_calc.columns else trait
                    if col_z in df_calc.columns:
                        df_calc["EBV"] += (df_calc[col_z] * w) / toplam_agirlik

                binary_traits = [
                    "fusarium_I","tmv","nematod","rin","pto","ty1",
                    "sw5","mi12","kok_guclu","soguk_dayanikli","kuraklık_toleransi",
                ]
                pairs: List[Dict] = []
                hat_ids = df_calc["hat_id"].tolist()
                n = len(hat_ids)
                for i in range(n):
                    for j in range(i + 1, n):
                        row_a = df_calc.iloc[i]
                        row_b = df_calc.iloc[j]
                        ebv_a = row_a["EBV"]
                        ebv_b = row_b["EBV"]
                        combined_ebv = (ebv_a + ebv_b) / 2.0
                        set_a = set(t for t in binary_traits if row_a.get(t, 0) == 1)
                        set_b = set(t for t in binary_traits if row_b.get(t, 0) == 1)
                        similarity = jaccard(set_a, set_b)
                        pair_score = combined_ebv * (1.0 - inbreeding_penalty * similarity)
                        pairs.append({
                            "Anne"             : hat_ids[i],
                            "Baba"             : hat_ids[j],
                            "EBV_Anne"         : round(ebv_a, 4),
                            "EBV_Baba"         : round(ebv_b, 4),
                            "Birlesik_EBV"     : round(combined_ebv, 4),
                            "Genetik_Benzerlik": round(similarity, 3),
                            "Eslesme_Skoru"    : round(pair_score, 4),
                        })

                pair_df = pd.DataFrame(pairs)
                if not pair_df.empty:
                    pair_df = pair_df.sort_values("Eslesme_Skoru", ascending=False).head(int(top_n))

                st.dataframe(
                    pair_df.style.background_gradient(
                        subset=["Eslesme_Skoru","Birlesik_EBV"], cmap="YlGnBu"
                    ).format({"Eslesme_Skoru":"{:.4f}","Birlesik_EBV":"{:.4f}"}),
                    use_container_width=True,
                    height=450,
                )

                if not pair_df.empty:
                    top_row = pair_df.iloc[0]
                    st.success(
                        "En Iyi Cift: " + str(top_row["Anne"]) + " x " + str(top_row["Baba"]) +
                        " (Skor: %" + str(round(top_row["Eslesme_Skoru"]*100, 1)) + ")"
                    )
                    a_idx = df[df["hat_id"] == top_row["Anne"]].index[0]
                    b_idx = df[df["hat_id"] == top_row["Baba"]].index[0]
                    traits_plot = [t for t in ["verim","brix","raf"] if t in df.columns]
                    vals_a = [df.iloc[a_idx].get(t, 0) for t in traits_plot]
                    vals_b = [df.iloc[b_idx].get(t, 0) for t in traits_plot]
                    fig_pair = go.Figure()
                    fig_pair.add_trace(go.Bar(
                        name        = str(df.iloc[a_idx].get("hat_adi","Anne")),
                        x           = traits_plot,
                        y           = vals_a,
                        marker_color= PAL["g_hi"],
                        offsetgroup = 0,
                    ))
                    fig_pair.add_trace(go.Bar(
                        name        = str(df.iloc[b_idx].get("hat_adi","Baba")),
                        x           = traits_plot,
                        y           = vals_b,
                        marker_color= PAL["gold"],
                        offsetgroup = 1,
                    ))
                    fig_pair.update_layout(
                        barmode      = "group",
                        paper_bgcolor= PLOTLY_BG,
                        plot_bgcolor = "rgba(13,31,13,0.6)",
                        font         = dict(color=PAL["txt"]),
                        title        = dict(
                            text = "Onerilen Ciftin Hedef Ozellik Karsilastirmasi",
                            font = dict(color=PAL["gold"], size=13),
                        ),
                        legend  = dict(bgcolor="rgba(13,31,13,.85)"),
                        yaxis   = dict(gridcolor=PAL["border"], tickfont=dict(color=PAL["txt_dim"])),
                        xaxis   = dict(gridcolor=PAL["border"], tickfont=dict(color=PAL["txt_dim"])),
                        margin  = dict(l=40, r=20, t=50, b=40),
                        height  = 350,
                    )
                    st.plotly_chart(fig_pair, use_container_width=True)

# -----------------------------------------------------------------------------
# §16  ANA CALISTIRMA BLOGU
# -----------------------------------------------------------------------------

def main() -> None:
    # Hero banner
    st.markdown(
        "<div class='bv-hero'>"
        "<div style='font-size:2.2rem;font-weight:900;color:#4ade80;'>&#x1F9EC; BIOVALENT SENTINEL</div>"
        "<div style='color:#fbbf24;font-size:1rem;margin-top:6px;letter-spacing:1px;font-weight:700;'>"
        "v" + VER + " - " + SLOGAN + "</div>"
        "</div>",
        unsafe_allow_html=True,
    )

    # Veri yukle
    df = sidebar_yukle()

    # Ana sekmeler
    tab1, tab2, tab3, tab4 = st.tabs([
        "Proteomik & Motif",
        "Toplu Yukleme (Bulk)",
        "Sanal Eslestirme",
        "Envanter & Linkage",
    ])

    with tab1:
        try:
            sekme_proteomik(df)
        except Exception as exc:
            st.error("Proteomik modul hatasi: " + str(exc))
            st.code(traceback.format_exc())

    with tab2:
        try:
            sekme_bulk_upload(df)
        except Exception as exc:
            st.error("Bulk Upload modul hatasi: " + str(exc))
            st.code(traceback.format_exc())

    with tab3:
        try:
            sekme_matchmaker(df)
        except Exception as exc:
            st.error("Matchmaker modul hatasi: " + str(exc))
            st.code(traceback.format_exc())

    with tab4:
        st.markdown("## Envanter Analizi & Linkage Risk Taramasi")
        st.markdown(
            "Mevcut envanterdeki hatlar arasi genetik benzerlik ve "
            "kromozomal yakinlik alarmlarini goruntuleyin."
        )

        # KPI metrikleri
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Toplam Hat", len(df))
        if "verim" in df.columns:
            m2.metric("Ort. Verim",  str(round(df["verim"].mean(),1)) + " t/ha")
        if "brix" in df.columns:
            m3.metric("Ort. Brix",   str(round(df["brix"].mean(),1)))
        if "raf" in df.columns:
            m4.metric("Ort. Raf",    str(round(df["raf"].mean(),0)) + " gun")

        # Linkage Drag
        st.markdown("### Linkage Drag & Yakinlik Alarmi")
        if len(df) >= 2:
            try:
                alarmlar = otonom_linkage_tara(df)
                if alarmlar:
                    st.warning(
                        str(len(alarmlar)) + " adet potansiyel linkage yakinligi tespit edildi. "
                        "Ilk alarm mesafesi: " + str(alarmlar[0]["mesafe_cM"]) + " cM."
                    )
                    alarm_df = pd.DataFrame([{
                        "Tur"        : a.get("tur","?"),
                        "Gen A"      : a.get("gen_a","?"),
                        "Gen B"      : a.get("gen_b","?"),
                        "Mesafe (cM)": a.get("mesafe_cM",0),
                        "Surukleme %": a.get("surukleme",0),
                        "Risk"       : a.get("seviye","?"),
                        "Gerekli Bitki": a.get("gerekli",0),
                    } for a in alarmlar])
                    st.dataframe(alarm_df.head(20), use_container_width=True)
                else:
                    st.success("Tespit edilen kritik linkage yakinligi bulunmuyor.")
            except Exception as exc:
                st.error("Linkage analizi hatasi: " + str(exc))

            # Jaccard isi haritasi
            if len(df) <= 30:
                st.markdown("### Genetik Benzerlik Isi Haritasi (Jaccard)")
                try:
                    ids = df["hat_id"].tolist()
                    mat_data = [
                        [jaccard(ozellik_seti(df.iloc[i]), ozellik_seti(df.iloc[j]))
                         for j in range(len(df))]
                        for i in range(len(df))
                    ]
                    mat = pd.DataFrame(mat_data, index=ids, columns=ids)
                    st.plotly_chart(fig_heatmap(mat), use_container_width=True)
                except Exception as exc:
                    st.error("Isi haritasi hatasi: " + str(exc))
            else:
                st.info("Isi haritasi performans koruma icin maks 30 hat ile calisir.")
        else:
            st.info("Linkage analizi icin en az 2 hat gereklidir.")

    # Footer
    st.markdown("---")
    st.markdown(
        "<div style='text-align:center;color:#6b7280;font-size:0.75rem;padding:1rem 0'>"
        "&#169; " + str(datetime.now().year) + " Biovalent AgTech Solutions. "
        "Bu sistem yalnizca arastirma ve karar destek amaclidir."
        "</div>",
        unsafe_allow_html=True,
    )

# -----------------------------------------------------------------------------
# §17  GiRiS NOKTASI
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error("Uygulama baslatılamadi: " + str(e))
        st.code(traceback.format_exc())

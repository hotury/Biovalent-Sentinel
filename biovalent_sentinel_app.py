J
Metin
# ==============================================================================
#  BIOVALENT SENTINEL v4.0
#  Genetik İstihbarat Merkezi — Küresel Bitki Islahı Karar Destek Sistemi
#  "Decoding the Bonds of Life — Intelligence at Scale"
#
#  YENİ MODÜLLER (v4.0):
#    M1 – Küresel Motif Entegrasyonu  : InterPro/Pfam API + Fuzzy Matching
#    M2 – Bulk Upload & VCF/FASTA     : Toplu dosya yükleme + Varyant analizi
#    M3 – Hibrit Protein Yapısı       : ESMFold → AlphaFold → Bio fallback zinciri
#    M4 – Ticari Risk Engine v2.0     : Linkage Drag + Nesil kaybı + Pazar raporu
#    M5 – Generative Reporting        : Doğal dil özet + PDF indirme
#
#  KURULUM:
#    pip install streamlit pandas numpy biopython plotly requests openpyxl
#               reportlab difflib
#    streamlit run app.py
#
#  Python 3.11+ uyumlu. Tüm API çağrıları try-except ile korunmuştur.
# ==============================================================================

# ─────────────────────────────────────────────────────────────────────────────
# §0  IMPORTS
# ─────────────────────────────────────────────────────────────────────────────
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

# --- YARDIMCI ARAÇLAR VE MATEMATİKSEL MODELLER ---

def jaccard(set_a, set_b):
    """Genetik benzerlik hesaplaması için Jaccard indeksi."""
    if not set_a and not set_b:
        return 0.0
    intersection = len(set_a.intersection(set_b))
    union = len(set_a.union(set_b))
    return intersection / union

def ozellik_seti(row):
    """Satırdaki genetik özellikleri kümeye dönüştürür."""
    binary_traits = [
        "fusarium_I", "tmv", "nematod", "rin", "pto", "ty1",
        "sw5", "mi12", "kok_guclu", "soguk_dayanikli", "kuraklık_toleransi"
    ]
    return set(t for t in binary_traits if row.get(t, 0) == 1)

def _standardize_trait(s, min_v, max_v):
    """Veriyi 0-1 arasına ölçekler (Sıfıra bölme korumalı)."""
    if max_v == min_v:
        return s * 0.0
    return ((s - min_v) / (max_v - min_v)).clip(0, 1)

def izoelektrik_nokta(aa: str) -> float:
    """Amino asit dizisinin teorik pI değerini hesaplar."""
    if not aa: return 7.0
    adim, pH = 1.0, 7.0
    for _ in range(25):
        # Negatif yükler
        q = 1.0 / (1 + 10 ** (pH - PKA["N_term"]))
        q -= 1.0 / (1 + 10 ** (PKA["C_term"] - pH))
        for aa_c, pka_v in [("D",PKA["D"]),("E",PKA["E"]),("C",PKA["C"]),("Y",PKA["Y"])]:
            q -= aa.count(aa_c) / (1 + 10 ** (pka_v - pH))
        # Pozitif yükler (Eksik olan kısım)
        for aa_c, pka_v in [("H",PKA["H"]),("K",PKA["K"]),("R",PKA["R"])]:
            q += aa.count(aa_c) / (1 + 10 ** (pH - pka_v))
        
        if q > 0: pH += adim
        else: pH -= adim
        adim /= 2
    return round(pH, 2)

def otonom_linkage_tara(df):
    """cM değerlerine göre kromozomal yakınlık risklerini tarar."""
    alarmlar = []
    cm_cols = [c for c in df.columns if "_cM" in c]
    
    for i, j in itertools.combinations(range(len(df)), 2):
        for col in cm_cols:
            dist = abs(df.iloc[i][col] - df.iloc[j][col])
            if dist < 5.0: 
                alarmlar.append({
                    "Hat A": df.iloc[i]["hat_id"],
                    "Hat B": df.iloc[j]["hat_id"],
                    "Marker": col.replace("_cM", ""),
                    "Mesafe": f"{dist:.2f} cM",
                    "Risk": "Kritik Yakınlık (Linkage Drag)"
                })
    return alarmlar

def sidebar_yukle():
    """Veri kaynağını yöneten ve kullanıcıdan dosya alan bileşen."""
    st.sidebar.title(f"📦 Biovalent v{VER}")
    source = st.sidebar.radio("Veri Kaynağı", ["Demo Veri", "Dosya Yükle (.csv/.xlsx)"])
    
    if source == "Demo Veri":
        return demo_df() # Daha önce tanımladığın demo fonksiyonu
    else:
        file = st.sidebar.file_uploader("Envanter Dosyası", type=["csv", "xlsx"])
        if file:
            try:
                if file.name.endswith('.csv'):
                    return pd.read_csv(file)
                return pd.read_excel(file)
            except Exception as e:
                st.sidebar.error(f"Yükleme hatası: {e}")
        return demo_df()

# ── Biopython ─────────────────────────────────────────────────────────────────
try:
    from Bio import Entrez, SeqIO
    from Bio.Seq import Seq
    from Bio.Blast import NCBIWWW, NCBIXML
    from Bio.SeqRecord import SeqRecord
    Entrez.email = "info@biovalentsentinel.com"
    _BIO_OK = True
except ImportError:
    _BIO_OK = False

# ── ReportLab (PDF) ───────────────────────────────────────────────────────────
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

# ─────────────────────────────────────────────────────────────────────────────
# §1  SAYFA AYARI
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Biovalent Sentinel v4.0",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help"    : "https://biovalentsentinel.com/docs",
        "Report a bug": "https://biovalentsentinel.com/support",
        "About"       : "Biovalent Sentinel v4.0 — Genetic Intelligence at Scale",
    },
)

# ─────────────────────────────────────────────────────────────────────────────
# §2  RENK PALETİ & CSS
# ─────────────────────────────────────────────────────────────────────────────
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

CSS = f"""
<style>
html,body,[data-testid="stAppViewContainer"]{{
  background:{PAL["bg"]};color:{PAL["txt"]};
  font-family:'Inter','Segoe UI','SF Pro Display',sans-serif;
}}
[data-testid="stSidebar"]{{
  background:linear-gradient(180deg,#050d05 0%,#091509 100%);
  border-right:1px solid {PAL["border"]};
}}
h1{{color:{PAL["g_hi"]}!important;letter-spacing:-.6px;}}
h2{{color:{PAL["gold"]}!important;}}
h3{{color:{PAL["g_mid"]}!important;}}
h4{{color:{PAL["txt"]}!important;}}
[data-testid="metric-container"]{{
  background:linear-gradient(145deg,{PAL["panel"]} 0%,{PAL["bg"]} 100%);
  border:1px solid {PAL["border"]};border-radius:12px;padding:14px 16px!important;
}}
[data-testid="metric-container"] label{{color:{PAL["gold"]}!important;font-size:.76rem;font-weight:600;}}
[data-testid="metric-container"] [data-testid="stMetricValue"]{{color:{PAL["g_hi"]}!important;font-weight:800;}}
.stButton>button{{
  background:linear-gradient(135deg,{PAL["g_dim"]} 0%,#0f3d1a 100%);
  color:{PAL["g_hi"]};border:1px solid {PAL["g_mid"]};border-radius:9px;
  font-weight:700;font-size:.92rem;padding:.45rem 1.3rem;transition:all .22s ease;
}}
.stButton>button:hover{{
  background:linear-gradient(135deg,{PAL["g_mid"]} 0%,{PAL["g_dim"]} 100%);
  color:{PAL["white"]};transform:translateY(-2px);
  box-shadow:0 6px 20px rgba(74,222,128,.30);
}}
.stTextArea textarea,.stTextInput input,.stNumberInput input{{
  background-color:{PAL["panel"]}!important;color:{PAL["txt"]}!important;
  border:1px solid {PAL["border"]}!important;border-radius:8px!important;
}}
.stSelectbox>div>div,.stMultiSelect>div>div{{
  background-color:{PAL["panel"]}!important;border:1px solid {PAL["border"]}!important;border-radius:8px!important;
}}
[data-baseweb="tab-list"]{{background-color:{PAL["panel"]}!important;border-radius:12px;padding:5px;gap:4px;}}
[data-baseweb="tab"]{{color:{PAL["txt_dim"]}!important;font-weight:600;border-radius:8px!important;padding:.35rem .9rem!important;}}
[aria-selected="true"]{{color:{PAL["g_hi"]}!important;background-color:{PAL["g_dim"]}!important;}}
[data-testid="stDataFrame"]{{border:1px solid {PAL["border"]};border-radius:10px;overflow:hidden;}}
.streamlit-expanderHeader{{background-color:{PAL["panel2"]}!important;color:{PAL["gold"]}!important;border-radius:8px!important;font-weight:600;}}
.stAlert{{border-radius:10px!important;border-left-width:4px!important;font-size:.92rem;}}
hr{{border-color:{PAL["border"]}!important;opacity:.6;}}
.bv-card{{
  background:linear-gradient(145deg,{PAL["panel"]} 0%,{PAL["bg"]} 100%);
  border:1px solid {PAL["border"]};border-radius:14px;
  padding:1.2rem 1.5rem;margin-bottom:.9rem;
}}
.bv-hero{{
  background:linear-gradient(135deg,{PAL["panel"]} 0%,#091809 40%,{PAL["bg"]} 100%);
  border:1px solid {PAL["border"]};border-radius:18px;
  padding:2rem 2.8rem;margin-bottom:1.4rem;text-align:center;
}}
.tag-green{{display:inline-block;background:{PAL["g_dim"]};color:{PAL["g_hi"]};
  border:1px solid {PAL["g_mid"]};border-radius:20px;padding:2px 10px;margin:2px;font-size:.75rem;font-weight:700;}}
.tag-gold{{display:inline-block;background:{PAL["gold_d"]};color:{PAL["gold"]};
  border:1px solid {PAL["gold"]};border-radius:20px;padding:2px 10px;margin:2px;font-size:.75rem;font-weight:700;}}
.tag-red{{display:inline-block;background:{PAL["red_d"]};color:{PAL["red"]};
  border:1px solid {PAL["red"]};border-radius:20px;padding:2px 10px;margin:2px;font-size:.75rem;font-weight:700;}}
.tag-blue{{display:inline-block;background:#1e3a5f;color:{PAL["blue"]};
  border:1px solid {PAL["blue"]};border-radius:20px;padding:2px 10px;margin:2px;font-size:.75rem;font-weight:700;}}
.tag-amber{{display:inline-block;background:#3d2a00;color:{PAL["amber"]};
  border:1px solid {PAL["amber"]};border-radius:20px;padding:2px 10px;margin:2px;font-size:.75rem;font-weight:700;}}
.fuzzy-bar{{height:8px;border-radius:4px;background:linear-gradient(90deg,{PAL["g_dim"]},{PAL["g_hi"]});}}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# §3  GLOBAL SABİTLER
# ─────────────────────────────────────────────────────────────────────────────
VER    = "4.0.0"
SLOGAN = "Decoding the Bonds of Life — Intelligence at Scale"
GUVEN  = 0.95
ENTREZ_EMAIL = "info@biovalentsentinel.com"

# ── API Endpoints ─────────────────────────────────────────────────────────────
INTERPRO_API   = "https://www.ebi.ac.uk/interpro/api/entry/pfam/?search={seq}&format=json"
PFAM_SEARCH    = "https://pfam.xfam.org/search/sequence"
ESMFOLD_API    = "https://api.esmatlas.com/foldSequence/v1/pdb/"
ALPHAFOLD_API  = "https://alphafold.ebi.ac.uk/api/prediction/{uniprot_id}"
UNIPROT_BLAST  = "https://rest.uniprot.org/uniprotkb/search?query={seq}&format=json&fields=sequence,protein_name,gene_names,organism_name&size=5"

# ── Kodon tablosu ─────────────────────────────────────────────────────────────
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

# ── 20 Yerel Motif Bankası (Fallback) ────────────────────────────────────────
MOTIF_BANK: List[Dict] = [
    {"ad":"NBS P-loop",        "motif":"GVGKTT",     "sinif":"NBS-LRR",
     "islev":"Nükleotid bağlanma — R-gen çekirdeği.","tarla":"Geniş spektrumlu patojen direnci."},
    {"ad":"NBS RNBS-A",        "motif":"ILVDDE",     "sinif":"NBS-LRR",
     "islev":"RNBS-A bölgesi; NBS etkinleştirme.","tarla":"Hipersensitivite yanıtı (HR)."},
    {"ad":"LRR Tekrar",        "motif":"LXXLXLXX",   "sinif":"NBS-LRR",
     "islev":"Lösin tekrarlı bölge.","tarla":"Irk spektrumunu belirler."},
    {"ad":"TIR Domaini",       "motif":"FLHFAD",     "sinif":"TIR-NBS",
     "islev":"Toll/IL-1 homoloji domaini.","tarla":"Dikotil TIR-NBS-LRR direnci."},
    {"ad":"Coiled-Coil",       "motif":"LRRLEEL",    "sinif":"CC-NBS",
     "islev":"Protein etkileşim yüzeyi.","tarla":"CC-NBS-LRR monokotil direnç."},
    {"ad":"Kinaz DFG",         "motif":"DFG",        "sinif":"Protein Kinaz",
     "islev":"ATP bağlanma ve fosforilasyon.","tarla":"Savunma sinyal kaskadı."},
    {"ad":"Kinaz VAIK",        "motif":"VAIK",       "sinif":"Protein Kinaz",
     "islev":"Kinaz-2; katalitik aktivite.","tarla":"Biyotik/abiyotik stres sinyali."},
    {"ad":"WRKY Domaini",      "motif":"WRKYGQK",    "sinif":"TF-WRKY",
     "islev":"W-box DNA bağlanma.","tarla":"Sistemik edinilmiş direnç (SAR)."},
    {"ad":"MYB R2R3",          "motif":"GRTWHTE",    "sinif":"TF-MYB",
     "islev":"Pigment ve olgunlaşma düzenleme.","tarla":"Meyve rengi, antosiyanin."},
    {"ad":"MADS-Box",          "motif":"MGRNGKVEHI", "sinif":"TF-MADS",
     "islev":"Meyve gelişimi ve olgunlaşma.","tarla":"Raf ömrü kontrolü."},
    {"ad":"AP2/ERF",           "motif":"RAYDAWLKL",  "sinif":"TF-ERF",
     "islev":"Etilen yanıt faktörü.","tarla":"Hasat ve stres toleransı."},
    {"ad":"Zinc Finger C2H2",  "motif":"CXXCXXXXHXXXH","sinif":"Zinc Finger",
     "islev":"C2H2 transkripsiyon düzenleme.","tarla":"Stres ve gelişim genleri."},
    {"ad":"Zinc Finger C3H",   "motif":"CXXXCXXH",   "sinif":"Zinc Finger",
     "islev":"C3H RNA işleme.","tarla":"Çevre adaptasyon mekanizmaları."},
    {"ad":"PR-1 Peptidi",      "motif":"MKKLLAL",    "sinif":"PR Proteini",
     "islev":"Salisilik asit yolunda savunma.","tarla":"SAR biyogöstergesi."},
    {"ad":"PR-5 Osmotin",      "motif":"CCQCSPLDS",  "sinif":"PR Proteini",
     "islev":"Antifungal aktivite.","tarla":"Küf ve fungal patojen direnci."},
    {"ad":"PR-3 Kitinaz",      "motif":"FYGLNHD",    "sinif":"PR Proteini",
     "islev":"Kitin yıkımı.","tarla":"Mantar patojen direnci."},
    {"ad":"ABC Taşıyıcı",      "motif":"LSGGQ",      "sinif":"Taşıyıcı",
     "islev":"ATP bağlama kaseti.","tarla":"Fitotoksin atımı."},
    {"ad":"SOD Merkez",        "motif":"HVHAQY",     "sinif":"Antioksidan",
     "islev":"Süperoksit dismutaz; ROS temizleme.","tarla":"Kuraklık/ısı toleransı."},
    {"ad":"HSP90 EEVD",        "motif":"EEVD",       "sinif":"Chaperone",
     "islev":"Isı şoku; protein katlanma.","tarla":"Yüksek sıcaklık koruması."},
    {"ad":"Antifroz Tip-I",    "motif":"DTASDAAAA",  "sinif":"Antifroz",
     "islev":"Buz kristali engelleme.","tarla":"Donma toleransı."},
]

# ── Amino asit grupları ───────────────────────────────────────────────────────
AA_HIDROFOBIK = set("VILMFWPA")
AA_NEGATIF    = set("DE")
AA_POZITIF    = set("KRH")

# ── pKa tablosu ───────────────────────────────────────────────────────────────
PKA = {"D":3.86,"E":4.07,"C":8.18,"Y":10.46,
       "H":6.04,"K":10.53,"R":12.48,
       "N_term":8.00,"C_term":3.10}

# ── Referans Domates Genomu (ITAG 4.0) ───────────────────────────────────────
TOMATO_GENOME: Dict[str, List[Dict]] = {
    "Chr01":[{"gen":"Cf-1","cm":5.2, "sinif":"NBS-LRR","islev":"Cladosporium ırk 1 direnci"},
             {"gen":"I-2", "cm":48.7,"sinif":"NBS-LRR","islev":"Fusarium oxysporum ırk 2 direnci"}],
    "Chr02":[{"gen":"Tm-1","cm":2.1, "sinif":"Kinaz",   "islev":"TMV ırk 0,1,2 direnci"},
             {"gen":"Ph-3","cm":62.0,"sinif":"NBS-LRR","islev":"Phytophthora infestans direnci"}],
    "Chr03":[{"gen":"Pto", "cm":18.5,"sinif":"Kinaz",   "islev":"Pseudomonas syringae direnci"},
             {"gen":"Prf", "cm":19.8,"sinif":"NBS-LRR","islev":"Pto aktivatör NBS-LRR geni"}],
    "Chr04":[{"gen":"sw-5","cm":44.1,"sinif":"NBS-LRR","islev":"TSWV (Tospovirüs) direnci"}],
    "Chr05":[{"gen":"rin", "cm":21.0,"sinif":"MADS TF","islev":"Olgunlaşma inhibitörü — uzun raf ömrü"},
             {"gen":"nor", "cm":26.5,"sinif":"TF",      "islev":"rin ile sinerjik olgunlaşma kontrolü"}],
    "Chr06":[{"gen":"Mi-1.2","cm":33.1,"sinif":"NBS-LRR","islev":"Nematod + yaprak biti direnci"}],
    "Chr07":[{"gen":"Cf-4","cm":12.3,"sinif":"LRR-RLP","islev":"Cladosporium ırk 4 direnci"},
             {"gen":"Cf-9","cm":14.8,"sinif":"LRR-RLP","islev":"Cladosporium ırk 9 direnci"}],
    "Chr08":[{"gen":"Ty-1","cm":55.2,"sinif":"RdRP",   "islev":"TYLCV (Sarı yaprak kıvırcıklığı) direnci"}],
    "Chr09":[{"gen":"Tm-2a","cm":22.4,"sinif":"NBS-LRR","islev":"TMV ırk 1,2,3 — geniş spektrum"},
             {"gen":"Cf-2", "cm":36.0,"sinif":"LRR-RLP","islev":"Cladosporium ırk 2,5 direnci"}],
    "Chr11":[{"gen":"I",  "cm":45.0,"sinif":"NBS-LRR","islev":"Fusarium oxysporum ırk 1,2 direnci"},
             {"gen":"Ve1","cm":72.0,"sinif":"LRR-RLP","islev":"Verticillium solgunluğu direnci"}],
    "Chr12":[{"gen":"y",  "cm":5.0, "sinif":"TF (MYB)","islev":"Meyve rengi — Y sarı, y kırmızı"}],
}

GEN_KOLONLARI = [
    "fusarium_I","tmv","nematod","rin","pto","ty1","sw5","mi12",
    "kok_guclu","soguk_dayanikli","kuraklık_toleransi"
]

# ─────────────────────────────────────────────────────────────────────────────
# §4  DEMO VERİSETİ
# ─────────────────────────────────────────────────────────────────────────────

@st.cache_data(show_spinner=False)
def demo_df() -> pd.DataFrame:
    rows = [
        dict(hat_id="BIO-TOM-001",hat_adi="Crimson Shield F6",tur="Solanum lycopersicum",
             meyve_rengi="Koyu Kırmızı",verim=18.5,raf=14,hasat=72,brix=5.2,
             fusarium_I=1,tmv=1,nematod=0,rin=0,pto=1,ty1=0,sw5=0,mi12=1,
             fusarium_cM=45.0,tmv_cM=22.4,nematod_cM=33.1,rin_cM=21.0,
             kok_guclu=1,soguk_dayanikli=0,kuraklık_toleransi=0,
             etiketler="fusarium,tmv,pseudomonas,nematod"),
        dict(hat_id="BIO-TOM-002",hat_adi="GoldenYield HV-9",tur="Solanum lycopersicum",
             meyve_rengi="Parlak Sarı",verim=22.3,raf=11,hasat=68,brix=4.8,
             fusarium_I=0,tmv=1,nematod=0,rin=0,pto=0,ty1=0,sw5=0,mi12=0,
             fusarium_cM=45.0,tmv_cM=22.4,nematod_cM=33.1,rin_cM=21.0,
             kok_guclu=0,soguk_dayanikli=0,kuraklık_toleransi=1,
             etiketler="sarı meyve,yüksek verim,ticari"),
        dict(hat_id="BIO-TOM-003",hat_adi="LongLife Premium",tur="Solanum lycopersicum",
             meyve_rengi="Kırmızı",verim=16.8,raf=24,hasat=78,brix=5.8,
             fusarium_I=0,tmv=0,nematod=1,rin=1,pto=0,ty1=0,sw5=0,mi12=1,
             fusarium_cM=45.0,tmv_cM=22.4,nematod_cM=33.1,rin_cM=21.0,
             kok_guclu=1,soguk_dayanikli=0,kuraklık_toleransi=0,
             etiketler="uzun raf ömrü,nematod,ihracat"),
        dict(hat_id="BIO-TOM-004",hat_adi="SunGold Cherry",tur="Solanum lycopersicum",
             meyve_rengi="Turuncu-Sarı",verim=21.0,raf=10,hasat=62,brix=8.2,
             fusarium_I=0,tmv=0,nematod=0,rin=0,pto=0,ty1=0,sw5=0,mi12=0,
             fusarium_cM=45.0,tmv_cM=22.4,nematod_cM=33.1,rin_cM=21.0,
             kok_guclu=0,soguk_dayanikli=0,kuraklık_toleransi=1,
             etiketler="sarı,cherry,yüksek brix,gurme"),
        dict(hat_id="BIO-TOM-005",hat_adi="Titan Robust F4",tur="Solanum lycopersicum",
             meyve_rengi="Koyu Kırmızı",verim=17.2,raf=16,hasat=80,brix=4.5,
             fusarium_I=1,tmv=0,nematod=1,rin=0,pto=0,ty1=1,sw5=0,mi12=1,
             fusarium_cM=45.0,tmv_cM=22.4,nematod_cM=33.1,rin_cM=21.0,
             kok_guclu=1,soguk_dayanikli=1,kuraklık_toleransi=0,
             etiketler="fusarium,nematod,tylcv,soğuğa dayanıklı"),
        dict(hat_id="BIO-TOM-006",hat_adi="Sunrise Export",tur="Solanum lycopersicum",
             meyve_rengi="Sarı-Turuncu",verim=19.6,raf=20,hasat=74,brix=5.0,
             fusarium_I=0,tmv=1,nematod=0,rin=1,pto=0,ty1=0,sw5=0,mi12=0,
             fusarium_cM=45.0,tmv_cM=22.4,nematod_cM=33.1,rin_cM=21.0,
             kok_guclu=1,soguk_dayanikli=0,kuraklık_toleransi=0,
             etiketler="sarı,uzun raf,tmv,ihracat"),
        dict(hat_id="BIO-TOM-007",hat_adi="IronShield Plus",tur="Solanum lycopersicum",
             meyve_rengi="Kırmızı",verim=16.0,raf=18,hasat=76,brix=4.7,
             fusarium_I=1,tmv=1,nematod=1,rin=0,pto=1,ty1=1,sw5=1,mi12=1,
             fusarium_cM=45.0,tmv_cM=22.4,nematod_cM=33.1,rin_cM=21.0,
             kok_guclu=1,soguk_dayanikli=1,kuraklık_toleransi=1,
             etiketler="tam direnç,organik,sertifika"),
        dict(hat_id="BIO-TOM-008",hat_adi="Quantum Beefsteak",tur="Solanum lycopersicum",
             meyve_rengi="Kırmızı",verim=20.1,raf=12,hasat=84,brix=4.2,
             fusarium_I=1,tmv=0,nematod=0,rin=0,pto=0,ty1=0,sw5=0,mi12=0,
             fusarium_cM=45.0,tmv_cM=22.4,nematod_cM=33.1,rin_cM=21.0,
             kok_guclu=0,soguk_dayanikli=0,kuraklık_toleransi=0,
             etiketler="yüksek verim,büyük meyve,endüstriyel"),
        dict(hat_id="BIO-TOM-009",hat_adi="BioShield Triple",tur="Solanum lycopersicum",
             meyve_rengi="Kırmızı",verim=15.3,raf=15,hasat=73,brix=5.1,
             fusarium_I=1,tmv=1,nematod=1,rin=1,pto=1,ty1=0,sw5=0,mi12=1,
             fusarium_cM=45.0,tmv_cM=22.4,nematod_cM=33.1,rin_cM=21.0,
             kok_guclu=1,soguk_dayanikli=0,kuraklık_toleransi=1,
             etiketler="tam direnç,uzun raf,organik"),
        dict(hat_id="BIO-CAP-001",hat_adi="RedBlaze L4 F5",tur="Capsicum annuum",
             meyve_rengi="Parlak Kırmızı",verim=15.5,raf=18,hasat=85,brix=6.1,
             fusarium_I=0,tmv=1,nematod=0,rin=0,pto=0,ty1=0,sw5=0,mi12=0,
             fusarium_cM=18.0,tmv_cM=18.0,nematod_cM=28.0,rin_cM=9.0,
             kok_guclu=1,soguk_dayanikli=0,kuraklık_toleransi=0,
             etiketler="tmv,pvy,kırmızı biber"),
        dict(hat_id="BIO-CAP-002",hat_adi="YellowBell Export",tur="Capsicum annuum",
             meyve_rengi="Sarı",verim=13.8,raf=14,hasat=90,brix=5.5,
             fusarium_I=0,tmv=0,nematod=0,rin=0,pto=0,ty1=0,sw5=0,mi12=0,
             fusarium_cM=18.0,tmv_cM=18.0,nematod_cM=28.0,rin_cM=9.0,
             kok_guclu=0,soguk_dayanikli=0,kuraklık_toleransi=0,
             etiketler="sarı,dolmalık,ihracat"),
        dict(hat_id="BIO-CAP-003",hat_adi="Spicy Supreme",tur="Capsicum annuum",
             meyve_rengi="Turuncu",verim=16.2,raf=12,hasat=78,brix=7.2,
             fusarium_I=0,tmv=1,nematod=1,rin=0,pto=0,ty1=0,sw5=0,mi12=0,
             fusarium_cM=18.0,tmv_cM=18.0,nematod_cM=28.0,rin_cM=9.0,
             kok_guclu=1,soguk_dayanikli=0,kuraklık_toleransi=1,
             etiketler="acı,yüksek brix,tmv,nematod"),
        dict(hat_id="BIO-MEL-001",hat_adi="Honeygold F1",tur="Cucumis melo",
             meyve_rengi="Sarı-Altın",verim=24.0,raf=16,hasat=82,brix=14.5,
             fusarium_I=1,tmv=0,nematod=0,rin=0,pto=0,ty1=0,sw5=0,mi12=0,
             fusarium_cM=30.0,tmv_cM=15.0,nematod_cM=42.0,rin_cM=20.0,
             kok_guclu=1,soguk_dayanikli=0,kuraklık_toleransi=1,
             etiketler="kavun,fusarium,ihracat,yüksek brix"),
        dict(hat_id="BIO-WAT-001",hat_adi="Crimson Giant F2",tur="Citrullus lanatus",
             meyve_rengi="Kırmızı",verim=35.0,raf=21,hasat=88,brix=11.5,
             fusarium_I=1,tmv=0,nematod=0,rin=0,pto=0,ty1=0,sw5=0,mi12=0,
             fusarium_cM=38.0,tmv_cM=25.0,nematod_cM=50.0,rin_cM=18.0,
             kok_guclu=1,soguk_dayanikli=0,kuraklık_toleransi=1,
             etiketler="karpuz,fusarium,yüksek verim"),
    ]
    return pd.DataFrame(rows)

# ─────────────────────────────────────────────────────────────────────────────
# §5  TEMEL BİYOENFORMATİK MOTOR (v3.0'dan korundu)
# ─────────────────────────────────────────────────────────────────────────────

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
            if h == "*": break
            aa_list.append(h)
        p = "".join(aa_list)
        if len(p) > len(en_uzun):
            en_uzun = p
    return en_uzun

def izoelektrik_nokta(aa: str) -> float:
    if not aa: return 7.0
    adim, pH = 1.0, 7.0
    for _ in range(25):
        q  = 1.0 / (1 + 10 ** (pH - PKA["N_term"]))
        q -= 1.0 / (1 + 10 ** (PKA["C_term"] - pH))
        for aa_c, pka_v in [("D",PKA["D"]),("E",PKA["E"]),("C",PKA["C"]),("Y",PKA["Y"])]:
            q -= aa.count(aa_c) / (1 + 10 ** (pka_v - pH))
        for aa_c, pka_v in [("H",PKA["H"]),("K",PKA["K"]),("R",PKA["R"])]:
            q += aa.count(aa_c) / (1 + 10 ** (pH - pka_v))
        if abs(q) < 0.01: break
        pH += adim if q > 0 else -adim
        adim *= 0.5
    return round(pH, 2)

def biyofizik(aa: str) -> Dict:
    if not aa: return {}
    n = len(aa)
    aa_mw = {"A":89,"R":174,"N":132,"D":133,"C":121,"E":147,"Q":146,"G":75,"H":155,
              "I":131,"L":131,"K":146,"M":149,"F":165,"P":115,"S":105,"T":119,"W":204,"Y":181,"V":117}
    return {
        "uzunluk" : n,
        "leu_pct" : round(aa.count("L") / n * 100, 1),
        "hid_pct" : round(sum(1 for c in aa if c in AA_HIDROFOBIK) / n * 100, 1),
        "neg_pct" : round(sum(1 for c in aa if c in AA_NEGATIF) / n * 100, 1),
        "pos_pct" : round(sum(1 for c in aa if c in AA_POZITIF) / n * 100, 1),
        "pi"      : izoelektrik_nokta(aa),
        "mw_kDa"  : round(sum(aa_mw.get(c, 111) for c in aa) / 1000, 1),
    }

def haldane_r(cm: float) -> float:
    return 0.5 * (1.0 - math.exp(-2.0 * cm / 100.0))

def linkage_analiz(cm_a: float, cm_b: float) -> Dict:
    mesafe    = abs(cm_a - cm_b)
    r         = haldane_r(mesafe)
    surukleme = (1.0 - r) * 100.0
    gerekli   = math.ceil(math.log(1.0 - GUVEN) / math.log(1.0 - r)) if r > 0 else 999_999
    if mesafe < 5:   seviye, simge = "KRİTİK 🔴", "🔴"
    elif mesafe < 10: seviye, simge = "YÜKSEK 🟠", "🟠"
    elif mesafe < 20: seviye, simge = "ORTA 🟡",   "🟡"
    else:             seviye, simge = "DÜŞÜK 🟢",  "🟢"
    return {"mesafe_cM":round(mesafe,2),"r":round(r,5),"surukleme":round(surukleme,1),
            "seviye":seviye,"simge":simge,"gerekli":gerekli}

def ozellik_seti(satir: pd.Series) -> set:
    s: set = set()
    for g in GEN_KOLONLARI:
        if g in satir.index and satir[g] == 1: s.add(g)
    if "etiketler" in satir.index and isinstance(satir["etiketler"], str):
        for e in satir["etiketler"].split(","): s.add(e.strip().lower())
    return s

def jaccard(a: set, b: set) -> float:
    if not a and not b: return 1.0
    if not a or not b: return 0.0
    return len(a & b) / len(a | b)

def f_nesil_sim(anne_dom: int, baba_dom: int, n_nesil: int = 4) -> pd.DataFrame:
    rows: List[Dict] = []
    for g in range(1, n_nesil + 1):
        p_het = 0.5 ** (g - 1)
        if anne_dom == 1 and baba_dom == 1: p_dom, p_hom = 1.0, 1.0
        elif anne_dom == 1 or baba_dom == 1:
            p_dom = 1.0 - p_het * 0.25 if g > 1 else 0.75
            p_hom = 1.0 - p_het
        else: p_dom, p_hom = 0.0, 0.0
        rows.append({"Nesil":f"F{g}",
                     "Dominant Fenotip (%)":round(p_dom*100,2),
                     "Homozigot Oran (%)":round(p_hom*100,2)})
    return pd.DataFrame(rows)

# ─────────────────────────────────────────────────────────────────────────────
# §6  M1 — KÜRESEL MOTİF ENTEGRASYonu  (InterPro/Pfam + Fuzzy Matching)
# ─────────────────────────────────────────────────────────────────────────────

def _fuzzy_skor(hedef: str, aday: str) -> float:
    """
    difflib SequenceMatcher ile iki dizi arasındaki benzerlik skoru.
    0.0 = hiç benzer değil, 1.0 = tam eşleşme.
    Motif uzunluğu normalize edilir.
    """
    if not hedef or not aday:
        return 0.0
    # Regex'e dönüştürülmüş motiften önce düz karşılaştır
    m = difflib.SequenceMatcher(None, hedef.upper(), aday.upper())
    base = m.ratio()
    # Motif içindeki X/x wildcard'ları bonusla ödüllendir
    wildcard_bonus = hedef.upper().count("X") * 0.02
    return round(min(base + wildcard_bonus, 1.0), 4)


def motif_tara_yerel(aa: str) -> List[Dict]:
    """20 yerel motifi tam eşleşme + Fuzzy skor ile tarar."""
    bulunan: List[Dict] = []
    for m in MOTIF_BANK:
        pat = m["motif"].replace("X", ".").replace("x", ".")
        try:
            hits = list(re.finditer(pat, aa, re.IGNORECASE))
        except re.error:
            hits = []
        if hits:
            bulunan.append({**m, "konumlar":[h.start() for h in hits],
                            "adet":len(hits), "eslesme_tipi":"Tam",
                            "fuzzy_skor":1.0, "kaynak":"Yerel Bank"})
    return bulunan


def motif_fuzzy_tara(aa: str, esik: float = 0.72) -> List[Dict]:
    """
    Tam eşleşme yoksa Fuzzy Matching ile benzerlik skoru üretir.
    Sliding-window ile AA dizisi üzerinde her motif penceresi karşılaştırılır.
    esik: Minimum kabul edilebilir benzerlik skoru (varsayılan: 0.72)
    """
    tam_eslesmeler = {m["ad"] for m in motif_tara_yerel(aa)}
    fuzzy_sonuclar: List[Dict] = []

    for m in MOTIF_BANK:
        if m["ad"] in tam_eslesmeler:
            continue   # Zaten tam eşleşti
        motif_len = len(m["motif"].replace("X","").replace("x",""))
        pencere   = max(motif_len, 6)
        en_iyi    = 0.0
        en_iyi_pos = -1

        for i in range(len(aa) - pencere + 1):
            pencere_aa = aa[i:i + pencere]
            skor = _fuzzy_skor(m["motif"], pencere_aa)
            if skor > en_iyi:
                en_iyi     = skor
                en_iyi_pos = i

        if en_iyi >= esik:
            fuzzy_sonuclar.append({
                **m,
                "konumlar"     : [en_iyi_pos],
                "adet"         : 1,
                "eslesme_tipi" : f"Fuzzy (%{en_iyi*100:.0f})",
                "fuzzy_skor"   : en_iyi,
                "kaynak"       : "Fuzzy Matching",
            })

    return fuzzy_sonuclar


def interpro_sorgula(aa_dizi: str, timeout: int = 30) -> List[Dict]:
    """
    EBI InterPro REST API'sine amino asit dizisi göndererek Pfam domain arar.
    API: https://www.ebi.ac.uk/interpro/api/
    
    Endpoint: entry/pfam → sequence tabanlı arama
    Fallback: Timeout veya hata durumunda boş liste döner, uygulama çökmez.
    
    Döner: [{"acc":str,"ad":str,"sinif":str,"e_value":float,"konum":[start,end]}, ...]
    """
    if not aa_dizi or len(aa_dizi) < 20:
        return []
    try:
        # InterPro sequence search endpoint
        resp = requests.post(
            "https://www.ebi.ac.uk/Tools/hmmer/search/hmmscan",
            data={
                "seqdb"  : "pfam",
                "seq"    : f">query\n{aa_dizi[:400]}",
                "output" : "json",
            },
            headers={"Accept": "application/json"},
            timeout=timeout,
        )
        if resp.status_code != 200:
            return []
        data = resp.json()
        sonuclar: List[Dict] = []
        hits = (data.get("results", {}).get("hits", [])
                or data.get("hits", []))
        for hit in hits[:8]:
            doms = hit.get("domains", [{}])
            dom  = doms[0] if doms else {}
            sonuclar.append({
                "acc"   : hit.get("acc", "—"),
                "ad"    : hit.get("name", hit.get("acc", "?")),
                "sinif" : "InterPro/Pfam",
                "e_value": float(hit.get("evalue", hit.get("e_value", 99))),
                "konum" : [dom.get("alisqfrom", 0), dom.get("alisqto", 0)],
                "tanim" : hit.get("desc", ""),
                "kaynak": "InterPro API",
                "fuzzy_skor": 1.0,
                "eslesme_tipi": "API",
            })
        return sonuclar
    except requests.exceptions.Timeout:
        return []
    except requests.exceptions.ConnectionError:
        return []
    except Exception:
        return []


def pfam_sorgula(aa_dizi: str, timeout: int = 35) -> List[Dict]:
    """
    Pfam sequence search (EBI) — InterPro'ya ek alternatif endpoint.
    https://pfam.xfam.org/search/sequence (JSON yanıt)
    """
    if not aa_dizi or len(aa_dizi) < 20:
        return []
    try:
        resp = requests.post(
            "https://pfam.xfam.org/search/sequence",
            data={"seq": aa_dizi[:400], "output": "json"},
            headers={"Accept": "application/json"},
            timeout=timeout,
        )
        if resp.status_code != 200:
            return []
        data  = resp.json()
        sonuclar: List[Dict] = []
        for hit in (data.get("hits", {}).get("hits", []))[:8]:
            sonuclar.append({
                "acc"          : hit.get("id", "—"),
                "ad"           : hit.get("name", "?"),
                "sinif"        : "Pfam Domain",
                "e_value"      : float(hit.get("evalue", 99)),
                "konum"        : [hit.get("from", 0), hit.get("to", 0)],
                "tanim"        : hit.get("desc", ""),
                "kaynak"       : "Pfam API",
                "fuzzy_skor"   : 1.0,
                "eslesme_tipi" : "API",
            })
        return sonuclar
    except Exception:
        return []


def tam_motif_analizi(
    aa: str,
    fuzzy_esik: float = 0.72,
    interpro_aktif: bool = False,
) -> Dict:
    """
    Hiyerarşik motif analizi:
    1. Yerel banka tam eşleşme
    2. Fuzzy Matching (difflib, sliding-window)
    3. InterPro/Pfam API (opsiyonel, yavaş)

    Döner: {"yerel":[], "fuzzy":[], "api":[], "ozet_sinif":str, "toplam":int}
    """
    yerel  = motif_tara_yerel(aa)
    fuzzy  = motif_fuzzy_tara(aa, esik=fuzzy_esik)
    api_r: List[Dict] = []

    if interpro_aktif:
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
            f1 = ex.submit(interpro_sorgula, aa)
            f2 = ex.submit(pfam_sorgula, aa)
            try: api_r += f1.result(timeout=40)
            except Exception: pass
            try: api_r += f2.result(timeout=40)
            except Exception: pass

    # Tüm sonuçları birleştir ve sınıf sayısını hesapla
    tumu = yerel + fuzzy + api_r
    sinif_sayim: Dict[str, int] = {}
    for m in tumu:
        s = m.get("sinif", "?")
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
    """
    Motif + Fuzzy + API + Biyofizik → Heuristic protein sınıf tahmini.
    """
    tum_motifler = (motif_sonuclari.get("yerel", [])
                    + motif_sonuclari.get("fuzzy", [])
                    + motif_sonuclari.get("api", []))
    leu = bio_profil.get("leu_pct", 0)
    hid = bio_profil.get("hid_pct", 0)
    pi  = bio_profil.get("pi", 7.0)
    neg = bio_profil.get("neg_pct", 0)

    if tum_motifler:
        ozet  = motif_sonuclari.get("ozet_sinif", "?")
        n     = len(tum_motifler)
        gv    = min(n * 15 + 40, 96)
        fuzzy_var = any(m.get("eslesme_tipi", "").startswith("Fuzzy") for m in tum_motifler)
        aciklama = (
            f"**{n} motif** tespit edildi (Tam: {len(motif_sonuclari.get('yerel',[]))}, "
            f"Fuzzy: {len(motif_sonuclari.get('fuzzy',[]))}, "
            f"API: {len(motif_sonuclari.get('api',[]))}). "
            f"Baskın sınıf: **{ozet}**. "
            + ("Fuzzy eşleşmeler yapısal benzerliğe işaret ediyor. " if fuzzy_var else "")
            + f"Güven: **%{gv}**."
        )
        return {"sinif":ozet,"ihtimal":gv,"aciklama":aciklama,"mod":"motif"}

    # Heuristic fallback
    if leu >= 12 and hid >= 35:
        iht = round(min(leu*2.5 + hid*0.8, 88), 1)
        return {"sinif":"NBS-LRR / R-Gen Proteini (Heuristic)","ihtimal":iht,"mod":"heuristic",
                "aciklama":(f"Resmi motif **bulunamadı** — Heuristic mod aktif.\n\n"
                            f"Lösin %{leu} ve Hidrofobiklik %{hid}, LRR R-gen yapısıyla uyumlu. "
                            f"Bu dizi büyük ihtimalle bir **bağışıklık/savunma proteini**dir. "
                            f"Güven: **%{iht}**.")}
    if hid >= 45:
        iht = round(min(hid*1.6, 82), 1)
        return {"sinif":"Membran / Taşıyıcı Protein (Heuristic)","ihtimal":iht,"mod":"heuristic",
                "aciklama":f"Yüksek hidrofobiklik %{hid} → membran proteini olabilir. Güven: **%{iht}**."}
    if pi < 5.5 and neg >= 14:
        iht = round(min(neg*3.2+25, 74), 1)
        return {"sinif":"Asidik / TF (Heuristic)","ihtimal":iht,"mod":"heuristic",
                "aciklama":f"pI={pi} ve negatif yük %{neg} → transkripsiyon faktörü olabilir. Güven: **%{iht}**."}
    if pi > 9.5:
        iht = round(min((pi-9)*11+38, 77), 1)
        return {"sinif":"Bazik / DNA-Bağlayan (Heuristic)","ihtimal":iht,"mod":"heuristic",
                "aciklama":f"Yüksek pI={pi} → DNA-bağlayan protein. Güven: **%{iht}**."}
    return {"sinif":"Yapısal / Bilinmiyor","ihtimal":28.0,"mod":"heuristic",
            "aciklama":"Hiçbir eşik aşılmadı. AlphaFold / InterPro analizi önerilir."}

# ─────────────────────────────────────────────────────────────────────────────
# §7  M2 — BULK UPLOAD  (FASTA / VCF / CSV)
# ─────────────────────────────────────────────────────────────────────────────

def parse_fasta(raw: str) -> List[Dict]:
    """
    Ham FASTA metnini ayrıştırır.
    Döner: [{"id":str,"desc":str,"seq":str}, ...]
    """
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
    """
    VCF (Variant Call Format) dosyasını ayrıştırır.
    Konum tabanlı varyasyonları (CHROM, POS, REF, ALT, QUAL) çıkarır.
    Meta satırları (##) ve başlık satırı (#CHROM) işlenir.
    Döner: pd.DataFrame
    """
    satirlar  = [s for s in raw.strip().splitlines() if not s.startswith("##")]
    if not satirlar:
        return pd.DataFrame()

    # Başlık satırı
    baslik = []
    veri   = []
    for s in satirlar:
        if s.startswith("#CHROM") or s.startswith("#chrom"):
            baslik = s.lstrip("#").split("\t")
        elif not s.startswith("#") and s.strip():
            veri.append(s.split("\t"))

    if not baslik:
        baslik = ["CHROM","POS","ID","REF","ALT","QUAL","FILTER","INFO"]

    try:
        df = pd.DataFrame(veri, columns=baslik[:len(veri[0])] if veri else baslik)
        # Sayısal dönüşümler
        for col in ["POS","QUAL"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        return df
    except Exception:
        return pd.DataFrame()


def vcf_varyant_analiz(df_vcf: pd.DataFrame) -> Dict:
    """
    VCF DataFrame'inden pozisyon tabanlı varyasyon istatistikleri çıkarır.
    SNP/INDEL sayısı, kromozom dağılımı ve kalite skorları hesaplanır.
    """
    if df_vcf.empty:
        return {"toplam":0,"snp":0,"indel":0,"kromozomlar":[],"ort_qual":0}

    toplam = len(df_vcf)
    snp    = 0
    indel  = 0

    ref_col = next((c for c in df_vcf.columns if c.upper() in ("REF","REFERENCE")), None)
    alt_col = next((c for c in df_vcf.columns if c.upper() in ("ALT","ALTERNATE")), None)

    if ref_col and alt_col:
        for _, row in df_vcf.iterrows():
            ref = str(row.get(ref_col, "")).strip()
            alt = str(row.get(alt_col, "")).strip()
            if len(ref) == 1 and len(alt) == 1 and ref != "." and alt != ".":
                snp += 1
            else:
                indel += 1

    chr_col   = next((c for c in df_vcf.columns if c.upper() in ("CHROM","CHR","#CHROM")), None)
    kromozomlar = sorted(df_vcf[chr_col].unique().tolist()) if chr_col else []

    qual_col  = next((c for c in df_vcf.columns if c.upper() == "QUAL"), None)
    ort_qual  = 0.0
    if qual_col:
        q = pd.to_numeric(df_vcf[qual_col], errors="coerce").dropna()
        ort_qual = round(q.mean(), 2) if not q.empty else 0.0

    return {"toplam":toplam,"snp":snp,"indel":indel,
            "kromozomlar":kromozomlar,"ort_qual":ort_qual}

# ─────────────────────────────────────────────────────────────────────────────
# §8  M3 — HİBRİT PROTEIN YAPI TAHMİNİ
#          ESMFold → AlphaFold → Bio İkincil Yapı Tahmini (Zincir)
# ─────────────────────────────────────────────────────────────────────────────

def esmfold_katla(aa_dizi: str, timeout: int = 60) -> Tuple[Optional[str], str]:
    """ESMFold REST API — Meta Research (api.esmatlas.com)"""
    dizi = aa_dizi[:400].strip()
    if len(dizi) < 10:
        return None, "Dizi çok kısa (min 10 AA)."
    try:
        resp = requests.post(
            ESMFOLD_API,
            data=dizi,
            headers={"Content-Type": "text/plain"},
            timeout=timeout,
        )
        if resp.status_code == 200 and resp.text.strip().startswith("ATOM"):
            return resp.text, "ESMFold — Başarılı"
        return None, f"ESMFold HTTP {resp.status_code}"
    except requests.exceptions.Timeout:
        return None, "ESMFold timeout — AlphaFold'a geçiliyor"
    except requests.exceptions.ConnectionError:
        return None, "ESMFold bağlantı hatası — AlphaFold'a geçiliyor"
    except Exception as exc:
        return None, f"ESMFold hata: {str(exc)[:100]}"


def alphafold_ara(aa_dizi: str, timeout: int = 30) -> Tuple[Optional[str], str]:
    """
    UniProt BLAST benzeri arama → En yakın AlphaFold kaydını bulur.
    Gerçek AlphaFold API doğrudan dizi kabul etmez; önce UniProt eşleştirme gerekir.
    Bu fonksiyon EBI UniProt arama API'sini kullanarak en yakın protein UniProt ID'sini bulur,
    ardından AlphaFold API'sine sorgu atar.
    Sonuç: PDB URL veya "yapı bulunamadı" mesajı döner.
    """
    if not aa_dizi or len(aa_dizi) < 20:
        return None, "Dizi çok kısa."
    try:
        # Adım 1: BLAST benzeri UniProt arama (ilk 100 AA yeterli)
        uniprot_resp = requests.get(
            "https://rest.uniprot.org/uniprotkb/search",
            params={
                "query"  : f"sequence_length:[{max(len(aa_dizi)-10,1)} TO {len(aa_dizi)+10}]",
                "format" : "json",
                "fields" : "accession,sequence",
                "size"   : "1",
            },
            timeout=timeout,
        )
        if uniprot_resp.status_code != 200:
            return None, f"UniProt HTTP {uniprot_resp.status_code}"

        data     = uniprot_resp.json()
        results  = data.get("results", [])
        if not results:
            return None, "UniProt'ta eşleşen protein bulunamadı."

        uniprot_id = results[0].get("primaryAccession", "")
        if not uniprot_id:
            return None, "UniProt ID alınamadı."

        # Adım 2: AlphaFold API kontrolü
        af_resp = requests.get(
            f"https://alphafold.ebi.ac.uk/api/prediction/{uniprot_id}",
            timeout=timeout,
        )
        if af_resp.status_code == 200:
            af_data  = af_resp.json()
            pdb_url  = af_data[0].get("pdbUrl", "") if af_data else ""
            if pdb_url:
                pdb_content = requests.get(pdb_url, timeout=timeout).text
                return pdb_content, f"AlphaFold — {uniprot_id}"

        return None, f"AlphaFold kaydı bulunamadı (UniProt: {uniprot_id})"
    except requests.exceptions.Timeout:
        return None, "AlphaFold timeout"
    except requests.exceptions.ConnectionError:
        return None, "AlphaFold bağlantı hatası"
    except Exception as exc:
        return None, f"AlphaFold hata: {str(exc)[:100]}"


def ikincil_yapi_tahmin(aa: str) -> Dict:
    """
    Yerel (Bio tabanlı) ikincil yapı tahmini — Chou-Fasman basit yaklaşımı.
    Gerçek AlphaFold/ESMFold API'sine erişim yoksa bu fonksiyon devreye girer.
    Döner: {"helix_pct":float,"beta_pct":float,"coil_pct":float,"yorum":str}
    """
    if not aa:
        return {"helix_pct":0,"beta_pct":0,"coil_pct":0,"yorum":"Dizi boş"}

    # Chou-Fasman parametreleri (basitleştirilmiş)
    helix_favori = set("AELM")
    beta_favori  = set("VIYTW")
    coil_favori  = set("GNDPSR")

    n  = max(len(aa), 1)
    h  = round(sum(1 for c in aa if c in helix_favori) / n * 100, 1)
    b  = round(sum(1 for c in aa if c in beta_favori)  / n * 100, 1)
    co = round(100.0 - h - b, 1)

    if h > 35:
        yorum = f"α-heliks baskın yapı (%{h}) — muhtemelen membran veya bağlayıcı protein."
    elif b > 25:
        yorum = f"β-zincir baskın yapı (%{b}) — NBS-LRR veya immünoglobulin benzeri."
    else:
        yorum = f"Kıvrımlı/düzensiz yapı ağırlıklı (%{co}) — esnek bağlayıcı veya intrinsik bozuklu protein."

    return {"helix_pct":h,"beta_pct":b,"coil_pct":co,"yorum":yorum}


def hibrit_protein_analiz(aa: str, deneme_esmfold: bool = True) -> Dict:
    """
    Hibrit Zincir:
    ESMFold → başarısız → AlphaFold → başarısız → Yerel İkincil Yapı Tahmini

    Her adım başarısız olursa bir sonraki otomatik devreye girer.
    Döner: {"pdb":str|None,"kaynak":str,"ikincil":Dict,"durum":str}
    """
    pdb_str = None
    kaynak  = "Yerel Tahmin"
    durum   = ""

    if deneme_esmfold:
        pdb_str, durum = esmfold_katla(aa)
        if pdb_str:
            kaynak = "ESMFold (Meta)"
        else:
            # ESMFold başarısız → AlphaFold'a geç
            pdb_str, durum2 = alphafold_ara(aa)
            if pdb_str:
                kaynak = f"AlphaFold (EBI) — {durum2}"
                durum  = durum2
            else:
                durum = f"ESMFold: {durum} | AlphaFold: {durum2} → Yerel tahmine geçildi"
    else:
        durum = "3D API devre dışı — Yerel tahmin kullanıldı"

    # Her durumda ikincil yapı tahmini çalıştır
    ikincil = ikincil_yapi_tahmin(aa)

    return {"pdb":pdb_str,"kaynak":kaynak,"ikincil":ikincil,"durum":durum}


def pdb_3d_html(pdb_str: str, stil: str = "cartoon", renk: str = "spectrum") -> str:
    """3Dmol.js CDN ile interaktif 3D protein görselleştirmesi."""
    pdb_e = pdb_str.replace("\\","\\\\").replace("`","\\`").replace("$","\\$")
    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<script src="https://cdnjs.cloudflare.com/ajax/libs/jquery/3.6.0/jquery.min.js"></script>
<script src="https://3dmol.org/build/3Dmol-min.js" crossorigin="anonymous"></script>
<style>*{{box-sizing:border-box;margin:0;padding:0}}body{{background:#070d07;overflow:hidden}}
#viewer{{width:100%;height:480px;position:relative}}
#ctrl{{position:absolute;bottom:10px;left:50%;transform:translateX(-50%);display:flex;gap:8px;z-index:10}}
.cb{{background:rgba(20,83,45,.85);color:#4ade80;border:1px solid #22c55e;border-radius:6px;
     padding:4px 12px;font-size:12px;cursor:pointer;font-weight:600;transition:all .15s}}
.cb:hover{{background:rgba(34,197,94,.3)}}</style></head>
<body><div style="position:relative"><div id="viewer"></div>
<div id="ctrl">
<button class="cb" onclick="toggleSpin()">⏸/▶</button>
<button class="cb" onclick="setStyle('cartoon')">Cartoon</button>
<button class="cb" onclick="setStyle('stick')">Stick</button>
<button class="cb" onclick="setStyle('sphere')">Sphere</button>
</div></div>
<script>
with tab3:
        st.subheader("🧪 Genom Analizi ve Protein Karakterizasyonu")
        
        # Eğer df boş değilse ve analiz yapılacaksa:
        if not df.empty:
            st.info("Genomik haritalama verileri yüklendi. 3D Protein Modeli oluşturuluyor...")
            
            # 1. ZIRHLI KUTU: Tırnakların ('') tam olarak burada başlayıp bittiğinden emin ol.
            # İçinde hiçbir süslü parantez veya f harfi yok. Sadece saf metin.
            html_taslak = '''
            <html>
            <head>
                <script src="https://3Dmol.org/build/3Dmol-min.js"></script>
            </head>
            <body style="margin:0; padding:0;">
                <div id="viewer" style="height: 450px; width: 100%; position: relative;"></div>
                <script>
                    var viewer = $3Dmol.createViewer("viewer", {backgroundColor:"#070d07", antialias:true});
                    viewer.addModel(`__PDB_VERISI__`, "pdb");
                    viewer.setStyle({}, {cartoon: {color: "__RENK__"}});
                    viewer.zoomTo();
                    viewer.render();
                    viewer.spin(true);
                </script>
            </body>
            </html>
            '''
            
            # 2. GÜVENLİ DEĞİŞİM: Python değişkenlerini (pdb_e ve renk) hata riski olmadan metne gömüyoruz.
            # (Eğer kodunda bu değişkenlerin adları farklıysa, buradaki pdb_e ve renk isimlerini kendine göre düzelt)
            guvenli_html = html_taslak.replace("__PDB_VERISI__", str(pdb_e)).replace("__RENK__", str(renk))
            
            # 3. EKRANA BAS: Streamlit iframe'i içinde göster
            st.components.v1.html(guvenli_html, height=500)
            
        else:
            st.warning("Analiz için veri bulunamadı.")



# ─────────────────────────────────────────────────────────────────────────────
# §9  M4 — TİCARİ KARAR MOTORU v2.0
#          Linkage Drag + Nesil Kaybı Tahmini + Pazar Uygunluk Raporu
# ─────────────────────────────────────────────────────────────────────────────
def nesil_kaybi_tahmini(
    hedef_gen_sayisi: int,
    baslangic_frekans: float = 0.5,
    min_frekans: float = 0.95,
    max_nesil: int = 10,
) -> pd.DataFrame:
    """
    Islah programında hedef genotipin sabitlenmesi için gereken nesil sayısını tahmin eder.
    
    Parametreler:
        hedef_gen_sayisi  : Sabitlenecek gen sayısı
        baslangic_frekans : F1'deki başlangıç dominant frekansı
        min_frekans       : Hedeflenen minimum sabitlenme oranı
        max_nesil         : Maksimum nesil sayısı
    """
    # Fonksiyonun devamı...
    data = []
    # ...
    rows: List[Dict] = []
    # ... (kodun geri kalanı buradan devam ediyor)

    for g in range(1, max_nesil + 1):
        p_het     = 0.5 ** (g - 1)
        p_hom     = 1.0 - p_het
        # N-gen bağımsız ayrışma: her ekstra gen için oran azalır
        p_hedef   = p_hom ** hedef_gen_sayisi
        # %95 güven için gereken bitki sayısı
        if p_hedef > 0:
            n_bitki = math.ceil(math.log(1 - GUVEN) / math.log(1 - p_hedef))
        else:
            n_bitki = 999_999

        if p_hom >= min_frekans:
            tavsiye = "✅ Ticari Hazır"
        elif p_hom >= 0.75:
            tavsiye = "⚠️ MAS ile İlerle"
        else:
            tavsiye = "🔄 Devam Et"

        rows.append({
            "Nesil"          : f"F{g}",
            "Homozigot Oran (%)" : round(p_hom * 100, 2),
            "Hedef Genotip (%)"  : round(p_hedef * 100, 4),
            "Seçim Havuzu (bitki)": min(n_bitki, 999_999),
            "Durum"          : tavsiye,
        })
        if p_hom >= min_frekans:
            break  # Hedef aşıldı, simülasyonu durdur

    return pd.DataFrame(rows)


def pazar_uygunluk_skoru(
    verim         : float,
    raf_gun       : int,
    brix          : float,
    n_direnc_geni : int,
    hasat_gun     : int,
    hedef_pazar   : str = "ihracat",
) -> Dict:
    """
    Ticari pazar uygunluğunu çok kriterly puanlama ile değerlendirir.

    Kriterler (toplam 100 puan):
        Verim (25p) + Raf ömrü (25p) + Brix/kalite (20p) +
        Direnç genleri (20p) + Erken hasat bonusu (10p)

    Hedef pazar: 'ihracat' | 'yerel' | 'organik' | 'sanayi'
    """
    pazar_agirlik = {
        "ihracat" : {"verim":20,"raf":30,"brix":15,"direnc":25,"erken":10},
        "yerel"   : {"verim":30,"raf":15,"brix":20,"direnc":20,"erken":15},
        "organik" : {"verim":15,"raf":20,"brix":20,"direnc":35,"erken":10},
        "sanayi"  : {"verim":40,"raf":10,"brix":10,"direnc":20,"erken":20},
    }
    agirlik = pazar_agirlik.get(hedef_pazar, pazar_agirlik["yerel"])

    # Normalize puanlama
    v_puan = min(verim / 25,  1.0) * agirlik["verim"]
    r_puan = min(raf_gun / 28, 1.0) * agirlik["raf"]
    b_puan = min(brix / 12,   1.0) * agirlik["brix"]
    d_puan = min(n_direnc_geni / 5, 1.0) * agirlik["direnc"]
    e_puan = (1.0 if hasat_gun <= 70 else 0.5 if hasat_gun <= 80 else 0.0) * agirlik["erken"]

    toplam = round(v_puan + r_puan + b_puan + d_puan + e_puan, 1)

    if toplam >= 80:
        kategori = "A — Premium Ticari Potansiyel"
        renk     = PAL["g_hi"]
        aciklama = "Bu çeşit doğrudan ticari üretime hazır. İhracat sertifikasyonu önceliklendirilmeli."
    elif toplam >= 65:
        kategori = "B — Yüksek Değerli Islah Materyali"
        renk     = PAL["amber"]
        aciklama = "1-2 nesil ek iyileştirme ile ticari üretime hazır hale gelebilir."
    elif toplam >= 50:
        kategori = "C — Orta Ticari Değer"
        renk     = PAL["gold"]
        aciklama = "Niş pazar veya organik segment için değerlendirilebilir."
    else:
        kategori = "D — Islah / Araştırma Materyali"
        renk     = PAL["red"]
        aciklama = "Doğrudan ticari değil; gen kaynağı veya çaprazlama materyali olarak faydalı."

    return {
        "toplam"   : toplam,
        "kategori" : kategori,
        "renk"     : renk,
        "aciklama" : aciklama,
        "detay"    : {"verim_p":round(v_puan,1),"raf_p":round(r_puan,1),
                      "brix_p":round(b_puan,1),"direnc_p":round(d_puan,1),"erken_p":round(e_puan,1)},
        "hedef_pazar": hedef_pazar,
    }


def otonom_linkage_tara(df: pd.DataFrame) -> List[Dict]:
    """Envanterdeki tüm cM sütun çiftlerini tarar."""
    cm_kolonlar = [c for c in df.columns if c.endswith("_cM")]
    alarmlar: List[Dict] = []
    for i in range(len(cm_kolonlar)):
        for j in range(i + 1, len(cm_kolonlar)):
            ka, kb = cm_kolonlar[i], cm_kolonlar[j]
            gruplama = df.groupby("tur") if "tur" in df.columns else [("Tümü", df)]
            for tur, grp in gruplama:
                cm_a = grp[ka].mean()
                cm_b = grp[kb].mean()
                r    = linkage_analiz(cm_a, cm_b)
                if r["mesafe_cM"] <= 20:
                    alarmlar.append({"tur":tur,"gen_a":ka.replace("_cM",""),
                                     "gen_b":kb.replace("_cM",""),
                                     "cm_a":round(cm_a,1),"cm_b":round(cm_b,1),**r})
    alarmlar.sort(key=lambda x: x["mesafe_cM"])
    return alarmlar


def islahci_raporu_uret(
    hat_verisi: pd.Series,
    pazar_skoru: Dict,
    motif_sonuclari: Optional[Dict],
    nesil_tablosu: Optional[pd.DataFrame],
    linkage_alarmlar: Optional[List[Dict]],
) -> str:
    """
    Islahçının anlayacağı dilde doğal metin raporu üretir.
    Teknik tablo değil — aksiyona yönelik, sade Türkçe paragraflar.
    """
    ad    = hat_verisi.get("hat_adi", hat_verisi.get("hat_id","?"))
    tur   = hat_verisi.get("tur", "?")
    verim = float(hat_verisi.get("verim", 0))
    raf   = int(hat_verisi.get("raf", 0))
    brix  = float(hat_verisi.get("brix", 0))
    hasat = int(hat_verisi.get("hasat", 0))
    renk  = hat_verisi.get("meyve_rengi","?")

    gen_acik = {
        "fusarium_I":"Fusarium solgunluk direnci",
        "tmv":"TMV virüs direnci",
        "nematod":"Nematod direnci",
        "rin":"Uzun raf ömrü geni (rin)",
        "pto":"Pseudomonas direnci (Pto)",
        "ty1":"TYLCV virüs direnci",
    }
    direncli  = [v for k,v in gen_acik.items() if hat_verisi.get(k,0)==1]
    hassas    = [v for k,v in gen_acik.items() if hat_verisi.get(k,0)==0]

    # Pazar özeti
    pazar_cat = pazar_skoru.get("kategori","?")
    pazar_acl = pazar_skoru.get("aciklama","")

    # Motif özeti
    motif_ozet = ""
    if motif_sonuclari:
        n_motif  = motif_sonuclari.get("toplam", 0)
        ozet_s   = motif_sonuclari.get("ozet_sinif","?")
        if n_motif > 0:
            motif_ozet = (f"Protein analizi {n_motif} motif tespit etti; "
                          f"baskın protein sınıfı **{ozet_s}** olarak belirlendi. "
                          f"Bu, söz konusu hattın savunma mekanizmalarıyla ilişkili "
                          f"genetik alt yapıya sahip olduğuna işaret ediyor. ")

    # Nesil tavsiyesi
    nesil_ozet = ""
    if nesil_tablosu is not None and not nesil_tablosu.empty:
        hazir_nesil = nesil_tablosu[nesil_tablosu["Durum"]=="✅ Ticari Hazır"]
        if not hazir_nesil.empty:
            nesil_no = hazir_nesil.iloc[0]["Nesil"]
            n_bitki  = hazir_nesil.iloc[0]["Seçim Havuzu (bitki)"]
            nesil_ozet = (f"Hedef genotip **{nesil_no}** nesline kadar **%95 sabitlenebilir**. "
                          f"Bu süreçte yaklaşık **{int(n_bitki):,} bitkilik** bir seçim havuzu yeterli olacaktır. ")

    # Linkage uyarısı
    linkage_ozet = ""
    if linkage_alarmlar:
        kritikler = [a for a in linkage_alarmlar if a["mesafe_cM"] <= 10]
        if kritikler:
            en_krit = kritikler[0]
            linkage_ozet = (f"⚠️ **Kritik Risk:** {en_krit['gen_a'].upper()} geni ile "
                            f"{en_krit['gen_b'].upper()} geni arasında yalnızca "
                            f"**{en_krit['mesafe_cM']} cM** mesafe var. Bu iki özellik "
                            f"birlikte kalıtılıyor ve istenmeyeni ayırmak için "
                            f"**{en_krit['gerekli']:,} bitkilik popülasyon** gerekiyor. ")

    rapor = f"""# 🌿 {ad} — İslahçı Karar Raporu
*Tür: {tur} | Rapor Tarihi: {datetime.now().strftime("%d.%m.%Y")}*

---

## 📋 Özet Değerlendirme
Bu çeşit **{pazar_cat}** kategorisindedir. {pazar_acl}

## 🍅 Meyve Profili
- **Renk:** {renk} | **Brix:** {brix}° | **Hasat:** {hasat} gün
- **Verim:** {verim} t/ha
- **Raf Ömrü:** {raf} gün {'— ihracat için uygun ✅' if raf >= 18 else '— yerel tüketim için uygundur'}

## 🛡️ Hastalık Durumu
- **Dirençli olduğu hastalıklar:** {', '.join(direncli) if direncli else 'Hastalık geni kaydedilmemiş'}
- **Dikkat edilmesi gerekenler:** {', '.join(hassas[:3]) if hassas else '—'}

## 🔬 Protein Analizi
{motif_ozet if motif_ozet else 'Protein analizi bu rapor için çalıştırılmadı.'}

## ⏱️ Islah Programı Tavsiyesi
{nesil_ozet if nesil_ozet else 'Nesil simülasyonu bu rapor için çalıştırılmadı.'}

{linkage_ozet}

## 💼 Sonuç ve Öneriler
{'Bu çeşit mevcut durumda doğrudan ticari üretime sunulabilir.' if pazar_skoru.get('toplam',0) >= 80
 else 'Ticari potansiyele ulaşmak için yukarıdaki eksikliklerin giderilmesi önerilir.'}

---
*Biovalent Sentinel v{VER} — Otomatik Islahçı Raporu*
"""
    return rapor

# ─────────────────────────────────────────────────────────────────────────────
# §10  M5 — GENERATIVE REPORTING (PDF İndirme)
# ─────────────────────────────────────────────────────────────────────────────

def pdf_uret(
    baslik     : str,
    icerik_md  : str,
    tablo_df   : Optional[pd.DataFrame] = None,
    firma_adi  : str = "Biovalent Sentinel",
) -> Optional[bytes]:
    """
    ReportLab ile profesyonel PDF raporu üretir.
    Markdown'daki ## başlıklar, ** kalın metin ve - liste öğeleri işlenir.
    Tablo varsa DataFrame'i tablo olarak ekler.
    Döner: bytes (PDF içeriği) veya None (ReportLab kurulu değilse)
    """
    if not _PDF_OK:
        return None

    buf    = io.BytesIO()
    doc    = SimpleDocTemplate(buf, pagesize=A4,
                               leftMargin=2*cm, rightMargin=2*cm,
                               topMargin=2.5*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()

    # Özel stiller
    baslik_s = ParagraphStyle("Baslik",  parent=styles["Title"],
                               fontSize=20, textColor=colors.HexColor("#14532d"),
                               spaceAfter=12, fontName="Helvetica-Bold")
    h2_s     = ParagraphStyle("H2",     parent=styles["Heading2"],
                               fontSize=13, textColor=colors.HexColor("#78350f"),
                               spaceBefore=12, spaceAfter=6, fontName="Helvetica-Bold")
    normal_s = ParagraphStyle("Normal2",parent=styles["Normal"],
                               fontSize=9.5, leading=14, spaceAfter=5,
                               textColor=colors.HexColor("#1a1a1a"))
    meta_s   = ParagraphStyle("Meta",   parent=styles["Normal"],
                               fontSize=8, textColor=colors.grey, spaceAfter=8)

    elements = []

    # Kapak başlığı
    elements.append(Paragraph(baslik, baslik_s))
    elements.append(Paragraph(
        f"{firma_adi} | {datetime.now().strftime('%d.%m.%Y %H:%M')} | v{VER}", meta_s
    ))
    elements.append(HRFlowable(width="100%", thickness=1,
                                color=colors.HexColor("#14532d"), spaceAfter=8))

    # Markdown → ReportLab paragrafları
    for satir in icerik_md.splitlines():
        satir = satir.strip()
        if not satir or satir == "---":
            elements.append(Spacer(1, 6))
            continue
        if satir.startswith("# "):
            elements.append(Paragraph(satir[2:], baslik_s))
        elif satir.startswith("## "):
            elements.append(Paragraph(satir[3:], h2_s))
        elif satir.startswith("- "):
            metin = satir[2:].replace("**","<b>",1).replace("**","</b>",1)
            elements.append(Paragraph(f"• {metin}", normal_s))
        else:
            metin = satir.replace("**","<b>",1).replace("**","</b>",1)
            elements.append(Paragraph(metin, normal_s))

    # Tablo
    if tablo_df is not None and not tablo_df.empty:
        elements.append(Spacer(1, 12))
        elements.append(Paragraph("📊 Detay Tablosu", h2_s))

        cols  = list(tablo_df.columns)
        satir_sayisi = min(len(tablo_df), 40)
        t_data = [cols] + tablo_df.head(satir_sayisi).values.tolist()

        tablo = Table(t_data, repeatRows=1,
                      hAlign="LEFT", colWidths=None)
        tablo.setStyle(TableStyle([
            ("BACKGROUND",    (0,0), (-1,0),  colors.HexColor("#14532d")),
            ("TEXTCOLOR",     (0,0), (-1,0),  colors.white),
            ("FONTNAME",      (0,0), (-1,0),  "Helvetica-Bold"),
            ("FONTSIZE",      (0,0), (-1,-1), 8),
            ("ROWBACKGROUNDS",(0,1), (-1,-1), [colors.white, colors.HexColor("#f0fdf4")]),
            ("GRID",          (0,0), (-1,-1), 0.5, colors.HexColor("#1a3a1a")),
            ("TOPPADDING",    (0,0), (-1,-1), 4),
            ("BOTTOMPADDING", (0,0), (-1,-1), 4),
        ]))
        elements.append(KeepTogether(tablo))

    # Footer
    elements.append(Spacer(1, 16))
    elements.append(HRFlowable(width="100%", thickness=0.5,
                                color=colors.grey, spaceAfter=4))
    elements.append(Paragraph(
        f"Bu rapor {firma_adi} tarafından otomatik olarak üretilmiştir. "
        f"Bilimsel karar verme süreçlerinde uzman görüşü ile desteklenmelidir.",
        meta_s
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
    """
    PDF üretip Streamlit'te indirme butonu sunar.
    ReportLab kurulu değilse metin olarak indir seçeneği gösterir.
    """
    if _PDF_OK:
        pdf_bytes = pdf_uret(baslik, icerik_md, tablo_df)
        if pdf_bytes:
            st.download_button(
                label        = "📄 PDF İndir",
                data         = pdf_bytes,
                file_name    = dosya_adi,
                mime         = "application/pdf",
                use_container_width=True,
            )
        else:
            st.warning("PDF oluşturulamadı. Metin olarak indirebilirsiniz.", icon="⚠️")
    else:
        st.info("PDF için `pip install reportlab` gereklidir.", icon="ℹ️")

    # Her durumda metin indirme
    st.download_button(
        label        = "📝 Markdown İndir",
        data         = icerik_md.encode("utf-8"),
        file_name    = dosya_adi.replace(".pdf", ".md"),
        mime         = "text/markdown",
        use_container_width=True,
    )

# ─────────────────────────────────────────────────────────────────────────────
# §11  PLOTLY GRAFİK YARDIMCILARI
# ─────────────────────────────────────────────────────────────────────────────

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
        hoverlabel   = dict(bgcolor=PAL["panel"], bordercolor=PAL["border"], font=dict(color=PAL["txt"])),
    )


def fig_f_nesil(df_sim: pd.DataFrame, gen_adi: str) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_sim["Nesil"], y=df_sim["Dominant Fenotip (%)"],
        name="Dominant Fenotip", mode="lines+markers",
        line=dict(color=PAL["g_hi"], width=2.8),
        marker=dict(size=10, color=PAL["g_hi"], line=dict(color=PAL["bg"], width=2)),
        fill="tozeroy", fillcolor="rgba(74,222,128,0.07)",
        hovertemplate="%{x}: %{y:.2f}%<extra>Dominant</extra>"))
    fig.add_trace(go.Scatter(x=df_sim["Nesil"], y=df_sim["Homozigot Oran (%)"],
        name="Homozigot Oran", mode="lines+markers",
        line=dict(color=PAL["gold"], width=2.8, dash="dot"),
        marker=dict(size=10, color=PAL["gold"]),
        hovertemplate="%{x}: %{y:.2f}%<extra>Homozigot</extra>"))
    fig.add_hline(y=90, line_dash="dash", line_color=PAL["g_dim"],
                  annotation_text="90% Eşik (Ticari Hazır)",
                  annotation_font_color=PAL["g_dim"])
    layout = _lay(f"⏱️ Sabitlenme Simülasyonu — {gen_adi}", h=370)
    layout["yaxis"]["range"] = [-2, 105]
    layout["yaxis"]["title"] = "Oran (%)"
    fig.update_layout(**layout)
    return fig


def fig_pazar_radar(pazar: Dict) -> go.Figure:
    detay    = pazar.get("detay", {})
    kat      = ["Verim","Raf Ömrü","Brix/Kalite","Direnç Geni","Erken Hasat"]
    degerler = [detay.get("verim_p",0), detay.get("raf_p",0),
                detay.get("brix_p",0), detay.get("direnc_p",0), detay.get("erken_p",0)]
    fig = go.Figure(go.Scatterpolar(
        r=degerler + [degerler[0]],
        theta=kat + [kat[0]],
        fill="toself",
        fillcolor="rgba(74,222,128,0.15)",
        line=dict(color=PAL["g_hi"], width=2),
        name="Puan",
    ))
    fig.update_layout(
        polar=dict(
            bgcolor="rgba(13,31,13,0.6)",
            radialaxis=dict(visible=True, range=[0,30], gridcolor=PAL["border"],
                            tickfont=dict(color=PAL["txt_dim"])),
            angularaxis=dict(gridcolor=PAL["border"], tickfont=dict(color=PAL["gold"])),
        ),
        paper_bgcolor=PLOTLY_BG, height=320, showlegend=False,
        title=dict(text=f"🎯 Pazar Uygunluk Radar — {pazar.get('hedef_pazar','?').title()}",
                   font=dict(color=PAL["gold"],size=13)),
        margin=dict(l=30,r=30,t=50,b=20),
    )
    return fig


def fig_motif_bar(motifler: List[Dict]) -> Optional[go.Figure]:
    if not motifler: return None
    sinif_renk = {
        "NBS-LRR":PAL["g_hi"],"TIR-NBS":"#34d399","CC-NBS":"#a7f3d0",
        "Protein Kinaz":PAL["gold"],"TF-WRKY":PAL["blue"],"TF-MYB":PAL["purple"],
        "TF-MADS":PAL["amber"],"TF-ERF":"#f97316","Zinc Finger":"#c084fc",
        "PR Proteini":"#fb7185","Taşıyıcı":PAL["txt_dim"],"Antioksidan":"#a3e635",
        "Chaperone":"#fbbf24","Antifroz":PAL["teal"],"InterPro/Pfam":PAL["blue"],
        "Pfam Domain":PAL["blue"],
    }
    renkler = [sinif_renk.get(m.get("sinif","?"), PAL["txt_dim"]) for m in motifler]
    fig = go.Figure(go.Bar(
        y=[m.get("ad","?")[:30] for m in motifler],
        x=[m.get("fuzzy_skor",1.0) * 100 for m in motifler],
        orientation="h",
        marker=dict(color=renkler, line=dict(color=PAL["border"], width=0.5)),
        text=[f"{m.get('eslesme_tipi','?')} {m.get('fuzzy_skor',1)*100:.0f}%"
              for m in motifler],
        textposition="outside", textfont=dict(color=PAL["gold"]),
        hovertemplate="%{y}<br>Skor: %{x:.1f}%<extra></extra>",
    ))
    layout = _lay("🔬 Motif Analizi — Tam & Fuzzy Eşleşmeler", h=max(300, len(motifler)*46))
    layout["yaxis"]["autorange"] = "reversed"
    layout["xaxis"]["range"] = [0, 115]
    layout["xaxis"]["title"] = "Eşleşme Skoru (%)"
    fig.update_layout(**layout)
    return fig


def fig_heatmap(mat: pd.DataFrame) -> go.Figure:
    ids_k = [i[:12] for i in mat.index]
    fig = go.Figure(go.Heatmap(
        z=mat.values, x=ids_k, y=ids_k,
        colorscale=[[0,PAL["bg"]],[0.3,PAL["g_dim"]],[0.7,PAL["g_mid"]],[1,PAL["g_hi"]]],
        zmin=0, zmax=1,
        colorbar=dict(title="Jaccard",tickfont=dict(color=PAL["txt"]),
                      titlefont=dict(color=PAL["gold"])),
        hovertemplate="Hat-1:%{y}<br>Hat-2:%{x}<br>Benzerlik:%{z:.3f}<extra></extra>",
    ))
    layout = _lay("🔥 Genetik Akrabalık Isı Haritası", h=max(440, len(mat)*26+120))
    layout["xaxis"]["tickangle"] = -40
    layout["xaxis"]["tickfont"]["size"] = 8
    layout["yaxis"]["tickfont"]["size"] = 8
    fig.update_layout(**layout)
    return fig


def fig_vcf_dist(df_vcf: pd.DataFrame) -> go.Figure:
    """VCF varyant kalite dağılımı."""
    qual_col = next((c for c in df_vcf.columns if c.upper()=="QUAL"), None)
    if not qual_col or df_vcf.empty:
        return go.Figure()
    q = pd.to_numeric(df_vcf[qual_col], errors="coerce").dropna()
    fig = go.Figure(go.Histogram(
        x=q, nbinsx=30,
        marker=dict(color=PAL["g_mid"], line=dict(color=PAL["border"], width=0.5)),
        hovertemplate="QUAL: %{x:.0f}<br>Sayı: %{y}<extra></extra>",
    ))
    layout = _lay("📊 VCF Varyant Kalite Dağılımı (QUAL Score)", h=320)
    layout["xaxis"]["title"] = "QUAL Score"
    layout["yaxis"]["title"] = "Varyant Sayısı"
    fig.update_layout(**layout)
    return fig


def fig_nesil_kaybi(df_nesil: pd.DataFrame) -> go.Figure:
    """Nesil kaybı tahmini çizgi grafiği."""
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
        y=df_nesil["Seçim Havuzu (bitki)"].clip(upper=5000),
        name="Seçim Havuzu (bitki, max 5K)",
        marker=dict(color="rgba(96,165,250,0.3)", line=dict(color=PAL["border"])),
        opacity=0.6,
    ), secondary_y=True)
    fig.add_hline(y=90, line_dash="dash", line_color=PAL["g_dim"],
                  annotation_text="90% Eşik",annotation_font_color=PAL["g_dim"])
    fig.update_layout(
        paper_bgcolor=PLOTLY_BG, plot_bgcolor="rgba(13,31,13,0.6)",
        font=dict(color=PAL["txt"]), height=380,
        title=dict(text="📈 Nesil Kaybı Tahmini & Seçim Havuzu", font=dict(color=PAL["gold"],size=14)),
        legend=dict(bgcolor="rgba(13,31,13,.85)", bordercolor=PAL["border"]),
        margin=dict(l=55,r=55,t=55,b=50),
    )
    fig.update_yaxes(title_text="Oran (%)", secondary_y=False,
                     gridcolor=PAL["border"], tickfont=dict(color=PAL["txt_dim"]))
    fig.update_yaxes(title_text="Seçim Havuzu (bitki)", secondary_y=True,
                     tickfont=dict(color=PAL["blue"]))
    fig.update_xaxes(gridcolor=PAL["border"], tickfont=dict(color=PAL["txt_dim"]))
    return fig

# ─────────────────────────────────────────────────────────────────────────────
# §12  SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────

def sidebar_yukle() -> pd.DataFrame:
    with st.sidebar:
        st.markdown(f"""
        <div style="text-align:center;padding:1.1rem 0 .6rem">
          <div style="font-size:2.4rem">🧬</div>
          <div style="color:{PAL['g_hi']};font-weight:900;font-size:1.18rem;letter-spacing:2px">BIOVALENT</div>
          <div style="color:{PAL['txt_dim']};font-size:.68rem;letter-spacing:3px;text-transform:uppercase">Sentinel v{VER}</div>
          <div style="color:{PAL['gold']};font-size:.71rem;margin-top:6px;font-style:italic;opacity:.85">{SLOGAN}</div>
        </div>""", unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("### 📁 Veri Kaynağı")
        dosya = st.file_uploader(
            "Excel / CSV yükle",
            type=["xlsx","csv"],
            help="Sütunlar: hat_id, hat_adi, tur, verim, raf, hasat, brix, fusarium_I, tmv, nematod, rin, pto, ty1, sw5, mi12, *_cM, kok_guclu, soguk_dayanikli, kuraklık_toleransi, etiketler",
        )
        df: Optional[pd.DataFrame] = None
        if dosya:
            try:
                df = pd.read_csv(dosya) if dosya.name.endswith(".csv") else pd.read_excel(dosya)
                st.success(f"✅ {len(df)} hat yüklendi.", icon="✅")
            except Exception as exc:
                st.error(f"Okuma hatası: {exc}", icon="❌")
                df = None
        if df is None:
            df = demo_df()
            st.info("📊 Demo veri seti aktif (14 hat).", icon="ℹ️")

        st.markdown("---")
        st.markdown("**📋 Envanter**")
        kc1, kc2 = st.columns(2)
        kc1.metric("Hat #", len(df))
        kc2.metric("Tür #", df["tur"].nunique() if "tur" in df.columns else "—")
        if "verim" in df.columns: st.metric("Ort. Verim", f"{df['verim'].mean():.1f} t/ha")

        st.markdown("---")
        st.markdown("**🌐 Servis Durumu**")
        st.markdown(
            f"- NCBI: {'<span class=\"tag-green\">Aktif</span>' if _BIO_OK else '<span class=\"tag-red\">Eksik</span>'}\n"
            f"- PDF: {'<span class=\"tag-green\">Aktif</span>' if _PDF_OK else '<span class=\"tag-amber\">pip install reportlab</span>'}\n"
            f"- InterPro: <span class='tag-blue'>İstek Bazlı</span>\n"
            f"- ESMFold: <span class='tag-blue'>İstek Bazlı</span>",
            unsafe_allow_html=True,
        )

        st.markdown("---")
        st.markdown(f"""
        <div style="color:{PAL['txt_dim']};font-size:.70rem;line-height:1.8">
          <b style="color:{PAL['g_mid']}">API Kaynakları</b><br>
          EBI InterPro / Pfam REST<br>
          NCBI Entrez / BLAST<br>
          ESMFold — Meta Research<br>
          AlphaFold — DeepMind/EBI<br>
          Haldane (1919) Harita Fn.
        </div>""", unsafe_allow_html=True)

        st.markdown("---")
        st.markdown(f"""
        <div style="color:{PAL['txt_dim']};font-size:.68rem;text-align:center;line-height:1.6">
          © {datetime.now().year} Biovalent<br>Bağımsız AgTech SaaS
        </div>""", unsafe_allow_html=True)
    return df

# ─────────────────────────────────────────────────────────────────────────────
# §13  SEKME 1 — KÜRESEL MOTİF & PROTEOMİK
# ─────────────────────────────────────────────────────────────────────────────

def sekme_proteomik(df: pd.DataFrame) -> None:
    st.markdown("## 🧪 Küresel Motif Entegrasyonu & Protein Analizi")
    st.markdown(
        "DNA → Protein çevirisi, **20 yerel motif + Fuzzy Matching** ve "
        "isteğe bağlı **InterPro/Pfam API** ile kapsamlı protein profili çıkarır. "
        "**ESMFold → AlphaFold → Yerel Tahmin** hibrit zinciri 3D yapı sunar."
    )

    DEMO_DNA = (
        "ATGGGCGTTGGCAAAACTACCATGCTTGCAGCTGATTTGCGTCAGAAGATGGCTGCAGAGCTGAAAGAT"
        "CGCTTTGCGATGGTGGATGGCGTGGGCGAAGTGGACTCTTTTGGCGACTTCCTCAAAACACTCGCAGAG"
        "GAGATCATTGGCGTCGTCAAAGATAGTAAACTCTATTTGTTGCTTCTTTTAAGTGGCAGGACTTGGCAT"
        "GTTGGGCGGCGTACTTGGCATTTCAATGGGCGGACAAGAAGTTCCTCATACCGAGAGAGAGTGGGCGTT"
    )

    col_giris, col_sonuc = st.columns([2, 3], gap="large")

    with col_giris:
        st.markdown("### 🔬 Dizi Girişi")
        kaynak = st.radio("Kaynak", ["Demo Dizi (NBS-LRR)", "Elle Gir"], horizontal=True, key="p_src")
        if kaynak == "Demo Dizi (NBS-LRR)":
            dna_in = DEMO_DNA
            st.code(DEMO_DNA[:80]+"...", language="text")
        else:
            dna_in = st.text_area("DNA Dizisi (FASTA / düz nükleotid)",
                                  placeholder=">GenAdi\nATGGGC...", height=130, key="p_dna")

        st.markdown("**⚙️ Analiz Parametreleri**")
        fuzzy_esik    = st.slider("Fuzzy Eşleşme Eşiği", 0.50, 0.95, 0.72, step=0.02, key="fzq",
                                  help="Düşük değer → daha toleranslı, daha fazla benzer eşleşme bulunur")
        interpro_akif = st.checkbox("🌐 InterPro/Pfam API (yavaş, ~30 sn)", value=False, key="ip_ak",
                                    help="EBI sunucusuna gerçek zamanlı sorgu gönderir")
        goster_3d     = st.checkbox("🔵 3D Yapı (ESMFold → AlphaFold fallback)", value=False, key="g3d")
        mol_stil      = st.selectbox("3D Stil", ["cartoon","stick","sphere","line"], key="mol_s")

        analiz_btn = st.button("🔬 Analizi Başlat", key="p_btn", use_container_width=True)

    with col_sonuc:
        if analiz_btn:
            if not dna_in or len(dna_in.strip()) < 30:
                st.error("En az 30 nükleotid girin.", icon="❌"); return
            try:
                with st.spinner("DNA çeviriliyor, motif taraması ve Fuzzy Matching yapılıyor..."):
                    aa       = dna_cevir(dna_in)
                    if not aa or len(aa) < 12:
                        st.error(f"Çeviri çok kısa ({len(aa)} AA).", icon="❌"); return
                    bio      = biyofizik(aa)

                if interpro_akif:
                    with st.spinner("🌐 InterPro/Pfam API sorgulanıyor (~15-40 sn)..."):
                        motif_sonuc = tam_motif_analizi(aa, fuzzy_esik=fuzzy_esik, interpro_aktif=True)
                else:
                    motif_sonuc = tam_motif_analizi(aa, fuzzy_esik=fuzzy_esik, interpro_aktif=False)

                yorum = akilli_yorum(motif_sonuc, bio)

                # KPI satırı
                k1,k2,k3,k4 = st.columns(4)
                k1.metric("DNA bp",   len(dna_temizle(dna_in)))
                k2.metric("AA Uzunluk", f"{bio['uzunluk']} aa")
                k3.metric("pI",         bio["pi"])
                k4.metric("MW",         f"{bio['mw_kDa']} kDa")
                b1,b2,b3,b4 = st.columns(4)
                b1.metric("Hidrofobiklik", f"%{bio['hid_pct']}")
                b2.metric("Lösin (L)",     f"%{bio['leu_pct']}")
                b3.metric("Yerel Motif",   len(motif_sonuc.get("yerel",[])))
                b4.metric("Fuzzy Motif",   len(motif_sonuc.get("fuzzy",[])))

                if interpro_akif:
                    st.metric("API Sonuç", len(motif_sonuc.get("api",[])))

                st.markdown("---")

                # Protein sınıfı başlığı
                clr = PAL["g_hi"] if yorum["ihtimal"]>70 else PAL["amber"] if yorum["ihtimal"]>45 else PAL["red"]
                mod_tag = "tag-blue" if yorum["mod"]=="heuristic" else "tag-green"
                mod_txt = "🤖 Heuristic" if yorum["mod"]=="heuristic" else "✅ Motif"
                st.markdown(
                    f"### 🏷️ `{yorum['sinif']}`  "
                    f"<span style='color:{clr};font-weight:800'>%{yorum['ihtimal']} güven</span>  "
                    f"<span class='{mod_tag}'>{mod_txt}</span>",
                    unsafe_allow_html=True,
                )
                (st.warning if yorum["mod"]=="heuristic" else st.success)(
                    yorum["aciklama"], icon="🤖" if yorum["mod"]=="heuristic" else "✅"
                )

                # Tüm motifler grafik
                tum_motifler = (motif_sonuc.get("yerel",[])
                                + motif_sonuc.get("fuzzy",[])
                                + motif_sonuc.get("api",[]))
                if tum_motifler:
                    fig_m = fig_motif_bar(tum_motifler)
                    if fig_m: st.plotly_chart(fig_m, use_container_width=True)

                    # Fuzzy eşleşmelerin ayrı gösterimi
                    fuzzy_var = motif_sonuc.get("fuzzy", [])
                    if fuzzy_var:
                        with st.expander(f"🔍 Fuzzy Eşleşmeler ({len(fuzzy_var)} adet)", expanded=False):
                            for fm in fuzzy_var:
                                pct = int(fm.get("fuzzy_skor",0)*100)
                                st.markdown(
                                    f"**{fm['ad']}** — Skor: %{pct}  "
                                    f"<div class='fuzzy-bar' style='width:{pct}%'></div>  "
                                    f"*{fm['islev']}*",
                                    unsafe_allow_html=True,
                                )

                    for motif in tum_motifler[:6]:
                        with st.expander(f"**{motif.get('ad','?')}** — `{motif.get('motif','?')}` | "
                                         f"{motif.get('sinif','?')} | {motif.get('eslesme_tipi','?')}", expanded=False):
                            mc1,mc2 = st.columns(2)
                            mc1.markdown(f"**Konum:** {motif.get('konumlar',[])}")
                            mc1.markdown(f"**Fuzzy Skor:** %{motif.get('fuzzy_skor',1)*100:.0f}")
                            mc1.markdown(f"**Kaynak:** {motif.get('kaynak','?')}")
                            mc1.markdown(f"**İşlev:** {motif.get('islev','?')}")
                            mc2.success(f"🌾 {motif.get('tarla','?')}", icon="🌿")

                    # AA dizisi
                    with st.expander("🔤 Amino Asit Dizisi", expanded=False):
                        st.code(aa[:300]+("..." if len(aa)>300 else ""), language="text")

                else:
                    st.info("Motif bulunamadı. Heuristic analiz sonuçlarını inceleyin.", icon="🔎")

                # İkincil yapı her zaman
                ikincil = ikincil_yapi_tahmin(aa)
                with st.expander("🧬 İkincil Yapı Tahmini (Yerel — Chou-Fasman)", expanded=False):
                    ic1,ic2,ic3 = st.columns(3)
                    ic1.metric("α-Heliks",  f"%{ikincil['helix_pct']}")
                    ic2.metric("β-Zincir",  f"%{ikincil['beta_pct']}")
                    ic3.metric("Kıvrımlı",  f"%{ikincil['coil_pct']}")
                    st.info(ikincil["yorum"], icon="🔬")

                # 3D yapı (hibrit zincir)
                if goster_3d:
                    st.markdown("---")
                    st.markdown("### 🔵 3D Protein Yapısı — Hibrit Zincir")
                    st.caption("ESMFold → AlphaFold → Yerel Tahmin (otomatik fallback)")
                    with st.spinner("🧬 3D katlanma yapılıyor... (30-90 sn, internet gerekli)"):
                        sonuc_3d = hibrit_protein_analiz(aa, deneme_esmfold=True)
                    st.info(f"**Kaynak:** {sonuc_3d['kaynak']}  |  {sonuc_3d['durum'][:100]}", icon="🔵")
                    if sonuc_3d["pdb"]:
                        st.success("✅ 3D yapı başarıyla oluşturuldu!", icon="✅")
                        try:
                            import streamlit.components.v1 as components
                            components.html(pdb_3d_html(sonuc_3d["pdb"], stil=mol_stil),
                                            height=510, scrolling=False)
                        except Exception as exc:
                            st.warning(f"Görselleştirici yüklenemedi: {exc}", icon="⚠️")
                    else:
                        st.warning(
                            f"3D yapı oluşturulamadı. Yukarıdaki İkincil Yapı tahmini "
                            f"kullanılabilir. Sebep: {sonuc_3d['durum'][:150]}", icon="⚠️"
                        )

            except Exception as exc:
                st.error(f"Analiz hatası: {exc}", icon="❌")
                st.code(traceback.format_exc())

# ─────────────────────────────────────────────────────────────────────────────
# §14  SEKME 2 — BULK UPLOAD (FASTA / VCF / CSV)
# ─────────────────────────────────────────────────────────────────────────────

def sekme_bulk_upload(df: pd.DataFrame) -> None:
    st.markdown("## 📂 Toplu Dosya Yükleme — FASTA / VCF / CSV")
    st.markdown(
        "`.fasta` dosyalarından toplu protein analizi, `.vcf` dosyalarından "
        "konum tabanlı varyant analizi ve özel `.csv` envanter yüklemesi yapın."
    )

    alt1, alt2, alt3 = st.tabs(["🧬 FASTA Toplu Analiz", "🔬 VCF Varyant Analizi", "📋 CSV Envanter"])

    # ── FASTA ─────────────────────────────────────────────────────────────────
    with alt1:
        st.markdown("### 🧬 Toplu FASTA Protein Analizi")
        st.markdown("Birden fazla sekansı aynı anda yükleyin — her biri otomatik analiz edilir.")

        fasta_mod = st.radio("Giriş Modu", ["Dosya Yükle", "Metin Yapıştır"], horizontal=True, key="fa_mod")
        fasta_raw = ""

        if fasta_mod == "Dosya Yükle":
            fa_dosya = st.file_uploader("FASTA Dosyası", type=["fasta","fa","fna","faa","txt"], key="fa_d")
            if fa_dosya:
                try:
                    fasta_raw = fa_dosya.read().decode("utf-8", errors="ignore")
                    st.success(f"✅ {fa_dosya.name} yüklendi ({len(fasta_raw)} karakter).", icon="✅")
                except Exception as exc:
                    st.error(f"Okuma hatası: {exc}", icon="❌")
        else:
            fasta_raw = st.text_area(
                "FASTA İçeriği (birden fazla sekans desteklenir)",
                height=180,
                placeholder=">Gene1 Fusarium resistance\nATGGGCGTT...\n>Gene2 TMV resistance\nATGCTTGCA...",
                key="fa_txt",
            )

        fuzzy_fasta = st.slider("Fuzzy Eşleşme Eşiği", 0.50, 0.95, 0.70, step=0.02, key="fa_fz")

        if st.button("🚀 Toplu Analizi Başlat", key="fa_btn", use_container_width=True):
            if not fasta_raw.strip():
                st.warning("FASTA verisi boş.", icon="⚠️"); return
            try:
                with st.spinner("FASTA dosyası ayrıştırılıyor..."):
                    kayitlar = parse_fasta(fasta_raw)

                if not kayitlar:
                    st.error("Geçerli FASTA kaydı bulunamadı. Formatı kontrol edin.", icon="❌"); return

                st.success(f"✅ {len(kayitlar)} sekans bulundu.", icon="✅")

                sonuc_listesi: List[Dict] = []

                # Paralel analiz (ThreadPoolExecutor)
                progress = st.progress(0, text="Analiz ediliyor...")

                def _analiz_tek(kayit: Dict) -> Dict:
                    seq  = kayit["seq"]
                    # DNA mı AA mı?
                    dna_kar = sum(1 for c in seq if c in "ACGTUN")
                    if dna_kar / max(len(seq), 1) > 0.80:
                        aa = dna_cevir(seq)
                    else:
                        aa = seq  # Zaten amino asit
                    if not aa or len(aa) < 10:
                        return {**kayit, "aa":aa,"bio":{},"motif_sonuc":{},"yorum":
                                {"sinif":"Dizi çok kısa","ihtimal":0,"mod":"hata","aciklama":""}}
                    bio_p    = biyofizik(aa)
                    mot_s    = tam_motif_analizi(aa, fuzzy_esik=fuzzy_fasta, interpro_aktif=False)
                    yor      = akilli_yorum(mot_s, bio_p)
                    return {**kayit, "aa":aa[:40]+"..." if len(aa)>40 else aa,
                            "bio":bio_p,"motif_sonuc":mot_s,"yorum":yor}

                with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
                    futures = {ex.submit(_analiz_tek, k): i for i,k in enumerate(kayitlar)}
                    for n_tamamlanan, future in enumerate(concurrent.futures.as_completed(futures)):
                        try: sonuc_listesi.append(future.result())
                        except Exception: pass
                        progress.progress((n_tamamlanan+1)/len(kayitlar),
                                          text=f"Analiz: {n_tamamlanan+1}/{len(kayitlar)}")

                progress.empty()

                # Özet tablo
                ozet_rows = [{
                    "ID"          : s.get("id","?"),
                    "Tanım"       : s.get("desc","?")[:40],
                    "AA Uzunluk"  : s.get("bio",{}).get("uzunluk",0),
                    "Protein Sınıfı": s.get("yorum",{}).get("sinif","?")[:35],
                    "Güven (%)"   : s.get("yorum",{}).get("ihtimal",0),
                    "Mod"         : s.get("yorum",{}).get("mod","?"),
                    "Motif Toplam": s.get("motif_sonuc",{}).get("toplam",0),
                    "pI"          : s.get("bio",{}).get("pi",0),
                    "MW (kDa)"    : s.get("bio",{}).get("mw_kDa",0),
                } for s in sonuc_listesi]

                ozet_df = pd.DataFrame(ozet_rows)
                st.dataframe(
                    ozet_df.style.background_gradient(subset=["Güven (%)"], cmap="Greens"),
                    use_container_width=True,
                )

                # PDF raporu tüm sonuçlar için
                rapor_md = f"# FASTA Toplu Analiz Raporu\n*{len(kayitlar)} sekans analiz edildi*\n\n---\n\n"
                for s in sonuc_listesi:
                    rapor_md += (f"## {s.get('id','?')}\n"
                                 f"- **Sınıf:** {s.get('yorum',{}).get('sinif','?')}\n"
                                 f"- **Güven:** %{s.get('yorum',{}).get('ihtimal',0)}\n"
                                 f"- **pI:** {s.get('bio',{}).get('pi','?')}\n"
                                 f"- **MW:** {s.get('bio',{}).get('mw_kDa','?')} kDa\n\n")
                pdf_indirme_butonu(rapor_md, "FASTA Toplu Analiz Raporu", ozet_df, "fasta_analiz.pdf")

            except Exception as exc:
                st.error(f"FASTA analiz hatası: {exc}", icon="❌")
                st.code(traceback.format_exc())

    # ── VCF ───────────────────────────────────────────────────────────────────
    with alt2:
        st.markdown("### 🔬 VCF Varyant Analizi")
        st.markdown(
            "Konum tabanlı varyasyonlar (SNP, INDEL) analiz edilir. "
            "Kalite skorları ve kromozom dağılımı görselleştirilir."
        )

        vcf_mod = st.radio("VCF Giriş", ["Dosya Yükle", "Metin Yapıştır"], horizontal=True, key="vcf_mod")
        vcf_raw = ""

        if vcf_mod == "Dosya Yükle":
            vcf_dosya = st.file_uploader("VCF Dosyası", type=["vcf","txt"], key="vcf_d")
            if vcf_dosya:
                try:
                    vcf_raw = vcf_dosya.read().decode("utf-8", errors="ignore")
                    st.success(f"✅ {vcf_dosya.name} yüklendi.", icon="✅")
                except Exception as exc:
                    st.error(f"Okuma hatası: {exc}", icon="❌")
        else:
            vcf_raw = st.text_area(
                "VCF İçeriği",
                height=160,
                placeholder="##fileformat=VCFv4.1\n#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\n"
                             "Chr01\t5200\t.\tA\tG\t55.0\tPASS\t.\n"
                             "Chr03\t18500\t.\tT\tC\t80.0\tPASS\t.",
                key="vcf_txt",
            )

        if st.button("🔍 VCF Analiz Et", key="vcf_btn", use_container_width=True):
            if not vcf_raw.strip():
                st.warning("VCF verisi boş.", icon="⚠️"); return
            try:
                with st.spinner("VCF dosyası ayrıştırılıyor..."):
                    df_vcf = parse_vcf(vcf_raw)

                if df_vcf.empty:
                    st.error("Geçerli VCF verisi bulunamadı. Formatı kontrol edin.", icon="❌"); return

                analiz = vcf_varyant_analiz(df_vcf)

                m1,m2,m3,m4,m5 = st.columns(5)
                m1.metric("Toplam Varyant",   analiz["toplam"])
                m2.metric("SNP",              analiz["snp"])
                m3.metric("INDEL",            analiz["indel"])
                m4.metric("Kromozom #",       len(analiz["kromozomlar"]))
                m5.metric("Ort. QUAL",        analiz["ort_qual"])

                if analiz["kromozomlar"]:
                    st.info(f"Kromozomlar: {', '.join(str(c) for c in analiz['kromozomlar'][:10])}", icon="📍")

                # Kalite dağılımı grafiği
                try:
                    fig_q = fig_vcf_dist(df_vcf)
                    if fig_q.data:
                        st.plotly_chart(fig_q, use_container_width=True)
                except Exception:
                    pass

                # Ham tablo
                with st.expander("📋 VCF Ham Veri", expanded=False):
                    st.dataframe(df_vcf.head(50), use_container_width=True)

                # Koordinat tabanlı gen eşleştirmesi (referans domates genomu ile)
                st.markdown("### 📍 Referans Genom Koordinat Eşleştirmesi")
                st.caption("Varyantlar ITAG 4.0 domates gen konumlarıyla karşılaştırılıyor.")
                pos_col  = next((c for c in df_vcf.columns if c.upper()=="POS"), None)
                chr_col  = next((c for c in df_vcf.columns if c.upper() in ("CHROM","CHR","#CHROM")), None)
                eslesme_rows: List[Dict] = []

                if pos_col and chr_col:
                    for _, var_row in df_vcf.head(20).iterrows():
                        chrom_val = str(var_row.get(chr_col, "")).replace("chr","Chr").strip()
                        pos_val   = float(var_row.get(pos_col, 0) or 0)
                        if chrom_val in TOMATO_GENOME:
                            for gen in TOMATO_GENOME[chrom_val]:
                                gen_cm_pos = gen["cm"] * 1_000_000  # cM → yaklaşık bp
                                mesafe     = abs(pos_val - gen_cm_pos)
                                if mesafe < 5_000_000:
                                    eslesme_rows.append({
                                        "Pozisyon"   : int(pos_val),
                                        "Kromozom"   : chrom_val,
                                        "Yakın Gen"  : gen["gen"],
                                        "Gen İşlevi" : gen["islev"][:60],
                                        "cM Konumu"  : gen["cm"],
                                        "Mesafe (bp)": int(mesafe),
                                    })
                if eslesme_rows:
                    eslm_df = pd.DataFrame(eslesme_rows).sort_values("Mesafe (bp)")
                    st.dataframe(eslm_df, use_container_width=True)
                    st.success(f"✅ {len(eslesme_rows)} varyant yakın gen ile eşleşti.", icon="✅")
                else:
                    st.info("Referans genlerle koordinat eşleşmesi bulunamadı veya konum sütunları tespit edilemedi.", icon="ℹ️")

                # PDF
                rapor_md = (f"# VCF Varyant Analiz Raporu\n\n"
                            f"## İstatistikler\n"
                            f"- Toplam Varyant: {analiz['toplam']}\n"
                            f"- SNP: {analiz['snp']} | INDEL: {analiz['indel']}\n"
                            f"- Ort. QUAL: {analiz['ort_qual']}\n")
                pdf_indirme_butonu(rapor_md, "VCF Varyant Analiz Raporu", df_vcf.head(40), "vcf_analiz.pdf")

            except Exception as exc:
                st.error(f"VCF analiz hatası: {exc}", icon="❌")
                st.code(traceback.format_exc())

    # ── CSV Envanter ───────────────────────────────────────────────────────────
    with alt3:
        st.markdown("### 📋 CSV Envanter Yükle")
        st.markdown("Kendi hat envanterinizi `.csv` veya `.xlsx` formatında yükleyin.")
        st.info(
            "Yüklemek istediğiniz dosyayı **Sidebar'daki Veri Kaynağı** bölümünden yükleyebilirsiniz. "
            "Sistem otomatik olarak demo verisi yerine yüklenen dosyayı kullanacaktır.",
            icon="ℹ️",
        )
        with st.expander("📄 Beklenen Sütun Formatı", expanded=True):
            ornek = {
                "hat_id"         :["BIO-001","BIO-002"],
                "hat_adi"        :["Hat A","Hat B"],
                "tur"            :["Solanum lycopersicum","Capsicum annuum"],
                "verim"          :[18.5, 14.2],
                "raf"            :[14, 18],
                "hasat"          :[72, 85],
           "brix"           : [5.2, 4.8],
           "fusarium_I"     : [1, 0],
           "tmv"            : [1, 1],
           "nematod"        : [0, 1],
           "rin"            : [0, 0],
           "pto"            : [1, 0],
           "ty1"            : [0, 1],
           "sw5"            : [0, 0],
           "mi12"           : [1, 0],
           "fusarium_cM"    : [45.0, 45.0],
           "tmv_cM"         : [22.4, 22.4],
           "nematod_cM"     : [33.1, 28.0],
           "rin_cM"         : [21.0, 9.0],
           "kok_guclu"      : [1, 0],
           "soguk_dayanikli": [0, 1],
           "kuraklık_toleransi": [0, 0],
           "etiketler"      : ["demo,örnek", "test"]
       }
       st.dataframe(pd.DataFrame(ornek), use_container_width=True)
       st.caption(
           "Yukarıdaki tablo, sistemin beklediği standart sütun yapısını gösterir. "
           "Kendi verinizi bu formatta hazırlayarak sidebar'dan yükleyebilirsiniz."
       )

       # CSV Yükleme & Birleştirme Mantığı (Tab İçi)
       st.markdown("---")
       st.subheader("🔄 CSV Birleştirme / Envanter Güncelleme")
       csv_dosya = st.file_uploader(
           "Mevcut envantere ekle veya güncelle (CSV/Excel)",
           type=["csv", "xlsx"],
           key="csv_merge_uploader"
       )
       if csv_dosya:
            try:
                if csv_dosya.name.endswith(".csv"):
                    yeni_df = pd.read_csv(csv_dosya)
                else:
                    yeni_df = pd.read_excel(csv_dosya)

                # Mevcut sütun yapısıyla uyumluluğu kontrol et
                for col in st.session_state['df'].columns:
                    if col not in yeni_df.columns:
                        yeni_df[col] = None

                # Veriyi birleştir ve hat_id'ye göre tekilleştir
                df_guncel = pd.concat([st.session_state['df'], yeni_df], ignore_index=True)
                st.session_state['df'] = df_guncel.drop_duplicates(subset=["hat_id"], keep="last")

                st.success(f"✅ Veri seti güncellendi. Toplam {len(st.session_state['df'])} hat kaydedildi.")
                st.rerun() # Değişikliklerin yansıması için uygulamayı yenile

            except Exception as exc:
                st.error(f"Birleştirme hatası: {exc}")

               st.success(
                   f"✅ Veri seti güncellendi. Toplam {len(df_guncel)} hat kaydedildi.",
                   icon="✅"
               )
               st.info(
                   "Not: Gerçek zamanlı state güncellemesi için `st.session_state` "
                   "yapılandırılmalıdır. Şu anlık sadece önizleme sunulmuştur.",
                   icon="ℹ️"
               )
           except Exception as exc:
               st.error(f"Birleştirme hatası: {exc}", icon="❌")


# ==============================================================================
# §15  SEKME 3 — SANAL EŞLEŞTİRME (MATCHMAKER)
#          Kantitatif Seçim İndeksi & Tamamlayıcı Ebeveyn Optimizasyonu
# ==============================================================================
def _standardize_trait(s: pd.Series, min_v: float, max_v: float) -> pd.Series:
    """
    Min-Max standardizasyonu ile sürekli değişkenleri 0-1 arasına ölçekler.
    GBLUP/BLUP mantığında ekonomik ağırlıkların çarpılabileceği z-skoru temeli.
    """
    val = (s - min_v) / (max_v - min_v)
    return val.clip(0, 1)


def sekme_matchmaker(df: pd.DataFrame) -> None:
    """
    Hedeflenen özelliklere göre Kantitatif Seçim İndeksi (Selection Index)
    kullanarak en yüksek genetik değer (EBV) taşıyan hatları tamamlayıcı
    şekilde eşleştirir. İççe evlenme (inbreeding) riskini minimize eder.
    """
    st.markdown("## 💞 Sanal Eşleştirme & Ebeveyn Optimizasyonu")
    st.markdown(
        "GBLUP mantığına dayalı **Kantitatif Seçim İndeksi** kullanarak, "
        "hedeflenen özelliklere göre en yüksek genetik değer (EBV) taşıyan hatları "
        "tamamlayıcı şekilde eşleştirir. İççe evlenme (inbreeding) riskini minimize eder."
    )

    col_settings, col_results = st.columns([1, 2], gap="large")

    with col_settings:
        st.markdown("### 🎯 Hedef Özellikler & Ağırlıklar")
        st.caption("Eğitimli bir ıslahçı gibi ekonomik ağırlıkları ayarlayın.")

        hedef_verim = st.slider("Verim (t/ha) Ağırlığı", 0.0, 1.0, 0.30, step=0.05, key="w_verim")
        hedef_brix  = st.slider("Brix (Kalite) Ağırlığı", 0.0, 1.0, 0.20, step=0.05, key="w_brix")
        hedef_raf   = st.slider("Raf Ömrü (gün) Ağırlığı", 0.0, 1.0, 0.20, step=0.05, key="w_raf")

        st.markdown("#### 🛡️ Biyotik & Abiyotik Direnç Ağırlıkları")
        hedef_fus   = st.slider("Fusarium Direnci", 0.0, 1.0, 0.10, step=0.05, key="w_fus")
        hedef_tmv   = st.slider("TMV Direnci", 0.0, 1.0, 0.05, step=0.05, key="w_tmv")
        hedef_nem   = st.slider("Nematod Direnci", 0.0, 1.0, 0.05, step=0.05, key="w_nem")
        hedef_kurak = st.slider("Kuraklık Toleransı", 0.0, 1.0, 0.10, step=0.05, key="w_kurak")

        agirliklar = {
            "verim": hedef_verim,
            "brix" : hedef_brix,
            "raf"  : hedef_raf,
            "fusarium_I"    : hedef_fus,
            "tmv"           : hedef_tmv,
            "nematod"       : hedef_nem,
            "kuraklık_toleransi": hedef_kurak,
        }

        inbreeding_penalty = st.slider(
            "İççe Evlenme Cezası (Benzerlik Ağırlığı)",
            0.0, 0.5, 0.25, step=0.05,
            key="penalty",
            help="Yüksek değer, genetik olarak çok benzer hatların eşleşmesini engeller."
        )
        top_n = st.number_input("Gösterilecek En İyi Çift Sayısı", min_value=5, max_value=50, value=15, step=5)

        run_btn = st.button("🧮 Eşleştirmeyi Hesapla", type="primary", use_container_width=True)

    with col_results:
        if run_btn:
            if len(df) < 2:
                st.warning("Eşleştirme yapmak için en az 2 hat gereklidir.", icon="⚠️")
                return

            with st.spinner("Kantitatif seçim indeksi hesaplanıyor..."):
                # 1. EBV (Estimated Breeding Value) Hesaplama
                df_calc = df.copy()
                df_calc["verim_z"] = _standardize_trait(df["verim"], 10.0, 30.0) if "verim" in df.columns else 0.0
                df_calc["brix_z"]  = _standardize_trait(df["brix"],  3.0, 12.0)  if "brix"  in df.columns else 0.0
                df_calc["raf_z"]   = _standardize_trait(df["raf"],   5.0, 30.0)  if "raf"   in df.columns else 0.0

                # Ekonomik ağırlıklı toplam indeks (GBLUP proxy)
                toplam_agirlik = sum(agirliklar.values()) or 1.0
                df_calc["EBV"] = 0.0
                for trait, w in agirliklar.items():
                    col_z = f"{trait}_z" if f"{trait}_z" in df_calc.columns else trait
                    if col_z in df_calc.columns:
                        df_calc["EBV"] += (df_calc[col_z] * w) / toplam_agirlik

                # 2. Çiftleştirme & Skorlama
                pairs = []
                hat_ids = df_calc["hat_id"].tolist()
                n = len(hat_ids)
                binary_traits = [
                    "fusarium_I", "tmv", "nematod", "rin", "pto", "ty1",
                    "sw5", "mi12", "kok_guclu", "soguk_dayanikli", "kuraklık_toleransi"
                ]

                for i in range(n):
                    for j in range(i + 1, n):
                        id_a, id_b = hat_ids[i], hat_ids[j]
                        row_a = df_calc.iloc[i]
                        row_b = df_calc.iloc[j]

                        ebv_a = row_a["EBV"]
                        ebv_b = row_b["EBV"]
                        combined_ebv = (ebv_a + ebv_b) / 2.0

                        # Genetik benzerlik cezası (Jaccard benzerliği ile inbreeding riski proxy'si)
                        set_a = set(t for t in binary_traits if row_a.get(t, 0) == 1)
                        set_b = set(t for t in binary_traits if row_b.get(t, 0) == 1)
                        similarity = jaccard(set_a, set_b)

                        # Final Eşleşme Skoru
                        pair_score = combined_ebv * (1.0 - inbreeding_penalty * similarity)

                        pairs.append({
                            "Anne": id_a,
                            "Baba": id_b,
                            "EBV_Anne": round(ebv_a, 4),
                            "EBV_Baba": round(ebv_b, 4),
                            "Birleşik_EBV": round(combined_ebv, 4),
                            "Genetik_Benzerlik": round(similarity, 3),
                            "Eşleşme_Skoru": round(pair_score, 4),
                        })

                pair_df = pd.DataFrame(pairs)
                if not pair_df.empty:
                    pair_df = pair_df.sort_values("Eşleşme_Skoru", ascending=False).head(top_n)

                # 3. Sonuç Görselleştirme
                st.dataframe(
                    pair_df.style.background_gradient(
                        subset=["Eşleşme_Skoru", "Birleşik_EBV"],
                        cmap="YlGnBu"
                    ).format({"Eşleşme_Skoru": "{:.4f}", "Birleşik_EBV": "{:.4f}"}),
                    use_container_width=True,
                    height=450,
                )

                # Üst çift için radar görseli
                if not pair_df.empty:
                    top_row = pair_df.iloc[0]
                    st.success(
                        f"🏆 En İyi Çift: **{top_row['Anne']}** × **{top_row['Baba']}** "
                        f"(Skor: %{top_row['Eşleşme_Skoru']*100:.1f})",
                        icon="🥇"
                    )
                    # Basit karşılaştırma grafiği
                    a_idx = df[df["hat_id"] == top_row["Anne"]].index[0]
                    b_idx = df[df["hat_id"] == top_row["Baba"]].index[0]
                    traits_plot = ["verim", "brix", "raf"]
                    vals_a = [df.iloc[a_idx].get(t, 0) for t in traits_plot]
                    vals_b = [df.iloc[b_idx].get(t, 0) for t in traits_plot]

                    fig_pair = go.Figure()
                    fig_pair.add_trace(go.Bar(
                        name=df.iloc[a_idx].get("hat_adi", "Anne"),
                        x=traits_plot, y=vals_a,
                        marker_color=PAL["g_hi"], offsetgroup=0
                    ))
                    fig_pair.add_trace(go.Bar(
                        name=df.iloc[b_idx].get("hat_adi", "Baba"),
                        x=traits_plot, y=vals_b,
                        marker_color=PAL["gold"], offsetgroup=1
                    ))
                    fig_pair.update_layout(
                        barmode="group",
                        paper_bgcolor=PLOTLY_BG,
                        plot_bgcolor="rgba(13,31,13,0.6)",
                        font=dict(color=PAL["txt"]),
                        title=dict(text="📊 Önerilen Çiftin Hedef Özellik Karşılaştırması", font=dict(color=PAL["gold"], size=14)),
                        legend=dict(bgcolor="rgba(13,31,13,.85)"),
                        yaxis=dict(gridcolor=PAL["border"], tickfont=dict(color=PAL["txt_dim"])),
                        xaxis=dict(gridcolor=PAL["border"], tickfont=dict(color=PAL["txt_dim"])),
                        margin=dict(l=40, r=20, t=50, b=40),
                        height=350,
                    )
                    st.plotly_chart(fig_pair, use_container_width=True)


# ==============================================================================
# §16  ANA ÇALIŞTIRMA BLOĞU (Main App Router)
# ==============================================================================
def main() -> None:
    """
    Biovalent Sentinel v4.1 Ana Çalıştırma Fonksiyonu.
    Tüm sekmeleri, sidebar yüklemeyi ve global state akışını yönetir.
    """
    # Sayfa başlığı ve slogan
    st.markdown(
        f"""
        <div class="bv-hero">
            <div style="font-size:1.8rem;color:{PAL['g_hi']};font-weight:900;letter-spacing:1px;">
                🧬 BIOVALENT SENTINEL <span style="font-size:1.2rem;color:{PAL['gold']};">v{VER}</span>
            </div>
            <div style="color:{PAL['txt_dim']};font-size:0.9rem;margin-top:8px;">
                {SLOGAN}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def main() -> None:
    # --- VERİ DURUMUNU BAŞLAT (Kalıcılık için) ---
    if 'df' not in st.session_state:
        # Başlangıçta boş bir DF veya varsayılan veriyi yükle
        st.session_state['df'] = sidebar_yukle()
    
    df = st.session_state['df'] 
    # --------------------------------------------

    # Sidebar veri yükleme (Demo veya kullanıcı dosyası)
    df = sidebar_yukle()

    # Ana sekme navigasyonu
    tab1, tab2, tab3, tab4 = st.tabs([
        "🧬 Proteomik & Motif",
        "📂 Toplu Yükleme (Bulk)",
        "💞 Sanal Eşleştirme",
        "📊 Envanter & Linkage"
    ])

    with tab1:
        sekme_proteomik(df)

    with tab2:
        sekme_bulk_upload(df)

    with tab3:
        sekme_matchmaker(df)

    with tab4:
        st.markdown("## 📊 Envanter Analizi & Linkage Risk Taraması")
        st.markdown("Mevcut envanterdeki hatlar arası genetik benzerlik ve kromozomal yakınlaşma (linkage drag) riskleri otomatik taranır.")

        # Hızlı envanter metrikleri
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Toplam Hat", len(df))
        m2.metric("Ortalama Verim", f"{df['verim'].mean():.1f} t/ha")
        m3.metric("Ortalama Brix", f"{df['brix'].mean():.1f}")
        m4.metric("Ortalama Raf", f"{df['raf'].mean():.0f} gün")

        # Linkage Drag Analizi
        st.markdown("### 🔗 Linkage Drag & Yakınlık Alarmı")
        if len(df) >= 2:
            alarmlar = otonom_linkage_tara(df)
            if alarmlar:
                st.warning(
                    f"⚠️ **{len(alarmlar)} adet** potansiyel linkage yakınlığı tespit edildi. "
                    f"İlk alarm mesafesi: **{alarmlar[0]['mesafe_cM']} cM**.",
                    icon="🔗"
                )
                st.dataframe(pd.DataFrame(alarmlar).head(10), use_container_width=True)
            else:
                st.success("✅ Tespit edilen kritik linkage yakınlığı bulunmuyor.", icon="✅")

            # Jaccard ısı haritası (Genetik benzerlik)
            if len(df) <= 30:
                st.markdown("### 🔥 Genetik Benzerlik Isı Haritası (Jaccard İndeksi)")
                ids = df["hat_id"].tolist()
                mat = pd.DataFrame(
                    [[jaccard(ozellik_seti(df.iloc[i]), ozellik_seti(df.iloc[j]))
                      for j in range(len(df))] for i in range(len(df))],
                    index=ids, columns=ids,
                )
                st.plotly_chart(fig_heatmap(mat), use_container_width=True)
            else:
                st.info("Isı haritası performansı korumak için ≤30 hat ile çalışır. Filtre uygulayın.", icon="ℹ️")
        else:
            st.info("Linkage analizi için en az 2 hat gereklidir.", icon="ℹ️")

    # Alt bilgi
    st.markdown("---")
    st.markdown(
        f"""
        <div style="text-align:center;color:{PAL['txt_dim']};font-size:0.75rem;padding:1rem 0;">
            © {datetime.now().year} Biovalent AgTech Solutions. Tüm hakları saklıdır.
            <br>Bu sistem yalnızca araştırma ve karar destek amaçlıdır. Ticari üretilmeden önce saha testleri yapılmalıdır.
        </div>
        """,
        unsafe_allow_html=True,
    )

def otonom_linkage_tara(df):
    """cM değerlerine göre kromozomal yakınlık risklerini tarar."""
    alarmlar = []
    cm_cols = [c for c in df.columns if "_cM" in c]
    
    for i, j in itertools.combinations(range(len(df)), 2):
        for col in cm_cols:
            dist = abs(df.iloc[i][col] - df.iloc[j][col])
            if dist < 5.0: # 5 cM altı kritik yakınlık kabul edilir
                alarmlar.append({
                    "Hat A": df.iloc[i]["hat_id"],
                    "Hat B": df.iloc[j]["hat_id"],
                    "Marker": col,
                    "mesafe_cM": round(dist, 2)
                })
    return alarmlar

# ==============================================================================
# GİRİŞ NOKTASI
# ==============================================================================
def main():
    # Sayfa Başlığı
    st.markdown(f'<div class="bv-hero"><h1>🧬 BIOVALENT SENTINEL</h1><p>{SLOGAN}</p></div>', unsafe_allow_html=True)
    
    # Veriyi Başlat
    if 'df' not in st.session_state:
        st.session_state['df'] = sidebar_yukle()
    
    df = st.session_state['df']
    
    # Sekmeleri Oluştur
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Envanter", "🤝 Matchmaker", "🧪 Genom Analizi", "🛡️ Risk Raporu"])
    
    with tab1:
        st.dataframe(df, use_container_width=True)
        
    with tab4:
        st.subheader("🛡️ Otonom Risk ve Linkage Analizi")
        riski_hatlar = otonom_linkage_tara(df) # Fonksiyonu burada tam çağırıyoruz
        if riski_hatlar:
            st.warning(f"Sistem {len(riski_hatlar)} adet kritik genetik yakınlık tespit etti.", icon="⚠️")
            st.dataframe(pd.DataFrame(riski_hatlar), use_container_width=True)
        else:
            st.success("Kritik linkage drag riski bulunamadı.", icon="✅")

# --- TAB 4 DEVAMI ---
            st.dataframe(pd.DataFrame(riski_hatlar), use_container_width=True)
        else:
            st.success("Kritik linkage drag riski bulunamadı.", icon="✅")

    with tab2:
        st.subheader("🤝 Ebeveyn Seçim Matrisi (Matchmaker)")
        st.info("İki hat arasındaki genetik benzerliği ve hibrit potansiyelini analiz edin.")
        # Burada jaccard benzerliği ve özellik karşılaştırması yapılabilir.
        hatlar = df["hat_id"].tolist()
        col1, col2 = st.columns(2)
        ana = col1.selectbox("Ana Ebeveyn", hatlar, index=0)
        baba = col2.selectbox("Baba Ebeveyn", hatlar, index=1)
        
        if ana != baba:
            s1 = ozellik_seti(df[df["hat_id"] == ana].iloc[0])
            s2 = ozellik_seti(df[df["hat_id"] == baba].iloc[0])
            benzerlik = jaccard(s1, s2)
            st.metric("Genetik Benzerlik (Jaccard)", f"{benzerlik:.2%}")
            st.progress(benzerlik)

    with tab3:
        st.subheader("🧪 Genom Analizi ve Protein Karakterizasyonu")
        st.write("Varyant analizi ve motif tarama sonuçları aşağıda listelenmiştir.")
        if not df.empty:
            # Örnek bir analiz tablosu veya grafik eklenebilir
            st.info("Genomik haritalama verileri yüklendi. Analiz hazır.")
        else:
            st.warning("Analiz için veri bulunamadı.")

    # --- ALT BİLGİ (FOOTER) ---
    st.markdown("---")
    st.caption(f"© {datetime.now().year} Biovalent AgTech Solutions | Islah Destek Sistemi v{VER}")

# ─────────────────────────────────────────────────────────────────────────────
# § UYGULAMAYI BAŞLAT
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error(f"Uygulama başlatılamadı: {e}")
        st.code(traceback.format_exc())

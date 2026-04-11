"""
╔══════════════════════════════════════════════════════════════════════╗
║   BIOVALENT SENTINEL v9.0  —  Streamlit Web Application             ║
║   Decoding the Bonds of Life                                         ║
║                                                                      ║
║   KURULUM:                                                           ║
║       pip install streamlit matplotlib numpy biopython               ║
║       streamlit run biovalent_sentinel_app.py                        ║
║                                                                      ║
║   Google Colab:                                                      ║
║       !pip install streamlit matplotlib numpy biopython pyngrok -q   ║
║       !streamlit run biovalent_sentinel_app.py &                     ║
║       from pyngrok import ngrok; print(ngrok.connect(8501))          ║
╚══════════════════════════════════════════════════════════════════════╝
"""

# ─────────────────────────────────────────────────────────────────────
# §0  BAĞIMLILIKLAR
# ─────────────────────────────────────────────────────────────────────
import sys, re, math, itertools, traceback
from copy import deepcopy
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Tuple

import streamlit as st

try:
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    import matplotlib.gridspec as gridspec
    _MPL_OK = True
except ImportError:
    _MPL_OK = False

try:
    import numpy as np
    _NP_OK = True
except ImportError:
    _NP_OK = False

# ─────────────────────────────────────────────────────────────────────
# §1  SAYFA KONFİGÜRASYONU & TEMA  (Streamlit'e özgü, import'tan hemen sonra)
# ─────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Biovalent Sentinel v9.0",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS: Koyu Lacivert + Neon Yeşil/Mint teması ──────────────────────
CUSTOM_CSS = """
<style>
/* ── Temel arka plan ── */
html, body, [data-testid="stAppViewContainer"] {
    background-color: #0b1120;
    color: #e2e8f0;
    font-family: 'Inter', 'Segoe UI', sans-serif;
}
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0d1b2a 0%, #0f2040 100%);
    border-right: 1px solid #1e3a5f;
}
/* ── Başlık ── */
h1 { color: #00ffaa !important; letter-spacing: -0.5px; }
h2 { color: #7de8c5 !important; }
h3 { color: #a8edda !important; }
/* ── Metrik kartları ── */
[data-testid="metric-container"] {
    background: linear-gradient(135deg, #0d2137 0%, #0a1628 100%);
    border: 1px solid #1e4d7b;
    border-radius: 12px;
    padding: 16px !important;
}
[data-testid="metric-container"] label { color: #7de8c5 !important; font-size:0.8rem; }
[data-testid="metric-container"] [data-testid="stMetricValue"] { color: #00ffaa !important; }
/* ── Butonlar ── */
.stButton>button {
    background: linear-gradient(135deg, #00c87a 0%, #00a86b 100%);
    color: #0b1120;
    border: none;
    border-radius: 8px;
    font-weight: 700;
    padding: 0.5rem 1.4rem;
    font-size: 0.95rem;
    letter-spacing: 0.3px;
    transition: all 0.2s ease;
}
.stButton>button:hover {
    background: linear-gradient(135deg, #00ffaa 0%, #00c87a 100%);
    transform: translateY(-1px);
    box-shadow: 0 4px 20px rgba(0,200,122,0.35);
}
/* ── Metin alanları & inputlar ── */
.stTextArea textarea, .stTextInput input, .stSelectbox select {
    background-color: #0d2137 !important;
    color: #e2e8f0 !important;
    border: 1px solid #1e4d7b !important;
    border-radius: 8px !important;
}
/* ── Multiselect ── */
.stMultiSelect > div { background-color: #0d2137 !important; }
/* ── Kartlar (info/success/warning/error) ── */
.stAlert {
    border-radius: 10px !important;
    border-left-width: 4px !important;
}
/* ── Ayırıcı çizgi ── */
hr { border-color: #1e3a5f !important; }
/* ── Sidebar menü ögeleri ── */
[data-testid="stSidebarNav"] { background: transparent; }
/* ── Expander ── */
.streamlit-expanderHeader {
    background-color: #0d2137 !important;
    color: #7de8c5 !important;
    border-radius: 8px !important;
}
/* ── Dataframe / tablo ── */
[data-testid="stDataFrame"] {
    border: 1px solid #1e4d7b;
    border-radius: 8px;
}
/* ── Sayfa içi kart ── */
.bv-card {
    background: linear-gradient(135deg, #0d2137 0%, #0a1a2e 100%);
    border: 1px solid #1e4d7b;
    border-radius: 14px;
    padding: 1.4rem 1.6rem;
    margin-bottom: 1rem;
}
.bv-badge-green  { background:#003d26; color:#00ffaa; padding:3px 10px;
                   border-radius:20px; font-size:0.78rem; font-weight:600; }
.bv-badge-yellow { background:#332700; color:#ffd166; padding:3px 10px;
                   border-radius:20px; font-size:0.78rem; font-weight:600; }
.bv-badge-red    { background:#3d0000; color:#ff6b6b; padding:3px 10px;
                   border-radius:20px; font-size:0.78rem; font-weight:600; }
/* ── Logo başlık alanı ── */
.bv-hero {
    background: linear-gradient(135deg, #0d2137 0%, #0a1628 50%, #001a0d 100%);
    border: 1px solid #1e4d7b;
    border-radius: 16px;
    padding: 2rem 2.5rem;
    margin-bottom: 1.5rem;
    text-align: center;
}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────
# §2  GLOBAL SABİTLER
# ─────────────────────────────────────────────────────────────────────
VER    = "9.0.0"
FIRMA  = "Biovalent"
SLOGAN = "Decoding the Bonds of Life"
GUVEN  = 0.95

# Matplotlib koyu tema sabitleri
BG    = "#0b1120"; PANEL = "#0d2137"; EDGE  = "#1e4d7b"
GRN   = "#00c87a"; MINT  = "#00ffaa"; RED   = "#ff6b6b"
YLW   = "#ffd166"; GREY  = "#4a6a8a"; WHT   = "#e2e8f0"

# ─────────────────────────────────────────────────────────────────────
# §3  BIYOENFORMATIK MOTOR  (v9.0 motoru — terminal bağımlılıklarından arındırılmış)
# ─────────────────────────────────────────────────────────────────────

class Alel(str, Enum):
    DOM_HOM = "dominant_homozigot"
    HET     = "heterozigot"
    REC_HOM = "resesif_homozigot"

ALEL_ETIKET = {
    Alel.DOM_HOM: "Dominant Homozigot (AA)",
    Alel.HET    : "Heterozigot (Aa)",
    Alel.REC_HOM: "Resesif Homozigot (aa)",
}


@dataclass
class GeneticMarker:
    gen    : str
    lokus  : str
    alel   : Alel
    cM     : float = 0.0
    kaynak : str   = ""

    def __post_init__(self):
        if not isinstance(self.alel, Alel):
            self.alel = Alel(self.alel)

    @property
    def aleller(self) -> Tuple[str, str]:
        B, k = self.gen[0].upper(), self.gen[0].lower()
        return {Alel.DOM_HOM:(B,B), Alel.HET:(B,k), Alel.REC_HOM:(k,k)}[self.alel]

    def genotip(self) -> str:
        return "".join(self.aleller)

    def is_dominant(self) -> bool:
        return self.alel in (Alel.DOM_HOM, Alel.HET)


@dataclass
class PhysicalTraits:
    meyve_rengi     : str       = "Tanımsız"
    meyve_agirlik_g : float     = 0.0
    verim_skoru     : float     = 0.0
    hasat_gunu      : int       = 0
    brix            : float     = 0.0
    raf_omru_gun    : int       = 0
    dayaniklilik    : List[str] = field(default_factory=list)
    notlar          : str       = ""


class BreederLine:
    def __init__(self, line_id, adi, tur, dna_dizisi=None,
                 fiziksel=None, markorler=None, etiketler=None):
        self.line_id   = line_id.strip().upper()
        self.adi       = adi.strip()
        self.tur       = tur.strip()
        self.dna_dizisi= self._norm_dna(dna_dizisi)
        self.fiziksel  = fiziksel  or PhysicalTraits()
        self.markorler = markorler or []
        self.etiketler = [e.lower().strip() for e in (etiketler or [])]

    @staticmethod
    def _norm_dna(s):
        if not s: return None
        lines = s.strip().splitlines()
        clean = "".join(l.strip() for l in lines if not l.startswith(">"))
        return "".join(c for c in clean.upper() if c in "ACGTUNRYSWKMBDHV-") or None

    def markor(self, gen):
        for m in self.markorler:
            if m.gen.upper() == gen.upper(): return m
        return None

    def ozet(self):
        return {
            "Line ID": self.line_id, "Ad": self.adi, "Tür": self.tur,
            "DNA (bp)": len(self.dna_dizisi) if self.dna_dizisi else 0,
            "Markör #": len(self.markorler),
            "Meyve Rengi": self.fiziksel.meyve_rengi,
            "Verim (1-10)": self.fiziksel.verim_skoru,
            "Hasat (gün)": self.fiziksel.hasat_gunu,
            "Raf (gün)": self.fiziksel.raf_omru_gun,
        }

    def __repr__(self):
        return f"<BreederLine {self.line_id}>"


class Inventory:
    def __init__(self):
        self._db: Dict[str, BreederLine] = {}

    def ekle(self, hat):
        self._db[hat.line_id] = hat
        return self

    def getir(self, lid):
        return self._db.get(lid.strip().upper())

    def hepsi(self):
        return list(self._db.values())

    def listele(self):
        return [h.ozet() for h in self._db.values()]

    def ids(self):
        return list(self._db.keys())

    def __len__(self):
        return len(self._db)


# ── M1: Matchmaker ────────────────────────────────────────────────────

@dataclass
class MatchSonucu:
    ana: BreederLine; baba: BreederLine
    puan: float; hedef_p_f1: float; hedef_p_f2: float
    karsilanan: List[str]; eksik: List[str]; yorum: str


class Matchmaker:
    @staticmethod
    def _etiket_eslesme(ana, baba, hedefler):
        havuz = set(ana.etiketler + baba.etiketler)
        k, e = [], []
        for h in hedefler:
            (k if any(h in x or x in h for x in havuz) else e).append(h)
        return len(k) / max(len(hedefler), 1) * 100, k, e

    @staticmethod
    def _mendel_f2_p(ana, baba, genler):
        p = 1.0
        for g in genler:
            ma, mb = ana.markor(g), baba.markor(g)
            aa = ma.aleller if ma else (g[0].lower(), g[0].lower())
            ab = mb.aleller if mb else (g[0].lower(), g[0].lower())
            f1a = sorted([aa[0], ab[0]], key=lambda x: (x.islower(), x))
            a1, a2 = f1a[0], f1a[1] if len(f1a) > 1 else f1a[0]
            if a1.isupper() and a2.isupper(): p_g = 1.00
            elif a1.isupper() and a2.islower(): p_g = 0.75
            else: p_g = 0.00
            p *= p_g
        return round(p, 6)

    @staticmethod
    def _fenotip_puani(ana, baba):
        v = (ana.fiziksel.verim_skoru + baba.fiziksel.verim_skoru) / 2
        r = (ana.fiziksel.raf_omru_gun + baba.fiziksel.raf_omru_gun) / 2
        return round((min(v/10,1)*0.6 + min(r/30,1)*0.4) * 20, 2)

    def en_iyi(self, inv, hedefler, hedef_genler=None, n=3):
        hatlar = inv.hepsi(); genler = hedef_genler or []
        if len(hatlar) < 2: return []
        sonuclar = []
        for ana, baba in itertools.permutations(hatlar, 2):
            if ana.tur != baba.tur: continue
            ep, k, e = self._etiket_eslesme(ana, baba, hedefler)
            fp       = self._fenotip_puani(ana, baba)
            f2_p     = self._mendel_f2_p(ana, baba, genler) if genler else 0.5
            f1_p     = 1.0 if f2_p >= 0.75 else 0.75 if f2_p > 0 else 0.0
            mp = sum(15 if m.is_dominant() else 0 for m in ana.markorler)
            puan = min(ep*0.50 + mp*0.30 + fp*0.20, 100)
            yorum = ("✅ Tüm hedefler karşılanabilir." if not e
                     else f"⚠️ {len(e)} hedef eksik." if len(k)>=len(hedefler)*0.7
                     else f"❌ {len(e)} kritik hedef karşılanamıyor.")
            sonuclar.append(MatchSonucu(ana, baba, round(puan,2), f1_p, f2_p, k, e, yorum))
        sonuclar.sort(key=lambda x: x.puan, reverse=True)
        seen, uniq = set(), []
        for s in sonuclar:
            key = frozenset([s.ana.line_id, s.baba.line_id])
            if key not in seen:
                seen.add(key); uniq.append(s)
        return uniq[:n]


# ── M2: Linkage Drag ──────────────────────────────────────────────────

@dataclass
class LinkageSonucu:
    gen_hedef: str; gen_surukle: str; cm_mesafe: float
    suruklenme_r: float; rekomb_p: float; gerekli_bitki: int
    uyari_seviye: str; aciklama: str


class LinkageDragEngine:
    _MAP: Dict[str, Dict[str, float]] = {
        "I"    : {"Mi-1.2": 72.0, "Pto": 45.0},
        "Tm-2a": {"Cf-9": 12.0},
        "Cf-9" : {"Tm-2a": 12.0, "Cf-4": 8.0},
        "Cf-4" : {"Cf-9": 8.0},
        "rin"  : {"nor": 6.0},
        "nor"  : {"rin": 6.0},
        "y"    : {"B": 25.0},
    }

    @staticmethod
    def haldane(cm): return 0.5 * (1 - math.exp(-2*cm/100))

    @staticmethod
    def min_bitki(r, guven=GUVEN):
        if r<=0: return 999_999
        if r>=1: return 1
        return math.ceil(math.log(1-guven)/math.log(1-r))

    def analiz_et(self, genler, ek_map=None):
        harita = deepcopy(self._MAP)
        if ek_map:
            for g, km in ek_map.items():
                harita.setdefault(g, {}).update(km)
        sonuclar = []
        for gen in genler:
            for mk, komsular in harita.items():
                if mk.upper() != gen.upper(): continue
                for kg, cm in komsular.items():
                    r = self.haldane(cm)
                    n = self.min_bitki(r)
                    if cm < 5:
                        sev = "YÜKSEK"
                        aciklama = f"Kritik bağlantı! {gen} ↔ {kg}: {cm:.1f} cM. {n:,} rekombinan bitki gerekli."
                    elif cm < 20:
                        sev = "ORTA"
                        aciklama = f"Orta risk. {gen} ↔ {kg}: {cm:.1f} cM. {n:,} bitki ile ayrıştırılabilir."
                    else:
                        sev = "DÜŞÜK"
                        aciklama = f"Düşük risk. {gen} ↔ {kg}: {cm:.1f} cM. {n:,} bitki yeterli."
                    sonuclar.append(LinkageSonucu(gen, kg, cm, round(1-r,4), round(r,4), n, sev, aciklama))
        return sorted(sonuclar, key=lambda x: x.cm_mesafe)


# ── M3: Genetic Detective ──────────────────────────────────────────────

@dataclass
class EbeveynTahmini:
    hat1: BreederLine; hat2: BreederLine
    kinship: float; benzerlik_pct: float; toplam: float; aciklama: str


class GeneticDetective:
    @staticmethod
    def _kmer(a, b, k=8):
        if not a or not b: return 0.0
        def km(s): return set(s[i:i+k] for i in range(len(s)-k+1))
        ka, kb = km(a), km(b)
        if not ka or not kb: return 0.0
        return len(ka & kb) / len(ka | kb)

    @staticmethod
    def _kinship(h1, h2, hibrit):
        if not hibrit.markorler: return 0.5
        ac = 0
        for mh in hibrit.markorler:
            ma, mb = h1.markor(mh.gen), h2.markor(mh.gen)
            ah = set(mh.aleller)
            aa = set(ma.aleller) if ma else set()
            ab = set(mb.aleller) if mb else set()
            if ah & (aa | ab): ac += 1
        return ac / len(hibrit.markorler)

    def tanimlama_yap(self, inv, hibrit, n=3):
        hatlar = inv.hepsi()
        if len(hatlar) < 2: return []
        adaylar = []
        for h1, h2 in itertools.combinations(hatlar, 2):
            kin = self._kinship(h1, h2, hibrit)
            dna_sim = 0.5
            if hibrit.dna_dizisi:
                sims = [self._kmer(hibrit.dna_dizisi, h.dna_dizisi)
                        for h in (h1,h2) if h.dna_dizisi]
                dna_sim = sum(sims)/len(sims) if sims else 0.5
            toplam = round(kin*0.6 + dna_sim*0.4, 4)
            aciklama = (f"Kinship: %{kin*100:.1f}  |  "
                        f"DNA Benzerlik: %{dna_sim*100:.1f}  |  "
                        f"Toplam Güven: %{toplam*100:.1f}")
            adaylar.append(EbeveynTahmini(h1, h2, kin, dna_sim*100, toplam, aciklama))
        adaylar.sort(key=lambda x: x.toplam, reverse=True)
        return adaylar[:n]


# ── M4: Proteomik Yorumlayıcı ─────────────────────────────────────────

_KODON: Dict[str, str] = {
    'TTT':'F','TTC':'F','TTA':'L','TTG':'L','CTT':'L','CTC':'L','CTA':'L','CTG':'L',
    'ATT':'I','ATC':'I','ATA':'I','ATG':'M','GTT':'V','GTC':'V','GTA':'V','GTG':'V',
    'TCT':'S','TCC':'S','TCA':'S','TCG':'S','CCT':'P','CCC':'P','CCA':'P','CCG':'P',
    'ACT':'T','ACC':'T','ACA':'T','ACG':'T','GCT':'A','GCC':'A','GCA':'A','GCG':'A',
    'TAT':'Y','TAC':'Y','TAA':'*','TAG':'*','CAT':'H','CAC':'H','CAA':'Q','CAG':'Q',
    'AAT':'N','AAC':'N','AAA':'K','AAG':'K','GAT':'D','GAC':'D','GAA':'E','GAG':'E',
    'TGT':'C','TGC':'C','TGA':'*','TGG':'W','CGT':'R','CGC':'R','CGA':'R','CGG':'R',
    'AGT':'S','AGC':'S','AGA':'R','AGG':'R','GGT':'G','GGC':'G','GGA':'G','GGG':'G',
}
_MOTIFLER: List[Dict] = [
    {"isim":"NBS (P-loop)","motif":"GVGKTT","kategori":"NBS-LRR Direnç Reseptörü",
     "islev":"Nükleotid bağlanma; NBS-LRR direnç proteinlerinin çekirdeği.",
     "tarla":"Patojen direnci — hastalık belirtisi azalır veya görülmez."},
    {"isim":"LRR Tekrar","motif":"LXXLXLXX","kategori":"NBS-LRR Direnç Reseptörü",
     "islev":"Lösin tekrarlı bölge; protein-protein etkileşimi.",
     "tarla":"Geniş ırk spektrumlu hastalık direnci potansiyeli."},
    {"isim":"Kinaz DFG","motif":"DFG","kategori":"Serin/Treonin Kinaz",
     "islev":"ATP bağlanma ve fosforilasyon; sinyal iletim kaskadı.",
     "tarla":"Sinyal yolu aktivasyonu — biyotik/abiyotik stres yanıtı."},
    {"isim":"WRKY TF","motif":"WRKYGQK","kategori":"Transkripsiyon Faktörü",
     "islev":"W-box DNA bağlanma; savunma geni ifadesini düzenler.",
     "tarla":"Sistemik edinilmiş direnç (SAR) mekanizmasında rol oynar."},
    {"isim":"PR-1 Peptidi","motif":"MKKLLAL","kategori":"PR Proteini",
     "islev":"Salisilik asit yolunda patojene karşı savunma proteini.",
     "tarla":"PR-1 ekspresyonu hastalık direncinin göstergesi."},
    {"isim":"ABC Taşıyıcı","motif":"LSGGQ","kategori":"ABC Taşıyıcı Protein",
     "islev":"ATP bağlama kaseti; membran geçişinde molekül taşınımı.",
     "tarla":"İlaç/toksin direnci veya metabolit taşınımı."},
    {"isim":"MYB Domaini","motif":"GRTWHTE","kategori":"MYB Transkripsiyon Faktörü",
     "islev":"Pigment, çiçeklenme ve meyve olgunlaşması düzenleme.",
     "tarla":"Meyve rengi, olgunlaşma zamanı ve aroma bileşiklerine etki."},
    {"isim":"SOD Merkez","motif":"HVHAQY","kategori":"Antioksidan Enzim (SOD)",
     "islev":"Süperoksit dismutaz; reaktif oksijen türlerini nötralize eder.",
     "tarla":"Kuraklık, ısı stresi ve pestisit toleransıyla ilişkili."},
]

@dataclass
class ProteomikSonuc:
    dna_uzunluk: int; aa_dizisi: str; aa_uzunluk: int
    motifler: List[Dict]; protein_sinifi: str
    fonksiyon: str; tarla_etkisi: str; guven: str


class ProteomikYorumlayici:
    @staticmethod
    def _cevir(dna):
        en_uzun = ""
        for f in range(3):
            aa = []
            for i in range(f, len(dna)-2, 3):
                k = dna[i:i+3]
                if len(k)<3: break
                h = _KODON.get(k,"X")
                if h=="*": break
                aa.append(h)
            p = "".join(aa)
            if len(p) > len(en_uzun): en_uzun = p
        return en_uzun

    @staticmethod
    def _tara(aa):
        bulunan = []
        for m in _MOTIFLER:
            pat = m["motif"].replace("X",".").replace("x",".")
            try:
                hits = list(re.finditer(pat, aa, re.IGNORECASE))
            except re.error:
                hits = []
            if hits:
                bulunan.append({**m, "konumlar": [h.start() for h in hits]})
        return bulunan

    def analiz_et(self, dizi):
        lines = dizi.strip().splitlines()
        dna   = "".join(l.strip() for l in lines if not l.startswith(">")).upper()
        dna   = "".join(c for c in dna if c in "ACGTUNRYSWKMBDHV")
        aa    = self._cevir(dna)
        motifler = self._tara(aa)
        siniflar = [m["kategori"] for m in motifler]
        if "NBS-LRR Direnç Reseptörü" in siniflar:
            ps, fn, te = ("NBS-LRR Direnç Reseptörü",
                          "Patojen effektör tanıma ve hipersensitivite yanıtı tetikleme.",
                          "Hastalık belirtisi görülmez veya minimize olur.")
        elif "Serin/Treonin Kinaz" in siniflar:
            ps, fn, te = ("Serin/Treonin Protein Kinaz",
                          "Sinyal iletim kaskadı — stres veya gelişim sinyali.",
                          "Biyotik/abiyotik stres yanıtı veya verim ile ilgili fenotip.")
        elif any(x in siniflar for x in ["Transkripsiyon Faktörü","MYB Transkripsiyon Faktörü"]):
            ps, fn, te = ("Transkripsiyon Faktörü",
                          "Gen ifadesini düzenler (pigment, olgunlaşma veya savunma yolları).",
                          "Meyve rengi, olgunlaşma zamanı veya stres toleransı.")
        elif "ABC Taşıyıcı Protein" in siniflar:
            ps, fn, te = ("ABC Taşıyıcı Protein",
                          "Hücre zarından molekül geçişi; detoksifikasyon ve beslenme.",
                          "Herbisit/fungisit direnci veya mineral alımı ile ilgili.")
        elif "Antioksidan Enzim (SOD)" in siniflar:
            ps, fn, te = ("Antioksidan Enzim (SOD)",
                          "Reaktif oksijen türlerini nötralize eder.",
                          "Kuraklık ve ısı toleransı artışı beklenir.")
        elif motifler:
            ps = motifler[0]["kategori"]
            fn = motifler[0]["islev"]
            te = motifler[0]["tarla"]
        else:
            ps = "Bilinmiyor / Yapısal Protein"
            fn = "Bilinen motif bulunamadı. AlphaFold veya InterPro analizi önerilir."
            te = "Fenotipik etki tahmin edilemiyor. Tarla doğrulaması gereklidir."
        guven = (f"{'YÜKSEK' if len(motifler)>=2 else 'ORTA' if motifler else 'DÜŞÜK'} güven — "
                 f"{len(motifler)} motif tespit edildi.")
        return ProteomikSonuc(len(dna), aa[:80]+("..." if len(aa)>80 else ""),
                              len(aa), motifler, ps, fn, te, guven)


# ── M5: Populasyon Planlayıcısı ───────────────────────────────────────

@dataclass
class PopulasyonPlan:
    hedef_tanim: str; hedef_genler: List[str]
    f1_genotip: Dict; f2_tablo: Dict[str,float]; hedef_p: float
    min_bitki: int; tampon: int; toplam: int; secim: int
    strateji: str; tavsiye: str


class Planlayici:
    @staticmethod
    def _f1(ana, baba, genler):
        f1 = {}
        for g in genler:
            ma, mb = ana.markor(g), baba.markor(g)
            aa = ma.aleller if ma else (g[0].lower(), g[0].lower())
            ab = mb.aleller if mb else (g[0].lower(), g[0].lower())
            pair = tuple(sorted([aa[0], ab[0]], key=lambda x: (x.islower(), x)))
            f1[g] = pair
        return f1

    @staticmethod
    def _f2(f1):
        def pn(a1,a2):
            if a1.isupper() and a2.isupper(): return {"D":1.00,"r":0.00}
            if a1.isupper() and a2.islower(): return {"D":0.75,"r":0.25}
            return {"D":0.00,"r":1.00}
        genler = list(f1.keys())
        gen_p  = {g: pn(*f1[g]) for g in genler}
        tablo  = {}
        for kombin in itertools.product(["D","r"], repeat=len(genler)):
            p  = 1.0; parcalar = []
            for i, g in enumerate(genler):
                d = kombin[i]; p *= gen_p[g][d]
                parcalar.append(f"{g}:{'Dom' if d=='D' else 'Rec'}")
            if p > 1e-9:
                tablo[" | ".join(parcalar)] = round(p, 8)
        hedef_e = " | ".join(f"{g}:Dom" for g in genler)
        return tablo, tablo.get(hedef_e, 0.0)

    @staticmethod
    def _min(p, guven=GUVEN):
        if p<=0: return 999_999
        if p>=1: return 1
        return math.ceil(math.log(1-guven)/math.log(1-p))

    def planla(self, ana, baba, genler, tanim="", tampon_pct=0.20, secim_oran=0.25):
        f1 = self._f1(ana, baba, genler)
        tablo, p = self._f2(f1)
        mn = self._min(p); tam = math.ceil(mn*tampon_pct); top = mn+tam
        sec = math.ceil(top*secim_oran)
        if p>=0.50:   st_str = "F2 Direkt Seçim — küçük popülasyon, düşük maliyet."
        elif p>=0.25: st_str = "F2 Geniş Populasyon + MAS (Markör Destekli Seçim)."
        elif p>=0.06: st_str = "F3 Backcross (BC1) + MAS kombinasyonu."
        else:         st_str = "Piramitleme + çok nesil backcross — uzun vadeli plan."
        tavsiye = (f"{'✅' if p>=0.25 else '⚠️' if p>=0.06 else '❌'} "
                   f"F2 hedef p = %{p*100:.4f}. "
                   f"Min {mn:,} + {tam:,} tampon = {top:,} bitki. {sec:,} birey F3'e.")
        return PopulasyonPlan(
            tanim or ", ".join(genler), genler,
            {"".join(f1[g]): g for g in genler}, tablo, p,
            mn, tam, top, sec, st_str, tavsiye
        )


# ─────────────────────────────────────────────────────────────────────
# §4  ÖRNEK ENVANTER
# ─────────────────────────────────────────────────────────────────────

@st.cache_resource
def demo_envanter() -> Inventory:
    inv = Inventory()
    PTO = ("ATGGAGAGTGGAATTTCAGATTTTAAGTTTGATGAAGATGATGATGACGATGATGATGATG"
           "ATGATGATTCTTTTGGAGAGGGAGATGAAGGAAGTGCAAATGGAGAAAGCAGAAAAGATTC"
           "TCAAGCTTTTGGAGAAGGTGATGTCAACCCTTGTGACGATAGACCTCTTGTTGGTGTTTCC"
           "GGGAAAGCTGTAATAAAAGAACTGGATACAGAAGGGCTTGGAAGTGGGACTTCAGGTGTTG"
           "AGCTTGTTTTGGAGAAAGAAGAAAAGCATCCCCTAGGAGTTGAGTTGGTTGTAAATGTAGA")
    NBS = ("ATGGGCGTTGGCAAAACTACCATGCTTGCAGCTGATTTGCGTCAGAAGATGGCTGCAGAGCTGAAAGAT"
           "CGCTTTGCGATGGTGGATGGCGTGGGCGAAGTGGACTCTTTTGGCGACTTCCTCAAAACACTCGCAGAG"
           "GAGATCATTGGCGTCGTCAAAGATAGTAAACTCTATTTGTTGCTTCTTTTAAGTGGCAGGACTTGGCAT"
           "GTTGGGCGGCGTACTTGGCATTTCAATGGGCGGACAAGAAGTTCCTCATACCGAGAGAGAGTGGGCGTT")
    inv.ekle(BreederLine("BIO-TOM-001","Crimson Shield F6","Solanum lycopersicum",PTO,
        PhysicalTraits("Koyu Kırmızı",182,8.5,72,5.2,14,["Fusarium","TMV","Pseudomonas"]),
        [GeneticMarker("I","11q13",Alel.DOM_HOM,45,"Jones 1993"),
         GeneticMarker("Tm-2a","9p",Alel.DOM_HOM,22,"Pelham 1966"),
         GeneticMarker("Pto","5q",Alel.DOM_HOM,15,"Martin 1993"),
         GeneticMarker("y","1p",Alel.REC_HOM,5,"Tomes 1954")],
        ["kırmızı meyve","fusarium direnci","tmv direnci","virüs direnci","orta verim"]))
    inv.ekle(BreederLine("BIO-TOM-002","GoldenYield HV-9","Solanum lycopersicum",None,
        PhysicalTraits("Parlak Sarı",228,9.2,68,4.8,11),
        [GeneticMarker("I","11q13",Alel.REC_HOM,45),
         GeneticMarker("Tm-2a","9p",Alel.HET,22),
         GeneticMarker("y","1p",Alel.DOM_HOM,5)],
        ["sarı meyve","yüksek verim","ticari hat"]))
    inv.ekle(BreederLine("BIO-TOM-003","LongLife Premium","Solanum lycopersicum",None,
        PhysicalTraits("Kırmızı",195,7.8,78,5.8,24,["rin uzun raf ömrü"]),
        [GeneticMarker("rin","5q",Alel.HET,12,"Giovannoni 2004"),
         GeneticMarker("Mi-1.2","6p",Alel.DOM_HOM,33,"Rossi 1998"),
         GeneticMarker("y","1p",Alel.REC_HOM,5)],
        ["uzun raf ömrü","nematod direnci","raf ömrü","ihracat"]))
    inv.ekle(BreederLine("BIO-TOM-004","SunGold Cherry","Solanum lycopersicum",None,
        PhysicalTraits("Turuncu-Sarı",22,9.5,62,8.2,10),
        [GeneticMarker("y","1p",Alel.DOM_HOM,5),
         GeneticMarker("Tm-2a","9p",Alel.REC_HOM,22)],
        ["sarı meyve","cherry","yüksek brix","gourmet","yüksek verim"]))
    inv.ekle(BreederLine("BIO-TOM-005","Titan Robust F4","Solanum lycopersicum",NBS,
        PhysicalTraits("Koyu Kırmızı",265,8.0,80,4.5,16,["Fusarium","Mi-1.2"]),
        [GeneticMarker("I","11q13",Alel.DOM_HOM,45),
         GeneticMarker("Mi-1.2","6p",Alel.DOM_HOM,33),
         GeneticMarker("Tm-2a","9p",Alel.REC_HOM,22),
         GeneticMarker("y","1p",Alel.REC_HOM,5)],
        ["kırmızı meyve","fusarium direnci","nematod direnci","virüs direnci"]))
    inv.ekle(BreederLine("BIO-TOM-006","Sunrise Export","Solanum lycopersicum",None,
        PhysicalTraits("Sarı-Turuncu",185,8.8,74,5.0,20,["TMV","rin"]),
        [GeneticMarker("y","1p",Alel.DOM_HOM,5),
         GeneticMarker("rin","5q",Alel.HET,12),
         GeneticMarker("Tm-2a","9p",Alel.DOM_HOM,22)],
        ["sarı meyve","uzun raf ömrü","tmv direnci","virüs direnci","ihracat","yüksek verim"]))
    inv.ekle(BreederLine("BIO-CAP-001","RedBlaze L4 F5","Capsicum annuum",None,
        PhysicalTraits("Parlak Kırmızı",145,8.2,85,6.1,18,["L4 TMV","PVY"]),
        [GeneticMarker("L","11q",Alel.DOM_HOM,18,"Boukema 1980"),
         GeneticMarker("pvr","3q",Alel.REC_HOM,9,"Caranta 1997")],
        ["kırmızı meyve","tmv direnci","pvy direnci","virüs direnci"]))
    inv.ekle(BreederLine("BIO-CAP-002","YellowBell Export","Capsicum annuum",None,
        PhysicalTraits("Sarı",198,7.5,90,5.5,14),
        [GeneticMarker("L","11q",Alel.REC_HOM,18)],
        ["sarı meyve","dolmalık biber","ihracat"]))
    inv.ekle(BreederLine("BIO-CAP-003","Spicy Supreme","Capsicum annuum",None,
        PhysicalTraits("Kırmızı-Turuncu",42,9.0,78,7.2,12,["Phytophthora"]),
        [GeneticMarker("pvr","3q",Alel.HET,9),
         GeneticMarker("L","11q",Alel.HET,18)],
        ["acı biber","yüksek brix","yüksek verim","gourmet"]))
    return inv


# ─────────────────────────────────────────────────────────────────────
# §5  GRAFİK YARDIMCILARI
# ─────────────────────────────────────────────────────────────────────

def _ax_style(ax, title="", xlabel="", ylabel=""):
    ax.set_facecolor(PANEL)
    ax.set_title(title, color=MINT, fontsize=11, fontweight="bold", pad=10)
    if xlabel: ax.set_xlabel(xlabel, color=WHT, fontsize=9)
    if ylabel: ax.set_ylabel(ylabel, color=WHT, fontsize=9)
    ax.tick_params(colors=GREY)
    for sp in ax.spines.values(): sp.set_color(EDGE)


def fig_matchmaker(matches: List[MatchSonucu]):
    if not matches or not _MPL_OK: return None
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5), facecolor=BG)
    # — Bar: Uyum Puanı —
    ax = axes[0]
    isimler = [f"#{i+1}\n{m.ana.line_id[:8]}×{m.baba.line_id[:8]}" for i,m in enumerate(matches)]
    puanlar = [m.puan for m in matches]
    renkler = [MINT, GRN, GREY][:len(matches)]
    bars = ax.bar(isimler, puanlar, color=renkler, edgecolor=EDGE, linewidth=0.8)
    for b,p in zip(bars, puanlar):
        ax.text(b.get_x()+b.get_width()/2, b.get_height()+0.5,
                f"{p:.1f}", ha="center", fontsize=10, color=WHT, fontweight="bold")
    ax.set_ylim(0, 115)
    _ax_style(ax, "En İyi Eşleşmeler — Uyum Puanı", ylabel="Puan (0-100)")
    # — Radar: F2 olasılık karşılaştırması —
    ax2 = axes[1]
    kategoriler = ["Uyum\nPuanı", "F2\nOlasılık", "Verim", "Raf\nÖmrü", "Markör"]
    N = len(kategoriler)
    import numpy as np
    acılar = np.linspace(0, 2*np.pi, N, endpoint=False).tolist()
    acılar += acılar[:1]
    ax_r = fig.add_axes([0.555, 0.08, 0.42, 0.84], polar=True)
    ax_r.set_facecolor(PANEL)
    rk = [MINT, GRN, GREY]
    for idx, m in enumerate(matches[:3]):
        avg_v  = (m.ana.fiziksel.verim_skoru + m.baba.fiziksel.verim_skoru) / 2
        avg_r  = (m.ana.fiziksel.raf_omru_gun + m.baba.fiziksel.raf_omru_gun) / 2
        avg_mk = (len(m.ana.markorler) + len(m.baba.markorler)) / 2
        vals = [m.puan/100, m.hedef_p_f2, avg_v/10, min(avg_r/30,1), min(avg_mk/10,1)]
        vals += vals[:1]
        ax_r.plot(acılar, vals, linewidth=1.8, color=rk[idx],
                  label=f"#{idx+1} {m.ana.line_id[:5]}×{m.baba.line_id[:5]}")
        ax_r.fill(acılar, vals, alpha=0.1, color=rk[idx])
    ax_r.set_xticks(acılar[:-1]); ax_r.set_xticklabels(kategoriler, fontsize=8, color=WHT)
    ax_r.tick_params(colors=GREY); ax_r.spines["polar"].set_color(EDGE)
    ax_r.grid(color=EDGE, alpha=0.5)
    ax_r.set_title("Çok Boyutlu Karşılaştırma", color=MINT, fontsize=10, fontweight="bold", pad=15)
    ax_r.legend(loc="upper right", bbox_to_anchor=(1.4, 1.1), fontsize=8,
                facecolor=PANEL, labelcolor=WHT, edgecolor=EDGE)
    axes[1].axis("off")
    plt.tight_layout()
    return fig


def fig_linkage(link_list: List[LinkageSonucu]):
    if not link_list or not _MPL_OK: return None
    fig, ax = plt.subplots(figsize=(9, 4.5), facecolor=BG)
    ax.set_facecolor(PANEL)
    rk_map = {"YÜKSEK": RED, "ORTA": YLW, "DÜŞÜK": GRN}
    for s in link_list:
        clr = rk_map.get(s.uyari_seviye, GREY)
        ax.scatter(s.cm_mesafe, s.suruklenme_r*100, c=clr, s=180, zorder=5,
                   edgecolors=EDGE, linewidth=0.8)
        ax.annotate(f"{s.gen_hedef}↔{s.gen_surukle}",
                    (s.cm_mesafe, s.suruklenme_r*100),
                    textcoords="offset points", xytext=(7,5),
                    fontsize=8, color=WHT)
    ax.axvline(5,  color=RED,  linestyle="--", linewidth=1, alpha=0.7, label="5 cM (Kritik Eşik)")
    ax.axvline(20, color=YLW, linestyle="--", linewidth=1, alpha=0.7, label="20 cM (Orta Eşik)")
    for lbl, clr in [("Yüksek Risk",RED),("Orta Risk",YLW),("Düşük Risk",GRN)]:
        ax.scatter([],[],c=clr,s=80,label=lbl)
    ax.legend(fontsize=8, facecolor=PANEL, labelcolor=WHT, edgecolor=EDGE)
    _ax_style(ax, "Linkage Drag Haritası", "Genetik Mesafe (cM)", "Sürüklenme Riski (%)")
    plt.tight_layout(); return fig


def fig_f2(plan: PopulasyonPlan):
    if not plan or not _MPL_OK: return None
    fig, ax = plt.subplots(figsize=(9, 4), facecolor=BG)
    ax.set_facecolor(PANEL)
    hedef = " | ".join(f"{g}:Dom" for g in plan.hedef_genler)
    labels = list(plan.f2_tablo.keys())
    vals   = [v*100 for v in plan.f2_tablo.values()]
    colors = [MINT if e == hedef else "#1e4d7b" for e in labels]
    bars   = ax.bar(range(len(labels)), vals, color=colors, edgecolor=EDGE, linewidth=0.8)
    for b,v in zip(bars, vals):
        ax.text(b.get_x()+b.get_width()/2, b.get_height()+0.3,
                f"{v:.1f}%", ha="center", fontsize=8, color=WHT)
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels([l[:20] for l in labels], rotation=32, ha="right", fontsize=7.5, color=WHT)
    h_p = mpatches.Patch(color=MINT, label=f"Hedef fenotip (%{plan.hedef_p*100:.2f})")
    o_p = mpatches.Patch(color="#1e4d7b", label="Diğer fenotip")
    ax.legend(handles=[h_p,o_p], fontsize=8, facecolor=PANEL, labelcolor=WHT, edgecolor=EDGE)
    _ax_style(ax, "F2 Fenotip Olasılık Dağılımı", ylabel="Olasılık (%)")
    plt.tight_layout(); return fig


def fig_scatter_matrix(inv: Inventory):
    if not _MPL_OK: return None
    fig, ax = plt.subplots(figsize=(9, 5), facecolor=BG)
    ax.set_facecolor(PANEL)
    tur_renk = {}; palet = [MINT, YLW, "#388bfd","#a371f7", RED]
    tc = 0
    for h in inv.hepsi():
        if h.tur not in tur_renk:
            tur_renk[h.tur] = palet[tc % len(palet)]; tc += 1
    for h in inv.hepsi():
        ax.scatter(h.fiziksel.verim_skoru, h.fiziksel.raf_omru_gun,
                   color=tur_renk[h.tur], s=100, zorder=5, edgecolors=EDGE, linewidth=0.7)
        ax.annotate(h.line_id, (h.fiziksel.verim_skoru, h.fiziksel.raf_omru_gun),
                    textcoords="offset points", xytext=(5,4), fontsize=8, color=WHT)
    for tur, clr in tur_renk.items():
        ax.scatter([],[],color=clr,label=tur[:25],s=70)
    ax.legend(fontsize=8, facecolor=PANEL, labelcolor=WHT, edgecolor=EDGE)
    _ax_style(ax, "Hat Matrisi: Verim × Raf Ömrü", "Verim Skoru (1-10)", "Raf Ömrü (gün)")
    plt.tight_layout(); return fig


# ─────────────────────────────────────────────────────────────────────
# §6  STREAMLIT SAYFALARI
# ─────────────────────────────────────────────────────────────────────

def page_dashboard(inv: Inventory):
    st.markdown("""
    <div class="bv-hero">
        <h1 style="font-size:2.6rem;margin-bottom:0.2rem">🧬 Biovalent Sentinel</h1>
        <p style="color:#7de8c5;font-size:1.15rem;margin:0;letter-spacing:1.5px">
            DECODING THE BONDS OF LIFE
        </p>
        <p style="color:#4a6a8a;font-size:0.85rem;margin-top:0.5rem">
            v9.0 · Global Bioinformatics SaaS Platform
        </p>
    </div>
    """, unsafe_allow_html=True)

    # KPI satırı
    hatlar = inv.hepsi()
    turler = len(set(h.tur for h in hatlar))
    dna_var = sum(1 for h in hatlar if h.dna_dizisi)
    toplam_markor = sum(len(h.markorler) for h in hatlar)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("🌱 Toplam Hat", len(inv))
    c2.metric("🔬 Tür Sayısı", turler)
    c3.metric("🧪 DNA Kayıtlı", f"{dna_var}/{len(inv)}")
    c4.metric("📍 Toplam Markör", toplam_markor)

    st.markdown("---")
    col_l, col_r = st.columns([3, 2])
    with col_l:
        st.markdown("### 📋 Hat Envanteri")
        import pandas as pd
        df = pd.DataFrame(inv.listele())
        st.dataframe(df, use_container_width=True, height=320)
    with col_r:
        st.markdown("### 🗺️ Verim × Raf Ömrü Matrisi")
        fig = fig_scatter_matrix(inv)
        if fig: st.pyplot(fig, use_container_width=True)

    st.markdown("---")
    st.markdown("### 📚 Platform Modülleri")
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown("""<div class="bv-card">
            <h4 style="color:#00ffaa">🧬 Matchmaker</h4>
            <p style="color:#8ab0cc;font-size:0.87rem">
            Hedef fenotipe en uygun ebeveyn çiftlerini otomatik sıralar.
            Mendel + etiket + fenotip uyum skoru kullanır.</p>
        </div>""", unsafe_allow_html=True)
    with m2:
        st.markdown("""<div class="bv-card">
            <h4 style="color:#ffd166">⚠️ Risk Engine</h4>
            <p style="color:#8ab0cc;font-size:0.87rem">
            Linkage drag'i Haldane harita fonksiyonu ile hesaplar.
            Rekombinasyon için gereken bitki sayısını verir.</p>
        </div>""", unsafe_allow_html=True)
    with m3:
        st.markdown("""<div class="bv-card">
            <h4 style="color:#7de8c5">🔍 Genetic Detective</h4>
            <p style="color:#8ab0cc;font-size:0.87rem">
            Bilinmeyen hibritin olası ebeveynlerini k-mer Jaccard
            ve IBS kinship analizi ile tahmin eder.</p>
        </div>""", unsafe_allow_html=True)
    with m4:
        st.markdown("""<div class="bv-card">
            <h4 style="color:#a78bfa">🧪 Proteomic Insights</h4>
            <p style="color:#8ab0cc;font-size:0.87rem">
            DNA → amino asit çevirisi ve motif taraması ile
            protein sınıfı ve tarla etkisini yorumlar.</p>
        </div>""", unsafe_allow_html=True)

    st.markdown("---")
    st.caption(f"© {datetime.now().year} {FIRMA} · {SLOGAN} · v{VER}")


def page_matchmaker(inv: Inventory):
    st.markdown("## 🧬 Matchmaker — Akıllı Ebeveyn Seçici")
    st.info("Hedef fenotip etiketleri ve markör genlerini girerek envanterdeki en uyumlu ebeveyn çiftlerini bulun.", icon="ℹ️")

    with st.expander("📖 Algoritma Açıklaması", expanded=False):
        st.markdown("""
        **Uyum Puanı (0-100)** şu üç bileşenden oluşur:
        - **Etiket eşleşmesi (%50)** — Hedef etiketlerin Ana+Baba etiket havuzunda bulunma oranı
        - **Markör uyumu (%30)** — Dominant markör sayısına göre genetik uyum
        - **Fenotipik yakınlık (%20)** — Normalize edilmiş verim × raf ömrü ortalaması

        **F2 Hedef Olasılığı** — Mendel bağımsız ayrışma yasasına göre F1×F1 çaprazlamasında
        tüm hedef genlerin dominant fenotipte görülme olasılığı.
        """)

    col1, col2 = st.columns([1, 1])
    with col1:
        hedef_str = st.text_input(
            "🎯 Hedef Etiketler (virgülle ayırın)",
            value="sarı meyve, uzun raf ömrü, virüs direnci",
            help="Örn: sarı meyve, fusarium direnci, yüksek verim"
        )
        hedef_genler_str = st.text_input(
            "🧬 Mendel Analizi için Gen Listesi (virgülle ayırın)",
            value="y, rin, Tm-2a",
            help="Örn: I, Tm-2a, y  — Büyük/küçük harf duyarsız"
        )
    with col2:
        n_eslesme = st.slider("En İyi Kaç Eşleşme?", 1, 5, 3)
        tür_filtre = st.selectbox(
            "Tür Filtresi (opsiyonel)",
            ["Tümü"] + list(set(h.tur for h in inv.hepsi()))
        )

    if st.button("🚀 Eşleştirme Analizini Başlat", key="mm_btn"):
        hedefler  = [h.strip() for h in hedef_str.split(",") if h.strip()]
        genler    = [g.strip() for g in hedef_genler_str.split(",") if g.strip()]

        # Tür filtresi
        filtreli_inv = Inventory()
        for h in inv.hepsi():
            if tür_filtre == "Tümü" or h.tur == tür_filtre:
                filtreli_inv.ekle(h)

        if len(filtreli_inv) < 2:
            st.warning("En az 2 hat gereklidir. Tür filtresini genişletin.", icon="⚠️")
            return

        with st.spinner("Genetik uyum analizi yapılıyor..."):
            mm = Matchmaker()
            sonuclar = mm.en_iyi(filtreli_inv, hedefler, genler, n_eslesme)

        if not sonuclar:
            st.error("Uyumlu çift bulunamadı. Hedefleri veya tür filtresini gözden geçirin.")
            return

        st.success(f"✅ {len(sonuclar)} eşleşme bulundu.", icon="✅")

        # Metrik satırı
        best = sonuclar[0]
        m1, m2, m3 = st.columns(3)
        m1.metric("🥇 En İyi Puan", f"{best.puan:.1f}/100")
        m2.metric("F2 Hedef Olasılığı", f"%{best.hedef_p_f2*100:.2f}")
        m3.metric("Karşılanan Hedefler", f"{len(best.karsilanan)}/{len(hedefler)}")

        # Grafik
        fig = fig_matchmaker(sonuclar)
        if fig:
            st.pyplot(fig, use_container_width=True)

        st.markdown("---")
        st.markdown("### 🏆 Sıralı Eşleşme Raporu")

        madalya = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
        for i, s in enumerate(sonuclar):
            with st.expander(
                f"{madalya[i]}  #{i+1}  —  {s.ana.line_id} (♀) × {s.baba.line_id} (♂)"
                f"  |  Puan: {s.puan:.1f}/100",
                expanded=(i==0)
            ):
                c_l, c_r = st.columns(2)
                with c_l:
                    st.markdown(f"**Ana (♀):** `{s.ana.line_id}` — {s.ana.adi}")
                    st.markdown(f"**Baba (♂):** `{s.baba.line_id}` — {s.baba.adi}")
                    st.markdown(f"**F1 Hedef p:** %{s.hedef_p_f1*100:.1f}")
                    st.markdown(f"**F2 Hedef p:** %{s.hedef_p_f2*100:.4f}")
                with c_r:
                    if s.karsilanan:
                        st.success("✅ Karşılanan: " + ", ".join(s.karsilanan))
                    if s.eksik:
                        st.warning("⚠️ Eksik: " + ", ".join(s.eksik))
                    else:
                        st.success("Tüm hedefler karşılanabilir!")
                st.info(s.yorum, icon="💡")

                # Populasyon planı butonu
                if st.button(f"📊 Bu çift için Populasyon Planı Oluştur",
                             key=f"pop_{i}_{s.ana.line_id}"):
                    pl = Planlayici()
                    plan = pl.planla(s.ana, s.baba, genler,
                                     f"{s.ana.line_id} × {s.baba.line_id}")
                    st.markdown("#### 🌱 F1 Genotipi")
                    for geno, gen in plan.f1_genotip.items():
                        st.code(f"{gen:>10}  →  {geno}")
                    st.markdown("#### 📊 Populasyon Büyüklüğü")
                    pc1, pc2, pc3, pc4 = st.columns(4)
                    pc1.metric("Minimum Bitki", f"{plan.min_bitki:,}")
                    pc2.metric("+ Tampon", f"{plan.tampon:,}")
                    pc3.metric("Toplam F2", f"{plan.toplam:,}")
                    pc4.metric("Seçim Havuzu (→F3)", f"{plan.secim:,}")
                    fig_f2_chart = fig_f2(plan)
                    if fig_f2_chart:
                        st.pyplot(fig_f2_chart, use_container_width=True)
                    st.info(plan.tavsiye, icon="📋")


def page_risk_engine(inv: Inventory):
    st.markdown("## ⚠️ Risk Engine — Genetik Bağlantı & Linkage Drag Analizi")
    st.info(
        "Belirtilen genler için bilinen genetik bağlantı verilerini analiz eder. "
        "Yüksek risk, istenmeyen genlerin hedef genlerle birlikte kalıtılma olasılığını gösterir.",
        icon="ℹ️"
    )

    with st.expander("📖 Bilimsel Temel", expanded=False):
        st.markdown("""
        **Haldane Harita Fonksiyonu:**  `r = 0.5 × (1 − e^(−2d/100))`

        Burada `d` = centiMorgan (cM) cinsinden genetik mesafe, `r` = rekombinasyon frekansı.

        **Rekombinan Bitki Sayısı:** `n = ⌈ log(0.05) / log(1 − r) ⌉`  (%95 güven)

        | cM Mesafe | Risk | Yorum |
        |---|---|---|
        | < 5 cM | 🔴 Yüksek | Neredeyse her zaman birlikte kalıtılır |
        | 5–20 cM | 🟡 Orta | Linkage drag olası; izleme gerekli |
        | > 20 cM | 🟢 Düşük | Rekombinasyon görece kolay |
        """)

    gen_str = st.text_input(
        "🧬 Analiz Edilecek Genler (virgülle ayırın)",
        value="Tm-2a, rin, I, y",
        help="Dahili linkage haritasında bulunan genler analiz edilir."
    )

    st.markdown("**İsteğe Bağlı: Özel cM Haritası**")
    custom_cols = st.columns(3)
    with custom_cols[0]: c_gen_a = st.text_input("Gen A", placeholder="örn. MyGene")
    with custom_cols[1]: c_gen_b = st.text_input("Gen B", placeholder="örn. OtherGene")
    with custom_cols[2]: c_cm    = st.number_input("cM Mesafe", 0.0, 200.0, 10.0, step=0.5)

    if st.button("🔍 Risk Analizini Başlat", key="risk_btn"):
        genler = [g.strip() for g in gen_str.split(",") if g.strip()]
        ek_map = {}
        if c_gen_a and c_gen_b and c_cm > 0:
            ek_map[c_gen_a] = {c_gen_b: c_cm}
            ek_map[c_gen_b] = {c_gen_a: c_cm}

        with st.spinner("Linkage haritası analiz ediliyor..."):
            eng = LinkageDragEngine()
            sonuclar = eng.analiz_et(genler, ek_map if ek_map else None)

        if not sonuclar:
            st.success("✅ Analiz edilen genler arasında bilinen linkage bulunamadı.", icon="✅")
            return

        # Özet metrikler
        yuksek = sum(1 for s in sonuclar if s.uyari_seviye == "YÜKSEK")
        orta   = sum(1 for s in sonuclar if s.uyari_seviye == "ORTA")
        dusuk  = sum(1 for s in sonuclar if s.uyari_seviye == "DÜŞÜK")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Toplam Bağlantı", len(sonuclar))
        m2.metric("🔴 Yüksek Risk", yuksek)
        m3.metric("🟡 Orta Risk", orta)
        m4.metric("🟢 Düşük Risk", dusuk)

        # Grafik
        fig = fig_linkage(sonuclar)
        if fig:
            st.pyplot(fig, use_container_width=True)

        st.markdown("---")
        st.markdown("### 📋 Detaylı Risk Raporu")
        for s in sonuclar:
            sev_map = {"YÜKSEK": "error", "ORTA": "warning", "DÜŞÜK": "success"}
            sev_icon = {"YÜKSEK": "🔴", "ORTA": "🟡", "DÜŞÜK": "🟢"}
            fn = {"error": st.error, "warning": st.warning, "success": st.success}
            with st.expander(
                f"{sev_icon[s.uyari_seviye]}  {s.gen_hedef} ↔ {s.gen_surukle}"
                f"  |  {s.cm_mesafe:.1f} cM  |  Risk: {s.uyari_seviye}",
                expanded=(s.uyari_seviye == "YÜKSEK")
            ):
                cc1, cc2, cc3 = st.columns(3)
                cc1.metric("Genetik Mesafe", f"{s.cm_mesafe:.1f} cM")
                cc2.metric("Rekombinasyon p", f"%{s.rekomb_p*100:.2f}")
                cc3.metric("Gerekli Bitki", f"{s.gerekli_bitki:,}")
                fn[sev_map[s.uyari_seviye]](s.aciklama)


def page_detective(inv: Inventory):
    st.markdown("## 🔍 Genetic Detective — Tersine Soy Ağacı")
    st.info(
        "Bilinmeyen bir hibritin DNA dizisini ve/veya markörlerini girerek "
        "envanterdeki hatlarla en yüksek kinship uyumunu hesaplar.",
        icon="ℹ️"
    )

    with st.expander("📖 Yöntem Açıklaması", expanded=False):
        st.markdown("""
        **Toplam Güven Skoru** iki bileşenden oluşur:
        - **Kinship (%60)** — IBS (Identity-by-State): Hibritteki markörler ebeveyn
          havuzuyla ne kadar örtüşüyor?
        - **DNA Benzerliği (%40)** — k-mer Jaccard benzerliği (k=8): İki dizi arasında
          ortak 8-nükleotid alt dizisi oranı.

        > ⚠️ Bu analiz probabilistik bir ön tahmindir. Kesin parentage testi için
        > SNP çip verisi veya SSR markör paneli gereklidir.
        """)

    col1, col2 = st.columns([1, 1])
    with col1:
        hibrit_id  = st.text_input("Hibrit ID", value="HYB-UNKNOWN-01")
        hibrit_adi = st.text_input("Hibrit Adı", value="Bilinmeyen Sarı Hibrit")
        hibrit_tur = st.selectbox("Tür",
            ["Solanum lycopersicum","Capsicum annuum","Cucumis melo"])
        hibrit_dna = st.text_area(
            "DNA Dizisi (opsiyonel — FASTA veya düz nükleotid)",
            height=100,
            placeholder=">Hibrit_DNA\nATGGAGAGTGGAATTTCAGATTTTAAGT...",
        )
    with col2:
        st.markdown("**Hibrit Markör Profili**")
        st.caption("Aşağıya hibritte tespit edilen gen ve alel bilgilerini girin.")
        m_gen1  = st.text_input("Gen 1", value="y",     key="d_g1")
        m_alel1 = st.selectbox("Gen 1 Alel", list(ALEL_ETIKET.values()), key="d_a1", index=0)
        m_gen2  = st.text_input("Gen 2", value="Tm-2a", key="d_g2")
        m_alel2 = st.selectbox("Gen 2 Alel", list(ALEL_ETIKET.values()), key="d_a2", index=1)
        m_gen3  = st.text_input("Gen 3 (opsiyonel)", value="rin", key="d_g3")
        m_alel3 = st.selectbox("Gen 3 Alel", list(ALEL_ETIKET.values()), key="d_a3", index=1)

    if st.button("🔎 Ebeveyn Analizi Başlat", key="det_btn"):
        # Alel seçimlerini Alel enum'una çevir
        alel_ters = {v: k for k, v in ALEL_ETIKET.items()}
        markorler = []
        for gen, alel_etk in [(m_gen1, m_alel1), (m_gen2, m_alel2)]:
            if gen:
                markorler.append(GeneticMarker(gen, "?", alel_ters[alel_etk]))
        if m_gen3:
            markorler.append(GeneticMarker(m_gen3, "?", alel_ters[m_alel3]))

        hibrit = BreederLine(
            hibrit_id, hibrit_adi, hibrit_tur,
            dna_dizisi=hibrit_dna or None,
            markorler=markorler,
        )

        tür_filtreli = Inventory()
        for h in inv.hepsi():
            if h.tur == hibrit_tur:
                tür_filtreli.ekle(h)

        if len(tür_filtreli) < 2:
            st.warning("Seçilen türde en az 2 hat gereklidir.", icon="⚠️")
            return

        with st.spinner("Kinship ve DNA benzerlik analizi yapılıyor..."):
            det = GeneticDetective()
            adaylar = det.tanimlama_yap(tür_filtreli, hibrit, n=3)

        if not adaylar:
            st.error("Aday ebeveyn bulunamadı.")
            return

        st.success(f"✅ {len(adaylar)} aday ebeveyn çifti belirlendi.", icon="🔬")

        best = adaylar[0]
        m1, m2, m3 = st.columns(3)
        m1.metric("En Yüksek Güven", f"%{best.toplam*100:.1f}")
        m2.metric("Kinship Skoru", f"%{best.kinship*100:.1f}")
        m3.metric("DNA Benzerliği", f"%{best.benzerlik_pct:.1f}")

        st.markdown("---")
        for i, a in enumerate(adaylar):
            with st.expander(
                f"{'🥇' if i==0 else '🥈' if i==1 else '🥉'}  Aday #{i+1}  "
                f"— {a.hat1.line_id} × {a.hat2.line_id}  "
                f"|  Güven: %{a.toplam*100:.1f}",
                expanded=(i==0)
            ):
                ac1, ac2 = st.columns(2)
                with ac1:
                    st.markdown(f"**Hat-1:** `{a.hat1.line_id}` — {a.hat1.adi}")
                    st.markdown(f"**Hat-2:** `{a.hat2.line_id}` — {a.hat2.adi}")
                with ac2:
                    st.metric("Kinship", f"%{a.kinship*100:.1f}")
                    st.metric("DNA Benzerliği", f"%{a.benzerlik_pct:.1f}")
                if a.toplam >= 0.6:
                    st.success(a.aciklama, icon="🟢")
                elif a.toplam >= 0.4:
                    st.warning(a.aciklama, icon="🟡")
                else:
                    st.info(a.aciklama, icon="🔵")


def page_proteomic(inv: Inventory):
    st.markdown("## 🧪 Proteomic Insights — Evrensel Proteomik Yorumlayıcı")
    st.info(
        "DNA dizisini amino asite çevirir, bilinen protein motiflerini tarar "
        "ve tarladaki beklenen etkiyi yorumlar. "
        "Veritabanında tanımlı olmayan diziler için sıfır-bilgi analizi yapar.",
        icon="ℹ️"
    )

    with st.expander("📖 Analiz Süreci", expanded=False):
        st.markdown("""
        1. **DNA Temizleme** — FASTA başlıkları, boşluklar, geçersiz karakterler kaldırılır.
        2. **3-Çerçeve Çevirisi** — Her üç okuma çerçevesi denenir; en uzun ORF seçilir.
        3. **Motif Taraması** — 8 bilinen protein motifi (regex) ile amino asit dizisi taranır.
        4. **Protein Sınıfı Tayini** — Bulunan motiflere göre hiyerarşik sınıflandırma.
        5. **Tarla Etkisi Yorumu** — Tespit edilen protein sınıfının beklenen fenotipik etkisi.

        > ⚠️ Bu analiz örüntü eşleşmesi tabanlıdır. Kesin sonuç için AlphaFold /
        > InterPro / Pfam kullanılması önerilir.
        """)

    # Demo dizisi seç veya elle gir
    demo_dizi = (
        "ATGGGCGTTGGCAAAACTACCATGCTTGCAGCTGATTTGCGTCAGAAGATGGCTGCAGAGCTGAAAGAT"
        "CGCTTTGCGATGGTGGATGGCGTGGGCGAAGTGGACTCTTTTGGCGACTTCCTCAAAACACTCGCAGAG"
        "GAGATCATTGGCGTCGTCAAAGATAGTAAACTCTATTTGTTGCTTCTTTTAAGTGGCAGGACTTGGCAT"
        "GTTGGGCGGCGTACTTGGCATTTCAATGGGCGGACAAGAAGTTCCTCATACCGAGAGAGAGTGGGCGTT"
        "GGCAAAACTACCGTATGGGCGGCAAGAAGTTCCTTGAGGGGGTGGCAAAACCATGGCTGGCAGACTTGC"
    )

    col_opt, col_inv = st.columns([2, 1])
    with col_opt:
        kaynak = st.radio("DNA Kaynağı", ["Demo Dizi (NBS-LRR)", "Envanterdeki Hat", "Elle Gir"],
                          horizontal=True)
    with col_inv:
        secili_hat = None
        if kaynak == "Envanterdeki Hat":
            secili_hat = st.selectbox("Hat Seç",
                [h.line_id for h in inv.hepsi() if h.dna_dizisi])

    if kaynak == "Demo Dizi (NBS-LRR)":
        dna_input = demo_dizi
        st.code(dna_input[:120] + "...", language="text")
    elif kaynak == "Envanterdeki Hat" and secili_hat:
        hat = inv.getir(secili_hat)
        dna_input = hat.dna_dizisi or ""
        st.code((dna_input[:120] + "...") if dna_input else "DNA yok", language="text")
    else:
        dna_input = st.text_area(
            "DNA Dizisi (FASTA veya düz nükleotid)",
            height=160,
            placeholder=">Bilinmeyen_Gen\nATGGGCGTTGGCAAAACTACC...",
        )

    if st.button("🔬 Proteomik Analizi Başlat", key="prot_btn"):
        if not dna_input or len(dna_input.strip()) < 30:
            st.error("Lütfen en az 30 nükleotid içeren bir dizi girin.", icon="❌")
            return

        with st.spinner("DNA çevirisi ve motif taraması yapılıyor..."):
            prot = ProteomikYorumlayici()
            sonuc = prot.analiz_et(dna_input)

        # KPI satırı
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("DNA Uzunluğu", f"{sonuc.dna_uzunluk} bp")
        m2.metric("AA Uzunluğu", f"{sonuc.aa_uzunluk} aa")
        m3.metric("Bulunan Motif", len(sonuc.motifler))
        guven_kisa = sonuc.guven.split(" ")[0]
        m4.metric("Güven", guven_kisa)

        st.markdown("---")

        # Protein sınıfı
        st.markdown(f"### 🏷️ Protein Sınıfı: `{sonuc.protein_sinifi}`")
        st.markdown(f"**Biyolojik İşlev:** {sonuc.fonksiyon}")
        st.success(f"🌾 Tarla Etkisi: {sonuc.tarla_etkisi}", icon="🌿")

        # AA dizisi
        with st.expander("🔤 Amino Asit Dizisi (ilk 80)", expanded=False):
            st.code(sonuc.aa_dizisi, language="text")

        st.markdown("---")
        st.markdown("### 🔬 Bulunan Protein Motifleri")
        if sonuc.motifler:
            for m in sonuc.motifler:
                pozisyonlar = ", ".join(str(k) for k in m.get("konumlar",[]))
                with st.expander(f"**{m['isim']}** — `{m['motif']}`  |  {m['kategori']}"):
                    mc1, mc2 = st.columns(2)
                    with mc1:
                        st.markdown(f"**Kategori:** {m['kategori']}")
                        st.markdown(f"**Motif Pattern:** `{m['motif']}`")
                        st.markdown(f"**Konum(lar):** {pozisyonlar}")
                    with mc2:
                        st.markdown(f"**Biyolojik İşlev:** {m['islev']}")
                        st.info(f"🌾 Tarla Etkisi: {m['tarla']}", icon="🌾")
        else:
            st.warning("Bilinen motif bulunamadı. AlphaFold veya InterPro analizi önerilir.", icon="⚠️")

        st.caption(f"⚠️ Güven Notu: {sonuc.guven}")


# ─────────────────────────────────────────────────────────────────────
# §7  SIDEBAR & ROUTER
# ─────────────────────────────────────────────────────────────────────

def sidebar():
    with st.sidebar:
        st.markdown("""
        <div style="text-align:center;padding:1.2rem 0 0.5rem">
            <div style="font-size:2.2rem">🧬</div>
            <div style="color:#00ffaa;font-weight:800;font-size:1.15rem;letter-spacing:1px">
                BIOVALENT
            </div>
            <div style="color:#4a6a8a;font-size:0.72rem;letter-spacing:2px;margin-top:2px">
                SENTINEL v9.0
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")

        sayfa = st.radio(
            "Navigasyon",
            options=[
                "🏠 Dashboard",
                "🧬 Matchmaker",
                "⚠️ Risk Engine",
                "🔍 Genetic Detective",
                "🧪 Proteomic Insights",
            ],
            label_visibility="collapsed",
        )

        st.markdown("---")
        st.markdown("""
        <div style="color:#4a6a8a;font-size:0.75rem;line-height:1.6">
            <b style="color:#7de8c5">Bilimsel Referanslar</b><br>
            Jones et al. (1993) — Fusarium <i>I</i> geni<br>
            Pelham (1966) — TMV <i>Tm-2a</i><br>
            Martin et al. (1993) — <i>Pto</i> kinaz<br>
            Giovannoni (2004) — <i>rin</i> geni<br>
            Rossi et al. (1998) — <i>Mi-1.2</i>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("""
        <div style="color:#4a6a8a;font-size:0.72rem;text-align:center">
            © 2025 Biovalent · Decoding the Bonds of Life<br>
            <span style="color:#1e4d7b">SaaS Platformu · Kurumsal Lisans</span>
        </div>
        """, unsafe_allow_html=True)

    return sayfa


def main():
    inv   = demo_envanter()
    sayfa = sidebar()

    if "Dashboard" in sayfa:
        page_dashboard(inv)
    elif "Matchmaker" in sayfa:
        page_matchmaker(inv)
    elif "Risk Engine" in sayfa:
        page_risk_engine(inv)
    elif "Detective" in sayfa:
        page_detective(inv)
    elif "Proteomic" in sayfa:
        page_proteomic(inv)


# ─────────────────────────────────────────────────────────────────────
# §8  GİRİŞ NOKTASI
# ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    main()

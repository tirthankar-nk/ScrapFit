
import json
import re
import uuid
from pathlib import Path

import streamlit as st

# -------------------- CONFIGURATION --------------------

st.set_page_config(
    page_title="ScrapFit",
    page_icon="♻️",
    layout="wide",
)

# -------------------- SCRAPFIT UI THEME --------------------

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@400;500;600;700;800&display=swap');

    :root {
        --forest: #215747;
        --forest-dark: #173F34;
        --mint: #E8F1E9;
        --paper: #F7F8F4;
        --ink: #202B26;
        --muted: #718078;
        --line: #E1E7E0;
    }

    .stApp {
        background: var(--paper);
        color: var(--ink);
        font-family: 'DM Sans', sans-serif;
    }

    [data-testid="stHeader"] {
        background: rgba(247, 248, 244, 0.92);
    }

    [data-testid="stSidebar"] {
        background: #EDF2EB;
        border-right: 1px solid var(--line);
    }

    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {
        color: var(--forest-dark);
        font-family: 'Manrope', sans-serif;
    }

    h1, h2, h3 {
        color: var(--forest-dark);
        font-family: 'Manrope', sans-serif !important;
        letter-spacing: -0.5px;
    }

    h1 {
        font-weight: 800 !important;
    }

    p, label, .stMarkdown {
        color: var(--ink);
    }

    [data-testid="stMetric"] {
        background: white;
        border: 1px solid var(--line);
        border-radius: 14px;
        padding: 14px 16px;
        box-shadow: 0 2px 8px rgba(23, 63, 52, 0.035);
    }

    [data-testid="stMetricLabel"] {
        color: var(--muted);
        font-weight: 600;
    }

    [data-testid="stMetricValue"] {
        color: var(--forest);
        font-family: 'Manrope', sans-serif;
        font-weight: 800;
    }

    .stButton > button,
    .stFormSubmitButton > button {
        background: var(--forest);
        color: white;
        border: 1px solid var(--forest);
        border-radius: 9px;
        min-height: 42px;
        font-weight: 600;
        transition: all 0.2s ease;
    }

    .stButton > button:hover,
    .stFormSubmitButton > button:hover {
        background: var(--forest-dark);
        color: white;
        border-color: var(--forest-dark);
        transform: translateY(-1px);
    }

    /* Home hero action buttons: light background with readable dark text */
    .st-key-home_hero .stButton > button {
        background: #F0F5F0;
        color: #205747;
        border-color: #F0F5F0;
    }

    .st-key-home_hero .stButton > button:hover {
        background: #DCE9DF;
        color: #173F34;
        border-color: #DCE9DF;
    }

    .stTextInput input,
    .stNumberInput input,
    .stTextArea textarea,
    [data-baseweb="select"] > div {
        border-radius: 9px;
        border-color: #D8E1D8;
    }

    [data-baseweb="tab-list"] {
        gap: 8px;
        border-bottom: 1px solid var(--line);
    }

    [data-baseweb="tab"] {
        background: transparent;
        border-radius: 8px 8px 0 0;
        padding: 10px 14px;
        font-weight: 600;
    }

    [aria-selected="true"][data-baseweb="tab"] {
        color: var(--forest) !important;
    }

    [data-testid="stVerticalBlockBorderWrapper"] {
        border-color: var(--line);
        border-radius: 14px;
        background: white;
        padding: 10px;
        box-shadow: 0 2px 8px rgba(23, 63, 52, 0.025);
    }

    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
        color: var(--muted);
    }

    [data-testid="stSidebar"] [role="radiogroup"] {
        gap: 6px;
    }

    [data-testid="stSidebar"] [role="radiogroup"] label {
        padding: 8px 10px;
        border-radius: 9px;
    }

    [data-testid="stSidebar"] [role="radiogroup"] label:hover {
        background: #DDE9DE;
    }

    .scrapfit-about-card {
        background: white;
        border: 1px solid var(--line);
        border-radius: 14px;
        padding: 18px;
        height: 100%;
    }

    .scrapfit-about-card h3 {
        margin-top: 0;
    }

    [data-testid="stAlert"] {
        border-radius: 12px;
    }

    hr {
        border-color: var(--line);
    }

    .st-key-home_hero {
        background: linear-gradient(120deg, #173F34 0%, #215747 58%, #2F6B52 100%);
        color: white;
        padding: 30px 32px 26px 32px;
        border-radius: 18px;
        margin: 8px 0 24px 0;
        overflow: hidden;
        border: 1px solid rgba(255,255,255,0.08);
    }
    .st-key-home_hero h1, .st-key-home_hero h2, .st-key-home_hero h3,
    .st-key-home_hero p, .st-key-home_hero label,
    .st-key-home_hero [data-testid="stMarkdownContainer"] {
        color: #FFFFFF !important;
    }
    .st-key-home_hero .scrapfit-eyebrow {
        color: #C6E1CD !important;
        font-size: 0.78rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 2px;
        margin-bottom: 12px;
    }
    .st-key-home_hero .scrapfit-hero-art {
        min-height: 180px;
        display: flex;
        align-items: center;
        justify-content: center;
        border: 1px solid rgba(255,255,255,0.16);
        border-radius: 16px;
        background: rgba(232,241,233,0.09);
        padding: 12px;
    }
    .st-key-home_hero .scrapfit-hero-art svg { width: 100%; max-width: 360px; height: auto; display: block; }
    .st-key-home_hero [data-testid="stButton"] > button,
    .st-key-home_hero [data-testid="stButton"] > button * {
        background: #F0F5F0 !important;
        color: #173F34 !important;
        -webkit-text-fill-color: #173F34 !important;
        border-color: #F0F5F0 !important;
        font-weight: 700 !important;
        min-height: 46px;
        opacity: 1 !important;
    }
    .st-key-home_hero [data-testid="stButton"] > button:hover,
    .st-key-home_hero [data-testid="stButton"] > button:hover * {
        background: #DDE9DE !important;
        color: #173F34 !important;
        -webkit-text-fill-color: #173F34 !important;
        border-color: #DDE9DE !important;
    }
    .st-key-home_hero [data-testid="stImage"] img {
        width: 100%;
        height: 220px;
        object-fit: cover;
        border-radius: 16px;
        border: 1px solid rgba(255,255,255,0.2);
    }

    .scrapfit-hero-grid {
        display: grid;
        grid-template-columns: minmax(0, 1.35fr) minmax(220px, 0.8fr);
        align-items: center;
        gap: 24px;
    }

    .scrapfit-hero-copy { min-width: 0; }
    .scrapfit-hero-art {
        min-height: 190px;
        display: flex;
        align-items: center;
        justify-content: center;
        border: 1px solid rgba(255,255,255,0.16);
        border-radius: 16px;
        background: rgba(232,241,233,0.09);
        padding: 12px;
    }
    .scrapfit-hero-art svg { width: 100%; max-width: 360px; height: auto; display: block; }

    @media (max-width: 760px) {
        .scrapfit-hero-grid { grid-template-columns: 1fr; }
        .scrapfit-hero-art { min-height: 130px; }
    }

    .scrapfit-hero h1 {
        color: white !important;
        font-size: 2.2rem;
        line-height: 1.15;
        margin-bottom: 12px;
    }

    .scrapfit-hero p {
        color: #E1EEE4;
        font-size: 1.05rem;
        line-height: 1.7;
        max-width: 650px;
        margin-bottom: 0;
    }

    .scrapfit-eyebrow {
        color: #C6E1CD;
        font-size: 0.78rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 2px;
        margin-bottom: 12px;
    }

    .scrapfit-section-label {
        color: var(--forest);
        font-size: 0.78rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1.4px;
    }

    .scrapfit-note {
        background: var(--mint);
        border-left: 4px solid var(--forest);
        border-radius: 5px 12px 12px 5px;
        padding: 14px 18px;
        margin: 12px 0 20px 0;
        color: var(--forest-dark);
        line-height: 1.6;
    }

    @media (max-width: 768px) {
        .scrapfit-hero {
            padding: 25px 22px;
        }

        .scrapfit-hero h1 {
            font-size: 1.8rem;
        }
    }


    /* Professional ScrapFit design system */
    .block-container { padding-top: 2rem; padding-bottom: 3rem; max-width: 1440px; }
    [data-testid="stSidebar"] { background: #EEF3ED; }
    [data-testid="stSidebar"] [data-testid="stRadio"] label { font-weight: 600; color: #34483D; }
    [data-testid="stSidebar"] [data-testid="stRadio"] label[data-checked="true"] { background: #DCE9DE; }
    .sf-eyebrow { color: #A8D5B7; font-size: .74rem; font-weight: 800; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 14px; }
    .sf-hero-title { font-family: 'Manrope', sans-serif; color: #FFFFFF; font-size: clamp(2.15rem, 3.3vw, 3.5rem); font-weight: 800; line-height: 1.08; letter-spacing: -1.6px; margin: 0 0 18px 0; }
    .sf-hero-copy { color: #E5F0E7; font-size: 1.04rem; line-height: 1.75; max-width: 720px; }
    .sf-hero-kicker { color: #D0E7D5; font-size: .9rem; font-weight: 600; margin-top: 18px; }
    .sf-section-kicker { color: #47745B; text-transform: uppercase; font-size: .73rem; font-weight: 800; letter-spacing: 1.8px; margin-bottom: 6px; }
    .sf-section-title { font-family: 'Manrope', sans-serif; color: #173F34; font-size: 1.8rem; font-weight: 800; letter-spacing: -.6px; margin: 0 0 8px 0; }
    .sf-section-copy { color: #65756B; font-size: .98rem; line-height: 1.7; margin-bottom: 18px; }
    .sf-card { background: #FFFFFF; border: 1px solid #E0E8DF; border-radius: 16px; padding: 22px; height: 100%; box-shadow: 0 5px 18px rgba(23,63,52,.045); }
    .sf-card-icon { display: inline-flex; width: 44px; height: 44px; border-radius: 13px; background: #EAF3E9; color: #215747; align-items: center; justify-content: center; font-size: 1.35rem; margin-bottom: 14px; }
    .sf-card h3 { color: #173F34; font-size: 1.08rem; margin: 0 0 8px 0; letter-spacing: -.2px; }
    .sf-card p { color: #65756B; line-height: 1.65; font-size: .92rem; margin: 0; }
    .sf-step { background: #F0F5EF; border: 1px solid #E0E8DF; border-radius: 14px; padding: 18px; height: 100%; }
    .sf-step-num { font-size: .75rem; color: #47745B; font-weight: 800; letter-spacing: 1.2px; margin-bottom: 8px; }
    .sf-step h3 { font-size: 1rem; color: #173F34; margin: 0 0 8px 0; }
    .sf-step p { color: #65756B; font-size: .9rem; line-height: 1.6; margin: 0; }
    .sf-callout { background: #EAF3E9; border: 1px solid #D7E6D7; border-left: 4px solid #47745B; border-radius: 12px; padding: 16px 18px; color: #254D3B; line-height: 1.65; }
    .sf-flow { display: flex; align-items: center; justify-content: space-between; gap: 8px; background: #173F34; color: white; border-radius: 14px; padding: 20px; }
    .sf-flow span { text-align: center; flex: 1; font-size: .88rem; font-weight: 700; }
    .sf-flow b { color: #A8D5B7; font-size: 1.15rem; }
    .sf-footnote { color: #77857C; font-size: .8rem; line-height: 1.6; }
    .sf-divider { height: 1px; background: #E1E7E0; margin: 28px 0; }
    .st-key-home_hero { background: linear-gradient(125deg, #153D32 0%, #215747 56%, #2D6B51 100%); border-radius: 24px; padding: 34px; border: 1px solid rgba(255,255,255,.1); box-shadow: 0 14px 36px rgba(23,63,52,.12); }
    .st-key-home_hero [data-testid="stImage"] img { height: 310px; object-fit: cover; border-radius: 17px; border: 1px solid rgba(255,255,255,.22); }
    .st-key-home_hero h1, .st-key-home_hero h2, .st-key-home_hero h3, .st-key-home_hero p { color: #FFFFFF; }
    .st-key-home_hero [data-testid="stButton"] > button, .st-key-home_hero [data-testid="stButton"] > button * { background: #F2F6F0 !important; color: #173F34 !important; -webkit-text-fill-color: #173F34 !important; border: 1px solid #F2F6F0 !important; font-weight: 800 !important; opacity: 1 !important; }
    .st-key-home_hero [data-testid="stButton"] > button { min-height: 48px; border-radius: 11px; }
    .st-key-home_hero [data-testid="stButton"] > button:hover, .st-key-home_hero [data-testid="stButton"] > button:hover * { background: #DCE9DE !important; color: #173F34 !important; -webkit-text-fill-color: #173F34 !important; border-color: #DCE9DE !important; }
    @media (max-width: 760px) { .st-key-home_hero { padding: 22px; } .st-key-home_hero [data-testid="stImage"] img { height: 210px; } .sf-flow { flex-direction: column; } }

</style>
""", unsafe_allow_html=True)

DATA_FILE = Path(__file__).with_name("inventory.json")

SAMPLE_INVENTORY = [
    {
        "id": "S001",
        "material": "Wood",
        "name": "Plywood offcut",
        "length": 800,
        "width": 400,
        "thickness": 18,
        "condition": "A - Clean",
        "price": 120,
        "area": "Area A",
        "notes": "Clean rectangular piece",
    },
    {
        "id": "S002",
        "material": "Wood",
        "name": "Pine wood offcut",
        "length": 620,
        "width": 280,
        "thickness": 18,
        "condition": "B - Minor marks",
        "price": 60,
        "area": "Area A",
        "notes": "Minor surface marks",
    },
    {
        "id": "S003",
        "material": "Wood",
        "name": "Plywood panel",
        "length": 1000,
        "width": 500,
        "thickness": 12,
        "condition": "A - Clean",
        "price": 150,
        "area": "Area B",
        "notes": "Suitable for panels",
    },
    {
        "id": "S004",
        "material": "Wood",
        "name": "Small wood piece",
        "length": 550,
        "width": 300,
        "thickness": 18,
        "condition": "C - Usable for small parts",
        "price": 30,
        "area": "Area A",
        "notes": "Useful for smaller components",
    },
    {
        "id": "S005",
        "material": "Metal",
        "name": "Mild steel flat sheet",
        "length": 700,
        "width": 300,
        "thickness": 3,
        "condition": "A - Clean",
        "price": 180,
        "area": "Area B",
        "notes": "Sample mild steel sheet",
    },
    {
        "id": "S006",
        "material": "Metal",
        "name": "Steel offcut",
        "length": 450,
        "width": 250,
        "thickness": 3,
        "condition": "B - Minor marks",
        "price": 70,
        "area": "Area A",
        "notes": "Small reusable sheet",
    },
    {
        "id": "S007",
        "material": "Metal",
        "name": "Steel plate",
        "length": 900,
        "width": 400,
        "thickness": 5,
        "condition": "A - Clean",
        "price": 250,
        "area": "Area C",
        "notes": "Sample plate; verify material grade",
    },
]


def load_inventory():
    """Load saved inventory or create the initial demo inventory."""
    if not DATA_FILE.exists():
        save_inventory(SAMPLE_INVENTORY)
        return SAMPLE_INVENTORY.copy()

    try:
        with DATA_FILE.open("r", encoding="utf-8") as file:
            data = json.load(file)
        return data if isinstance(data, list) else SAMPLE_INVENTORY.copy()
    except (json.JSONDecodeError, OSError):
        st.error("Could not read inventory.json. Check the file before continuing.")
        return []


def save_inventory(items):
    """Save inventory to a local JSON file."""
    with DATA_FILE.open("w", encoding="utf-8") as file:
        json.dump(items, file, indent=2, ensure_ascii=False)


def find_matches(material, length, width, thickness, inventory, allowance_per_side=5):
    """Find pieces with enough extra room for cutting, preferring the smallest fit.

    allowance_per_side is added on every edge, so the piece must fit the
    required length + 2*allowance and width + 2*allowance. This is a simple
    planning allowance, not a guarantee of safe/accurate cutting.
    """
    matches = []
    cut_length = length + (2 * allowance_per_side)
    cut_width = width + (2 * allowance_per_side)

    for piece in inventory:
        if piece.get("material") != material:
            continue

        if piece.get("thickness") != thickness:
            continue

        piece_length = piece.get("length", 0)
        piece_width = piece.get("width", 0)

        fits_normal = piece_length >= cut_length and piece_width >= cut_width
        fits_rotated = piece_length >= cut_width and piece_width >= cut_length

        if not fits_normal and not fits_rotated:
            continue

        match = piece.copy()
        match["rotated"] = not fits_normal and fits_rotated
        # Rank using the material footprint reserved for the part plus allowance.
        match["waste_area"] = (
            piece_length * piece_width - cut_length * cut_width
        )
        match["allowance_per_side"] = allowance_per_side
        matches.append(match)

    # Least remaining area first: smallest suitable offcut is preferred.
    matches.sort(key=lambda item: (item["waste_area"], item.get("length", 0) * item.get("width", 0)))
    return matches


# Listing-specific illustrative stock photos. These are not photos of the exact
# demo pieces. Different listings use different images where possible.
WOOD_PLYWOOD_URL = "https://sosachen.de/cdn/shop/files/1573294661935---1.jpg?v=1738118210&width=1000"
WOOD_PINE_URL = "https://www.gardenbox.co.nz/cdn/shop/files/PineOffcutsFirewood_2.jpg?v=1771889997&width=1445"
WOOD_PANEL_URL = "https://gatediysupplies.co.uk/cdn/shop/files/PLYWOOD_OFFCUTS_85MM_2_6475f63f-24de-4435-ac49-cd3c0f6d570b_1500x.jpg?v=1746008188"
METAL_SHEET_URL = "https://i.etsystatic.com/55905389/r/il/750f82/6906538769/il_fullxfull.6906538769_4qog.jpg"
METAL_OFFCUT_URL = "https://images.unsplash.com/photo-1656285523078-b77363624310?auto=format&fit=crop&w=1000&q=80"
METAL_PLATE_URL = "https://sheetmetalindustries.com/app/uploads/2025/09/Steel-Plate-Supplier.webp"
METAL_RODS_URL = "https://tiimg.tistatic.com/fp/1/008/429/reliable-12-mm-solid-galvanized-finished-hot-rolled-iron-rods-329.jpg"

LISTING_IMAGES = {
    "S001": WOOD_PLYWOOD_URL,
    "S002": WOOD_PINE_URL,
    "S003": WOOD_PANEL_URL,
    "S004": WOOD_PINE_URL,
    "S005": METAL_SHEET_URL,
    "S006": METAL_OFFCUT_URL,
    "S007": METAL_PLATE_URL,
    "S9471E9": WOOD_PLYWOOD_URL,
    "S1537AE": METAL_RODS_URL,
}

STOCK_IMAGES = {"Wood": WOOD_PLYWOOD_URL, "Metal": METAL_SHEET_URL}

IDEA_IMAGES = {
    "Wall shelf": "https://media.homeboxstores.com/i/homebox/160595463-WS-04NSONOMA_02-2100.jpg?%24prodimg-m-sqr-pdp-2x%24=&%24quality-standard%24=&fmt=auto&sm=c",
    "Desk organiser": "https://www.kasahara-net.jp/media/001/202506/mode3_w820-%E3%83%9A%E3%83%B3%E7%AB%8B%E3%81%A6%E4%BB%98%E3%81%8D%E5%B0%8F%E7%89%A9%E5%85%A5%E3%82%8C.jpg",
    "Metal tool stand": "https://i.ebayimg.com/images/g/yyoAAOSwBuRjKVxH/s-l960.jpg",
    "Small planter stand": "https://media2.castorama.pl/is/image/CastoramaPL/stojak-na-doniczke-goodhome-drewniany-12-cm~3663602442356_21c?%24MOB_PREV%24=&%24height=600&%24width=600",
    "Metal parts tray": "https://eclipsemagnetics.shop/cdn/shop/articles/ChatGPT_Image_Dec_22_2025_12_17_46_PM_aeed89d1-e34f-44b1-9805-c85182f51a0b.png?v=1771849753",
}

def material_image(piece_or_material):
    if isinstance(piece_or_material, dict):
        return LISTING_IMAGES.get(
            str(piece_or_material.get("id", "")),
            STOCK_IMAGES.get(piece_or_material.get("material", "Wood"), STOCK_IMAGES["Wood"]),
        )
    return STOCK_IMAGES.get(piece_or_material, STOCK_IMAGES["Wood"])


def whatsapp_url(phone):
    """Build a WhatsApp URL only when a seller supplied a usable phone number."""
    digits = re.sub(r"\D", "", phone or "")
    if len(digits) < 8:
        return None
    return f"https://wa.me/{digits}"


def allocate_project_parts(material, parts, inventory, allowance_per_side=5):
    """Assign at most one whole offcut to each part and never reuse an offcut.

    Parts with fewer possible matches are handled first, reducing the chance
    that a difficult-to-match part loses its only suitable offcut. For each
    part, the smallest fitting available offcut is preferred.
    """
    prepared_parts = []

    for original_index, part in enumerate(parts):
        candidates = find_matches(
            material,
            part["length"],
            part["width"],
            part["thickness"],
            inventory,
            allowance_per_side=allowance_per_side,
        )
        prepared_parts.append({
            "original_index": original_index,
            "part": part,
            "candidates": candidates,
        })

    # Match the most constrained parts first; use original order for ties.
    prepared_parts.sort(
        key=lambda item: (len(item["candidates"]), item["original_index"])
    )

    used_piece_ids = set()
    allocated_by_index = {}

    for item in prepared_parts:
        assigned_piece = None
        for candidate in item["candidates"]:  # Already sorted best-fit first.
            # Listing IDs are unique in the app. The fallback also gives
            # older listings without an ID a stable key for this run.
            piece_key = candidate.get("id")
            if piece_key is None:
                piece_key = (
                    candidate.get("name"), candidate.get("material"),
                    candidate.get("length"), candidate.get("width"),
                    candidate.get("thickness"), candidate.get("area"),
                )

            if piece_key not in used_piece_ids:
                used_piece_ids.add(piece_key)
                assigned_piece = candidate
                break

        allocated_by_index[item["original_index"]] = (
            [assigned_piece] if assigned_piece is not None else []
        )

    # Return results in the same order the user entered the parts.
    return [
        (part, allocated_by_index[index])
        for index, part in enumerate(parts)
    ]


# -------------------- LOAD DATA --------------------

if "inventory" not in st.session_state:
    st.session_state.inventory = load_inventory()

inventory = st.session_state.inventory
if "saved_ids" not in st.session_state:
    st.session_state.saved_ids = []

# -------------------- SIDEBAR NAVIGATION --------------------

def navigate_to(target_page):
    # Streamlit executes this callback before creating the navigation radio
    # widget on rerun, so changing its keyed state here is safe.
    st.session_state["main_navigation"] = target_page


with st.sidebar:
    st.markdown("## ♻ ScrapFit")
    st.caption("Find the next use for every offcut")
    st.divider()
    page = st.radio(
        "Navigate",
        ["Home", "Find Scrap", "Project Planner", "Project Ideas", "List Scrap", "Inventory", "Save for Later"],
        label_visibility="collapsed",
        key="main_navigation",
    )
    st.divider()
    st.caption("Local prototype · Demo inventory")


# -------------------- HOME PAGE --------------------

if page == "Home":
    with st.container(key="home_hero"):
        hero_copy, hero_art = st.columns([1.2, 0.9], vertical_alignment="center")
        with hero_copy:
            st.markdown('<div class="sf-eyebrow">♻ Smart waste-to-value network</div>', unsafe_allow_html=True)
            st.markdown('<div class="sf-hero-title">Good materials deserve a second life.</div>', unsafe_allow_html=True)
            st.markdown(
                '<div class="sf-hero-copy">Usable workshop leftovers can be valuable to someone else. ScrapFit helps people discover reusable wood and metal offcuts, compare dimensions with project needs, and find suitable materials nearby before buying new.</div>',
                unsafe_allow_html=True,
            )
            st.markdown('<div class="sf-hero-kicker">Project-first matching · Quality-aware listings · Local pickup</div>', unsafe_allow_html=True)
        with hero_art:
            hero_image = Path(__file__).with_name("scrapfit_hero_photo.png")
            if hero_image.exists():
                st.image(str(hero_image), use_container_width=True)
            else:
                st.warning("Place scrapfit_hero_photo.png beside app.py to display the workshop photo.")

        st.markdown("### Start with what you need")
        st.markdown("Find a piece for a specific cut, plan a project from a parts list, or make leftover material available for reuse.")
        action1, action2, action3 = st.columns(3)
        with action1:
            st.button("⌕  Find Scrap", key="home_find_materials", use_container_width=True,
                      on_click=navigate_to, args=("Find Scrap",))
        with action2:
            st.button("▱  Plan a Project", key="home_plan_project", use_container_width=True,
                      on_click=navigate_to, args=("Project Planner",))
        with action3:
            st.button("＋  List Scrap", key="home_add_listing", use_container_width=True,
                      on_click=navigate_to, args=("List Scrap",))

    st.markdown('<div class="sf-divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="sf-section-kicker">Your material workspace</div><div class="sf-section-title">A clearer view of reusable resources</div>', unsafe_allow_html=True)
    st.markdown('<div class="sf-section-copy">These counts reflect the local prototype inventory currently loaded on this device. The listings are sample data for demonstration, not verified live offers.</div>', unsafe_allow_html=True)
    total_pieces = len(inventory)
    wood_pieces = sum(p.get("material") == "Wood" for p in inventory)
    metal_pieces = sum(p.get("material") == "Metal" for p in inventory)
    metric1, metric2, metric3 = st.columns(3)
    metric1.metric("Inventory listings", total_pieces, help="Number of individual listing records, not total quantity of pieces.")
    metric2.metric("Wood listings", wood_pieces)
    metric3.metric("Metal listings", metal_pieces)

    st.markdown('<div class="sf-divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="sf-section-kicker">Why ScrapFit</div><div class="sf-section-title">The problem is finding the right leftover</div>', unsafe_allow_html=True)
    st.markdown('<div class="sf-section-copy">Usable offcuts may be discarded, sold cheaply, or sent for recycling before anyone finds a practical use for them. At the same time, small businesses, students, makers, and repair providers may need only a small quantity of material. ScrapFit is designed to make those needs easier to connect.</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown('<div class="sf-card"><div class="sf-card-icon">⌕</div><h3>Search by project needs</h3><p>Start with the dimensions and material you need instead of browsing a pile of unrelated leftovers.</p></div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="sf-card"><div class="sf-card-icon">▤</div><h3>Prefer the smallest suitable piece</h3><p>The matching logic ranks pieces that fit, prioritising the smaller suitable offcut so larger pieces may remain available for future projects.</p></div>', unsafe_allow_html=True)
    with c3:
        st.markdown('<div class="sf-card"><div class="sf-card-icon">⌖</div><h3>Keep reuse local</h3><p>Pickup-area details help people narrow the search and contact a seller to discuss availability and collection.</p></div>', unsafe_allow_html=True)

    st.markdown('<div class="sf-divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="sf-section-kicker">How it works</div><div class="sf-section-title">From leftover material to a useful project</div>', unsafe_allow_html=True)
    st.markdown('<div class="sf-section-copy">ScrapFit brings together material details and project requirements in a simple workflow.</div>', unsafe_allow_html=True)
    step1, step2, step3 = st.columns(3)
    with step1:
        st.markdown('<div class="sf-step"><div class="sf-step-num">STEP 01</div><h3>List or describe</h3><p>Sellers record material type, dimensions, thickness, condition, price, quantity, and pickup details. Buyers enter a part requirement or a project cut list.</p></div>', unsafe_allow_html=True)
    with step2:
        st.markdown('<div class="sf-step"><div class="sf-step-num">STEP 02</div><h3>Check the fit</h3><p>Python-based rules compare material, thickness, dimensions, and cutting allowance, then rank the suitable listings by fit.</p></div>', unsafe_allow_html=True)
    with step3:
        st.markdown('<div class="sf-step"><div class="sf-step-num">STEP 03</div><h3>Review and arrange pickup</h3><p>Review the listing details, verify the actual material with the seller, and arrange local collection directly.</p></div>', unsafe_allow_html=True)

    st.markdown('<div class="sf-divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="sf-section-kicker">Who can benefit</div><div class="sf-section-title">Useful for more than one kind of maker</div>', unsafe_allow_html=True)
    b1, b2, b3, b4 = st.columns(4)
    with b1:
        st.markdown('<div class="sf-card"><div class="sf-card-icon">⚙</div><h3>Workshops</h3><p>Give usable metal and wood leftovers another chance to be used and potentially recover some value.</p></div>', unsafe_allow_html=True)
    with b2:
        st.markdown('<div class="sf-card"><div class="sf-card-icon">▦</div><h3>Small businesses</h3><p>Look for smaller quantities of material that fit a job without automatically buying a full sheet or board.</p></div>', unsafe_allow_html=True)
    with b3:
        st.markdown('<div class="sf-card"><div class="sf-card-icon">✎</div><h3>Students and makers</h3><p>Explore affordable material options for prototypes, creative builds, and practical projects.</p></div>', unsafe_allow_html=True)
    with b4:
        st.markdown('<div class="sf-card"><div class="sf-card-icon">⌁</div><h3>Repair providers</h3><p>Find reusable pieces for small repairs where an offcut may be enough for the required part.</p></div>', unsafe_allow_html=True)

    st.markdown('<div class="sf-divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="sf-section-kicker">Circular value</div><div class="sf-section-title">Keep useful materials in circulation</div>', unsafe_allow_html=True)
    st.markdown('<div class="sf-section-copy">The idea is simple: connect a material that is no longer needed in one place with a project that can use it somewhere nearby.</div>', unsafe_allow_html=True)
    st.markdown('<div class="sf-flow"><span>Workshop leftovers</span><b>→</b><span>ScrapFit matching</span><b>→</b><span>Local maker or business</span><b>→</b><span>Useful new product</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="sf-callout"><strong>Our mission</strong><br>Encourage the reuse of available materials by making them easier to find and access before purchasing new resources. ScrapFit aims to make local material reuse more practical through project-based matching and clearer listing details.</div>', unsafe_allow_html=True)

    st.markdown('<div class="sf-divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="sf-section-kicker">Built as a practical prototype</div><div class="sf-section-title">Start simple. Learn from real use.</div>', unsafe_allow_html=True)
    left, right = st.columns(2, gap="large")
    with left:
        st.markdown('<div class="sf-card"><h3>Available in this prototype</h3><p>• Browse sample wood and metal listings<br>• Search by dimensions and thickness<br>• Filter by pickup area<br>• Plan a project using a manual cut list<br>• Save listings temporarily for later<br>• Contact a seller using the available contact details</p></div>', unsafe_allow_html=True)
    with right:
        st.markdown('<div class="sf-card"><h3>Possible next steps</h3><p>• AI-assisted draft parts lists from a project description<br>• Seller photo uploads and QR-based material records<br>• More detailed quality and availability management<br>• Map-based local discovery<br>• A shared online database for wider participation</p><p class="sf-footnote">These are proposed future features, not all active in the current local demo.</p></div>', unsafe_allow_html=True)

    st.markdown('<p class="sf-footnote">Demo notice: this is a local prototype using sample inventory. Pickup areas and any illustrative visuals are not proof of a real listing or verified location. Always confirm dimensions, material grade, condition, price, availability, and collection arrangements with the seller before making a decision.</p>', unsafe_allow_html=True)

# -------------------- FIND SCRAP --------------------

if page == "Find Scrap":
    st.header("🔎 Find a piece for your project")
    st.write(
        "Enter the dimensions of the part you need. "
        "ScrapFit searches for pieces that can accommodate it."
    )

    with st.form("find_scrap_form"):
        col1, col2 = st.columns(2)

        with col1:
            material = st.selectbox(
                "Material",
                ["Wood", "Metal"],
                key="find_material",
            )
            length = st.number_input(
                "Required length (mm)",
                min_value=1,
                max_value=10000,
                value=500,
                step=10,
            )
            thickness = st.number_input(
                "Required thickness (mm)",
                min_value=1,
                max_value=500,
                value=18 if material == "Wood" else 3,
                step=1,
            )

        with col2:
            width = st.number_input(
                "Required width (mm)",
                min_value=1,
                max_value=10000,
                value=250,
                step=10,
            )
            allowance = st.number_input(
                "Extra cutting allowance per side (mm)",
                min_value=0,
                max_value=100,
                value=5,
                step=1,
                help="Adds this amount to every edge. For example, 5 mm per side means the offcut must fit a part 10 mm longer and 10 mm wider.",
            )
            st.caption(
                "Thickness must match exactly. The allowance helps leave room for cutting; confirm grain direction and actual cutting requirements with the seller."
            )

        search_area = st.text_input(
            "Pickup area / place (optional)",
            placeholder="e.g. Guindy, Chennai",
            help="Enter a neighbourhood or area name to limit results. This is a text-based area filter, not GPS distance search.",
        )

        search_submitted = st.form_submit_button(
            "Find Matching Scrap",
            type="primary",
            use_container_width=True,
        )

    if search_submitted:
        results = find_matches(
            material, int(length), int(width), int(thickness),
            [p for p in inventory if p.get("status", "Available") == "Available"],
            allowance_per_side=int(allowance),
        )
        if search_area.strip():
            area_query = search_area.strip().casefold()
            results = [p for p in results if area_query in str(p.get("area", "")).casefold() or area_query in str(p.get("pickup_location", "")).casefold()]

        st.session_state.find_results = results
        st.session_state.find_query = (
            material, int(length), int(width), int(thickness), int(allowance), search_area.strip()
        )

    if "find_results" in st.session_state:
        results = st.session_state.find_results
        query = st.session_state.find_query

        st.subheader("Matching results")

        st.caption(
            f"Requirement: {query[0]} | {query[1]} × {query[2]} × "
            f"{query[3]} mm"
        )

        if not results:
            st.warning(
                "No matching pieces found. Try different dimensions "
                "or check the available inventory."
            )
        else:
            st.success(f"Found {len(results)} compatible piece(s).")

            for index, piece in enumerate(results, start=1):
                with st.container(border=True):
                    photo_col, left, middle, right = st.columns([1.25, 2.5, 2, 1])

                    with photo_col:
                        st.image(material_image(piece), use_container_width=True)
                        st.caption("Illustrative stock photo")

                    with left:
                        st.markdown(f"**{index}. {piece['name']}**")
                        st.write(
                            f"{piece['material']} · {piece['condition']}"
                        )
                        st.caption(
                            f"Pickup area: {piece['area']}"
                        )

                    with middle:
                        st.write(
                            f"**Size:** {piece['length']} × "
                            f"{piece['width']} × "
                            f"{piece['thickness']} mm"
                        )
                        st.write(
                            f"**Unused surface area:** "
                            f"{piece['waste_area']:,} mm²"
                        )
                        if piece["rotated"]:
                            st.caption("Fits when rotated 90°")

                    with right:
                        st.metric("Price", f"₹{piece['price']}")
                        st.caption(f"ID: {piece['id']}")

                    if piece.get("notes"):
                        st.caption(piece["notes"])
                    if piece.get("seller_name"):
                        st.write(f"**Seller / shop:** {piece['seller_name']}")
                    if piece.get("pickup_location"):
                        st.write(f"**Pickup location:** {piece['pickup_location']}")
                    if piece.get("pickup_details"):
                        st.caption(f"Pickup details: {piece['pickup_details']}")
                    contact_url = whatsapp_url(piece.get("contact_phone", ""))
                    if contact_url:
                        st.markdown(f"[Contact seller on WhatsApp](<{contact_url}>)")
                    elif piece.get("contact_phone"):
                        st.caption(f"Seller contact: {piece['contact_phone']}")
                    else:
                        st.caption("Seller contact details have not been added to this listing yet.")
                    if st.button(
                        "♡ Save for Later" if piece["id"] not in st.session_state.saved_ids else "♥ Saved",
                        key=f"save_find_{piece['id']}",
                    ):
                        if piece["id"] not in st.session_state.saved_ids:
                            st.session_state.saved_ids.append(piece["id"])
                        st.toast("Saved for later")

            st.markdown("### Map view (demo locations)")
            st.caption("Hover over a pin to see the listing name, dimensions, price, condition and pickup area. Pins are illustrative, not verified seller addresses.")
            demo_points = []
            area_coords = {
                "Area A": (80.225, 13.055),
                "Area B": (80.245, 13.075),
                "Area C": (80.265, 13.045),
                "Chennai": (80.270, 13.082),
            }
            for idx, item in enumerate(results):
                area = item.get("area", "Chennai")
                lon, lat = area_coords.get(area, area_coords["Chennai"])
                # Small deterministic offsets keep pins visible when demo areas overlap.
                lon += (idx % 4) * 0.0025
                lat += (idx % 3) * 0.002
                demo_points.append({
                    "name": item.get("name", "Scrap"),
                    "id": item.get("id", ""),
                    "material": item.get("material", ""),
                    "dimensions": f"{item.get('length', '?')} × {item.get('width', '?')} × {item.get('thickness', '?')} mm",
                    "price": f"₹{item.get('price', '—')} per piece",
                    "condition": item.get("condition", "Not specified"),
                    "area": area,
                    "lon": lon,
                    "lat": lat,
                })
            if demo_points:
                try:
                    import pydeck as pdk
                    layer = pdk.Layer(
                        "ScatterplotLayer", data=demo_points,
                        get_position="[lon, lat]", get_radius=100,
                        get_fill_color=[33, 87, 71, 220], get_line_color=[255, 255, 255],
                        line_width_min_pixels=2, stroked=True, pickable=True,
                    )
                    tooltip = {"html": "<b>{name}</b><br/>ID: {id}<br/>{material} · {dimensions}<br/>{price}<br/>Condition: {condition}<br/>Pickup area: {area}", "style": {"backgroundColor": "#173F34", "color": "white", "padding": "10px", "borderRadius": "8px"}}
                    view_state = pdk.ViewState(latitude=13.07, longitude=80.245, zoom=11, pitch=0)
                    st.pydeck_chart(pdk.Deck(layers=[layer], initial_view_state=view_state, tooltip=tooltip, map_style=None), use_container_width=True)
                except Exception:
                    st.warning("Hoverable map needs pydeck. Showing the locations as a basic map instead.")
                    st.map(demo_points, latitude="lat", longitude="lon", size=80)


# -------------------- PROJECT CUT LIST --------------------

if page == "Project Planner":
    st.header("Project Planner")
    st.write(
        "Add the rectangular parts required for a project. ScrapFit leaves a cutting "
        "allowance, prioritizes the smallest suitable offcuts, and never assigns one "
        "listing to multiple parts in this project."
    )

    with st.form("cut_list_form"):
        project_name = st.text_input(
            "Project name", value="My Project"
        )

        part_count = st.number_input(
            "Number of different part requirements",
            min_value=1,
            max_value=10,
            value=2,
            step=1,
        )

        st.caption("All dimensions are in millimetres.")

        parts = []
        for i in range(int(part_count)):
            st.markdown(f"**Part {i + 1}**")
            c1, c2, c3, c4 = st.columns(4)

            with c1:
                part_name = st.text_input(
                    "Part name",
                    value=f"Part {i + 1}",
                    key=f"part_name_{i}",
                )
            with c2:
                part_length = st.number_input(
                    "Length",
                    min_value=1,
                    max_value=10000,
                    value=500,
                    step=10,
                    key=f"part_length_{i}",
                )
            with c3:
                part_width = st.number_input(
                    "Width",
                    min_value=1,
                    max_value=10000,
                    value=250,
                    step=10,
                    key=f"part_width_{i}",
                )
            with c4:
                part_thickness = st.number_input(
                    "Thickness",
                    min_value=1,
                    max_value=500,
                    value=18,
                    step=1,
                    key=f"part_thickness_{i}",
                )

            parts.append(
                {
                    "name": part_name,
                    "length": int(part_length),
                    "width": int(part_width),
                    "thickness": int(part_thickness),
                }
            )

        project_material = st.selectbox(
            "Material for these parts",
            ["Wood", "Metal"],
            key="project_material",
        )
        project_area = st.text_input(
            "Pickup area / place (optional)",
            placeholder="e.g. Guindy, Chennai",
            help="Enter a neighbourhood or area name to search only listings from that area. This is not a GPS distance filter.",
        )
        project_allowance = st.number_input(
            "Extra cutting allowance per side (mm)",
            min_value=0,
            max_value=100,
            value=5,
            step=1,
            help="Each offcut must be at least this much larger on every edge. Adjust for your cutting method and material.",
        )

        cut_list_submitted = st.form_submit_button(
            "Search for Project Materials",
            type="primary",
            use_container_width=True,
        )

    if cut_list_submitted:
        planner_inventory = [p for p in inventory if p.get("status", "Available") == "Available"]
        if project_area.strip():
            area_query = project_area.strip().casefold()
            planner_inventory = [p for p in planner_inventory if area_query in str(p.get("area", "")).casefold() or area_query in str(p.get("pickup_location", "")).casefold()]
        project_results = allocate_project_parts(
            project_material, parts, planner_inventory,
            allowance_per_side=int(project_allowance),
        )

        st.session_state.project_results = project_results
        st.session_state.project_title = project_name

    if "project_results" in st.session_state:
        project_results = st.session_state.project_results
        st.subheader(f"Matching results for: {st.session_state.project_title}")

        assigned_results = [
            (part, matches[0])
            for part, matches in project_results
            if matches
        ]
        unmatched_parts = [
            part for part, matches in project_results
            if not matches
        ]
        # Display the assigned listings from smallest suitable piece to largest.
        assigned_results.sort(
            key=lambda item: (
                item[1].get("length", 0) * item[1].get("width", 0),
                item[1].get("waste_area", 0),
            )
        )

        st.info(
            f"{len(assigned_results)} of {len(project_results)} part requirements have a unique offcut assigned. "
            "Results below are sorted from smaller offcuts to larger offcuts. "
            "Each listing is assigned to no more than one part in this project."
        )

        if assigned_results:
            st.markdown("### Available matched materials")
            for rank, (part, piece) in enumerate(assigned_results, start=1):
                with st.container(border=True):
                    title_col, price_col = st.columns([4, 1])
                    with title_col:
                        st.markdown(f"**{rank}. {piece.get('name', 'Unnamed offcut')}**")
                        st.caption(f"Assigned to: {part['name']} · Listing ID: {piece.get('id', 'N/A')}")
                    with price_col:
                        st.metric("Price", f"₹{piece.get('price', 0):,}")

                    detail_col, seller_col = st.columns(2)
                    with detail_col:
                        st.markdown("**Material details**")
                        st.write(f"**Material:** {piece.get('material', 'Not specified')}")
                        st.write(f"**Available size:** {piece.get('length', '?')} × {piece.get('width', '?')} × {piece.get('thickness', '?')} mm")
                        st.write(f"**Condition:** {piece.get('condition', 'Not specified')}")
                        st.write(f"**Required part:** {part['length']} × {part['width']} × {part['thickness']} mm")
                        st.write(f"**Cutting allowance:** {piece.get('allowance_per_side', 5)} mm per side")
                        if piece.get('rotated'):
                            st.caption("This part fits when the offcut is rotated 90°.")
                        st.write(f"**Extra surface area after allowance:** {piece.get('waste_area', 0):,} mm² (approx.)")
                        if piece.get("notes"):
                            st.write(f"**Seller's material description:** {piece['notes']}")

                    with seller_col:
                        st.markdown("**Seller and collection details**")
                        st.write(f"**Shop / seller:** {piece.get('seller_name') or 'Not provided'}")
                        st.write(f"**Pickup area:** {piece.get('area') or 'Not provided'}")
                        st.write(f"**Address / landmark:** {piece.get('pickup_location') or 'Ask seller for address'}")
                        st.write(f"**Pickup availability:** {piece.get('pickup_details') or 'Confirm pickup time with seller'}")
                        phone = piece.get('contact_phone', '').strip()
                        if phone:
                            st.write(f"**Phone:** {phone}")
                            contact_url = whatsapp_url(phone)
                            if contact_url:
                                st.markdown(f"[Contact seller on WhatsApp](<{contact_url}>)")
                        else:
                            st.warning("Contact number has not been provided for this listing.")

        if unmatched_parts:
            st.markdown("### Parts without an assigned offcut")
            st.warning(
                "No unused matching offcut could be assigned to these requirements. "
                "A suitable listing may not exist, or a suitable offcut may already be assigned to another part."
            )
            for part in unmatched_parts:
                st.write(
                    f"- **{part['name']}** — {part['length']} × {part['width']} × "
                    f"{part['thickness']} mm"
                )
        elif assigned_results:
            st.success("Every part requirement has a unique offcut assigned.")


# -------------------- LIST SCRAP --------------------

if page == "List Scrap":
    st.header("➕ List leftover material")
    st.write(
        "Enter the dimensions and details of a reusable offcut."
    )

    with st.form("list_scrap_form", clear_on_submit=True):
        listing_name = st.text_input(
            "Listing name", placeholder="e.g. Plywood offcut"
        )

        c1, c2 = st.columns(2)

        with c1:
            listing_material = st.selectbox(
                "Material", ["Wood", "Metal"]
            )
            listing_length = st.number_input(
                "Length (mm)",
                min_value=1,
                max_value=10000,
                value=600,
                step=10,
            )
            listing_thickness = st.number_input(
                "Thickness (mm)",
                min_value=1,
                max_value=500,
                value=18 if listing_material == "Wood" else 3,
                step=1,
            )
            listing_condition = st.selectbox(
                "Condition",
                [
                    "A - Clean",
                    "B - Minor marks",
                    "C - Usable for small parts",
                ],
            )

        with c2:
            listing_width = st.number_input(
                "Width (mm)",
                min_value=1,
                max_value=10000,
                value=300,
                step=10,
            )
            listing_quantity = st.number_input(
                "Number of identical pieces",
                min_value=1,
                max_value=1000,
                value=1,
                step=1,
                help="Use one listing for pieces with the same dimensions, condition and price.",
            )
            listing_price = st.number_input(
                "Price per piece (₹)",
                min_value=0,
                max_value=1000000,
                value=50,
                step=10,
            )
            listing_area = st.text_input(
                "Pickup area / neighbourhood *", placeholder="e.g. Guindy, Chennai"
            )

        st.markdown("**Seller and pickup details**")
        seller_name = st.text_input(
            "Seller or shop name", placeholder="e.g. ABC Fabrication Shop"
        )
        contact_phone = st.text_input(
            "Phone / WhatsApp number", placeholder="Include country code, e.g. +91..."
        )
        pickup_location = st.text_input(
            "Pickup address or landmark", placeholder="Shop address, street, or nearby landmark"
        )
        pickup_details = st.text_area(
            "When can the buyer collect it?",
            placeholder="e.g. Weekdays 10 AM–5 PM; call before visiting; bring your own transport.",
        )
        listing_notes = st.text_area(
            "Material description (optional)",
            placeholder="Describe marks, material grade, storage condition, or other details",
        )

        listing_submitted = st.form_submit_button(
            "Add Listing",
            type="primary",
            use_container_width=True,
        )

    if listing_submitted:
        if not listing_name.strip() or not listing_area.strip():
            st.error("Please enter a listing name and pickup area.")
        else:
            new_piece = {
                "id": "S" + uuid.uuid4().hex[:6].upper(),
                "material": listing_material,
                "name": listing_name.strip(),
                "length": int(listing_length),
                "width": int(listing_width),
                "thickness": int(listing_thickness),
                "condition": listing_condition,
                "price": int(listing_price),
                "quantity": int(listing_quantity),
                "status": "Available",
                "area": listing_area.strip(),
                "seller_name": seller_name.strip(),
                "contact_phone": contact_phone.strip(),
                "pickup_location": pickup_location.strip(),
                "pickup_details": pickup_details.strip(),
                "notes": listing_notes.strip(),
            }

            st.session_state.inventory.append(new_piece)
            save_inventory(st.session_state.inventory)
            st.success("Listing added to your local inventory.")
            st.rerun()


# -------------------- INVENTORY --------------------

if page == "Inventory":
    st.header("📦 Scrap inventory")
    st.caption("Browse and manage prototype listings. Quantity means identical pieces in one listing.")
    search_text = st.text_input("Search by name, ID or pickup area", key="inventory_search")
    filter_material = st.selectbox("Filter material", ["All", "Wood", "Metal"], key="inventory_material_filter")
    shown_inventory = [p for p in inventory if search_text.lower() in (str(p.get("name", "")) + str(p.get("id", "")) + str(p.get("area", ""))).lower() and (filter_material == "All" or p.get("material") == filter_material)]

    if not shown_inventory:
        st.info("No listings available yet.")
    else:
        for piece in shown_inventory:
            piece.setdefault("quantity", 1)
            piece.setdefault("status", "Available")
            with st.container(border=True):
                photo_col, c1, c2, c3 = st.columns([1.2, 2.5, 2, 1.3])

                with photo_col:
                    st.image(material_image(piece), use_container_width=True)
                    st.caption("Demo image")

                with c1:
                    st.markdown(f"**{piece['name']}**")
                    st.write(
                        f"{piece['material']} · {piece['condition']}"
                    )
                    st.caption(
                        f"ID: {piece['id']} · {piece['area']} · {piece.get('status', 'Available')}"
                    )
                    st.write(f"**Quantity:** {piece.get('quantity', 1)} piece(s)")

                with c2:
                    st.write(
                        f"{piece['length']} × {piece['width']} × "
                        f"{piece['thickness']} mm"
                    )
                    st.caption(piece.get("notes", ""))
                    if piece.get("seller_name"):
                        st.write(f"**Seller/shop:** {piece['seller_name']}")
                    if piece.get("pickup_location"):
                        st.caption(f"Address/landmark: {piece['pickup_location']}")
                    if piece.get("pickup_details"):
                        st.caption(f"Pickup: {piece['pickup_details']}")
                    if piece.get("contact_phone"):
                        st.caption(f"Contact: {piece['contact_phone']}")

                with c3:
                    st.metric("Price per piece", f"₹{piece['price']}")
                    new_status = st.selectbox("Status", ["Available", "Reserved", "Sold / Unavailable"], index=["Available", "Reserved", "Sold / Unavailable"].index(piece.get("status", "Available")) if piece.get("status", "Available") in ["Available", "Reserved", "Sold / Unavailable"] else 0, key=f"status_{piece['id']}")
                    if new_status != piece.get("status", "Available"):
                        piece["status"] = new_status
                        save_inventory(st.session_state.inventory)
                        st.rerun()
                    if st.button(
                        "Delete",
                        key=f"delete_{piece['id']}",
                    ):
                        st.session_state.inventory = [
                            item for item in st.session_state.inventory
                            if item["id"] != piece["id"]
                        ]
                        save_inventory(st.session_state.inventory)
                        st.rerun()

    st.divider()
    st.caption(
        "Inventory is stored in inventory.json beside app.py. "
        "Keep this file if you want to retain added listings."
    )


# -------------------- PROJECT IDEAS --------------------

if page == "Project Ideas":
    st.header("💡 Project Ideas")
    st.write("Explore simple ways to give leftover materials a second life. These are starter ideas for a prototype, not certified engineering designs.")
    idea_filter = st.selectbox("What do you have or want to make?", ["Any material", "Wood", "Metal"])
    ideas = [
        {"title": "Wall shelf", "material": "Wood", "difficulty": "Beginner", "parts": "2 side supports, 1 shelf panel", "tools": "Saw, drill, screws, measuring tape", "time": "2–4 hours", "description": "A small shelf for books, tools or everyday items."},
        {"title": "Desk organiser", "material": "Wood", "difficulty": "Beginner", "parts": "Base panel, dividers, back panel", "tools": "Saw, glue or screws, sandpaper", "time": "1–3 hours", "description": "A compact organiser for stationery or small workshop tools."},
        {"title": "Metal tool stand", "material": "Metal", "difficulty": "Intermediate", "parts": "Base plate, supports, brackets", "tools": "Measuring tools, drill; suitable metalworking equipment", "time": "Half a day", "description": "A small stand for organising workshop tools. Use safe, suitable fabrication methods."},
        {"title": "Small planter stand", "material": "Wood", "difficulty": "Beginner", "parts": "Top panel, four legs, braces", "tools": "Saw, drill, screws, sandpaper", "time": "2–4 hours", "description": "A simple stand for a small plant pot."},
        {"title": "Metal parts tray", "material": "Metal", "difficulty": "Intermediate", "parts": "Base sheet, side strips", "tools": "Metal shears or suitable workshop tools; gloves and eye protection", "time": "2–4 hours", "description": "A shallow tray for storing small parts."},
    ]
    shown = [i for i in ideas if idea_filter == "Any material" or i["material"] == idea_filter]
    for idea in shown:
        with st.container(border=True):
            photo_col, details_col = st.columns([1, 2.2], gap="medium")
            with photo_col:
                st.image(IDEA_IMAGES.get(idea["title"], material_image(idea["material"])), use_container_width=True)
                st.caption("Illustrative stock photo")
            with details_col:
                st.subheader(idea["title"])
                st.caption(f"{idea['material']} · {idea['difficulty']} · Estimated time: {idea['time']}")
                st.write(idea["description"])
                st.write(f"**Suggested parts:** {idea['parts']}")
                st.write(f"**Tools:** {idea['tools']}")
                st.button("Find materials for this idea", key=f"idea_{idea['title']}", on_click=navigate_to, args=("Find Scrap",))
    st.info("AI-generated ideas are not connected in this prototype. These sample ideas demonstrate how the feature could work; check dimensions, stability and safe construction before building.")


# -------------------- SAVE FOR LATER --------------------

if page == "Save for Later":
    st.header("♡ Save for Later")
    st.caption("Your saved items are temporary and may disappear when the session ends. There is no login or account.")
    saved_items = [p for p in inventory if p.get("id") in st.session_state.saved_ids]
    if not saved_items:
        st.info("You haven't saved any materials yet. Open Find Scrap and select Save for Later on a listing.")
    else:
        for piece in saved_items:
            with st.container(border=True):
                photo_col, a, b, c = st.columns([1.2, 2.5, 2, 1])
                with photo_col:
                    st.image(material_image(piece), use_container_width=True)
                    st.caption("Demo image")
                with a:
                    st.markdown(f"**{piece.get('name', 'Scrap listing')}**")
                    st.caption(f"{piece.get('material', '')} · {piece.get('area', '')} · {piece.get('status', 'Available')}")
                with b:
                    st.write(f"{piece.get('length')} × {piece.get('width')} × {piece.get('thickness')} mm")
                    st.write(f"₹{piece.get('price', 0)} per piece · Quantity: {piece.get('quantity', 1)}")
                with c:
                    if st.button("Remove", key=f"unsave_{piece['id']}"):
                        st.session_state.saved_ids.remove(piece["id"])
                        st.rerun()
                contact_url = whatsapp_url(piece.get("contact_phone", ""))
                if contact_url:
                    st.markdown(f"[Contact seller on WhatsApp](<{contact_url}>)")


# -------------------- FOOTER --------------------

st.divider()
st.caption(
    "ScrapFit MVP · Local prototype · Sample data is for demonstration "
    "only. Verify material grade, dimensions, condition and availability "
    "before real-world use."
)

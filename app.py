
import json
import os
import re
import uuid
import shutil
from pathlib import Path

import streamlit as st

# -------------------- CONFIGURATION --------------------

st.set_page_config(
    page_title="ScrapFit",
    page_icon="♻️",
    layout="wide",
)


# -------------------- OPTIONAL AI PROJECT DRAFTING --------------------

GEMINI_DEFAULT_MODEL = "gemini-3.1-flash-lite"


def get_gemini_api_key():
    """Read the Gemini key from Streamlit secrets or the environment; never hard-code it."""
    key = os.environ.get("GEMINI_API_KEY", "").strip()
    try:
        secret_key = st.secrets.get("GEMINI_API_KEY", "")
        if secret_key:
            key = str(secret_key).strip()
    except Exception:
        # st.secrets raises when no local secrets file exists; environment variables still work.
        pass
    return key


def generate_ai_project_draft(description, material):
    """Ask Gemini for an editable, approximate rectangular-parts draft (not engineering advice)."""
    api_key = get_gemini_api_key()
    if not api_key:
        raise ValueError("Gemini API key is not configured.")

    try:
        from google import genai
        from google.genai import types
    except ImportError as exc:
        raise RuntimeError("The google-genai package is missing. Install the updated requirements.txt.") from exc

    model = os.environ.get("GEMINI_MODEL", GEMINI_DEFAULT_MODEL).strip() or GEMINI_DEFAULT_MODEL
    prompt = f"""You help draft simple maker projects for a material-reuse app. Produce a preliminary cut list, not a certified engineering design.
User's project description: {description}
Primary material selected by the user: {material}

Return ONLY valid JSON with this structure:
{{
  "title": "short project title",
  "parts": [
    {{"name": "clear part name", "length_mm": 300, "width_mm": 100, "thickness_mm": 18, "quantity": 2, "reason": "brief purpose"}}
  ],
  "design_notes": ["short practical consideration"],
  "assumptions": ["dimensions are approximate starter estimates"]
}}

Requirements:
- Use only the selected primary material ({material}) for every part.
- Keep the cut list to 1–10 distinct rectangular pieces that could plausibly be cut from sheet/board/flat-stock offcuts.
- Use millimetres and integer dimensions. Length and width must be 1–10000 mm; thickness 1–500 mm; quantity 1–20.
- Choose sensible beginner-level, approximate dimensions where the user did not specify them. Include key panels, supports, legs or brackets where plausible, but do not overcomplicate.
- Do not claim the draft is structurally safe, code-compliant, or construction-ready. Add a note to verify stability, joinery, material grade, tool suitability and safety before building.
- Do not invent prices, inventory matches, seller details, or availability. ScrapFit's deterministic matcher handles inventory fits separately.
- Keep notes concise. JSON only; no Markdown fences or extra text."""

    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.2,
            max_output_tokens=1800,
        ),
    )
    response_text = getattr(response, "text", None)
    if not response_text:
        raise ValueError("Gemini returned an empty response.")
    try:
        payload = json.loads(response_text)
    except json.JSONDecodeError:
        # Defensive handling for SDK/model responses that wrap JSON in code fences.
        cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", response_text.strip(), flags=re.IGNORECASE)
        payload = json.loads(cleaned)

    if not isinstance(payload, dict) or not isinstance(payload.get("parts"), list):
        raise ValueError("The AI response did not contain a valid parts list.")
    if not 1 <= len(payload["parts"]) <= 10:
        raise ValueError("The AI draft must contain between 1 and 10 distinct parts. Please try a simpler description.")

    validated_parts = []
    total_pieces = 0
    for raw in payload["parts"]:
        if not isinstance(raw, dict):
            raise ValueError("One of the AI-generated parts was malformed. Generate the draft again.")
        name = str(raw.get("name", "")).strip()[:100]
        if not name:
            raise ValueError("A generated part did not have a name. Generate the draft again.")
        try:
            length = int(raw.get("length_mm"))
            width = int(raw.get("width_mm"))
            thickness = int(raw.get("thickness_mm"))
            quantity = int(raw.get("quantity", 1))
        except (TypeError, ValueError):
            raise ValueError("The AI returned non-numeric dimensions. Generate the draft again.")
        if not (1 <= length <= 10000 and 1 <= width <= 10000 and 1 <= thickness <= 500 and 1 <= quantity <= 20):
            raise ValueError("The AI returned dimensions or quantity outside the allowed range. Generate the draft again.")
        total_pieces += quantity
        validated_parts.append({
            "id": uuid.uuid4().hex[:10],
            "name": name,
            "length": length,
            "width": width,
            "thickness": thickness,
            "quantity": quantity,
            "reason": str(raw.get("reason", "")).strip()[:240],
        })
    if total_pieces > 30:
        raise ValueError("The AI draft contains too many physical pieces. Reduce the project scope and try again.")

    return {
        "title": str(payload.get("title", "Custom project")).strip()[:100] or "Custom project",
        "material": material,
        "parts": validated_parts,
        "design_notes": [str(x).strip()[:240] for x in payload.get("design_notes", []) if str(x).strip()][:6],
        "assumptions": [str(x).strip()[:240] for x in payload.get("assumptions", []) if str(x).strip()][:6],
        "source_description": description.strip(),
    }


def expand_part_quantities(parts):
    """Expand quantity into individual required pieces for the existing one-piece allocator."""
    expanded = []
    for part in parts:
        quantity = int(part.get("quantity", 1) or 1)
        for index in range(quantity):
            item = {key: value for key, value in part.items() if key != "id"}
            item["quantity"] = 1
            if quantity > 1:
                item["name"] = f"{part['name']} ({index + 1}/{quantity})"
            expanded.append(item)
    return expanded

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
IMAGE_DIR = Path(__file__).with_name("scrapfit_images")
IMAGE_DIR.mkdir(exist_ok=True)

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
    """Save inventory atomically to inventory.json beside app.py."""
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    temporary_file = DATA_FILE.with_suffix(DATA_FILE.suffix + ".tmp")
    with temporary_file.open("w", encoding="utf-8") as file:
        json.dump(items, file, indent=2, ensure_ascii=False)
        file.flush()
    temporary_file.replace(DATA_FILE)


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
WOOD_PLYWOOD_URL = "https://c.pxhere.com/photos/92/19/workshop_work_tool_wood_business-20011.jpg!d"
WOOD_PINE_URL = "https://c.pxhere.com/photos/3b/70/workshop_lumber_iron_metal_wood_tool_old_dirty-900855.jpg!d"
WOOD_PANEL_URL = "https://c.pxhere.com/photos/92/19/workshop_work_tool_wood_business-20011.jpg!d"
METAL_SHEET_URL = "https://images.unsplash.com/photo-1656285523078-b77363624310?auto=format&fit=crop&w=1000&q=80"
METAL_OFFCUT_URL = "https://images.unsplash.com/photo-1656285523078-b77363624310?auto=format&fit=crop&w=1000&q=80"
METAL_PLATE_URL = "https://c.pxhere.com/photos/86/86/tools_old_oxide_wood_iron-665653.jpg!d"
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
    """Use a real-photo URL for sample listings, or a seller-uploaded local photo."""
    if isinstance(piece_or_material, dict):
        image_name = piece_or_material.get("image_file")
        if image_name:
            local_path = IMAGE_DIR / Path(str(image_name)).name
            # Ignore old placeholder SVG drawings; use real photo URLs instead.
            if local_path.is_file() and local_path.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}:
                return str(local_path)
        return LISTING_IMAGES.get(
            str(piece_or_material.get("id", "")),
            STOCK_IMAGES.get(piece_or_material.get("material", "Wood"), STOCK_IMAGES["Wood"]),
        )
    return STOCK_IMAGES.get(piece_or_material, STOCK_IMAGES["Wood"])


def project_cost_summary(parts, inventory, material, allowance=5):
    """Estimate new-material area cost and whole-offcut cost after shared-stock cutting.

    New-material equivalent is a rough area-based proxy from sample inventory prices.
    Scrap cost counts each physical offcut used once, even when several parts are cut
    from it. Cutting patterns use a simple shelf-packing heuristic, not industrial nesting.
    """
    # Expand per-part quantities so cost and cutting estimates cover every required piece.
    parts = expand_part_quantities(parts)
    available_inventory = [
        item for item in inventory if item.get("status", "Available") == "Available"
    ]
    unit_rates = []
    for item in available_inventory:
        if item.get("material") == material:
            item_length = int(item.get("length", 0) or 0)
            item_width = int(item.get("width", 0) or 0)
            if item_length > 0 and item_width > 0:
                unit_rates.append(float(item.get("price", 0) or 0) / (item_length * item_width))
    rate = min(unit_rates) if unit_rates else 0

    new_total = sum(
        round(int(part.get("length", 0)) * int(part.get("width", 0)) * rate)
        for part in parts
    )
    allocations = allocate_project_parts(
        material, parts, available_inventory, allowance_per_side=allowance
    )

    scrap_total = 0
    counted_units = set()
    breakdown = []
    for part, assigned in allocations:
        area = int(part.get("length", 0)) * int(part.get("width", 0))
        estimate = round(area * rate)
        match = assigned[0] if assigned else None
        scrap_price = None
        scrap_note = "No suitable cut plan" if match is None else ""
        if match is not None:
            unit_key = match.get("cut_plan_unit_key")
            if unit_key not in counted_units:
                scrap_price = int(match.get("price", 0) or 0)
                scrap_total += scrap_price
                counted_units.add(unit_key)
                scrap_note = "Whole offcut cost counted once"
            else:
                scrap_price = 0
                scrap_note = "Same physical offcut; no extra listing cost"
        breakdown.append({
            "part": part.get("name", "Part"),
            "new_estimate": estimate,
            "scrap_price": scrap_price,
            "scrap_note": scrap_note,
            "match": match,
        })
    return breakdown, new_total, scrap_total


def whatsapp_url(phone):
    """Build a WhatsApp URL only when a seller supplied a usable phone number."""
    digits = re.sub(r"\D", "", phone or "")
    if len(digits) < 8:
        return None
    return f"https://wa.me/{digits}"


def allocate_project_parts(material, parts, inventory, allowance_per_side=5):
    """Plan a simple 2-D shelf cutting layout across available offcuts.

    Several required parts may be cut from one physical offcut. Listing quantity means
    the number of separate physical offcuts available. Parts must match material and
    thickness exactly; rotation is allowed. Each part gets allowance on all edges.

    This deterministic shelf-packing heuristic is intentionally explainable; it is not
    a guarantee of globally optimal nesting and does not model blade kerf or grain.
    Returns the same shape as before: (required_part, [assigned_stock_piece]) pairs.
    """
    # Create one bin per physical offcut. A listing with quantity=3 creates three bins.
    bins = []
    for listing_index, source in enumerate(inventory):
        if source.get("status", "Available") != "Available":
            continue
        quantity = max(0, min(100, int(source.get("quantity", 1) or 0)))
        for unit_index in range(quantity):
            source_id = source.get("id", f"listing-{listing_index}")
            unit_key = f"{source_id}::unit-{unit_index + 1}"
            bins.append({
                "unit_key": unit_key,
                "listing_index": listing_index,
                "unit_index": unit_index + 1,
                "piece": source.copy(),
                "rows": [],
                "used_width": 0,
                "assigned": [],
            })

    def fit_options(bin_state, part):
        stock = bin_state["piece"]
        if stock.get("material") != material:
            return []
        if int(stock.get("thickness", 0) or 0) != int(part.get("thickness", 0) or 0):
            return []
        stock_length = int(stock.get("length", 0) or 0)
        stock_width = int(stock.get("width", 0) or 0)
        need_l = int(part.get("length", 0) or 0) + 2 * int(allowance_per_side)
        need_w = int(part.get("width", 0) or 0) + 2 * int(allowance_per_side)
        if need_l <= 0 or need_w <= 0:
            return []

        orientations = [(need_l, need_w, False), (need_w, need_l, True)]
        # Try placing into existing shelves first, preferring a close fit.
        options = []
        for row_index, row in enumerate(bin_state["rows"]):
            for use_l, use_w, rotated in orientations:
                if use_l <= stock_length - row["used_length"] and use_w <= row["height"]:
                    options.append({
                        "kind": "existing", "row_index": row_index,
                        "length": use_l, "width": use_w, "rotated": rotated,
                        "score": (0, row["height"] - use_w,
                                  stock_length - row["used_length"] - use_l),
                    })
        if options:
            return sorted(options, key=lambda option: option["score"])

        # Otherwise create another shelf across the stock width.
        for use_l, use_w, rotated in orientations:
            if use_l <= stock_length and bin_state["used_width"] + use_w <= stock_width:
                options.append({
                    "kind": "new", "row_index": len(bin_state["rows"]),
                    "length": use_l, "width": use_w, "rotated": rotated,
                    "score": (1, use_w, stock_width - bin_state["used_width"] - use_w),
                })
        return sorted(options, key=lambda option: option["score"])

    def apply_placement(bin_state, part, option, part_index):
        if option["kind"] == "new":
            bin_state["rows"].append({
                "height": option["width"], "used_length": 0, "parts": []
            })
            bin_state["used_width"] += option["width"]
        row = bin_state["rows"][option["row_index"]]
        placement = {
            "part_index": part_index,
            "part_name": part.get("name", "Part"),
            "length_with_allowance": option["length"],
            "width_with_allowance": option["width"],
            "rotated": option["rotated"],
            "row_index": option["row_index"] + 1,
        }
        row["parts"].append(placement)
        row["used_length"] += option["length"]
        bin_state["assigned"].append(placement)

    # Largest pieces first improves the chance of fitting demanding parts, while
    # already-opened stock is preferred for smaller pieces so its cost is shared.
    indexed_parts = list(enumerate(parts))
    indexed_parts.sort(
        key=lambda pair: (
            -(int(pair[1].get("length", 0) or 0) * int(pair[1].get("width", 0) or 0)),
            pair[0],
        )
    )

    assigned_by_index = {}
    for part_index, part in indexed_parts:
        eligible = []
        for bin_state in bins:
            options = fit_options(bin_state, part)
            if not options:
                continue
            stock = bin_state["piece"]
            stock_area = int(stock.get("length", 0) or 0) * int(stock.get("width", 0) or 0)
            # Reusing an already-purchased physical offcut avoids buying another listing.
            # If opening a new offcut, prefer smaller area then lower price.
            opened = bool(bin_state["assigned"])
            score = (
                0 if opened else 1,
                options[0]["score"],
                0 if opened else stock_area,
                0 if opened else int(stock.get("price", 0) or 0),
                bin_state["listing_index"],
                bin_state["unit_index"],
            )
            eligible.append((score, bin_state, options[0]))
        if not eligible:
            assigned_by_index[part_index] = None
            continue
        _, chosen_bin, chosen_option = min(eligible, key=lambda item: item[0])
        apply_placement(chosen_bin, part, chosen_option, part_index)
        assigned_by_index[part_index] = chosen_bin

    # Decorate assignment copies with a stable physical-offcut key and cut-plan notes.
    results = []
    for part_index, part in enumerate(parts):
        chosen_bin = assigned_by_index.get(part_index)
        if chosen_bin is None:
            results.append((part, []))
            continue
        stock_copy = chosen_bin["piece"].copy()
        stock_copy["cut_plan_unit_key"] = chosen_bin["unit_key"]
        stock_copy["cut_plan_part_count"] = len(chosen_bin["assigned"])
        stock_copy["cut_plan_part_names"] = [entry["part_name"] for entry in chosen_bin["assigned"]]
        stock_copy["cut_plan_placement"] = next(
            entry for entry in chosen_bin["assigned"] if entry["part_index"] == part_index
        )
        stock_copy["rotated"] = stock_copy["cut_plan_placement"]["rotated"]
        stock_copy["waste_area"] = max(
            0,
            int(stock_copy.get("length", 0) or 0) * int(stock_copy.get("width", 0) or 0)
            - stock_copy["cut_plan_placement"]["length_with_allowance"]
            * stock_copy["cut_plan_placement"]["width_with_allowance"],
        )
        stock_copy["cut_plan_remaining_width"] = max(
            0,
            int(stock_copy.get("width", 0) or 0) - chosen_bin["used_width"],
        )
        results.append((part, [stock_copy]))
    return results


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


# Apply deferred navigation before the keyed radio widget is created.
# Widgets cannot have their own session-state key changed after instantiation.
if "pending_navigation" in st.session_state:
    st.session_state["main_navigation"] = st.session_state.pop("pending_navigation")

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
            st.markdown('<div class="sf-eyebrow">♻ Project-based matching for reusable materials</div>', unsafe_allow_html=True)
            st.markdown('<div class="sf-hero-title">Good materials deserve a second life.</div>', unsafe_allow_html=True)
            st.markdown(
                '<div class="sf-hero-copy">ScrapFit helps people find a next use for leftover wood and metal. Describe the parts a project needs, compare them with available offcuts, and explore local pickup options before buying new material.</div>',
                unsafe_allow_html=True,
            )
            st.markdown('<div class="sf-hero-kicker">Project-first matching · Cutting-plan assistance · Local reuse</div>', unsafe_allow_html=True)
        with hero_art:
            hero_image = Path(__file__).with_name("scrapfit_hero_photo.png")
            if hero_image.exists():
                st.image(str(hero_image), use_container_width=True)
            else:
                st.warning("Place scrapfit_hero_photo.png beside app.py to display the workshop photo.")

        st.markdown("### Start with what you need")
        st.markdown("Search for a suitable piece, plan a project from its parts list, or list leftover material for someone else to use.")
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
    st.markdown('<div class="sf-section-kicker">Material workspace</div><div class="sf-section-title">See what is available to explore</div>', unsafe_allow_html=True)
    st.markdown('<div class="sf-section-copy">These figures describe the demo inventory loaded by this app. Sample listings are used to demonstrate the workflow; they are not verified live offers from real sellers.</div>', unsafe_allow_html=True)
    total_pieces = len(inventory)
    wood_pieces = sum(p.get("material") == "Wood" for p in inventory)
    metal_pieces = sum(p.get("material") == "Metal" for p in inventory)
    metric1, metric2, metric3 = st.columns(3)
    metric1.metric("Demo listings", total_pieces, help="Number of listing records in the demo inventory, not the total quantity of physical pieces.")
    metric2.metric("Wood listings", wood_pieces)
    metric3.metric("Metal listings", metal_pieces)

    st.markdown('<div class="sf-divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="sf-section-kicker">Why ScrapFit</div><div class="sf-section-title">The hard part is finding the right leftover</div>', unsafe_allow_html=True)
    st.markdown('<div class="sf-section-copy">A usable offcut can be difficult to discover when leftover materials are stored without searchable dimensions. Meanwhile, a maker or workshop may need only one or two pieces—not a full board or sheet. ScrapFit is designed to connect those two sides through project requirements and clearer listing details.</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown('<div class="sf-card"><div class="sf-card-icon">⌕</div><h3>Search for a fit</h3><p>Filter by material, dimensions, thickness and pickup area to find offcuts that could meet a part requirement.</p></div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="sf-card"><div class="sf-card-icon">▤</div><h3>Plan more than one part</h3><p>Enter the parts a project needs. ScrapFit checks suitable pieces and can try grouping multiple parts onto the same offcut using a prototype cutting-layout heuristic.</p></div>', unsafe_allow_html=True)
    with c3:
        st.markdown('<div class="sf-card"><div class="sf-card-icon">⌖</div><h3>Keep reuse local</h3><p>Pickup-area details and approximate map locations help people explore nearby options and contact the listing owner to confirm the details.</p></div>', unsafe_allow_html=True)

    st.markdown('<div class="sf-divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="sf-section-kicker">How it works</div><div class="sf-section-title">From a project idea to a possible offcut</div>', unsafe_allow_html=True)
    st.markdown('<div class="sf-section-copy">The app keeps project suggestions and material-fit decisions separate: AI can help draft a parts list, while ScrapFit’s matching rules check the requirements against the inventory.</div>', unsafe_allow_html=True)
    step1, step2, step3 = st.columns(3)
    with step1:
        st.markdown('<div class="sf-step"><div class="sf-step-num">STEP 01</div><h3>List or describe</h3><p>A listing records material, dimensions, thickness, condition, price, quantity and pickup details. A buyer enters an individual part or a project cut list; Custom Project can generate an editable AI draft.</p></div>', unsafe_allow_html=True)
    with step2:
        st.markdown('<div class="sf-step"><div class="sf-step-num">STEP 02</div><h3>Check dimensions and quantity</h3><p>Rule-based matching checks the required material and dimensions, includes the configured cutting allowance, and ranks suitable available offcuts. The cutting layout is a prototype estimate, not a factory-validated nesting plan.</p></div>', unsafe_allow_html=True)
    with step3:
        st.markdown('<div class="sf-step"><div class="sf-step-num">STEP 03</div><h3>Review and arrange pickup</h3><p>Compare the match and rough cost estimates, inspect the listing details, and contact the seller to confirm the actual material, availability, price and collection.</p></div>', unsafe_allow_html=True)

    st.markdown('<div class="sf-divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="sf-section-kicker">Who it can help</div><div class="sf-section-title">Small quantities, practical projects</div>', unsafe_allow_html=True)
    b1, b2, b3, b4 = st.columns(4)
    with b1:
        st.markdown('<div class="sf-card"><div class="sf-card-icon">⚙</div><h3>Workshops</h3><p>Make reusable wood and metal leftovers easier to list and potentially recover value from.</p></div>', unsafe_allow_html=True)
    with b2:
        st.markdown('<div class="sf-card"><div class="sf-card-icon">▦</div><h3>Small businesses</h3><p>Look for smaller quantities that fit a job without automatically buying a full sheet or board.</p></div>', unsafe_allow_html=True)
    with b3:
        st.markdown('<div class="sf-card"><div class="sf-card-icon">✎</div><h3>Makers and students</h3><p>Explore material options for prototypes, creative builds and practical projects.</p></div>', unsafe_allow_html=True)
    with b4:
        st.markdown('<div class="sf-card"><div class="sf-card-icon">⌁</div><h3>Repair providers</h3><p>Find a usable piece for small repairs where an offcut may be enough.</p></div>', unsafe_allow_html=True)

    st.markdown('<div class="sf-divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="sf-section-kicker">Circular value</div><div class="sf-section-title">Keep useful material in circulation</div>', unsafe_allow_html=True)
    st.markdown('<div class="sf-section-copy">When an unused piece meets a real project requirement, material that might otherwise sit in storage or be discarded can continue to be useful.</div>', unsafe_allow_html=True)
    st.markdown('<div class="sf-flow"><span>Workshop leftovers</span><b>→</b><span>Project-based matching</span><b>→</b><span>Local collection</span><b>→</b><span>Useful new product</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="sf-callout"><strong>Our aim</strong><br>Make reuse a practical option by making leftover materials easier to describe, compare and discover before new material is purchased. ScrapFit starts with wood and metal, local pickup and a straightforward matching workflow.</div>', unsafe_allow_html=True)

    st.markdown('<div class="sf-divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="sf-section-kicker">Current build and next steps</div><div class="sf-section-title">A working prototype with room to grow</div>', unsafe_allow_html=True)
    st.markdown('<div class="sf-section-copy">The current app demonstrates the core workflow with sample inventory. The next improvements focus on making listings more dependable, cutting plans more useful and participation easier to scale.</div>', unsafe_allow_html=True)
    left, right = st.columns(2, gap="large")
    with left:
        st.markdown('<div class="sf-card"><h3>Available in this prototype</h3><p>• Browse sample wood and metal listings<br>• Filter by pickup area or search by dimensions and thickness<br>• Create a manual project cut list and set quantity for each part<br>• Generate and edit an AI-assisted draft parts list in Custom Project<br>• Match requirements against the inventory using rules<br>• View a prototype cutting plan and rough cost estimates<br>• View approximate pickup locations on a map<br>• Save listings temporarily and contact a seller using the listed details</p><p class="sf-footnote">Listing changes and uploaded photos are not yet backed by a shared permanent database; demo inventory and locations should be treated as illustrative.</p></div>', unsafe_allow_html=True)
    with right:
        st.markdown('<div class="sf-card"><h3>Planned enhancements</h3><p><strong>More reliable listings</strong><br>Verified workshop profiles, clearer condition grades and availability updates.<br><br><strong>Traceable inventory</strong><br>QR codes that open an individual offcut record and help workshops track stock.<br><br><strong>Smarter cutting plans</strong><br>Improve layout optimisation and account for blade kerf, grain direction and usable defects.<br><br><strong>Broader local reuse</strong><br>Persistent cloud inventory and photo storage, more material types, and ways to group nearby pickups.<br><br><strong>Sustainable business model</strong><br>Explore clearly labelled promoted shop listings or advertising; consider transaction commissions only when completed sales can be tracked reliably.</p><p class="sf-footnote">These are roadmap ideas, not features currently offered by the prototype.</p></div>', unsafe_allow_html=True)

    st.markdown('<p class="sf-footnote">Demo notice: sample listing details and approximate pickup locations are for demonstration and are not verified offers. Illustrative material photographs may not show the exact item listed. Before purchasing or building, confirm actual dimensions, material grade, condition, price, availability and collection with the seller. AI-generated part lists and cutting plans are estimates that require review.</p>', unsafe_allow_html=True)

# -------------------- FIND SCRAP --------------------

if page == "Find Scrap":
    st.header("🔎 Find a piece for your project")
    st.write(
        "Choose how you want to search. Only the fields for your selected search "
        "type will appear below."
    )

    # This is the first control on the page. The project-part dimensions are shown
    # only when the user chooses Dimensions or Pickup place + Dimensions.
    filter_mode = st.selectbox(
        "Filter by",
        ["Pickup place", "Dimensions", "Pickup place + Dimensions"],
        key="find_filter_mode_v3",
        help="Choose whether to browse by pickup place, match dimensions, or do both.",
    )

    available_inventory = [
        piece for piece in inventory
        if piece.get("status", "Available") == "Available"
    ]

    # Make one consistent dropdown list from saved place fields. We compare
    # exact normalized labels below instead of accepting free-text spellings.
    place_labels = {}
    for piece in available_inventory:
        for value in (piece.get("pickup_location"), piece.get("area")):
            if value and str(value).strip():
                label = str(value).strip()
                place_labels.setdefault(label.casefold(), label)
    place_options = ["All places"] + sorted(place_labels.values(), key=str.casefold)

    use_place = filter_mode in ("Pickup place", "Pickup place + Dimensions")
    use_dimensions = filter_mode in ("Dimensions", "Pickup place + Dimensions")

    selected_place = "All places"
    if use_place:
        selected_place = st.selectbox(
            "Choose pickup place",
            place_options,
            key="find_filter_place_v3",
            help="Select a saved pickup place; there is no free-text location field.",
        )

    # Project-part requirements are part of the Dimensions search option, not a
    # separate always-visible form. They are used for matching only in the two
    # modes that include Dimensions.
    required_material = None
    required_length = required_width = required_thickness = None
    cutting_allowance = 5
    if use_dimensions:
        st.markdown("#### Dimensions required for your project part")
        st.caption(
            "These are the dimensions of the part you need. They control material "
            "matching; they are not the optional listing-size filter fields."
        )
        dim_col1, dim_col2 = st.columns(2)
        with dim_col1:
            required_material = st.selectbox(
                "Material",
                ["Wood", "Metal"],
                key="find_required_material_v3",
            )
            required_length = st.number_input(
                "Required length (mm)", min_value=1, max_value=10000,
                value=500, step=10, key="find_required_length_v3",
            )
            required_thickness = st.number_input(
                "Required thickness (mm)", min_value=1, max_value=500,
                value=18 if required_material == "Wood" else 3,
                step=1, key="find_required_thickness_v3",
            )
        with dim_col2:
            required_width = st.number_input(
                "Required width (mm)", min_value=1, max_value=10000,
                value=250, step=10, key="find_required_width_v3",
            )
            cutting_allowance = st.number_input(
                "Extra cutting allowance per side (mm)", min_value=0,
                max_value=100, value=5, step=1,
                key="find_required_allowance_v3",
                help="Adds this allowance to each edge of the required part.",
            )
            st.caption(
                "Thickness must match exactly. Confirm grain direction and cutting "
                "requirements with the seller."
            )

    # Additional Amazon-style filters. Listing size bounds are independent of
    # the required project-part dimensions above, and are only shown when the
    # Dimensions mode is selected (the dropdown controls their visibility).
    with st.expander("More filters", expanded=False):
        if not use_dimensions:
            material_options = sorted({
                str(piece.get("material", "")).strip()
                for piece in available_inventory if piece.get("material")
            }, key=str.casefold)
            filter_material = st.selectbox(
                "Material type", ["All materials"] + material_options,
                key="find_listing_material_v3",
            )
        else:
            filter_material = "All materials"  # required material above is the material filter

        conditions = sorted({
            str(piece.get("condition", "Not specified"))
            for piece in available_inventory
        }, key=str.casefold)
        filter_condition = st.selectbox(
            "Condition", ["All conditions"] + conditions,
            key="find_listing_condition_v3",
        )
        all_prices = [int(piece.get("price", 0) or 0) for piece in available_inventory]
        price_cap = max(100, max(all_prices, default=100))
        min_price, max_price = st.slider(
            "Price range (₹ per piece)", 0, price_cap, (0, price_cap),
            step=max(1, price_cap // 100), key="find_listing_price_v3",
        )

        if use_dimensions:
            st.markdown("**Optional listing-size limits (independent of required part dimensions)**")
            size_left, size_right = st.columns(2)
            with size_left:
                min_listing_length = st.number_input(
                    "Minimum listing length (mm)", min_value=0, max_value=10000,
                    value=0, step=50, key="find_min_listing_length_v3",
                )
                min_listing_width = st.number_input(
                    "Minimum listing width (mm)", min_value=0, max_value=10000,
                    value=0, step=50, key="find_min_listing_width_v3",
                )
                min_listing_thickness = st.number_input(
                    "Minimum listing thickness (mm)", min_value=0, max_value=500,
                    value=0, step=1, key="find_min_listing_thickness_v3",
                )
            with size_right:
                max_listing_length = st.number_input(
                    "Maximum listing length (mm; 0 = any)", min_value=0,
                    max_value=10000, value=0, step=50,
                    key="find_max_listing_length_v3",
                )
                max_listing_width = st.number_input(
                    "Maximum listing width (mm; 0 = any)", min_value=0,
                    max_value=10000, value=0, step=50,
                    key="find_max_listing_width_v3",
                )
                max_listing_thickness = st.number_input(
                    "Maximum listing thickness (mm; 0 = any)", min_value=0,
                    max_value=500, value=0, step=1,
                    key="find_max_listing_thickness_v3",
                )
        else:
            min_listing_length = min_listing_width = min_listing_thickness = 0
            max_listing_length = max_listing_width = max_listing_thickness = 0

    button_label = "Find Matching Scrap" if use_dimensions else "Show Scrap at Selected Place"
    search_submitted = st.button(
        button_label, type="primary", use_container_width=True,
        key="find_apply_filters_v3",
    )

    if search_submitted:
        if use_dimensions:
            search_results = find_matches(
                required_material, int(required_length), int(required_width),
                int(required_thickness), available_inventory,
                allowance_per_side=int(cutting_allowance),
            )
        else:
            # In place-only mode, browse listings at the chosen place without
            # applying the separate required-project-dimensions matching rule.
            search_results = []
            for source_piece in available_inventory:
                piece = source_piece.copy()
                piece["rotated"] = False
                piece["waste_area"] = None
                search_results.append(piece)

        if use_place and selected_place != "All places":
            chosen_key = selected_place.casefold()
            search_results = [
                piece for piece in search_results
                if chosen_key in {
                    str(piece.get("area", "")).strip().casefold(),
                    str(piece.get("pickup_location", "")).strip().casefold(),
                }
            ]

        if filter_material != "All materials":
            search_results = [
                piece for piece in search_results
                if str(piece.get("material", "")).strip().casefold()
                == filter_material.casefold()
            ]
        if filter_condition != "All conditions":
            search_results = [
                piece for piece in search_results
                if str(piece.get("condition", "Not specified")) == filter_condition
            ]
        search_results = [
            piece for piece in search_results
            if min_price <= int(piece.get("price", 0) or 0) <= max_price
        ]

        if use_dimensions:
            search_results = [
                piece for piece in search_results
                if int(piece.get("length", 0) or 0) >= int(min_listing_length)
                and int(piece.get("width", 0) or 0) >= int(min_listing_width)
                and int(piece.get("thickness", 0) or 0) >= int(min_listing_thickness)
                and (not max_listing_length or int(piece.get("length", 0) or 0) <= int(max_listing_length))
                and (not max_listing_width or int(piece.get("width", 0) or 0) <= int(max_listing_width))
                and (not max_listing_thickness or int(piece.get("thickness", 0) or 0) <= int(max_listing_thickness))
            ]

        st.session_state.find_results_v3 = search_results
        st.session_state.find_search_mode_v3 = filter_mode
        st.session_state.find_search_place_v3 = selected_place
        st.session_state.find_search_dimensions_v3 = (
            (required_material, int(required_length), int(required_width),
             int(required_thickness), int(cutting_allowance)) if use_dimensions else None
        )

    # Hide stale results if the user switches search mode, so a Place-only page
    # never continues displaying results from a previous Dimensions search.
    if (
        "find_results_v3" in st.session_state
        and st.session_state.get("find_search_mode_v3") == filter_mode
    ):
        results = st.session_state.find_results_v3
        saved_place = st.session_state.get("find_search_place_v3", "All places")
        saved_dimensions = st.session_state.get("find_search_dimensions_v3")
        st.subheader("Matching results")

        if saved_dimensions:
            mat_q, len_q, wid_q, thick_q, allowance_q = saved_dimensions
            st.caption(
                f"Requirement: {mat_q} | {len_q} × {wid_q} × {thick_q} mm "
                f"(cutting allowance: {allowance_q} mm per side)"
            )
        elif saved_place == "All places":
            st.caption("Showing available listings across all pickup places; dimensions were not used to match this search.")
        else:
            st.caption(f"Showing available listings at {saved_place}; dimensions were not used to match this search.")

        if not results:
            st.warning("No listings match the selected filters. Try another place, widen the price or listing-size range, or change the condition.")
        else:
            st.success(f"Found {len(results)} listing(s) for the selected search.")
            for index, piece in enumerate(results, start=1):
                with st.container(border=True):
                    photo_col, left, middle, right = st.columns([1.25, 2.5, 2, 1])
                    with photo_col:
                        st.image(material_image(piece), use_container_width=True)
                        st.caption("Sample reference photo — not a photo of this exact piece")
                    with left:
                        st.markdown(f"**{index}. {piece.get('name', 'Unnamed offcut')}**")
                        st.write(f"{piece.get('material', 'Material unspecified')} · {piece.get('condition', 'Condition not specified')}")
                        st.caption(f"Pickup area: {piece.get('area') or piece.get('pickup_location') or 'Not specified'}")
                    with middle:
                        st.write(
                            f"**Size:** {piece.get('length', '?')} × "
                            f"{piece.get('width', '?')} × {piece.get('thickness', '?')} mm"
                        )
                        if piece.get("waste_area") is not None:
                            st.write(f"**Unused surface area:** {piece['waste_area']:,} mm²")
                            if piece.get("rotated"):
                                st.caption("Fits when rotated 90°")
                        else:
                            st.caption("Dimensions shown for reference; not used to match this Place-only search.")
                    with right:
                        st.metric("Price", f"₹{piece.get('price', '—')}")
                        st.caption(f"ID: {piece.get('id', '—')}")

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
                        "♡ Save for Later" if piece.get("id") not in st.session_state.saved_ids else "♥ Saved",
                        key=f"save_find_v3_{piece.get('id', index)}",
                    ):
                        if piece.get("id") not in st.session_state.saved_ids:
                            st.session_state.saved_ids.append(piece["id"])
                        st.toast("Saved for later")

            st.markdown("### Map view (demo locations)")
            st.caption("Hover over a pin to see listing details. Pins are illustrative demo locations, not verified seller addresses.")
            demo_points = []
            area_coords = {
                "Area A": (80.225, 13.055),
                "Area B": (80.245, 13.075),
                "Area C": (80.265, 13.045),
                "Chennai": (80.270, 13.082),
                "Padur": (80.2258, 12.8077),
            }
            for idx, item in enumerate(results):
                area = item.get("area") or item.get("pickup_location") or "Chennai"
                coords = item.get("coordinates") or {}
                if isinstance(coords, dict) and coords.get("lat") is not None and coords.get("lon") is not None:
                    lat, lon = float(coords["lat"]), float(coords["lon"])
                else:
                    lon, lat = area_coords.get(area, area_coords["Chennai"])
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
                    tooltip = {
                        "html": "<b>{name}</b><br/>ID: {id}<br/>{material} · {dimensions}<br/>{price}<br/>Condition: {condition}<br/>Pickup area: {area}",
                        "style": {"backgroundColor": "#173F34", "color": "white", "padding": "10px", "borderRadius": "8px"},
                    }
                    view_state = pdk.ViewState(latitude=13.07, longitude=80.245, zoom=11, pitch=0)
                    st.pydeck_chart(
                        pdk.Deck(layers=[layer], initial_view_state=view_state, tooltip=tooltip, map_style=None),
                        use_container_width=True,
                    )
                except Exception:
                    st.warning("Hoverable map needs pydeck. Showing the locations as a basic map instead.")
                    st.map(demo_points, latitude="lat", longitude="lon", size=80)


# -------------------- PROJECT CUT LIST --------------------

if page == "Project Planner":
    st.header("Project Planner")
    planner_available = [p for p in inventory if p.get("status", "Available") == "Available"]
    st.write(
        "Add the rectangular parts required for a project. ScrapFit leaves a cutting "
        "allowance and plans multiple parts from one physical offcut when a simple "
        "cutting layout fits. Set the quantity for repeated parts, such as four table legs."
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
            c1, c2, c3, c4, c5 = st.columns([2, 1, 1, 1, 0.9])

            with c1:
                part_name = st.text_input(
                    "Part name",
                    value=f"Part {i + 1}",
                    key=f"part_name_{i}",
                )
            with c2:
                part_length = st.number_input(
                    "Length (mm)",
                    min_value=1,
                    max_value=10000,
                    value=500,
                    step=10,
                    key=f"part_length_{i}",
                )
            with c3:
                part_width = st.number_input(
                    "Width (mm)",
                    min_value=1,
                    max_value=10000,
                    value=250,
                    step=10,
                    key=f"part_width_{i}",
                )
            with c4:
                part_thickness = st.number_input(
                    "Thickness (mm)",
                    min_value=1,
                    max_value=500,
                    value=18,
                    step=1,
                    key=f"part_thickness_{i}",
                )
            with c5:
                part_quantity = st.number_input(
                    "Quantity",
                    min_value=1,
                    max_value=30,
                    value=1,
                    step=1,
                    key=f"part_quantity_{i}",
                    help="How many identical pieces does the project need? For example, a table usually needs 4 legs.",
                )

            parts.append(
                {
                    "name": part_name.strip() or f"Part {i + 1}",
                    "length": int(part_length),
                    "width": int(part_width),
                    "thickness": int(part_thickness),
                    "quantity": int(part_quantity),
                }
            )

        project_material = st.selectbox(
            "Material for these parts",
            ["Wood", "Metal"],
            key="project_material",
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
        total_required_pieces = sum(int(part.get("quantity", 1)) for part in parts)
        if total_required_pieces > 30:
            st.session_state.pop("project_results", None)
            st.warning("This planner supports up to 30 physical pieces per search. Reduce the quantities and try again.")
        else:
            # Project Planner deliberately uses all available inventory; the optional
            # listing filters belong only on Find Scrap.
            planner_inventory = planner_available
            expanded_parts = expand_part_quantities(parts)
            project_results = allocate_project_parts(
                project_material, expanded_parts, planner_inventory,
                allowance_per_side=int(project_allowance),
            )

            st.session_state.project_results = project_results
            st.session_state.project_title = project_name
            st.session_state.project_parts = parts
            st.session_state.project_material_saved = project_material
            st.session_state.project_allowance_saved = int(project_allowance)

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
        # Group required parts by physical offcut so a shared cut plan and its cost
        # are displayed once rather than looking like repeated purchases.
        cut_groups = {}
        for part, piece in assigned_results:
            unit_key = piece.get("cut_plan_unit_key", f"legacy-{piece.get('id', piece.get('name'))}")
            if unit_key not in cut_groups:
                cut_groups[unit_key] = {"piece": piece, "parts": []}
            cut_groups[unit_key]["parts"].append(part)
        cut_groups = sorted(
            cut_groups.values(),
            key=lambda group: (
                int(group["piece"].get("length", 0) or 0) * int(group["piece"].get("width", 0) or 0),
                int(group["piece"].get("price", 0) or 0),
            ),
        )

        saved_parts = st.session_state.get("project_parts", [p for p, _ in project_results])
        saved_material = st.session_state.get("project_material_saved", "Wood")
        saved_allowance = st.session_state.get("project_allowance_saved", 5)
        cost_rows, estimated_new_cost, matched_scrap_cost = project_cost_summary(saved_parts, inventory, saved_material, saved_allowance)
        st.markdown("### Approximate material cost")
        st.caption("Planning estimate only. New-material estimate uses the lowest sample listing price per square millimetre as an area-based proxy. Scrap cost counts each whole physical offcut used once. Labour, transport and blade kerf are excluded; the cutting layout is a simple heuristic, not industrial nesting.")
        st.write(f"**Estimated new-material equivalent:** ₹{estimated_new_cost:,}")
        st.write(f"**Whole-offcut scrap estimate:** ₹{matched_scrap_cost:,}")
        st.dataframe([{"Part": r["part"], "Estimated new material (₹)": r["new_estimate"], "Scrap cost contribution (₹)": (r["scrap_price"] if r["scrap_price"] not in (None, 0) else ("Same offcut — cost counted once" if r["scrap_price"] == 0 else "No match"))} for r in cost_rows], use_container_width=True, hide_index=True)

        st.info(
            f"{len(assigned_results)} of {len(project_results)} required pieces can be cut from the current plan. "
            "The same physical offcut can serve multiple parts if the simple shelf-layout heuristic finds a fit; each offcut is purchased only once in the estimate."
        )

        if cut_groups:
            st.markdown("### Offcuts used in the cutting plan")
            for rank, group in enumerate(cut_groups, start=1):
                piece = group["piece"]
                parts_from_piece = group["parts"]
                with st.container(border=True):
                    title_col, price_col = st.columns([4, 1])
                    with title_col:
                        st.markdown(f"**{rank}. {piece.get('name', 'Unnamed offcut')}**")
                        st.caption(f"Listing ID: {piece.get('id', 'N/A')} · Physical offcut unit {piece.get('cut_plan_unit_key', '')}")
                    with price_col:
                        st.metric("Cost counted once", f"₹{piece.get('price', 0):,}")

                    st.write(f"**Available size:** {piece.get('length', '?')} × {piece.get('width', '?')} × {piece.get('thickness', '?')} mm")
                    st.write(f"**Material / condition:** {piece.get('material', 'Not specified')} / {piece.get('condition', 'Not specified')}")
                    st.write("**Parts planned from this offcut:**")
                    for part in parts_from_piece:
                        st.write(f"- {part['name']} — {part['length']} × {part['width']} × {part['thickness']} mm")
                    if piece.get("notes"):
                        st.write(f"**Seller's material description:** {piece['notes']}")
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
            st.success("Every required piece has been assigned in the current cutting plan.")


# -------------------- LIST SCRAP --------------------

if page == "List Scrap":
    st.header("➕ List leftover material")
    st.write("Enter the dimensions and details of a reusable offcut.")

    # Reset the previous successful submission only when the user returns to
    # this page. Failed validation or a save error never clears their entries.
    if st.session_state.pop("reset_listing_form", False):
        listing_defaults = {
            "listing_name_input": "",
            "listing_material_input": "Wood",
            "listing_length_input": 600,
            "listing_thickness_input": 18,
            "listing_condition_input": "A - Clean",
            "listing_width_input": 300,
            "listing_quantity_input": 1,
            "listing_price_input": 50,
            "listing_area_input": "",
            "listing_seller_input": "",
            "listing_phone_input": "",
            "listing_pickup_location_input": "",
            "listing_pickup_details_input": "",
            "listing_notes_input": "",
            "listing_lat_input": 13.0827,
            "listing_lon_input": 80.2707,
        }
        for state_key, default_value in listing_defaults.items():
            st.session_state[state_key] = default_value

    with st.form("list_scrap_form", clear_on_submit=False):
        listing_name = st.text_input(
            "Listing name", placeholder="e.g. Plywood offcut", key="listing_name_input"
        )

        c1, c2 = st.columns(2)

        with c1:
            listing_material = st.selectbox(
                "Material", ["Wood", "Metal"], key="listing_material_input"
            )
            listing_length = st.number_input(
                "Length (mm)", min_value=1, max_value=10000, value=600,
                step=10, key="listing_length_input"
            )
            default_thickness = 18 if listing_material == "Wood" else 3
            # Keep the material-specific default when the user changes material,
            # but don't overwrite a thickness value they have already entered.
            if "listing_thickness_input" not in st.session_state:
                st.session_state["listing_thickness_input"] = default_thickness
            listing_thickness = st.number_input(
                "Thickness (mm)", min_value=1, max_value=500,
                value=int(st.session_state.get("listing_thickness_input", default_thickness)),
                step=1, key="listing_thickness_input"
            )
            listing_condition = st.selectbox(
                "Condition",
                ["A - Clean", "B - Minor marks", "C - Usable for small parts"],
                key="listing_condition_input",
            )

        with c2:
            listing_width = st.number_input(
                "Width (mm)", min_value=1, max_value=10000, value=300,
                step=10, key="listing_width_input"
            )
            listing_quantity = st.number_input(
                "Number of identical pieces", min_value=1, max_value=1000,
                value=1, step=1, key="listing_quantity_input",
                help="Use one listing for pieces with the same dimensions, condition and price.",
            )
            listing_price = st.number_input(
                "Price per piece (₹)", min_value=0, max_value=1000000,
                value=50, step=10, key="listing_price_input"
            )
            listing_area = st.text_input(
                "Pickup area / neighbourhood *", placeholder="e.g. Guindy, Chennai",
                key="listing_area_input"
            )

        st.markdown("**Seller and pickup details**")
        seller_name = st.text_input(
            "Seller or shop name", placeholder="e.g. ABC Fabrication Shop",
            key="listing_seller_input"
        )
        contact_phone = st.text_input(
            "Phone / WhatsApp number", placeholder="Include country code, e.g. +91...",
            key="listing_phone_input"
        )
        pickup_location = st.text_input(
            "Pickup address or landmark", placeholder="Shop address, street, or nearby landmark",
            key="listing_pickup_location_input"
        )
        pickup_details = st.text_area(
            "When can the buyer collect it?",
            placeholder="e.g. Weekdays 10 AM–5 PM; call before visiting; bring your own transport.",
            key="listing_pickup_details_input",
        )
        listing_notes = st.text_area(
            "Material description (optional)",
            placeholder="Describe marks, material grade, storage condition, or other details",
            key="listing_notes_input",
        )
        listing_photo = st.file_uploader(
            "Upload a photo of this scrap (optional)",
            type=["png", "jpg", "jpeg", "webp"],
            help="For this local prototype, the photo is saved in a folder beside app.py on this computer.",
        )
        st.markdown("**Map pin (optional)**")
        listing_lat = st.number_input(
            "Latitude", min_value=-90.0, max_value=90.0, value=13.0827,
            format="%.6f", key="listing_lat_input",
            help="Use the approximate pickup location coordinates. Leave the default only for a demo pin.",
        )
        listing_lon = st.number_input(
            "Longitude", min_value=-180.0, max_value=180.0, value=80.2707,
            format="%.6f", key="listing_lon_input",
            help="Use the approximate pickup location coordinates. Leave the default only for a demo pin.",
        )

        listing_submitted = st.form_submit_button(
            "Add Listing", type="primary", use_container_width=True
        )

    if listing_submitted:
        # Validation is deliberately performed without clearing the form first.
        if not listing_name.strip() or not listing_area.strip():
            st.error("Please enter both a listing name and a pickup area. Your entries are still here—complete the missing fields and submit again.")
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
                "coordinates": {"lat": float(listing_lat), "lon": float(listing_lon)},
            }
            try:
                if listing_photo is not None:
                    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
                    safe_suffix = Path(listing_photo.name).suffix.lower()
                    if safe_suffix not in {".png", ".jpg", ".jpeg", ".webp"}:
                        safe_suffix = ".jpg"
                    image_filename = f"{new_piece['id']}{safe_suffix}"
                    image_path = IMAGE_DIR / image_filename
                    with image_path.open("wb") as image_file:
                        image_file.write(listing_photo.getbuffer())
                    new_piece["image_file"] = image_filename

                # Save the new list first. Only update session state and navigate
                # after the JSON write succeeds, preventing a false success message.
                updated_inventory = list(st.session_state.inventory)
                updated_inventory.append(new_piece)
                save_inventory(updated_inventory)
                st.session_state.inventory = updated_inventory
                st.session_state["listing_added_notice"] = (
                    f"Added '{new_piece['name']}' ({new_piece['id']}) to inventory."
                )
                st.session_state["reset_listing_form"] = True
                # Defer the navigation value until the next run, before the radio
                # widget with key="main_navigation" is instantiated.
                st.session_state["pending_navigation"] = "Inventory"
                st.rerun()
            except (OSError, TypeError, ValueError) as exc:
                st.error(
                    "ScrapFit couldn't save this listing to inventory.json. "
                    f"Your form entries are preserved. Details: {exc}"
                )


# -------------------- INVENTORY --------------------

if page == "Inventory":
    st.header("📦 Scrap inventory")
    added_notice = st.session_state.pop("listing_added_notice", None)
    if added_notice:
        st.success(added_notice)
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

    standard_tab, custom_tab = st.tabs(["Standard Projects", "Custom Project"])

    with custom_tab:
        # AI-powered custom project drafting is deliberately separate from the existing
        # standard project ideas and manual Project Planner.
        with st.container(border=True):
            st.subheader("✨ Custom Project — describe what you want to make")
            st.write("Describe your idea in everyday language. AI will suggest an editable starter cut list; ScrapFit's existing matching engine will then check available offcuts.")
            custom_description = st.text_area(
                "Project description",
                placeholder="e.g. A compact wooden study table with a top, four legs, and a shelf underneath. It should fit in a small room.",
                key="custom_ai_description",
                height=105,
            )
            custom_material_choice = st.selectbox(
                "Primary material for this draft", ["Wood", "Metal"], key="custom_ai_material"
            )
            st.caption("Gemini API setup is required for AI generation. The generated dimensions are estimates and must be reviewed before use.")
            has_ai_key = bool(get_gemini_api_key())
            if not has_ai_key:
                st.info("AI is not configured yet. Set GEMINI_API_KEY in .streamlit/secrets.toml or as an environment variable. You can still build a parts list manually in Project Planner.")
            if st.button("Generate draft parts list with AI", type="primary", key="custom_ai_generate", use_container_width=True):
                if len(custom_description.strip()) < 10:
                    st.warning("Describe your project in a little more detail before generating a draft.")
                elif not has_ai_key:
                    st.error("Gemini API key not found. Follow the setup instructions provided with this app, then restart Streamlit.")
                else:
                    try:
                        with st.spinner("Generating a starter cut list…"):
                            draft_payload = generate_ai_project_draft(custom_description, custom_material_choice)
                        st.session_state["custom_ai_draft"] = draft_payload
                        st.session_state.pop("custom_ai_match_results", None)
                        st.session_state.pop("custom_ai_match_signature", None)
                        st.success("Draft generated. Review every part and edit the dimensions before matching.")
                    except Exception as exc:
                        # Do not display raw exception text, which can contain request details.
                        if isinstance(exc, (ValueError, RuntimeError)):
                            st.error(str(exc))
                        else:
                            st.error(f"Gemini could not generate the draft ({type(exc).__name__}). Check your API key, model access, internet connection, and quota. Manual Project Planner remains available.")

            custom_draft = st.session_state.get("custom_ai_draft")
            if custom_draft:
                st.divider()
                st.markdown(f"### Review draft: {custom_draft.get('title', 'Custom project')}")
                st.caption(f"Primary material: {custom_draft.get('material', 'Wood')} · These are AI-generated estimates, not certified build dimensions.")
                if custom_draft.get("assumptions"):
                    st.markdown("**AI assumptions**")
                    for note in custom_draft["assumptions"]:
                        st.write(f"- {note}")
                edited_custom_parts = []
                for idx, part in enumerate(custom_draft["parts"]):
                    st.markdown(f"**Part {idx + 1}: {part['name']}**")
                    ca, cb, cc, cd, ce = st.columns([2, 1.2, 1.2, 1.1, 0.8])
                    with ca:
                        part_name = st.text_input("Part name", value=part["name"], key=f"custom_ai_name_{part['id']}")
                    with cb:
                        part_length = st.number_input("Length (mm)", min_value=1, max_value=10000, value=int(part["length"]), step=10, key=f"custom_ai_len_{part['id']}")
                    with cc:
                        part_width = st.number_input("Width (mm)", min_value=1, max_value=10000, value=int(part["width"]), step=10, key=f"custom_ai_wid_{part['id']}")
                    with cd:
                        part_thickness = st.number_input("Thickness (mm)", min_value=1, max_value=500, value=int(part["thickness"]), step=1, key=f"custom_ai_thick_{part['id']}")
                    with ce:
                        part_quantity = st.number_input("Quantity", min_value=1, max_value=20, value=int(part.get("quantity", 1)), step=1, key=f"custom_ai_qty_{part['id']}")
                    if part.get("reason"):
                        st.caption(part["reason"])
                    edited_custom_parts.append({
                        "id": part["id"], "name": part_name.strip() or f"Part {idx + 1}",
                        "length": int(part_length), "width": int(part_width),
                        "thickness": int(part_thickness), "quantity": int(part_quantity),
                    })

                cc1, cc2 = st.columns(2)
                with cc1:
                    custom_pickup_area = st.text_input("Pickup area (optional)", key="custom_ai_pickup_area", placeholder="e.g. Guindy, Chennai")
                with cc2:
                    custom_allowance = st.number_input("Cutting allowance per side (mm)", min_value=0, max_value=100, value=5, step=1, key="custom_ai_allowance")

                physical_piece_count = sum(int(part["quantity"]) for part in edited_custom_parts)
                if physical_piece_count > 30:
                    st.warning("This draft currently requires more than 30 individual pieces. Reduce the quantities before matching.")

                expanded_custom_parts = expand_part_quantities(edited_custom_parts)
                estimate_inventory = [item for item in inventory if item.get("status", "Available") == "Available"]
                if custom_pickup_area.strip():
                    area_query = custom_pickup_area.strip().casefold()
                    estimate_inventory = [item for item in estimate_inventory if area_query in (
                        str(item.get("area", "")).casefold() + " " + str(item.get("pickup_location", "")).casefold()
                    )]
                cost_rows, custom_new_estimate, custom_scrap_estimate = project_cost_summary(
                    expanded_custom_parts, estimate_inventory, custom_draft["material"], int(custom_allowance)
                )
                st.markdown("### Cost estimate")
                st.caption("Rough prototype estimate from sample inventory prices, not a live supplier quote. The new-material figure is area-based; the scrap figure counts each whole physical offcut used once. Labour, transport and blade kerf are not included.")
                st.write(f"**Estimated new-material equivalent:** ₹{custom_new_estimate:,} · **Whole-offcut scrap estimate:** ₹{custom_scrap_estimate:,}")
                st.dataframe(
                    [{"Part requirement": r["part"], "New-material estimate (₹)": r["new_estimate"], "Scrap cost contribution (₹)": (r["scrap_price"] if r["scrap_price"] not in (None, 0) else ("Same offcut — cost counted once" if r["scrap_price"] == 0 else "No match"))} for r in cost_rows],
                    use_container_width=True, hide_index=True
                )

                if st.button("Add another part", key="custom_ai_add_part"):
                    if len(edited_custom_parts) >= 10:
                        st.warning("A custom draft can contain up to 10 distinct part types.")
                    else:
                        draft_copy = dict(custom_draft)
                        draft_copy["parts"] = edited_custom_parts + [{
                            "id": uuid.uuid4().hex[:10], "name": f"Additional part {len(edited_custom_parts) + 1}",
                            "length": 200, "width": 100, "thickness": 18 if custom_draft["material"] == "Wood" else 3,
                            "quantity": 1, "reason": "Added by the user; adjust dimensions to suit your design."
                        }]
                        st.session_state["custom_ai_draft"] = draft_copy
                        st.session_state.pop("custom_ai_match_results", None)
                        st.session_state.pop("custom_ai_match_signature", None)
                        st.rerun()

                if edited_custom_parts and st.button("Remove a part…", key="custom_ai_toggle_remove"):
                    st.session_state["custom_ai_remove_mode"] = not st.session_state.get("custom_ai_remove_mode", False)
                    st.rerun()
                if st.session_state.get("custom_ai_remove_mode", False) and edited_custom_parts:
                    remove_index = st.selectbox(
                        "Choose the part to remove", options=list(range(len(edited_custom_parts))),
                        format_func=lambda i: f"{i + 1}. {edited_custom_parts[i]['name']}",
                        key="custom_ai_remove_index",
                    )
                    if st.button("Confirm remove part", key="custom_ai_confirm_remove"):
                        if len(edited_custom_parts) <= 1:
                            st.warning("Keep at least one part in the draft.")
                        else:
                            draft_copy = dict(custom_draft)
                            draft_copy["parts"] = edited_custom_parts[:remove_index] + edited_custom_parts[remove_index + 1:]
                            st.session_state["custom_ai_draft"] = draft_copy
                            st.session_state["custom_ai_remove_mode"] = False
                            st.session_state.pop("custom_ai_match_results", None)
                            st.session_state.pop("custom_ai_match_signature", None)
                            st.rerun()

                custom_signature = json.dumps({
                    "material": custom_draft["material"], "parts": expanded_custom_parts,
                    "area": custom_pickup_area.strip().casefold(), "allowance": int(custom_allowance)
                }, sort_keys=True)
                if st.button("Find matching scrap for this custom project", type="primary", key="custom_ai_match", use_container_width=True):
                    if not any(part["name"].strip() for part in edited_custom_parts):
                        st.warning("Add a name for at least one part.")
                    elif physical_piece_count > 30:
                        st.warning("Reduce the total quantity to 30 pieces or fewer before matching.")
                    else:
                        custom_inventory = [item for item in inventory if item.get("status", "Available") == "Available"]
                        if custom_pickup_area.strip():
                            q = custom_pickup_area.strip().casefold()
                            custom_inventory = [item for item in custom_inventory if q in (str(item.get("area", "")).casefold() + " " + str(item.get("pickup_location", "")).casefold())]
                        custom_matches = allocate_project_parts(
                            custom_draft["material"], expanded_custom_parts, custom_inventory,
                            allowance_per_side=int(custom_allowance),
                        )
                        st.session_state["custom_ai_match_results"] = custom_matches
                        st.session_state["custom_ai_match_signature"] = custom_signature

                if st.session_state.get("custom_ai_match_signature") == custom_signature:
                    custom_matches = st.session_state.get("custom_ai_match_results", [])
                    assigned_custom = [(part, pieces[0]) for part, pieces in custom_matches if pieces]
                    missing_custom = [part for part, pieces in custom_matches if not pieces]
                    st.markdown("### Matching results")
                    st.info(f"{len(assigned_custom)} of {len(custom_matches)} required pieces are assigned. Multiple parts may be cut from the same physical offcut when the simple layout fits; its listing price is counted only once. Rotation is allowed, and the planner includes {int(custom_allowance)} mm allowance on every edge. This is a heuristic cut plan, not an industrial nesting guarantee.")
                    if assigned_custom:
                        shown_cut_units = {}
                        for required_part, piece in assigned_custom:
                            unit_key = piece.get("cut_plan_unit_key", f"legacy-{piece.get('id', piece.get('name'))}")
                            if unit_key in shown_cut_units:
                                st.write(f"- **{required_part['name']}** → cut from the same offcut as **{shown_cut_units[unit_key]}** (no additional listing cost).")
                            else:
                                shown_cut_units[unit_key] = required_part["name"]
                                extra_names = [name for name in piece.get("cut_plan_part_names", []) if name != required_part["name"]]
                                suffix = f" · shared cut plan also covers: {', '.join(extra_names)}" if extra_names else ""
                                st.write(f"- **{required_part['name']}** → **{piece.get('name', 'Offcut')}** — {piece.get('length')} × {piece.get('width')} × {piece.get('thickness')} mm, ₹{piece.get('price', 0)} · {piece.get('area', 'Pickup area not provided')}{suffix}")
                    if missing_custom:
                        st.warning("No suitable offcut was assigned to: " + ", ".join(part["name"] for part in missing_custom) + ". Try changing dimensions, quantity or pickup area.")
                    elif assigned_custom:
                        st.success("All required pieces have a matching offcut in the current inventory.")

                if custom_draft.get("design_notes"):
                    st.markdown("**Review before building**")
                    for note in custom_draft["design_notes"]:
                        st.write(f"- {note}")
                st.caption("AI drafts are suggestions only. Verify dimensions, material grade, stability, joinery, tooling and safe construction with a qualified person where appropriate.")


    with standard_tab:
        st.subheader("Standard project ideas")
        idea_filter = st.selectbox("What do you have or want to make?", ["Any material", "Wood", "Metal"])
        ideas = [
            {"title": "Wall shelf", "material": "Wood", "difficulty": "Beginner", "parts": "2 side supports, 1 shelf panel", "tools": "Saw, drill, screws, measuring tape", "time": "2–4 hours", "description": "A small shelf for books, tools or everyday items."},
            {"title": "Desk organiser", "material": "Wood", "difficulty": "Beginner", "parts": "Base panel, dividers, back panel", "tools": "Saw, glue or screws, sandpaper", "time": "1–3 hours", "description": "A compact organiser for stationery or small workshop tools."},
            {"title": "Metal tool stand", "material": "Metal", "difficulty": "Intermediate", "parts": "Base plate, supports, brackets", "tools": "Measuring tools, drill; suitable metalworking equipment", "time": "Half a day", "description": "A small stand for organising workshop tools. Use safe, suitable fabrication methods."},
            {"title": "Small planter stand", "material": "Wood", "difficulty": "Beginner", "parts": "Top panel, four legs, braces", "tools": "Saw, drill, screws, sandpaper", "time": "2–4 hours", "description": "A simple stand for a small plant pot."},
            {"title": "Metal parts tray", "material": "Metal", "difficulty": "Intermediate", "parts": "Base sheet, side strips", "tools": "Metal shears or suitable workshop tools; gloves and eye protection", "time": "2–4 hours", "description": "A shallow tray for storing small parts."},
        ]
        idea_parts = {
            "Wall shelf": [{"name":"Shelf panel", "length":600, "width":250, "thickness":18, "quantity":1}, {"name":"Side support 1", "length":250, "width":150, "thickness":18, "quantity":1}, {"name":"Side support 2", "length":250, "width":150, "thickness":18, "quantity":1}],
            "Desk organiser": [{"name":"Base panel", "length":300, "width":180, "thickness":12, "quantity":1}, {"name":"Divider 1", "length":180, "width":100, "thickness":12, "quantity":1}, {"name":"Divider 2", "length":180, "width":100, "thickness":12, "quantity":1}],
            "Metal tool stand": [{"name":"Base plate", "length":300, "width":200, "thickness":3, "quantity":1}, {"name":"Support 1", "length":250, "width":50, "thickness":3, "quantity":1}, {"name":"Support 2", "length":250, "width":50, "thickness":3, "quantity":1}],
            "Small planter stand": [{"name":"Top panel", "length":300, "width":300, "thickness":18, "quantity":1}, {"name":"Leg 1", "length":300, "width":40, "thickness":18, "quantity":1}, {"name":"Leg 2", "length":300, "width":40, "thickness":18, "quantity":1}],
            "Metal parts tray": [{"name":"Base sheet", "length":300, "width":200, "thickness":3, "quantity":1}, {"name":"Side strip 1", "length":300, "width":40, "thickness":3, "quantity":1}, {"name":"Side strip 2", "length":200, "width":40, "thickness":3, "quantity":1}],
        }
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
                    if st.button("Review and customise project", key=f"idea_{idea['title']}"):
                        st.session_state.selected_idea = idea["title"]
                        st.session_state.idea_draft_parts = [x.copy() for x in idea_parts[idea["title"]]]
        if st.session_state.get("selected_idea"):
            selected_title = st.session_state.selected_idea
            selected_idea = next((x for x in ideas if x["title"] == selected_title), None)
            if selected_idea:
                st.divider()
                st.subheader(f"Review project draft: {selected_title}")
                st.caption("Edit each part's dimensions and quantity before searching. Dimensions are starter estimates, not a certified design.")
                draft_material = selected_idea["material"]
                edited_parts = []
                for idx, part in enumerate(st.session_state.idea_draft_parts):
                    st.markdown(f"**{part['name']}**")
                    a,b,c,d,e = st.columns(5)
                    with a: pname = st.text_input("Part name", value=part["name"], key=f"idea_name_{selected_title}_{idx}")
                    with b: plen = st.number_input("Length (mm)", min_value=1, max_value=10000, value=int(part["length"]), step=10, key=f"idea_len_{selected_title}_{idx}")
                    with c: pwid = st.number_input("Width (mm)", min_value=1, max_value=10000, value=int(part["width"]), step=10, key=f"idea_wid_{selected_title}_{idx}")
                    with d: pthick = st.number_input("Thickness (mm)", min_value=1, max_value=500, value=int(part["thickness"]), step=1, key=f"idea_thick_{selected_title}_{idx}")
                    with e: pqty = st.number_input("Quantity", min_value=1, max_value=100, value=int(part.get("quantity", 1)), step=1, key=f"idea_qty_{selected_title}_{idx}")
                    edited_parts.append({"name":pname, "length":int(plen), "width":int(pwid), "thickness":int(pthick), "quantity":int(pqty)})
                idea_area = st.text_input("Pickup place (optional)", key=f"idea_area_{selected_title}", placeholder="e.g. Guindy, Chennai")
                idea_allowance = st.number_input("Cutting allowance per side (mm)", min_value=0, max_value=100, value=5, key=f"idea_allowance_{selected_title}")
                cost_rows, new_est, scrap_est = project_cost_summary(edited_parts, inventory, draft_material, int(idea_allowance))
                st.markdown("### Cost estimate")
                st.caption("Rough prototype estimate from sample listing prices, not a live supplier quote. New-material cost is an area-based proxy; each whole offcut used is counted once. Labour, transport and blade kerf are excluded.")
                st.write(f"**Estimated new-material equivalent:** ₹{new_est:,} · **Whole-offcut scrap estimate:** ₹{scrap_est:,}")
                st.dataframe([{"Part":r["part"], "New material estimate (₹)":r["new_estimate"], "Scrap cost contribution (₹)": (r["scrap_price"] if r["scrap_price"] not in (None, 0) else ("Same offcut — cost counted once" if r["scrap_price"] == 0 else "No match"))} for r in cost_rows], use_container_width=True, hide_index=True)
                if st.button("Find matching scrap for this project", type="primary", key=f"idea_find_{selected_title}"):
                    idea_inventory = [x for x in inventory if x.get("status", "Available") == "Available"]
                    if idea_area.strip():
                        q = idea_area.strip().casefold()
                        idea_inventory = [x for x in idea_inventory if q in (str(x.get("area", "")).casefold()+" "+str(x.get("pickup_location", "")).casefold())]
                    matches = allocate_project_parts(draft_material, expand_part_quantities(edited_parts), idea_inventory, allowance_per_side=int(idea_allowance))
                    st.session_state.idea_match_results = matches
                    st.session_state.idea_match_title = selected_title
                if st.session_state.get("idea_match_title") == selected_title:
                    matches = st.session_state.get("idea_match_results", [])
                    found = [(part, pieces[0]) for part, pieces in matches if pieces]
                    missing = [part for part, pieces in matches if not pieces]
                    st.subheader("Matching materials")
                    if found:
                        st.caption("Several parts can share one offcut when the simple cutting layout permits it; the offcut price is counted once in the project estimate.")
                        shown_cut_units = {}
                        for part, piece in found:
                            unit_key = piece.get("cut_plan_unit_key", f"legacy-{piece.get('id', piece.get('name'))}")
                            if unit_key in shown_cut_units:
                                st.write(f"- **{part['name']}** → cut from the same offcut as **{shown_cut_units[unit_key]}** (no additional listing cost).")
                            else:
                                shown_cut_units[unit_key] = part["name"]
                                extra_names = [name for name in piece.get("cut_plan_part_names", []) if name != part["name"]]
                                suffix = f" · shared cut plan also covers: {', '.join(extra_names)}" if extra_names else ""
                                st.write(f"- **{part['name']}** → {piece['name']} ({piece['length']} × {piece['width']} × {piece['thickness']} mm), ₹{piece.get('price',0)} · {piece.get('area','Pickup area not provided')}{suffix}")
                    if missing:
                        st.warning("No matching material was found for: " + ", ".join(x["name"] for x in missing) + ". Try changing dimensions, material, or pickup area.")
                    elif not found:
                        st.warning("No matching materials found. Try changing dimensions or checking the inventory.")
                    else:
                        st.success(f"Matched {len(found)} of {len(matches)} part requirements. Unmatched parts are listed above if any.")
        st.info("These sample project ideas are starter drafts. Check dimensions, stability and safe construction before building.")


# -------------------- SAVE FOR LATER --------------------

if page == "Save for Later":
    st.header("♡ Save for Later")
    st.caption("Your saved items are temporary and may disappear when the session ends. There is no login or account.")
    saved_items = [p for p in inventory if p.get("id") in st.session_state.saved_ids]
    if not saved_items:
        st.info("You haven't saved any materials yet. Open Find Scrap and select Save for Later on a listing.")
    else:
        saved_total = sum(int(p.get("price", 0) or 0) for p in saved_items)
        st.metric("Total price of saved listings (one piece each)", f"₹{saved_total:,}")
        st.caption("This is the total of saved listing prices, not a complete project estimate.")
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

import streamlit as st

CB_GREEN = "#3DBE5B"
CB_GREEN_DARK = "#1F8A3D"
CB_BLUE = "#1565C0"
CB_ORANGE = "#E8730C"

THEME_CSS = """
<style>
:root {
  --cb-green: #3DBE5B;
  --cb-green-dark: #1F8A3D;
  --cb-blue: #1565C0;
  --cb-orange: #E8730C;
  --cb-border: #E3E6EA;
  --cb-bg: #F5F7FA;
}
.stApp { background-color: var(--cb-bg); }

.cb-header {
  padding-bottom: 0.9rem; margin-bottom: 1.1rem; border-bottom: 1px solid var(--cb-border);
}
.cb-header-row { display: flex; align-items: center; justify-content: space-between; }
.cb-header-sub { font-size: 0.85rem; color: #777; margin-top: 0.3rem; }
.cb-logo { font-size: 1.55rem; font-weight: 800; color: #1a1a1a; letter-spacing: -0.02em; }
.cb-logo span { color: var(--cb-green-dark); }
.cb-badge {
  background: #fff; border: 1px solid var(--cb-border); border-radius: 999px;
  padding: 0.4rem 1rem; font-size: 0.85rem; color: #555;
  box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}
.cb-badge b { color: #1a1a1a; }

.cb-kpi-row { display: flex; gap: 1rem; margin-bottom: 1.1rem; flex-wrap: wrap; }
.cb-card {
  background: #fff; border-radius: 14px; padding: 1rem 1.3rem; flex: 1; min-width: 150px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06); border: 1px solid var(--cb-border); text-align: center;
}
.cb-card-value { font-size: 1.8rem; font-weight: 800; line-height: 1.15; }
.cb-card-label { font-size: 0.82rem; color: #666; margin-top: 0.25rem; }
.cb-card-sub { font-size: 0.78rem; color: #999; margin-top: 0.2rem; }

.cb-donut-wrap {
  display: flex; align-items: center; gap: 1.5rem; background: #fff; border-radius: 14px;
  padding: 1.2rem 1.5rem; border: 1px solid var(--cb-border); box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  margin-bottom: 1.1rem;
}
.cb-donut { width: 96px; height: 96px; border-radius: 50%; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.cb-donut-hole { width: 60px; height: 60px; border-radius: 50%; background: #fff; }
.cb-donut-info { flex: 1; }
.cb-donut-top { display: flex; justify-content: space-between; align-items: baseline; }
.cb-donut-label { color: #555; font-size: 0.9rem; }
.cb-donut-pct { font-size: 1.5rem; font-weight: 800; color: var(--cb-green-dark); }
.cb-progress-track { background: #e3e6ea; border-radius: 999px; height: 8px; margin-top: 0.6rem; overflow: hidden; }
.cb-progress-fill { background: var(--cb-green); height: 100%; border-radius: 999px; }

div[data-testid="stDownloadButton"] button {
  border-radius: 999px !important; border: 1.5px solid var(--cb-blue) !important; color: var(--cb-blue) !important;
  background: #fff !important; font-weight: 600 !important;
}
div[data-testid="stDownloadButton"] button:hover { background: #EAF2FC !important; }
button[data-baseweb="tab"] { border-radius: 999px !important; }
</style>
"""


def inject_theme():
    st.markdown(THEME_CSS, unsafe_allow_html=True)


def app_header(subtitulo: str):
    st.markdown(
        f"""
        <div class="cb-header">
          <div class="cb-header-row">
            <div class="cb-logo">🔗 <span>Pre-Match</span></div>
            <div class="cb-badge">Trabajando con <b>{subtitulo}</b></div>
          </div>
          <div class="cb-header-sub">Procesamiento y cruce de movimientos bancarios y mayor contable.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def kpi_row(items: list[dict]):
    """items: lista de {"label":..., "value":..., "color": opcional, "sub": opcional}."""
    tarjetas = "".join(
        f'<div class="cb-card"><div class="cb-card-value" style="color:{it.get("color", "#1a1a1a")}">'
        f'{it["value"]}</div><div class="cb-card-label">{it["label"]}</div>'
        + (f'<div class="cb-card-sub">{it["sub"]}</div>' if it.get("sub") else "")
        + "</div>"
        for it in items
    )
    st.markdown(f'<div class="cb-kpi-row">{tarjetas}</div>', unsafe_allow_html=True)


def donut_progress(pct: float, label: str):
    pct = max(0.0, min(100.0, pct))
    st.markdown(
        f"""
        <div class="cb-donut-wrap">
          <div class="cb-donut" style="background: conic-gradient(var(--cb-green) {pct}%, #e3e6ea {pct}% 100%);">
            <div class="cb-donut-hole"></div>
          </div>
          <div class="cb-donut-info">
            <div class="cb-donut-top">
              <div class="cb-donut-label">{label}</div>
              <div class="cb-donut-pct">{pct:.0f}%</div>
            </div>
            <div class="cb-progress-track"><div class="cb-progress-fill" style="width:{pct:.0f}%"></div></div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

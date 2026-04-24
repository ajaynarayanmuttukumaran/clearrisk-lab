from __future__ import annotations

try:
    import streamlit as st
except Exception:  # pragma: no cover - optional dependency for phase 1
    st = None


def main() -> None:
    if st is None:
        print("Streamlit is not installed. Install dev dependencies and run again.")
        return

    st.set_page_config(page_title="ClearRisk Lab — CCP Stress Testing Dashboard", layout="wide")
    st.title("ClearRisk Lab — CCP Stress Testing Dashboard")
    st.caption("Phase 1 skeleton: controls and tabs are scaffolded; full analytics arrive in later phases.")

    tab_names = [
        "Scenario Setup",
        "Margin and Procyclicality",
        "Default Waterfall",
        "Cover-2 Adequacy",
        "Liquidity and Contagion",
        "Tail-Risk Comparison",
        "Risk Memo",
    ]
    tabs = st.tabs(tab_names)
    for tab, name in zip(tabs, tab_names):
        with tab:
            st.write(f"{name} panel scaffolded in Phase 1.")


if __name__ == "__main__":
    main()


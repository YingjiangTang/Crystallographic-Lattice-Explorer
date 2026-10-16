
import streamlit as st
import pandas as pd
import spglib

# ============================================================
# 1. Page configuration
# ============================================================

st.set_page_config(
    page_title="Crystallographic Lattice Explorer",
    page_icon="💎",
    layout="wide"
)

st.title("Crystallographic Lattice Explorer")
st.caption("Explore crystallographically derived lattice structures")


# ============================================================
# 2. Space group database
# ============================================================

CRYSTAL_SYSTEMS = [
    "Triclinic",
    "Monoclinic",
    "Orthorhombic",
    "Tetragonal",
    "Trigonal",
    "Hexagonal",
    "Cubic"
]

# Space group number ranges
SYSTEM_RANGES = {
    "Triclinic": (1, 2),
    "Monoclinic": (3, 15),
    "Orthorhombic": (16, 74),
    "Tetragonal": (75, 142),
    "Trigonal": (143, 167),
    "Hexagonal": (168, 194),
    "Cubic": (195, 230)
}

# Map centering to Bravais lattice symbol
BRAVAIS_MAP = {
    "Triclinic": {"P": "aP"},
    "Monoclinic": {"P": "mP", "C": "mC", "A": "mC", "B": "mC"},
    "Orthorhombic": {
        "P": "oP", "C": "oC", "A": "oC", "B": "oC",
        "I": "oI", "F": "oF"
    },
    "Tetragonal": {"P": "tP", "I": "tI"},
    "Trigonal": {"P": "hP", "R": "hR"},
    "Hexagonal": {"P": "hP"},
    "Cubic": {"P": "cP", "I": "cI", "F": "cF"}
}


def get_crystal_system(sg_number):
    for system, (start, end) in SYSTEM_RANGES.items():
        if start <= sg_number <= end:
            return system
    return None


@st.cache_data
def build_spacegroup_database():

    records = []

    for sg_number in range(1, 231):

        # Get the conventional space-group setting
        sg_info = None

        for hall_number in range(1, 531):

            info = spglib.get_spacegroup_type(hall_number)

            if info.number == sg_number:
                sg_info = info
                break

        if sg_info is None:
            continue

        system = get_crystal_system(sg_number)

        # First letter of international short symbol
        centering = sg_info.international_short[0]

        bravais = BRAVAIS_MAP[system].get(centering)

        records.append({
            "SpaceGroup": sg_number,
            "CrystalSystem": system,
            "Bravais": bravais,
            "Symbol": sg_info.international_short
        })

    return pd.DataFrame(records)


sg_database = build_spacegroup_database()


# ============================================================
# 3. Load lattice metadata
# ============================================================

@st.cache_data
def load_metadata():

    return pd.read_csv("metadata.csv")


metadata = load_metadata()

# Required columns:
# Name, SpaceGroup, Method, Zave

metadata["SpaceGroup"] = pd.to_numeric(
    metadata["SpaceGroup"], errors="coerce"
)

metadata = metadata.merge(
    sg_database,
    on="SpaceGroup",
    how="left"
)


# ============================================================
# 4. Page layout
# ============================================================

left_panel, right_panel = st.columns(
    [35, 65],
    gap="medium"
)


# ============================================================
# 5. Left panel: three scrollable selection columns
# ============================================================

with left_panel:

    st.subheader("Crystallographic Filters")

    col1, col2, col3 = st.columns(3)

    # ----------------------------
    # Crystal system
    # ----------------------------

    with col1:

        st.markdown("**Crystal System**")

        with st.container(height=350):

            selected_system = st.radio(
                "Select Crystal System",
                ["All"] + CRYSTAL_SYSTEMS,
                label_visibility="collapsed",
                key="crystal_system"
            )

    # ----------------------------
    # Bravais lattice
    # ----------------------------

    available_sg = sg_database.copy()

    if selected_system != "All":
        available_sg = available_sg[
            available_sg["CrystalSystem"] == selected_system
        ]

    available_bravais = sorted(
        available_sg["Bravais"].dropna().unique()
    )

    with col2:

        st.markdown("**Bravais Lattice**")

        with st.container(height=350):

            selected_bravais = st.radio(
                "Select Bravais Lattice",
                ["All"] + available_bravais,
                label_visibility="collapsed",
                key="bravais",
                index=0
            )

    # ----------------------------
    # Space group
    # ----------------------------

    if selected_bravais != "All":
        available_sg = available_sg[
            available_sg["Bravais"] == selected_bravais
        ]

    available_numbers = sorted(
        available_sg["SpaceGroup"].tolist()
    )

    with col3:

        st.markdown("**Space Group**")

        with st.container(height=350):

            selected_sg = st.radio(
                "Select Space Group",
                ["All"] + available_numbers,
                label_visibility="collapsed",
                key="space_group",
                index=0
            )


# ============================================================
# 6. Right panel: matching lattice entries
# ============================================================

with right_panel:

    st.subheader("Matching Lattices")

    filtered = metadata.copy()

    if selected_system != "All":
        filtered = filtered[
            filtered["CrystalSystem"] == selected_system
        ]

    if selected_bravais != "All":
        filtered = filtered[
            filtered["Bravais"] == selected_bravais
        ]

    if selected_sg != "All":
        filtered = filtered[
            filtered["SpaceGroup"] == selected_sg
        ]

    st.write(f"**{len(filtered)} matching entries**")

    if filtered.empty:
        st.info("No matching lattices found.")

    else:
        display_columns = [
            "Name",
            "SpaceGroup",
            "Bravais",
            "Zave"
        ]

        st.dataframe(
            filtered[display_columns],
            hide_index=True,
            use_container_width=True,
            height=450
        )

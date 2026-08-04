import streamlit as st
import pandas as pd
import random
import json
from mtranslate import translate
import streamlit.components.v1 as components
from streamlit_gsheets import GSheetsConnection

# App Style Configuration
st.set_page_config(page_title="Balagam - Your Family Tree", layout="wide")

# --- 🎨 PREMIUM STYLING & PRINT OPTIMIZATION ---
st.markdown("""
    <style>
        .main-title {
            font-size: 42px !important;
            font-weight: 800;
            background: linear-gradient(45deg, #1E3A8A, #10B981, #3B82F6);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            text-align: center;
            margin-bottom: 5px;
        }
        .sub-title {
            font-size: 19px !important;
            color: #475569;
            text-align: center;
            margin-bottom: 35px;
            font-weight: 500;
        }
        [data-testid="stForm"] {
            background: linear-gradient(135deg, #F0FDF4 0%, #E6F4EA 100%) !important;
            border: 3px solid #10B981 !important;
            border-radius: 15px !important;
            padding: 30px !important;
            box-shadow: 0 10px 30px rgba(16, 185, 129, 0.15) !important;
        }
        .section-box, .spouse-box, .parents-box, .desc-box {
            background-color: #FFFFFF !important;
            border-left: 6px solid #10B981;
            padding: 22px;
            border-radius: 12px;
            margin-bottom: 25px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.04);
        }
        .spouse-box { border-left-color: #F59E0B; }
        .parents-box { border-left-color: #3B82F6; }
        .desc-box { border-left-color: #8B5CF6; background-color: #FAF5FF !important; }
        
        .box-heading { 
            font-size: 24px !important; 
            font-weight: bold; 
            color: #1E293B; 
            margin-bottom: 15px; 
        }
        label p {
            font-size: 18px !important;
            font-weight: 700 !important;
            color: #0F172A !important;
        }
        .custom-table-container { 
            margin-top: 30px; 
            background: white; 
            padding: 20px; 
            border-radius: 12px; 
            box-shadow: 0 10px 25px rgba(0,0,0,0.1); 
        }
        @media print {
            [data-testid="stSidebar"], .stButton, button, header, footer {
                display: none !important;
            }
            .main-title {
                color: #1E3A8A !important;
                -webkit-text-fill-color: initial !important;
            }
            body {
                background-color: white !important;
            }
        }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">🌳 బలగం - మీ వంశవృక్షం | Balagam - Your Family Tree</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Interactive Zoomable & Draggable Multi-Generational Family Tree</div>', unsafe_allow_html=True)

# --- 📊 GOOGLE SHEETS LIVE DATABASE CONNECTION ---
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    try:
        return conn.read(worksheet="Sheet1", ttl=0).fillna("")
    except Exception as e:
        st.error(f"Error connecting to Google Sheets DB: {e}")
        return pd.DataFrame(columns=[
            "Family ID", "Surname", "Native Village", "Name (EN)", "Name (TE)", 
            "Gender", "Spouse (EN)", "Spouse (TE)", "Parents / Relation", "Relationship Description"
        ])

df_db = load_data()

# Session State లో సెర్చ్ చేసిన కుటుంబపు కౌంట్ ని స్టోర్ చేయడానికి
if 'searched_family_members_count' not in st.session_state:
    st.session_state.searched_family_members_count = 0
if 'searched_family_id_display' not in st.session_state:
    st.session_state.searched_family_id_display = "None"

# SideBar Stats (కేవలం సెర్చ్ చేసిన కుటుంబానికే వర్తిస్తుంది)
st.sidebar.markdown("### 📊 Family Statistics")
if st.session_state.searched_family_id_display != "None":
    st.sidebar.info(f"🏡 Family ID: {st.session_state.searched_family_id_display}")
    st.sidebar.metric(label="Selected Family Members", value=int(st.session_state.searched_family_members_count))
else:
    st.sidebar.metric(label="Selected Family Members", value=0)
    st.sidebar.caption("*(సెర్చ్ చేసిన తర్వాత ఆ కుటుంబ సభ్యుల సంఖ్య ఇక్కడ కనిపిస్తుంది)*")

st.sidebar.markdown("---")

option = st.sidebar.radio("Navigation Menu", [
    "🔍 Search & View Tree", 
    "📈 Generation-wise View", 
    "➕ Add Family Members", 
    "✏️ Edit Family Members"
])

def get_emoji(gender):
    return "👨" if str(gender).strip().lower() == "male" else "👩"

def get_or_generate_family_id(surname, village):
    if not df_db.empty:
        match = df_db[(df_db['Surname'].astype(str).str.strip().str.lower() == surname.strip().lower()) & 
                     (df_db['Native Village'].astype(str).str.strip().str.lower() == village.strip().lower())]
        if not match.empty:
            return str(match.iloc[0]['Family ID'])
    
    existing_ids = df_db['Family ID'].astype(str).values if not df_db.empty else []
    while True:
        new_id = str(random.randint(100000, 999999))
        if new_id not in existing_ids:
            return new_id

def auto_translate_to_telugu(text_en):
    if not str(text_en).strip(): return ""
    try: return translate(text_en, 'te').strip()
    except Exception: return ""

# ----------------- OPTION 1: SEARCH & VIEW TREE -----------------
if option == "🔍 Search & View Tree":
    st.subheader("Family Lineage Chart / వంశవృక్షం సెర్చ్")
    col_search1, col_search2, col_search3 = st.columns(3)
    
    with col_search1: search_id = st.text_input("1. Enter Family ID:", placeholder="e.g., 203222").strip()
    with col_search2: search_surname = st.text_input("2. Enter Surname:", placeholder="e.g., Thimmapuram").strip()
    with col_search3: search_village = st.text_input("3. Enter Native Village:", placeholder="e.g., Veeravelli").strip()
        
    if st.button("Generate Interactive Tree / వంశవృక్షాన్ని చూపించు", type="primary"):
        df_db = load_data()
        result = pd.DataFrame()
        if not df_db.empty:
            if search_id: 
                result = df_db[df_db['Family ID'].astype(str).str.strip() == search_id]
            elif search_surname: 
                result = df_db[df_db['Surname'].astype(str).str.strip().str.lower() == search_surname.lower()]
            elif search_village: 
                result = df_db[df_db['Native Village'].astype(str).str.strip().str.lower() == search_village.lower()]
        
        if not result.empty:
            unique_families = result['Family ID'].unique()
            for f_id in unique_families:
                family_data = result[result['Family ID'] == f_id]
                sample_row = family_data.iloc[0]
                
                spouses_in_fam = family_data['Spouse (EN)'].apply(lambda x: 1 if str(x).strip() != "" else 0).sum()
                fam_total_count = len(family_data) + spouses_in_fam
                
                st.session_state.searched_family_members_count = fam_total_count
                st.session_state.searched_family_id_display = f_id
                
                col_info, col_print = st.columns([3, 1])
                with col_info:
                    st.info(f"🏡 **Family ID: {f_id}** | Surname: {sample_row['Surname']} | Village: {sample_row['Native Village']} | Total Members: **{fam_total_count}**")
                with col_print:
                    components.html("""
                        <button onclick="window.parent.print()" style="
                            background-color: #10B981; color: white; padding: 10px 20px;
                            border: none; border-radius: 8px; font-weight: bold;
                            font-size: 16px; cursor: pointer; width: 100%; margin-top: 5px;">
                            🖨️ Print / Save PDF
                        </button>
                    """, height=50)

                nodes = []
                edges = []
                colors = ["#EF4444", "#F59E0B", "#10B981", "#3B82F6", "#8B5CF6", "#EC4899", "#6366F1"]
                
                parent_map = {}
                for idx, row in family_data.iterrows():
                    curr_key = f"{row['Name (EN)']}"
                    if str(row['Spouse (EN)']).strip() != "":
                        curr_key = f"{row['Name (EN)']} & {row['Spouse (EN)']}"
                    parent_map[curr_key.strip()] = str(row['Parents / Relation']).strip()
                
                def calculate_level_safe(node_key):
                    level = 0
                    current = node_key.strip()
                    visited = set()
                    while current in parent_map and parent_map[current] != "None (Eldest Generation)" and parent_map[current] != "":
                        if current in visited: break
                        visited.add(current)
                        current = parent_map[current]
                        level += 1
                        if level > 20: break
                    return level

                for index, (i, row) in enumerate(family_data.iterrows()):
                    p_emoji = get_emoji(row['Gender'])
                    s_emoji = "👩" if str(row['Gender']).strip().lower() == "male" else "👨"
                    
                    t_name = str(row['Name (TE)']).strip()
                    name_en = str(row['Name (EN)']).strip()
                    te_suffix = f" ({t_name})" if t_name and t_name != name_en else ""
                    person_label = f"{p_emoji} {name_en}{te_suffix}"
                    
                    if str(row['Spouse (EN)']).strip() != "":
                        sp_t_name = str(row['Spouse (TE)']).strip()
                        spouse_en = str(row['Spouse (EN)']).strip()
                        sp_te_suffix = f" ({sp_t_name})" if sp_t_name and sp_t_name != spouse_en else ""
                        spouse_label = f"{s_emoji} {spouse_en}{sp_te_suffix}"
                        
                        couple_name = f"{person_label}\n❤️\n{spouse_label}"
                        couple_key = f"{name_en} & {spouse_en}"
                    else:
                        couple_name = person_label
                        couple_key = f"{name_en}"
                    
                    node_level = calculate_level_safe(couple_key)
                    
                    nodes.append({
                        "id": couple_key,
                        "label": couple_name,
                        "shape": "dot",
                        "size": 25, 
                        "level": node_level,
                        "color": {"background": colors[index % len(colors)], "border": "#1E3A8A"},
                        "font": {
                            "size": 20, "face": "Arial", "color": "#1E293B", 
                            "bold": True, "align": "center"
                        },
                        "borderWidth": 4
                    })
                    
                    if str(row['Parents / Relation']).strip() and str(row['Parents / Relation']).strip() != "None (Eldest Generation)":
                        edges.append({
                            "from": str(row['Parents / Relation']).strip(),
                            "to": couple_key,
                            "arrows": "to",
                            "color": {"color": "#64748B"},
                            "width": 3
                        })
                
                nodes_json = json.dumps(nodes)
                edges_json = json.dumps(edges)
                
                html_code = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <script type="text/javascript" src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
                    <style>
                        #mynetwork {{
                            width: 100%; height: 750px; border: 3px solid #1E3A8A;
                            background-color: #f8fafc; border-radius: 12px;
                        }}
                    </style>
                </head>
                <body>
                    <div id="mynetwork"></div>
                    <script type="text/javascript">
                        var container = document.getElementById('mynetwork');
                        var data = {{
                            nodes: new vis.DataSet({nodes_json}),
                            edges: new vis.DataSet({edges_json})
                        }};
                        var options = {{
                            nodes: {{ font: {{ vadjust: 40 }} }},
                            layout: {{
                                hierarchical: {{
                                    enabled: true, direction: "UD", sortMethod: "hubsize",
                                    nodeSpacing: 380, levelSpacing: 280
                                }}
                            }},
                            physics: {{ enabled: false }},
                            interaction: {{ dragNodes: true, zoomView: true, dragView: true }}
                        }};
                        var network = new vis.Network(container, data, options);
                    </script>
                </body>
                </html>
                """
                st.write("📌 *Note: మీరు మీ మౌస్ లేదా మొబైల్ స్క్రీన్‌పై డ్రాగ్ చేస్తూ జూమ్ (Zoom) మరియు స్క్రోల్ (Scroll) చేసి చూడవచ్చు.*")
                components.html(html_code, height=780)

                st.markdown("### 📜 మూలాల వివరాలు (Family Data Table)")
                st.dataframe(family_data, use_container_width=True)
                
                csv = family_data.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Download Data as CSV",
                    data=csv,
                    file_name=f"Balagam_Family_{f_id}.csv",
                    mime="text/csv"
                )
                st.markdown("---")
        else:
            st.error("❌ No records found!")

# ----------------- OPTION 2: GENERATION-WISE VIEW -----------------
elif option == "📈 Generation-wise View":
    st.subheader("📈 Generation-wise Family View / తరాల వారీగా వంశవృక్షం")
    
    col_g1, col_g2, col_g3 = st.columns(3)
    with col_g1: gen_search_id = st.text_input("1. Enter Family ID:", placeholder="e.g., 203222").strip()
    with col_g2: gen_search_surname = st.text_input("2. Enter Surname:", placeholder="e.g., Thimmapuram").strip()
    with col_g3: gen_search_village = st.text_input("3. Enter Native Village:", placeholder="e.g., Veeravelli").strip()
    
    if st.button("Show Generation-wise View / తరాల వారీగా చూపించు", type="primary"):
        df_db = load_data()
        fam_data = pd.DataFrame()
        
        if not df_db.empty:
            if gen_search_id:
                fam_data = df_db[df_db['Family ID'].astype(str).str.strip() == gen_search_id]
            elif gen_search_surname:
                fam_data = df_db[df_db['Surname'].astype(str).str.strip().str.lower() == gen_search_surname.lower()]
            elif gen_search_village:
                fam_data = df_db[df_db['Native Village'].astype(str).str.strip().str.lower() == gen_search_village.lower()]
        
        if not fam_data.empty:
            unique_f_ids = fam_data['Family ID'].unique()
            for f_id in unique_f_ids:
                sub_fam_data = fam_data[fam_data['Family ID'] == f_id]
                sample_r = sub_fam_data.iloc[0]
                
                # టోటల్ ఫ్యామిలీ మెంబర్స్ కౌంట్ (భార్యాభర్తలతో కలిపి)
                spouses_count = sub_fam_data['Spouse (EN)'].apply(lambda x: 1 if str(x).strip() != "" else 0).sum()
                total_fam_members = len(sub_fam_data) + spouses_count
                
                st.info(f"🏡 **Family ID: {f_id}** | Surname: {sample_r['Surname']} | Village: {sample_r['Native Village']} | **Total Family Members: {total_fam_members}**")
                
                parent_map = {}
                for idx, row in sub_fam_data.iterrows():
                    curr_key = f"{row['Name (EN)']}"
                    if str(row['Spouse (EN)']).strip() != "":
                        curr_key = f"{row['Name (EN)']} & {row['Spouse (EN)']}"
                    parent_map[curr_key.strip()] = str(row['Parents / Relation']).strip()
                
                def get_level(node_key):
                    level = 0
                    current = node_key.strip()
                    visited = set()
                    while current in parent_map and parent_map[current] != "None (Eldest Generation)" and parent_map[current] != "":
                        if current in visited: break
                        visited.add(current)
                        current = parent_map[current]
                        level += 1
                        if level > 20: break
                    return level

                def compute_gen_level(r):
                    name = str(r['Name (EN)']).strip()
                    spouse = str(r['Spouse (EN)']).strip()
                    key = f"{name} & {spouse}" if spouse != "" else name
                    return get_level(key)

                sub_fam_data = sub_fam_data.copy()
                sub_fam_data['Generation_Level'] = sub_fam_data.apply(compute_gen_level, axis=1)
                
                max_gen = sub_fam_data['Generation_Level'].max()
                
                for gen in range(max_gen + 1):
                    gen_members = sub_fam_data[sub_fam_data['Generation_Level'] == gen]
                    if not gen_members.empty:
                        # ఆ తరంలో ఉన్న మెంబర్స్ + వారి స్పౌజ్ కౌంట్స్ లెక్కించడం
                        gen_spouses = gen_members['Spouse (EN)'].apply(lambda x: 1 if str(x).strip() != "" else 0).sum()
                        gen_total_count = len(gen_members) + gen_spouses
                        
                        gen_title = "1st Generation (మూల పురుషులు/పెద్దలు)" if gen == 0 else f"{gen + 1}th Generation / {gen + 1}వ తరము"
                        st.markdown(f"### 🌳 {gen_title} — <span style='color: #10B981; font-size: 18px;'>Total Members: {gen_total_count}</span>", unsafe_allow_html=True)
                        
                        for _, row in gen_members.iterrows():
                            p_emoji = "👨" if str(row['Gender']).strip().lower() == "male" else "👩"
                            spouse_info = f" ❤️ (Spouse: {row['Spouse (EN)']})" if str(row['Spouse (EN)']).strip() != "" else ""
                            relation_info = f" — *{row['Relationship Description']}*" if str(row['Relationship Description']).strip() else ""
                            
                            st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;👉 **{p_emoji} {row['Name (EN)']}" + 
                                        (f" ({row['Name (TE)']})" if row['Name (TE)'] else "") + 
                                        f"{spouse_info}{relation_info}**")
                        st.markdown("---")
        else:
            st.error("❌ ఇచ్చిన వివరాలతో ఎలాంటి కుటుంబ సభ్యులు కనుగొనబడలేదు.")
    else:
        st.info("ℹ️ దయచేసి పైన Family ID, Surname లేదా Native Village లో ఏదో ఒకటి ఎంటర్ చేసి 'Show Generation-wise View' బటన్ నొక్కండి.")

# ----------------- OPTION 3: ADD FAMILY MEMBERS -----------------
elif option == "➕ Add Family Members":
    st.subheader("Expand Your Family Tree / కొత్త సభ్యులను చేర్చండి")
    
    with st.form("add_member_form", clear_on_submit=True):
        st.markdown('<div class="section-box"><div class="box-heading">🏡 1. Basic Family Details</div>', unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1: surname = st.text_input("Family Surname * :").strip()
        with col2: village = st.text_input("Native Village * :").strip()
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="parents-box"><div class="box-heading">👤 2. Member Details</div>', unsafe_allow_html=True)
        col3, col4, col5 = st.columns(3)
        with col3: name_en = st.text_input("Name in English * :").strip()
        with col4: name_te = st.text_input("Name in Telugu (Optional):").strip()
        with col5: gender = st.selectbox("Gender:", ["Male", "Female"])
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="spouse-box"><div class="box-heading">👩‍❤️‍👨 3. Spouse Details</div>', unsafe_allow_html=True)
        col_s1, col_s2 = st.columns(2)
        with col_s1: spouse_en = st.text_input("Spouse Name (English):").strip()
        with col_s2: spouse_te = st.text_input("Spouse Name (Telugu):").strip()
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="parents-box"><div class="box-heading">👨‍👩‍👦 4. Parent Selection</div>', unsafe_allow_html=True)
        existing_couples = ["None (Eldest Generation)"]
        if not df_db.empty:
            for idx, row in df_db.iterrows():
                p_text = f"{row['Name (EN)']}"
                if str(row['Spouse (EN)']).strip() != "":
                    p_text += f" & {row['Spouse (EN)']}"
                if p_text not in existing_couples: existing_couples.append(p_text)
        parent_couple = st.selectbox("Who are the Parents?:", existing_couples)
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="desc-box"><div class="box-heading">🔮 5. Extra Description</div>', unsafe_allow_html=True)
        relation_desc_en = st.text_input("Relationship Description (Optional):", placeholder="e.g., Elder Son, Freedom Fighter, etc.").strip()
        st.markdown('</div>', unsafe_allow_html=True)
        
        submit_btn = st.form_submit_button("💾 Save Member to Tree", type="primary")
        
    if submit_btn:
        if surname and village and name_en:
            assigned_f_id = get_or_generate_family_id(surname, village)
            final_name_te = name_te.strip() if name_te.strip() else auto_translate_to_telugu(name_en)
            final_spouse_te = spouse_te.strip() if spouse_te.strip() else auto_translate_to_telugu(spouse_en)
            
            new_row = pd.DataFrame([{
                "Family ID": str(assigned_f_id), 
                "Surname": surname, 
                "Native Village": village, 
                "Name (EN)": name_en, 
                "Name (TE)": final_name_te, 
                "Gender": gender,
                "Spouse (EN)": spouse_en, 
                "Spouse (TE)": final_spouse_te,
                "Parents / Relation": parent_couple, 
                "Relationship Description": relation_desc_en if relation_desc_en else "Family Member"
            }])
            
            updated_df = pd.concat([df_db, new_row], ignore_index=True)
            conn.update(worksheet="Sheet1", data=updated_df)
            st.cache_data.clear()
            st.success(f"🚀 Saved Successfully to Google Sheets! Family ID: {assigned_f_id}")
            st.rerun()
        else:
            st.error("⚠️ ఖచ్చితంగా Surname, Village మరియు Name (EN) వివరాలను నమోదు చేయండి!")

    #st.markdown('<div class="custom-table-container">', unsafe_allow_html=True)
    #st.dataframe(df_db, use_container_width=True, height=320)
    #st.markdown('</div>', unsafe_allow_html=True)

# ----------------- OPTION 4: EDIT FAMILY MEMBERS -----------------
elif option == "✏️ Edit Family Members":
    st.subheader("✏️ Edit Family Member Details")
    
    col_e1, col_e2, col_e3 = st.columns(3)
    with col_e1: edit_search_id = st.text_input("Search by Family ID:", placeholder="e.g., 203222").strip()
    with col_e2: edit_search_surname = st.text_input("Search by Surname:", placeholder="e.g., Thimmapuram").strip()
    with col_e3: edit_search_village = st.text_input("Search by Village:", placeholder="e.g., Veeravelli").strip()
    
    filtered_edit_df = pd.DataFrame()
    if not df_db.empty:
        filtered_edit_df = df_db.copy()
        if edit_search_id:
            filtered_edit_df = filtered_edit_df[filtered_edit_df["Family ID"].astype(str).str.strip() == edit_search_id]
        if edit_search_surname:
            filtered_edit_df = filtered_edit_df[filtered_edit_df["Surname"].astype(str).str.strip().str.lower() == edit_search_surname.lower()]
        if edit_search_village:
            filtered_edit_df = filtered_edit_df[filtered_edit_df["Native Village"].astype(str).str.strip().str.lower() == edit_search_village.lower()]

    if not filtered_edit_df.empty:
        member_options = []
        for idx, row in filtered_edit_df.iterrows():
            member_options.append(f"{row['Name (EN)']} (ID: {row['Family ID']} - Village: {row['Native Village']})")
            
        selected_member_str = st.selectbox("Select Member to Edit:", member_options)
        
        if selected_member_str:
            selected_row_idx = filtered_edit_df.iloc[member_options.index(selected_member_str)].name
            member_to_edit = df_db.loc[selected_row_idx]
            
            with st.form("edit_member_form"):
                u_surname = st.text_input("Surname:", value=str(member_to_edit["Surname"]))
                u_village = st.text_input("Native Village:", value=str(member_to_edit["Native Village"]))
                u_name_en = st.text_input("Name in English:", value=str(member_to_edit["Name (EN)"]))
                u_name_te = st.text_input("Name in Telugu:", value=str(member_to_edit["Name (TE)"]))
                u_spouse_en = st.text_input("Spouse Name (English):", value=str(member_to_edit["Spouse (EN)"]))
                u_spouse_te = st.text_input("Spouse Name (Telugu):", value=str(member_to_edit["Spouse (TE)"]))
                
                edit_couples = ["None (Eldest Generation)"]
                for idx, row in df_db.iterrows():
                    if row['Name (EN)'] != member_to_edit['Name (EN)']:
                        p_text = f"{row['Name (EN)']}"
                        if str(row['Spouse (EN)']).strip() != "":
                            p_text += f" & {row['Spouse (EN)']}"
                        if p_text not in edit_couples: edit_couples.append(p_text)
                
                curr_parent = str(member_to_edit["Parents / Relation"]).strip()
                current_parent_index = edit_couples.index(curr_parent) if curr_parent in edit_couples else 0
                u_parents = st.selectbox("Who are the Parents?:", edit_couples, index=current_parent_index)
                u_relation = st.text_input("Relationship Description:", value=str(member_to_edit["Relationship Description"]))
                
                update_btn = st.form_submit_button("🔄 Update Member Details", type="primary")
                
            if update_btn:
                df_db.loc[selected_row_idx, "Surname"] = u_surname
                df_db.loc[selected_row_idx, "Native Village"] = u_village
                df_db.loc[selected_row_idx, "Name (EN)"] = u_name_en
                df_db.loc[selected_row_idx, "Name (TE)"] = u_name_te
                df_db.loc[selected_row_idx, "Spouse (EN)"] = u_spouse_en
                df_db.loc[selected_row_idx, "Spouse (TE)"] = u_spouse_te
                df_db.loc[selected_row_idx, "Parents / Relation"] = u_parents
                df_db.loc[selected_row_idx, "Relationship Description"] = u_relation
                
                conn.update(worksheet="Sheet1", data=df_db)
                st.cache_data.clear()
                st.success("🔄 Member updated in Google Sheets successfully!")
                st.rerun()
                
            if st.button("🗑️ Delete This Member", type="secondary"):
                df_db = df_db.drop(selected_row_idx).reset_index(drop=True)
                conn.update(worksheet="Sheet1", data=df_db)
                st.cache_data.clear()
                st.success("❌ Removed from Google Sheets successfully!")
                st.rerun()
    else:
        if edit_search_id or edit_search_surname or edit_search_village:
            st.warning("⚠️ ఇచ్చిన వివరాలతో ఎలాంటి సభ్యులు కనుగొనబడలేదు.")
        else:
            st.info("ℹ️ దయచేసి పైన Family ID, Surname లేదా Native Village లో ఏదో ఒకటి ఎంటర్ చేసి మెంబర్‌ని వెతకండి.")

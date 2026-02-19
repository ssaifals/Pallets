# app.py - Pallet Ledger 
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time
import os
import tempfile
from sqlalchemy import text


from auth import authenticate_user, create_initial_admin
from database import SessionLocal, init_db
from services.ledger_service import LedgerService
from models import LocationType, MovementType, MovementStatus, User

st.set_page_config(page_title="Pallet Ledger Pro", page_icon="🛡️", layout="wide")


if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'user_role' not in st.session_state:
    st.session_state['user_role'] = None


init_db()
db = SessionLocal()
create_initial_admin(db) 

# ==========================================
# 🔐 LOGIN SCREEN LOGIC
# ==========================================
if not st.session_state['logged_in']:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
            <div style='text-align: center; margin-top: 50px; margin-bottom: 30px;'>
                <div style='background: #1a5632; width: 80px; height: 80px; margin: 0 auto; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 40px;'>🛡️</div>
                <h1 style='color: #1a5632;'>Pallet Ledger Pro</h1>
                <p>Secure Logistics Command Center</p>
            </div>
        """, unsafe_allow_html=True)
        
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("🔒 Secure Login", type="primary", use_container_width=True)
            
            if submit:
                user = authenticate_user(db, username, password)
                if user:
                    st.session_state['logged_in'] = True
                    st.session_state['user_role'] = user.role
                    st.session_state['username'] = user.username
                    st.success("Access Granted")
                    st.rerun()
                else:
                    st.error("❌ Invalid credentials")
    
   
    st.stop()


st.markdown("""
<style>
    :root {
        --primary: #1a5632;
        --secondary: #1a73e8;
        --accent: #ff6b35;
        --dark: #0a1931;
        --light: #f8f9fa;
        --success: #2e7d32;
        --warning: #ff9800;
        --danger: #d32f2f;
    }
    
    .main-header {
        padding: 1.5rem;
        background: linear-gradient(135deg, var(--dark) 0%, #1a5632 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        border-left: 4px solid var(--primary);
        transition: transform 0.3s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.12);
    }
    
    .status-active {
        background: #e8f5e9; color: #2e7d32; padding: 0.25rem 0.75rem; 
        border-radius: 20px; font-weight: 600; font-size: 0.85rem;
    }
    
    .stDataFrame { border: 1px solid #e0e0e0; border-radius: 8px; }
    
    .alert-banner {
        padding: 1rem; background: #fff3e0; 
        border-left: 4px solid var(--warning); 
        border-radius: 4px; margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)




def get_service():
    """Initializes the DB connection and Service Layer for this specific run."""
    db = SessionLocal()
    return LedgerService(db)


service = get_service()


with st.sidebar:
    st.markdown("""
        <div style='
            text-align: center; 
            padding: 1.5rem 1rem;
            background: linear-gradient(135deg, #1a5632 0%, #2c8c5a 100%);
            border-radius: 12px;
            margin-bottom: 1.5rem;
            box-shadow: 0 4px 12px rgba(26, 86, 50, 0.15);
        '>
            <div style='
                background: white;
                width: 60px;
                height: 60px;
                margin: 0 auto 1rem;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 28px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            '>
                🛡️
            </div>
            <h2 style='
                color: white;
                margin: 0;
                font-weight: 600;
                font-size: 1.4rem;
            '>Pallet Ledger Pro</h2>
            <p style='
                color: rgba(255,255,255,0.9);
                margin: 0.25rem 0 0;
                font-size: 0.85rem;
                font-weight: 300;
            '>Secure Asset Management Platform</p>
        </div>
    """, unsafe_allow_html=True)
    
    
    st.markdown("### 📍 Navigation")
    
    menu_options = {
        "📊 Dashboard": "System overview and key metrics",
        "📍 Locations": "Manage warehouse locations",
        "✈️ Movements": "Track pallet transfers",
        "📦 Inventory": "Current stock levels",
        "📈 Analytics": "Reports & insights",
        "⚙️ Settings": "System configuration"
    }
    
    menu = st.radio(
        "Select a section",
        options=list(menu_options.keys()),
        format_func=lambda x: f"{x.split(' ')[0]} {x.split(' ')[1]}",
        label_visibility="collapsed"
    )
    
    
    st.markdown(f"""
        <div style='
            background: #f8f9fa;
            padding: 0.75rem;
            border-radius: 8px;
            border-left: 4px solid #1a5632;
            margin: 0.5rem 0 1.5rem;
            font-size: 0.85rem;
            color: #495057;
        '>
            {menu_options[menu]}
        </div>
    """, unsafe_allow_html=True)
    
    st.divider()
    
    
    st.markdown("### ⚡ Quick Actions")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📥 **Export**", use_container_width=True, help="Download system data"):
            @st.dialog("📦 Data Export Center", width="large")
            def export_dialog():
                st.markdown("#### Select Data Package")
                st.write("Choose the data you wish to export from the system.")
                
                
                locs_data = service.get_locations()
                moves_data = service.get_movements(limit=10000)
                
               
                locs_df = pd.DataFrame(locs_data) if locs_data else pd.DataFrame()
                moves_df = pd.DataFrame(moves_data) if moves_data else pd.DataFrame()
                
                
                if not locs_df.empty:
                    locs_df = locs_df[locs_df['code'] != 'SYSTEM']

                tab1, tab2, tab3 = st.tabs(["📊 Full Backup", "📍 Locations", "✈️ Movements"])
                
                with tab1:
                    st.markdown("##### Complete System Backup")
                    if not locs_df.empty or not moves_df.empty:
                        
                        full_df = pd.concat([locs_df, moves_df], axis=0, sort=False)
                        st.dataframe(full_df.head(), use_container_width=True)
                        
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
                        st.download_button(
                            "⬇️ Download Full Backup (.csv)",
                            full_df.to_csv(index=False),
                            f"MPL_Full_Backup_{timestamp}.csv",
                            "text/csv",
                            use_container_width=True,
                            type="primary"
                        )
                    else:
                        st.info("System data is currently empty.")
                
                with tab2:
                    if not locs_df.empty:
                        st.dataframe(locs_df.head(), use_container_width=True)
                        st.download_button(
                            "⬇️ Download Locations (.csv)",
                            locs_df.to_csv(index=False),
                            f"MPL_Locations_{datetime.now().date()}.csv",
                            "text/csv",
                            use_container_width=True
                        )
                    else:
                        st.warning("No locations found.")
                
                with tab3:
                    if not moves_df.empty:
                        st.dataframe(moves_df.head(), use_container_width=True)
                        st.download_button(
                            "⬇️ Download Movements (.csv)",
                            moves_df.to_csv(index=False),
                            f"MPL_Movements_{datetime.now().date()}.csv",
                            "text/csv",
                            use_container_width=True
                        )
                    else:
                        st.warning("No movements found.")
            
            export_dialog()
    
    with col2:
        if st.button("🔄 **Refresh**", use_container_width=True, help="Reload all data"):
            st.rerun()
    
    st.divider()
    
   
    st.markdown("### 📊 System Status")
    
    col_status, col_version = st.columns([2, 1])
    with col_status:
        st.markdown("""
            <div style='display: flex; align-items: center; gap: 0.5rem;'>
                <div style='width: 10px; height: 10px; background: #28a745; border-radius: 50%; animation: pulse 2s infinite;'></div>
                <span>Operational</span>
            </div>
            <style>
                @keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.5; } 100% { opacity: 1; } }
            </style>
        """, unsafe_allow_html=True)
    
    with col_version:
        st.caption("v2.1.4")
    
    
    with st.expander("📈 System Metrics", expanded=False):
        metric_locs = service.get_locations()
        metric_moves = service.get_movements(limit=500)
        
      
        active_count = 0
        if metric_locs:
            df_l = pd.DataFrame(metric_locs)
            active_count = len(df_l[(df_l['status'].astype(str).str.lower() == 'active') & (df_l['code'] != 'SYSTEM')])


        today_moves = 0
        move_delta = 0
        if metric_moves:
            df_m = pd.DataFrame(metric_moves)
            df_m['date'] = pd.to_datetime(df_m['timestamp']).dt.date
            today = datetime.now().date()
            yesterday = today - timedelta(days=1)
            
            today_moves = len(df_m[df_m['date'] == today])
            yest_moves = len(df_m[df_m['date'] == yesterday])
            move_delta = today_moves - yest_moves
            

            delta_symbol = "+" if move_delta >= 0 else ""
            delta_str = f"{delta_symbol}{move_delta} vs yest"
        else:
            delta_str = "0 vs yest"


        st.metric("Active Locations", active_count, help="Physical bases/depots")
        st.metric("Today's Movements", today_moves, delta_str)
        st.metric("System Uptime", "99.9%", "Stable")
    
    st.divider()
    

    st.markdown(f"""
        <div style='text-align: center; color: #6c757d; font-size: 0.75rem; padding: 1rem 0;'>
            © 2026 Pallet Ledger Pro<br>
            Last check: {datetime.now().strftime('%H:%M')}
        </div>
    """, unsafe_allow_html=True)
# ==========================================
# PAGE: DASHBOARD
# ==========================================

if menu == "📊 Dashboard":
    st.markdown("""
        <div class='main-header'>
            <h1 style='margin: 0;'>📊 Logistics Command Dashboard</h1>
            <p style='margin: 0.5rem 0 0 0; opacity: 0.9;'>Real-time asset tracking and management</p>
        </div>
    """, unsafe_allow_html=True)
    
    
    locs = service.get_locations()
    moves = service.get_movements(limit=500)
    summary = service.get_dashboard_summary()
    
    
    df_locs = pd.DataFrame(locs) if locs else pd.DataFrame()
    df_moves = pd.DataFrame(moves) if moves else pd.DataFrame()
    
    
    if not df_locs.empty:
        real_locs = df_locs[df_locs['code'] != 'SYSTEM']
        total_pallets = real_locs['current_stock'].sum()
    else:
        total_pallets = 0
    
    
    in_transit_count = 0
    if not df_moves.empty:
        
        mask_transit = df_moves['status'].astype(str).str.lower().isin(['in_transit', 'in transit', 'pending', 'in_progress'])
        in_transit_count = df_moves[mask_transit]['quantity'].sum()

    deployed_count = 0
    if not df_locs.empty:
        
        mask_deployed = (
            (df_locs['code'] != 'SYSTEM') & 
            (df_locs['location_type'].astype(str).str.lower().str.contains('forward'))
        )
        deployed_count = df_locs[mask_deployed]['current_stock'].sum()
        
    
    discrepancy_count = summary.get('discrepancies', 0)
    # ---------------------------------------------------------

   
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
            <div class='metric-card'>
                <div style='font-size: 0.9rem; color: #666; margin-bottom: 0.5rem;'>TOTAL PALLETS</div>
                <div style='font-size: 2rem; font-weight: 700; color: #1a5632;'>{total_pallets:,}</div>
                <div style='font-size: 0.8rem; color: #666; margin-top: 0.5rem;'>System Wide</div>
            </div>""", unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
            <div class='metric-card'>
                <div style='font-size: 0.9rem; color: #666; margin-bottom: 0.5rem;'>IN TRANSIT</div>
                <div style='font-size: 2rem; font-weight: 700; color: #1a73e8;'>{in_transit_count}</div>
                <div style='font-size: 0.8rem; color: #666; margin-top: 0.5rem;'>Active Movements</div>
            </div>""", unsafe_allow_html=True)
            
    with col3:
        st.markdown(f"""
            <div class='metric-card'>
                <div style='font-size: 0.9rem; color: #666; margin-bottom: 0.5rem;'>DEPLOYED</div>
                <div style='font-size: 2rem; font-weight: 700; color: #ff6b35;'>{deployed_count}</div>
                <div style='font-size: 0.8rem; color: #666; margin-top: 0.5rem;'>Forward Bases</div>
            </div>""", unsafe_allow_html=True)
            
    with col4:
        st.markdown(f"""
            <div class='metric-card'>
                <div style='font-size: 0.9rem; color: #666; margin-bottom: 0.5rem;'>DISCREPANCIES</div>
                <div style='font-size: 2rem; font-weight: 700; color: #d32f2f;'>{discrepancy_count}</div>
                <div style='font-size: 0.8rem; color: #666; margin-top: 0.5rem;'>Requires Action</div>
            </div>""", unsafe_allow_html=True)

    st.divider()
    
    
    c_chart1, c_chart2 = st.columns(2)
    
    if not df_locs.empty:
        with c_chart1:
            st.markdown("##### 📍 Top Stock Locations")
            
           
            chart_data = df_locs[df_locs['code'] != 'SYSTEM']
           
            top_stock = chart_data.sort_values('current_stock', ascending=False).head(10)
            
            fig = px.bar(top_stock, 
                         x='code', 
                         y='current_stock', 
                         color='location_type',
                         color_discrete_sequence=px.colors.qualitative.Set2)
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
            
    if not df_moves.empty:
        with c_chart2:
            st.markdown("##### 📈 Recent Activity Timeline")
            
            df_moves['date'] = pd.to_datetime(df_moves['timestamp']).dt.date
            daily = df_moves.groupby('date').size().reset_index(name='count')
            fig2 = px.line(daily, x='date', y='count', markers=True, line_shape="spline", title="Daily Movement Volume")
            fig2.update_layout(height=400)
            st.plotly_chart(fig2, use_container_width=True)

    # ---------------------------------------------------------
    # 4. RECENT LEDGER ENTRIES (Enhanced Card UI)
    # ---------------------------------------------------------
    st.divider()
    st.markdown("##### 📋 Recent Ledger Entries")
    
    if not df_moves.empty:
        
        df_recent = df_moves.sort_values('timestamp', ascending=False).head(5)
        
        
        st.markdown("""
        <style>
            .activity-card {
                background-color: #1e1e1e; /* Dark mode card bg */
                border: 1px solid #333;
                border-radius: 10px;
                padding: 15px;
                margin-bottom: 10px;
                display: flex;
                align-items: center;
                justify-content: space-between;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
            }
            .mission-group { display: flex; flex-direction: column; }
            .mission-id { font-size: 1.1em; font-weight: 700; color: #ffffff; }
            .meta-text { font-size: 0.85em; color: #888; margin-top: 4px; }
            
            .flow-group { display: flex; align-items: center; gap: 15px; }
            .loc-box { text-align: center; min-width: 80px; }
            .loc-code { font-weight: 600; color: #e0e0e0; font-size: 0.95em; }
            .loc-label { font-size: 0.7em; color: #666; text-transform: uppercase; }
            .arrow { color: #555; font-size: 1.2em; }
            
            .status-group { text-align: right; }
            .qty-pill { 
                background: #1a5632; 
                color: #fff; 
                padding: 4px 12px; 
                border-radius: 15px; 
                font-weight: bold; 
                font-size: 0.9em;
                display: inline-block;
                margin-bottom: 4px;
            }
            .status-text { font-size: 0.8em; font-weight: 600; text-transform: uppercase; }
            .st-completed { color: #4caf50; }
            .st-pending { color: #ff9800; }
        </style>
        """, unsafe_allow_html=True)

        
        for _, m in df_recent.iterrows():
        
            m_time = pd.to_datetime(m['timestamp'])
            diff = datetime.now() - m_time
            seconds = diff.total_seconds()
            
            if seconds < 60: time_str = "Just now"
            elif seconds < 3600: time_str = f"{int(seconds/60)}m ago"
            elif seconds < 86400: time_str = f"{int(seconds/3600)}h ago"
            else: time_str = f"{int(seconds/86400)}d ago"
            
           
            status_raw = str(m.get('status', 'Completed')).lower()
            status_cls = "st-completed" if "complete" in status_raw else "st-pending"
            status_display = m.get('status', 'Completed').upper()
            user = m.get('confirmed_by', 'System')
            
            
            html_card = f"""
<div class="activity-card">
    <div class="mission-group">
        <span class="mission-id">{m['mission_id']}</span>
        <span class="meta-text">🕒 {time_str} &nbsp;•&nbsp; 👤 {user}</span>
    </div>
    <div class="flow-group">
        <div class="loc-box">
            <div class="loc-code">{m['from_location_code']}</div>
            <div class="loc-label">Origin</div>
        </div>
        <div class="arrow">➜</div>
        <div class="loc-box">
            <div class="loc-code">{m['to_location_code']}</div>
            <div class="loc-label">Dest</div>
        </div>
    </div>
    <div class="status-group">
        <div class="qty-pill">{m['quantity']}</div><br>
        <span class="status-text {status_cls}">{status_display}</span>
    </div>
</div>
"""
            st.markdown(html_card, unsafe_allow_html=True)
            
    else:
        st.info("No recent movements found.")
# ==========================================
# PAGE: LOCATIONS
# ==========================================
elif menu == "📍 Locations":
    st.markdown("""
        <div class='main-header'>
            <h1 style='margin: 0;'>📍 Location Management</h1>
            <p style='margin: 0.5rem 0 0 0; opacity: 0.9;'>Manage bases, forward operating bases, and depots</p>
        </div>
    """, unsafe_allow_html=True)
    
    tabs = st.tabs(["📍 View All", "➕ Create New", "✏️ Edit", "🗑️ Delete", "🗺️ Map View"])
    
    
    # TAB 1: VIEW ALL
    with tabs[0]:
        locs = service.get_locations()
        if locs:
            df = pd.DataFrame(locs)
            
            
            df = df[df['code'] != 'SYSTEM'] 
            # -----------------------------------------------

            df['utilization'] = df.apply(lambda x: (x['current_stock'] / x['max_capacity'] * 100) if x['max_capacity'] > 0 else 0, axis=1).round(1)
            
            st.dataframe(
                df[['code', 'name', 'location_type', 'current_stock', 'max_capacity', 'utilization', 'status', 'contact_person']],
                column_config={
                    "utilization": st.column_config.ProgressColumn("Fill %", max_value=100),
                    "status": st.column_config.TextColumn("Status"),
                    "contact_person": "POC"
                },
                use_container_width=True
            )
        else:
            st.info("No locations found.")
    
    # TAB 2: CREATE NEW
    with tabs[1]:
        with st.form("new_loc", clear_on_submit=True):
            st.markdown("### Add New Location")
            c1, c2 = st.columns(2)
            code = c1.text_input("Code (e.g. DXB-HQ)*").upper()
            name = c2.text_input("Name*")
            
            c3, c4 = st.columns(2)
            ltype = c3.selectbox("Type", [t.value for t in LocationType])
            status = c4.selectbox("Status", ["active", "inactive", "maintenance"])
            
            c5, c6 = st.columns(2)
            capacity = c5.number_input("Max Capacity", value=1000, step=100)
            contact = c6.text_input("Contact Person")
            
            c7, c8 = st.columns(2)
            phone = c7.text_input("Contact Phone")
            coords = c8.text_input("Coordinates (Lat, Lon)", placeholder="25.2532, 55.3657")
            
            if st.form_submit_button("🚀 Create Location"):
                try:
                    
                    success, msg = service.create_location(
                        code=code, 
                        name=name, 
                        location_type=ltype, 
                        status=status,          
                        max_capacity=capacity,  
                        contact_person=contact, 
                        contact_phone=phone, 
                        coordinates=coords
                    )
                    
                    if success:
                        st.success(f"✅ {msg}")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(msg)
                except Exception as e:
                    st.error(f"System Error: {str(e)}")
    # TAB 3: EDIT
    with tabs[2]:
        st.markdown("### ✏️ Update Site Details")
        
        locs = service.get_locations()
        if locs:
            
            codes = [l['code'] for l in locs if l['code'] != 'SYSTEM']
            # -------------------------------------------
            
            sel_code = st.selectbox("Select Location to Edit", codes)
            
            if sel_code:
                
                curr = next((l for l in locs if l['code'] == sel_code), None)
                
                if curr:
                    with st.form("edit_loc"):
                        st.markdown(f"Editing **{curr['name']}**")
                        c1, c2 = st.columns(2)
                        new_name = c1.text_input("Name", value=curr['name'])
                        new_contact = c2.text_input("Contact Person", value=curr['contact_person'] or "")
                        
                        c3, c4 = st.columns(2)
                        new_coords = c3.text_input("Coordinates", value=curr['coordinates'] or "", help="Format: 25.123, 55.456")
                        
                        
                        status_opts = ["active", "inactive"]
                        curr_status = curr.get('status', 'active')
                        idx = 0 if curr_status == 'active' else 1
                        new_status = c4.selectbox("Status", status_opts, index=idx)
                        
                        if st.form_submit_button("💾 Save Changes"):
                            service.update_location(sel_code, {
                                "name": new_name, 
                                "contact_person": new_contact, 
                                "coordinates": new_coords, 
                                "operational_status": new_status
                            })
                            st.success("Updated Successfully!")
                            time.sleep(1)
                            st.rerun()
        else:
            st.info("No locations found to edit.")

    # TAB 4: DELETE
    with tabs[3]:
        st.markdown("### 🗑️ Decommission Location")
        
        
        locs = service.get_locations()
        
        if locs:
            
            codes = [l['code'] for l in locs]
            
            
            safe_codes = [c for c in codes if c != 'SYSTEM']
            # ---------------------------------------------
            
            del_code = st.selectbox("Select Location to Delete", safe_codes, key="del_sel")
            
            if del_code:
                st.error(f"⚠️ Warning: Deleting **{del_code}** is permanent and removes all inventory records for this site.")
                
                col1, col2 = st.columns(2)
                confirm = col1.checkbox("I understand the consequences")
                
                if col2.button("🗑️ Confirm Delete", disabled=not confirm):
                    success, msg = service.delete_location(del_code)
                    if success:
                        st.success(msg)
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(msg)
        else:
            st.info("No deletable locations available.")
    # TAB 5: MAP VIEW
    with tabs[4]:
        st.markdown("### 🗺️ Global Asset Map")
        
        locs = service.get_locations()
        if locs:
            df_map = pd.DataFrame(locs)
            
           
            df_map = df_map[df_map['code'] != 'SYSTEM']
            # -------------------------------------
            
            
            if 'coordinates' in df_map.columns:
                
                def parse_coords(coord_str):
                    try:
                        if not coord_str: return None, None
                        
                        clean = str(coord_str).upper().replace('°', '').replace('N', '').replace('E', '')
                        
                        parts = clean.split(',')
                        if len(parts) == 2:
                            lat = float(parts[0].strip())
                            lon = float(parts[1].strip())
                            
                            if 'S' in str(coord_str).upper(): lat = -lat
                            if 'W' in str(coord_str).upper(): lon = -lon
                            return lat, lon
                        return None, None
                    except:
                        return None, None

                
                coords = df_map['coordinates'].apply(parse_coords)
                df_map['lat'] = [c[0] for c in coords]
                df_map['lon'] = [c[1] for c in coords]
                
                
                map_data = df_map.dropna(subset=['lat', 'lon'])
                
                if not map_data.empty:
                    
                    fig = px.scatter_mapbox(
                        map_data,
                        lat="lat",
                        lon="lon",
                        hover_name="code",
                        hover_data={
                            "name": True,
                            "current_stock": True,
                            "max_capacity": True,
                            "lat": False, "lon": False
                        },
                        color="location_type",
                        size="max_capacity", 
                        color_discrete_sequence=px.colors.qualitative.Bold,
                        zoom=6,
                        height=600,
                        title="Operational Site Locations"
                    )
                    
                    
                    fig.update_layout(
                        mapbox_style="open-street-map", 
                        margin={"r":0,"t":40,"l":0,"b":0}
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    
                    missing = df_map[df_map['lat'].isna()]
                    if not missing.empty:
                        with st.expander(f"⚠️ {len(missing)} Locations missing coordinates"):
                            st.dataframe(missing[['code', 'name']], hide_index=True)
                else:
                    st.warning("⚠️ No locations have valid coordinates. Edit a location and add 'lat, lon' (e.g., 25.25, 55.36).")
            else:
                st.error("Coordinates column missing from database.")
        else:
            st.info("No locations found.")
# ==========================================
# PAGE: MOVEMENTS
# ==========================================
elif menu == "✈️ Movements":
    st.markdown("""
        <div class='main-header'>
            <h1 style='margin: 0;'>✈️ Movement Ledger</h1>
            <p style='margin: 0.5rem 0 0 0; opacity: 0.9;'>Track and manage all asset transfers</p>
        </div>
    """, unsafe_allow_html=True)
    
   
    tabs = st.tabs(["📋 Ledger History", "➕ Record Movement", "📊 Movement Analytics", "🔄 Bulk Operations"])
    
    # READ
    with tabs[0]:
        st.markdown("### Movement History")
        
        
        filter_col1, filter_col2, filter_col3, filter_col4 = st.columns(4)
        with filter_col1:
            filter_mission = st.text_input("Mission ID", key="movement_filter_mission")
        with filter_col2:
            filter_status = st.selectbox("Status", ["All", "Completed", "Pending", "Cancelled"], key="movement_filter_status")
        with filter_col3:
            filter_start_date = st.date_input("From Date", key="movement_filter_start")
        with filter_col4:
            filter_end_date = st.date_input("To Date", key="movement_filter_end")
        
        filters = {}
        if filter_mission:
            filters['mission_id'] = filter_mission
        if filter_status != "All":
            filters['status'] = filter_status
        if filter_start_date:
            filters['start_date'] = filter_start_date
        if filter_end_date:
            filters['end_date'] = filter_end_date
        
        movements = service.get_movements(filters=filters)
        
        if movements:
            df = pd.DataFrame(movements)
            
            
            sum_col1, sum_col2, sum_col3 = st.columns(3)
            with sum_col1:
                total_qty = df['quantity'].sum()
                st.metric("Total Pallets Moved", f"{total_qty:,}")
            with sum_col2:
                unique_missions = df['mission_id'].nunique()
                st.metric("Unique Missions", unique_missions)
            with sum_col3:
                avg_move = df['quantity'].mean()
                st.metric("Avg Move Size", f"{avg_move:.0f}")
            
            
            df_display = df.copy()
            df_display['timestamp'] = pd.to_datetime(df_display['timestamp']).dt.strftime('%Y-%m-%d %H:%M')
            
            
            cols_to_display = ['timestamp', 'mission_id', 'from_code', 'to_code', 'quantity']
            if 'movement_type' in df.columns: cols_to_display.append('movement_type')
            if 'status' in df.columns: cols_to_display.append('status')
            if 'priority' in df.columns: cols_to_display.append('priority')

            st.dataframe(
                df_display[cols_to_display],
                use_container_width=True,
                hide_index=True
            )
            
            
            csv = df_display.to_csv(index=False)
            st.download_button(
                label="📥 Export to CSV",
                data=csv,
                file_name=f"movements_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
        else:
            st.info("No movements found with current filters.")
    
    # CREATE
    with tabs[1]:
        st.markdown("### Record New Movement")
        
        locs = service.get_locations()
        location_options = [l['code'] for l in locs]
        
        with st.form("new_movement", clear_on_submit=True):
            col1, col2 = st.columns(2)
            mission_id = col1.text_input("Mission/Flight ID*", placeholder="e.g., FLT-2024-001")
            movement_date = col2.date_input("Movement Date*", value=datetime.now())
            
            col3, col4, col5 = st.columns(3)
            from_loc = col3.selectbox("From Location*", location_options, key="movement_from")
            to_loc = col4.selectbox("To Location*", location_options, key="movement_to")
            quantity = col5.number_input("Quantity*", min_value=1, value=10, step=5)
            
            col6, col7 = st.columns(2)
            movement_type = col6.selectbox("Movement Type", ["Transfer", "Deployment", "Return", "Replenishment", "Audit"])
            priority = col7.selectbox("Priority", ["Normal", "High", "Urgent", "Critical"])
            
            confirmed_by = st.text_input("Confirmed By", placeholder="Name of confirming officer")
            notes = st.text_area("Notes", placeholder="Additional details, special instructions...")
            
            
            if from_loc == to_loc:
                st.error("❌ Origin and destination cannot be the same location.")
            
            submitted = st.form_submit_button("🚀 Submit Movement", type="primary", use_container_width=True)
            
            if submitted and from_loc != to_loc:
                if not mission_id:
                    st.error("Mission ID is required")
                else:
                    success, msg = service.create_movement({
                        "mission": mission_id,
                        "from": from_loc,
                        "to": to_loc,
                        "qty": quantity,
                        "type": movement_type,
                        "priority": priority,
                        "status": "Completed",
                        "notes": notes,
                        "confirmed": confirmed_by
                    })
                    if success:
                        st.success(f"✅ {msg}")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(f"❌ {msg}")
    # 📊 MOVEMENT ANALYTICS
    with tabs[2]:
        st.markdown("### 📊 Operational Movement Analysis")
        
        
        movements = service.get_movements()
        
        if movements:
            df = pd.DataFrame(movements)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df['date'] = df['timestamp'].dt.date
            
            
            kpi1, kpi2, kpi3, kpi4 = st.columns(4)
            
            with kpi1:
                total_qty = df['quantity'].sum()
                st.metric("📦 Total Pallets Moved", f"{total_qty:,}")
                
            with kpi2:
                
                daily_vol = df.groupby('date')['quantity'].sum()
                peak_day = daily_vol.idxmax() if not daily_vol.empty else "N/A"
                peak_qty = daily_vol.max() if not daily_vol.empty else 0
                st.metric("📈 Peak Daily Volume", f"{peak_qty} pallets", f"{peak_day}")

            with kpi3:
                
                deps = len(df[df['movement_type'] == 'Deployment'])
                rets = len(df[df['movement_type'] == 'Return'])
                ratio = f"{deps}:{rets}" if rets > 0 else f"{deps}:0"
                st.metric("🔄 Deploy/Return Ratio", ratio)
                
            with kpi4:
                
                avg_size = df['quantity'].mean()
                st.metric("⚖️ Avg Mission Size", f"{avg_size:.1f} pallets")

            st.divider()

            
            c1, c2 = st.columns(2)
            
            
            with c1:
                st.markdown("#### 📅 Movement Volume Trends")
                daily_trend = df.groupby('date')[['quantity']].sum().reset_index()
                fig_trend = px.area(
                    daily_trend, 
                    x='date', 
                    y='quantity',
                    labels={'quantity': 'Pallets Moved', 'date': 'Date'},
                    color_discrete_sequence=['#1a5632'] 
                )
                fig_trend.update_layout(height=350, showlegend=False)
                st.plotly_chart(fig_trend, use_container_width=True)

            
            with c2:
                st.markdown("#### 🛣️ Busiest Supply Routes")
                
                df['route'] = df['from_code'] + " ➝ " + df['to_code']
                route_counts = df['route'].value_counts().head(7).reset_index()
                route_counts.columns = ['route', 'count']
                
                fig_routes = px.bar(
                    route_counts, 
                    x='count', 
                    y='route',
                    orientation='h',
                    labels={'count': 'Number of Missions', 'route': 'Route'},
                    color='count',
                    color_continuous_scale='Greens'
                )
                fig_routes.update_layout(height=350, yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig_routes, use_container_width=True)

            
            c3, c4 = st.columns(2)

            
            with c3:
                st.markdown("#### 🏷️ Mission Types")
                if 'movement_type' in df.columns:
                    type_counts = df['movement_type'].value_counts().reset_index()
                    fig_type = px.pie(
                        type_counts, 
                        values='count', 
                        names='movement_type', 
                        hole=0.4,
                        color_discrete_sequence=px.colors.qualitative.Set2
                    )
                    fig_type.update_layout(height=300)
                    st.plotly_chart(fig_type, use_container_width=True)
                else:
                    st.info("Movement Type data unavailable")

            
            with c4:
                st.markdown("#### 🚦 Mission Status")
                if 'status' in df.columns:
                    status_counts = df['status'].value_counts().reset_index()
                    fig_status = px.bar(
                        status_counts, 
                        x='status', 
                        y='count',
                        color='status',
                        color_discrete_map={
                            'Completed': '#2e7d32', 
                            'Pending': '#ff9800', 
                            'Cancelled': '#d32f2f'
                        }
                    )
                    fig_status.update_layout(height=300, showlegend=False)
                    st.plotly_chart(fig_status, use_container_width=True)
                else:
                    st.info("Status data unavailable")

        else:
            st.info("No movement data available for analytics.")
    
    # 🔄 BULK OPERATIONS
    with tabs[3]:
        st.markdown("### 🔄 Bulk Movement Import")
        st.info("Upload a CSV file to process multiple asset movements at once (e.g., Flight Manifests).")
        
        
        with st.expander("⬇️ Step 1: Download Template"):
            
            sample_data = pd.DataFrame({
                'Mission ID': ['FLT-101', 'FLT-102'],
                'From Location': ['DXB-HQ', 'FUJ-DEPOT'],
                'To Location': ['RAK-FWD', 'DXB-HQ'],
                'Quantity': [50, 20],
                'Type': ['Deployment', 'Return'],
                'Priority': ['Normal', 'High'],
                'Notes': ['Weekly supply', 'Repair return']
            })
            
            csv = sample_data.to_csv(index=False)
            st.download_button(
                label="📥 Download CSV Template",
                data=csv,
                file_name="bulk_movement_template.csv",
                mime="text/csv"
            )

       
        st.markdown("#### 📤 Step 2: Upload Manifest")
        uploaded_file = st.file_uploader("Upload CSV File", type=['csv'])
        
        if uploaded_file:
            try:
                
                df_upload = pd.read_csv(uploaded_file)
                st.markdown("##### Preview Data")
                st.dataframe(df_upload.head(), use_container_width=True)
                
                
                required_cols = ['Mission ID', 'From Location', 'To Location', 'Quantity']
                missing = [c for c in required_cols if c not in df_upload.columns]
                
                if missing:
                    st.error(f"❌ Missing required columns: {', '.join(missing)}")
                else:
                    st.markdown("#### 🚀 Step 3: Process Movements")
                    
                    if st.button("Start Bulk Processing", type="primary"):
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        
                        success_count = 0
                        errors = []
                        
                        for idx, row in df_upload.iterrows():
                            
                            progress = (idx + 1) / len(df_upload)
                            progress_bar.progress(progress)
                            status_text.text(f"Processing row {idx + 1} of {len(df_upload)}...")
                            
                            
                            payload = {
                                "mission": str(row['Mission ID']),
                                "from": str(row['From Location']).strip(),
                                "to": str(row['To Location']).strip(),
                                "qty": int(row['Quantity']),
                                "type": row.get('Type', 'Transfer'),
                                "priority": row.get('Priority', 'Normal'),
                                "status": "Completed",
                                "notes": row.get('Notes', 'Bulk Import'),
                                "confirmed": st.session_state.get('user_id', 'Admin') 
                            }
                            
                            
                            success, msg = service.create_movement(payload)
                            
                            if success:
                                success_count += 1
                            else:
                                errors.append(f"Row {idx+1} ({row['Mission ID']}): {msg}")
                            
                            
                            time.sleep(0.05)
                        
                        
                        progress_bar.progress(100)
                        status_text.empty()
                        
                        if success_count == len(df_upload):
                            st.success(f"✅ SUCCESS! All {success_count} movements processed successfully.")
                            st.balloons()
                            time.sleep(2)
                            st.rerun()
                        else:
                            st.warning(f"⚠️ Processed {success_count} out of {len(df_upload)} records.")
                            if errors:
                                with st.expander("❌ View Error Log", expanded=True):
                                    for err in errors:
                                        st.error(err)
                                        
            except Exception as e:
                st.error(f"Error reading file: {str(e)}")
# ==========================================
# PAGE: INVENTORY
# ==========================================
elif menu == "📦 Inventory":
    st.markdown("""
        <div class='main-header'>
            <h1 style='margin: 0;'>📦 Inventory & Assets</h1>
            <p style='margin: 0.5rem 0 0 0; opacity: 0.9;'>Manage stock levels and asset definitions</p>
        </div>
    """, unsafe_allow_html=True)
    
    tabs = st.tabs(["📊 Current Inventory", "🔄 Stock Adjustments", "📦 Asset Types", "🔍 Search & Filter"])
    
    
   # Current Inventory
    with tabs[0]:
        locs = service.get_locations()
        
        if locs:
            df = pd.DataFrame(locs)
            
            
            df = df[df['code'] != 'SYSTEM']
            # -------------------------------------
            
            
            total_stock = df['current_stock'].sum()
            total_capacity = df['max_capacity'].sum()
            
            utilization = (total_stock / total_capacity * 100) if total_capacity > 0 else 0
            
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total Pallets", f"{total_stock:,}")
            col2.metric("Total Capacity", f"{total_capacity:,}")
            col3.metric("System Utilization", f"{utilization:.1f}%")
            
            active_count = len(df[df['status'].astype(str).str.lower() == 'active'])
            col4.metric("Active Locations", active_count)
           
            st.markdown("### 📍 Location-wise Inventory")
            
            view_option = st.radio(
                "View Mode",
                ["Table View", "Card View", "Chart View"],
                horizontal=True
            )
            
            if view_option == "Table View":
                df_display = df[['code', 'name', 'location_type', 'current_stock', 'max_capacity', 'status']].copy()
                df_display['utilization'] = (df_display['current_stock'] / df_display['max_capacity'] * 100).round(1)
                
                st.dataframe(
                    df_display,
                    column_config={
                        "utilization": st.column_config.ProgressColumn(
                            "Utilization",
                            format="%.1f%%",
                            min_value=0,
                            max_value=100,
                        )
                    },
                    use_container_width=True,
                    hide_index=True
                )
            
            elif view_option == "Card View":
                cols = st.columns(3)
                
                for idx, row in df.reset_index().iterrows():
                    with cols[idx % 3]:
                        current_val = row['current_stock']
                        max_cap = row['max_capacity']
                        utilization = (current_val / max_cap * 100) if max_cap > 0 else 0
                        status_color = "🟢" if str(row['status']).lower() == 'active' else "🔴"
                        
                        st.markdown(f"""
                            <div style='padding: 1rem; border: 1px solid #e0e0e0; border-radius: 8px; margin-bottom: 1rem;'>
                                <div style='display: flex; justify-content: space-between; align-items: center;'>
                                    <h4 style='margin: 0;'>{row['code']}</h4>
                                    <span style='font-size: 1.2rem;'>{status_color}</span>
                                </div>
                                <p style='color: #666; margin: 0.5rem 0;'>{row['name']}</p>
                                <div style='margin: 1rem 0;'>
                                    <div style='display: flex; justify-content: space-between;'>
                                        <span>Stock:</span>
                                        <strong>{current_val}/{max_cap}</strong>
                                    </div>
                                    <div style='height: 8px; background: #e0e0e0; border-radius: 4px; margin-top: 0.25rem; overflow: hidden;'>
                                        <div style='height: 100%; width: {min(utilization, 100)}%; 
                                                 background: {'#ff6b35' if utilization > 80 else '#1a5632'};'>
                                        </div>
                                    </div>
                                </div>
                                <div style='font-size: 0.8rem; color: #666;'>
                                    {row['location_type']} • {utilization:.1f}% full
                                </div>
                            </div>
                        """, unsafe_allow_html=True)
            
            else:  
                fig = px.treemap(
                    df,
                    path=[px.Constant("All Locations"), 'location_type', 'code'],
                    values='current_stock',
                    color='current_stock',
                    color_continuous_scale='Viridis',
                    title="Inventory Distribution"
                )
                fig.update_layout(height=500)
                st.plotly_chart(fig, use_container_width=True)
   # 2. STOCK ADJUSTMENTS
    with tabs[1]:
        st.markdown("### 🛠️ Manual Stock Adjustment")
        st.warning("Use this feature for audit corrections and reconciliation.")
        
        
        locs = service.get_locations({'status': 'active'})
        
        
        loc_codes = [l['code'] for l in locs if l['code'] != 'SYSTEM']
        # --------------------------------------------------
        
        with st.form("adjust_stock"):
            col1, col2 = st.columns(2)
            location = col1.selectbox("Select Location", loc_codes)
            
            
            current_val = 0
            if location:
                
                found = next((l for l in locs if l['code'] == location), None)
                if found:
                    current_val = found.get('current_stock', 0)
            
            col2.metric("Current System Stock", current_val)
            # -------------------------------------
            
            col3, col4 = st.columns(2)
            
            adjustment_type = col3.selectbox("Adjustment Type", ["Correction", "Receipt", "Write-off", "Transfer Error"])
            
            
            new_quantity = col4.number_input("New Physical Count", min_value=0, value=int(current_val))
            
            reason = st.text_input("Reason for Adjustment*", placeholder="e.g., Physical count discrepancy")
            reference = st.text_input("Reference Document", placeholder="e.g., Audit Report #2024-001")
            adjusted_by = st.text_input("Adjusted By", placeholder="Name of person making adjustment")
            
            submitted = st.form_submit_button("🔧 Apply Adjustment", type="primary", use_container_width=True)
            
            if submitted:
                if not reason:
                    st.error("Please provide a reason for the adjustment")
                else:
                    
                    diff = new_quantity - current_val
                    
                    if diff != 0:
                       
                        success, msg = service.create_movement({
                            "mission": f"ADJ-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
                            "from": "SYSTEM" if diff > 0 else location,
                            "to": location if diff > 0 else "SYSTEM",
                            "qty": abs(diff),
                            "type": "Adjustment",
                            "priority": "Normal",
                            "status": "Completed",
                            "notes": f"{adjustment_type}: {reason}. Reference: {reference}. Adjusted by: {adjusted_by}",
                            "confirmed": adjusted_by
                        })
                        
                        if success:
                            st.success(f"✅ Stock adjusted by {diff:+} pallets")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error(f"❌ {msg}")
                    else:
                        st.info("No change detected in stock quantity.")
    # 📦 ASSET TYPES (CRUD)
    with tabs[2]:
        st.markdown("### 📦 Asset Type Management")
        
        
        asset_tabs = st.tabs(["📋 View Types", "➕ Add Type", "✏️ Edit/Delete"])
        
        with asset_tabs[0]:
            with service.engine.connect() as conn:
                result = conn.execute(text("SELECT * FROM asset_types ORDER BY code"))
                types = [dict(row._mapping) for row in result]
            
            if types:
                df_types = pd.DataFrame(types)
                st.dataframe(
                    df_types[['code', 'name', 'category', 'weight_kg', 'dimensions', 'requires_special_handling']],
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.info("No custom asset types defined. Standard Pallet (108x88) is used by default.")

        # 2. CREATE: Add New Asset Type
        with asset_tabs[1]:
            with st.form("add_asset_type"):
                c1, c2 = st.columns(2)
                new_code = c1.text_input("Asset Code*", placeholder="e.g., PLT-STD")
                new_name = c2.text_input("Full Name*", placeholder="e.g., Standard 108x88 Pallet")
                
                c3, c4 = st.columns(2)
                cat = c3.selectbox("Category", ["Pallets", "Containers", "Netting", "Hardware"])
                weight = c4.number_input("Weight (kg)", min_value=0.0, value=25.0)
                
                dims = st.text_input("Dimensions", placeholder="108 x 88 x 12 in")
                special = st.checkbox("Requires Special Handling (Hazardous/Fragile)")
                
                if st.form_submit_button("🚀 Register Asset Type"):
                    if new_code and new_name:
                        with service.engine.connect() as conn:
                            try:
                                conn.execute(text("""
                                    INSERT INTO asset_types (code, name, category, weight_kg, dimensions, requires_special_handling)
                                    VALUES (:code, :name, :cat, :weight, :dims, :special)
                                """), {"code": new_code.upper(), "name": new_name, "cat": cat, "weight": weight, "dims": dims, "special": special})
                                conn.commit()
                                st.success(f"Asset type {new_code} registered successfully!")
                                time.sleep(1)
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error: {e}")
                    else:
                        st.warning("Please fill in Code and Name.")

        # 3. UPDATE / DELETE
        with asset_tabs[2]:
            with service.engine.connect() as conn:
                result = conn.execute(text("SELECT code, name FROM asset_types"))
                type_options = {f"{row.code} - {row.name}": row.code for row in result}
            
            if type_options:
                selected_label = st.selectbox("Select Asset Type to Manage", list(type_options.keys()))
                target_code = type_options[selected_label]
                
                with st.form("edit_asset_type"):
                    
                    with service.engine.connect() as conn:
                        curr = conn.execute(text("SELECT * FROM asset_types WHERE code = :c"), {"c": target_code}).fetchone()
                    
                    st.write(f"Editing **{target_code}**")
                    upd_name = st.text_input("Name", value=curr.name)
                    upd_cat = st.selectbox("Category", ["Pallets", "Containers", "Netting", "Hardware"], 
                                         index=["Pallets", "Containers", "Netting", "Hardware"].index(curr.category) if curr.category in ["Pallets", "Containers", "Netting", "Hardware"] else 0)
                    upd_weight = st.number_input("Weight (kg)", value=float(curr.weight_kg))
                    
                    c_edit1, c_edit2 = st.columns(2)
                    if c_edit1.form_submit_button("💾 Update"):
                        with service.engine.connect() as conn:
                            conn.execute(text("""
                                UPDATE asset_types SET name=:name, category=:cat, weight_kg=:weight WHERE code=:code
                            """), {"name": upd_name, "cat": upd_cat, "weight": upd_weight, "code": target_code})
                            conn.commit()
                        st.success("Updated!"); time.sleep(1); st.rerun()
                    
                    if c_edit2.form_submit_button("🗑️ Delete"):
                        with service.engine.connect() as conn:
                            conn.execute(text("DELETE FROM asset_types WHERE code=:code"), {"code": target_code})
                            conn.commit()
                        st.success("Deleted!"); time.sleep(1); st.rerun()
            else:
                st.info("No asset types found to edit.")
    # 🔍 SEARCH & FILTER
    with tabs[3]:
        st.markdown("### 🔍 Advanced Inventory Search")
        
        
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            search_query = st.text_input("🔎 Search Keywords", placeholder="Search by Code, Name, or Contact Person...")
        
        with col2:
            
            type_filter = st.multiselect("Location Type", ["Main Base", "Forward Base", "Depot", "Port", "Airbase"])
            
        with col3:
            status_filter = st.selectbox("Status", ["All", "active", "inactive", "maintenance"], key="search_status")

        
        locs = service.get_locations()
        
        if locs:
            df = pd.DataFrame(locs)
            
           
            df = df[df['code'] != 'SYSTEM']
            # ----------------------------------------
            
            if search_query:
                mask = (
                    df['code'].astype(str).str.contains(search_query, case=False, na=False) |
                    df['name'].astype(str).str.contains(search_query, case=False, na=False) |
                    df['contact_person'].astype(str).str.contains(search_query, case=False, na=False)
                )
                df = df[mask]
            
            
            if type_filter:
                df = df[df['location_type'].isin(type_filter)]
            
            
            if status_filter != "All":
                df = df[df['status'] == status_filter]
            
            
            st.divider()
            
            if not df.empty:
                st.success(f"✅ Found {len(df)} locations matching your criteria.")
                
               
                df['utilization'] = df.apply(
                    lambda x: (x['current_stock'] / x['max_capacity'] * 100) if x['max_capacity'] > 0 else 0, 
                    axis=1
                ).round(1)
                
                
                cols = ['code', 'name', 'location_type', 'status', 'current_stock', 'max_capacity', 'utilization']
                if 'contact_person' in df.columns:
                    cols.append('contact_person')
                
                
                cols = [c for c in cols if c in df.columns]
                
                st.dataframe(
                    df[cols],
                    column_config={
                        "utilization": st.column_config.ProgressColumn(
                            "Fill Level", 
                            format="%.1f%%", 
                            min_value=0, 
                            max_value=100
                        ),
                        "current_stock": st.column_config.NumberColumn("Stock"),
                        "contact_person": "POC"
                    },
                    use_container_width=True,
                    hide_index=True
                )
                
                
                csv = df.to_csv(index=False)
                st.download_button(
                    label="📥 Export Search Results to CSV",
                    data=csv,
                    file_name=f"inventory_search_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
            else:
                st.warning("No locations found matching these filters.")
        else:
            st.info("System has no data.")
# ==========================================
# PAGE: ANALYTICS
# ==========================================
elif menu == "📈 Analytics":
    st.markdown("""
        <div class='main-header'>
            <h1 style='margin: 0;'>📈 Intelligence Reports</h1>
            <p style='margin: 0.5rem 0 0 0; opacity: 0.9;'>Predictive analysis, trends, and system audits</p>
        </div>
    """, unsafe_allow_html=True)
    
    tabs = st.tabs(["📊 Performance", "📅 Trends", "🔍 Advanced Analytics", "📄 Reports"])
    
    # 1. PERFORMANCE
    
    with tabs[0]:
        st.markdown("### System Performance Metrics")
        
        
        locs = service.get_locations()
        movements = service.get_movements(limit=5000) 
        
        if locs and movements:
            df_locs = pd.DataFrame(locs)
            
            df_locs = df_locs[df_locs['code'] != 'SYSTEM']
            # ------------------------------------------
            
            df_moves = pd.DataFrame(movements)
            df_moves['timestamp'] = pd.to_datetime(df_moves['timestamp']) 
            
           
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                
                stock_turnover = len(movements) / max(1, len(df_locs))
                st.metric("Avg Movements per Location", f"{stock_turnover:.1f}")
            
            with col2:
                avg_move_size = df_moves['quantity'].mean()
                st.metric("Avg Movement Size", f"{avg_move_size:.1f}")
            
            with col3:
                
                high_util_locs = len(df_locs[df_locs['current_stock'] / df_locs['max_capacity'].replace(0, 1) > 0.8])
                st.metric("High-Utilization Locations", high_util_locs)
            
            with col4:
                
                cutoff = pd.Timestamp.now() - pd.Timedelta(days=7)
                recent_moves = len(df_moves[df_moves['timestamp'] >= cutoff])
                st.metric("Movements (Last 7 Days)", recent_moves)
            
            col_chart1, col_chart2 = st.columns(2)
            
            with col_chart1:
                st.markdown("##### Top 10 Locations by Stock")
                top_locs = df_locs.nlargest(10, 'current_stock')
                fig = px.bar(
                    top_locs,
                    x='code',
                    y='current_stock',
                    color='location_type',
                    color_discrete_sequence=px.colors.qualitative.Set2
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col_chart2:
                st.markdown("##### Movement Volume by Type")
                if 'movement_type' in df_moves.columns:
                    move_types = df_moves['movement_type'].value_counts()
                    fig = px.pie(
                        values=move_types.values,
                        names=move_types.index,
                        hole=0.4
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Movement type data not available")
        else:
            st.info("Insufficient data for performance metrics.")
    # 2. TRENDS
    with tabs[1]:
        st.markdown("### 📅 Temporal Inventory Trends")
        
        
        movements = service.get_movements(limit=5000)
        if movements:
            df_m = pd.DataFrame(movements)
            df_m['timestamp'] = pd.to_datetime(df_m['timestamp'])
            
            col_t1, col_t2 = st.columns([1, 3])
            with col_t1:
                granularity = st.radio("Time View", ["Daily", "Weekly", "Monthly"], horizontal=True)
            
            resample_map = {"Daily": "D", "Weekly": "W", "Monthly": "ME"}
            df_m.set_index('timestamp', inplace=True)
            
            st.markdown("#### 🔄 Flow Trends: Total Throughput")
            
            
            inbound = df_m.resample(resample_map[granularity])['quantity'].sum().reset_index(name='Volume')
            
            fig_flow = px.line(inbound, x='timestamp', y='Volume', 
                              title=f"{granularity} Pallet Throughput",
                              line_shape="spline", render_mode="svg")
            fig_flow.update_traces(line_color='#1a5632', fill='tozeroy')
            st.plotly_chart(fig_flow, use_container_width=True)

            st.divider()
            col_t3, col_t4 = st.columns(2)
            
            with col_t3:
                st.markdown("#### ⚖️ Volatility Index (7-Day Rolling)")
                
                daily_data = df_m.resample('D')['quantity'].sum()
                daily_vol = daily_data.rolling(window=7).mean().reset_index()
                
                fig_vol = px.line(daily_vol, x='timestamp', y='quantity', labels={'quantity': 'Avg Volume'})
                st.plotly_chart(fig_vol, use_container_width=True)
                
            with col_t4:
                st.markdown("#### 📦 Supply Chain Health")
                fig_health = go.Figure(go.Indicator(
                    mode = "gauge+number",
                    value = 85, 
                    title = {'text': "Health Index"},
                    gauge = {
                        'axis': {'range': [0, 100]},
                        'bar': {'color': "#1a5632"},
                        'steps': [
                            {'range': [0, 50], 'color': "#ffebee"},
                            {'range': [50, 80], 'color': "#fff3e0"},
                            {'range': [80, 100], 'color': "#e8f5e9"}
                        ]
                    }
                ))
                fig_health.update_layout(height=300)
                st.plotly_chart(fig_health, use_container_width=True)

        else:
            st.info("Insufficient movement data to generate trend analysis.")

    # 3. ADVANCED ANALYTICS (PREDICTIVE)
    
    with tabs[2]:
        st.markdown("### 🔍 Predictive Logistics Intelligence")
        
        locs = service.get_locations()
        
        movements = service.get_movements(limit=5000)
        
        if locs and movements:
            df_loc = pd.DataFrame(locs)
            
            
            df_loc = df_loc[df_loc['code'] != 'SYSTEM']
            # ----------------------------------------------------
            
            df_mov = pd.DataFrame(movements)
            df_mov['timestamp'] = pd.to_datetime(df_mov['timestamp'])
            
            
            cutoff = pd.Timestamp.now() - pd.Timedelta(days=30)
            last_30 = df_mov[df_mov['timestamp'] >= cutoff]
            
           
            burn_rates = last_30.groupby('from_location_code')['quantity'].sum() / 30
            burn_rates.name = 'burn_rate'
            
            
            df_risk = df_loc.merge(burn_rates, left_on='code', right_index=True, how='left').fillna(0)
            
            
            df_risk['days_of_supply'] = df_risk['current_stock'] / df_risk['burn_rate'].replace(0, 0.01)
            
            
            def get_risk_level(row):
                if row['current_stock'] == 0: return 'Critical (Empty)'
                if row['burn_rate'] == 0: return 'Stagnant'
                if row['days_of_supply'] < 5: return 'High Risk (<5 Days)'
                if row['days_of_supply'] < 10: return 'Medium Risk (<10 Days)'
                return 'Safe'

            df_risk['risk_level'] = df_risk.apply(get_risk_level, axis=1)
            
            df_risk['utilization'] = df_risk.apply(
                lambda x: (x['current_stock'] / x['max_capacity'] * 100) if x['max_capacity'] > 0 else 0, 
                axis=1
            ).round(1)

            
            st.markdown("#### 🛡️ Inventory Health Matrix")
            st.caption("Risk = High Velocity (Burn Rate) + Low Stock")
            
            if not df_risk.empty:
                fig_matrix = px.scatter(
                    df_risk,
                    x="utilization",
                    y="burn_rate",
                    size="max_capacity",
                    color="risk_level",
                    hover_name="code",
                    title="Risk vs. Velocity Analysis",
                    labels={
                        "utilization": "Storage Utilization (%)",
                        "burn_rate": "Burn Rate (Pallets/Day)"
                    },
                    color_discrete_map={
                        "Safe": "#2e7d32",
                        "Stagnant": "#757575",
                        "Medium Risk (<10 Days)": "#ff9800",
                        "High Risk (<5 Days)": "#d32f2f",
                        "Critical (Empty)": "#000000"
                    }
                )
                st.plotly_chart(fig_matrix, use_container_width=True)

                
                st.divider()
                col_pred1, col_pred2 = st.columns([2, 1])
                
                with col_pred1:
                    st.markdown("#### 📉 Projected Stockouts (Next 14 Days)")
                    
                    risks = df_risk[
                        (df_risk['days_of_supply'] <= 14) & (df_risk['burn_rate'] > 0)
                    ].sort_values('days_of_supply')
                    
                    if not risks.empty:
                        st.dataframe(
                            risks[['code', 'name', 'current_stock', 'burn_rate', 'days_of_supply']],
                            column_config={
                                "burn_rate": st.column_config.NumberColumn("Avg Burn/Day", format="%.1f"),
                                "days_of_supply": st.column_config.ProgressColumn(
                                    "Days Left", min_value=0, max_value=14, format="%.1f Days"
                                )
                            },
                            use_container_width=True,
                            hide_index=True
                        )
                    else:
                        st.success("✅ No imminent stockout risks detected.")
                
                with col_pred2:
                    st.markdown("#### 📊 ABC Analysis")
                    total_burn = df_risk['burn_rate'].sum()
                    if total_burn > 0:
                        df_risk.sort_values('burn_rate', ascending=False, inplace=True)
                        df_risk['cum_burn'] = df_risk['burn_rate'].cumsum()
                        df_risk['cum_pct'] = 100 * df_risk['cum_burn'] / total_burn
                        
                        def classify_abc(pct):
                            if pct <= 80: return 'A (High)'
                            if pct <= 95: return 'B (Med)'
                            return 'C (Low)'
                        
                        df_risk['class'] = df_risk['cum_pct'].apply(classify_abc)
                        fig_abc = px.pie(df_risk, names='class', title="Volume Class", color='class',
                                        color_discrete_map={'A (High)':'#d32f2f', 'B (Med)':'#ff9800', 'C (Low)':'#2e7d32'})
                        st.plotly_chart(fig_abc, use_container_width=True)
                    else:
                        st.info("No outflow data to calculate ABC class.")
            else:
                st.info("No location data available for analysis.")
        else:
            st.info("Insufficient data for predictive models.")
    # 4. REPORTS
    with tabs[3]:
        st.markdown("### 📄 Operational Reporting Engine")
        
        c1, c2 = st.columns([1, 2])
        with c1:
            report_type = st.radio("Report Type", ["Inventory Summary", "Movement Manifest", "System Audit Log"])
        with c2:
            st.info(f"Generating **{report_type}**.")
            if report_type != "Inventory Summary":
                r_start = st.date_input("Start Date", value=datetime.now() - timedelta(days=30))
                r_end = st.date_input("End Date", value=datetime.now())

        st.divider()

        if report_type == "Inventory Summary":
            locs = service.get_locations()
            if locs:
                df = pd.DataFrame(locs)
                
                
                df = df[df['code'] != 'SYSTEM']
                # -------------------------------------

               
                cols = ['code', 'name', 'location_type', 'status', 'current_stock', 'max_capacity']
                df_final = df[[c for c in cols if c in df.columns]].copy()
                
                
                df_final.columns = [c.replace('_', ' ').upper() for c in df_final.columns]
                
                st.dataframe(df_final, use_container_width=True, hide_index=True)
                st.download_button("📥 Download CSV", df_final.to_csv(index=False), "inventory.csv", "text/csv")

        elif report_type == "Movement Manifest":
            
            filters = {
                'start_date': datetime.combine(r_start, datetime.min.time()),
                'end_date': datetime.combine(r_end, datetime.max.time())
            }
            moves = service.get_movements(limit=10000, filters=filters)
            
            if moves:
                df = pd.DataFrame(moves)
                st.dataframe(df, use_container_width=True)
                st.download_button("📥 Download CSV", df.to_csv(index=False), "manifest.csv", "text/csv")
            else:
                st.warning("No movements found in range.")

        elif report_type == "System Audit Log":
            try:
                
                with service.engine.connect() as conn:
                    query = text("""
                        SELECT * FROM ledger_audit_logs 
                        WHERE created_at BETWEEN :start AND :end 
                        ORDER BY created_at DESC
                    """)
                    result = conn.execute(query, {
                        "start": datetime.combine(r_start, datetime.min.time()),
                        "end": datetime.combine(r_end, datetime.max.time())
                    })
                    logs = [dict(row._mapping) for row in result]
                
                if logs:
                    df_log = pd.DataFrame(logs)
                    st.dataframe(df_log, use_container_width=True)
                    st.download_button("📥 Download CSV", df_log.to_csv(index=False), "audit_logs.csv", "text/csv")
                else:
                    st.info("No audit logs found.")
            except Exception as e:
                st.error(f"Error fetching logs: {e}")

# ==========================================
# PAGE: SETTINGS
# ==========================================
elif menu == "⚙️ Settings":
    st.markdown("""
        <div class='main-header'>
            <h1 style='margin: 0;'>⚙️ System Settings</h1>
            <p style='margin: 0.5rem 0 0 0; opacity: 0.9;'>Configuration and User Access</p>
        </div>
    """, unsafe_allow_html=True)
    
    col_a, col_b = st.columns([1, 3])
    
    with col_a:
        
        if st.button("🚪 Logout", type="secondary", use_container_width=True):
            st.session_state['logged_in'] = False
            st.rerun()

    st.divider()

    
    st.subheader("👥 User Management")
    
    users = db.query(User).all()
    user_data = [{
        "ID": u.id, 
        "Username": u.username, 
        "Role": u.role, 
        "Last Login": u.last_login.strftime('%Y-%m-%d %H:%M') if u.last_login else "Never"
    } for u in users]
    
    st.dataframe(pd.DataFrame(user_data), use_container_width=True, hide_index=True)

    
    if st.session_state['user_role'] == 'Commander':
        with st.expander("➕ Add New User"):
            with st.form("add_user"):
                new_user = st.text_input("New Username")
                new_pass = st.text_input("New Password", type="password")
                new_role = st.selectbox("Role", ["Commander", "Logistics Officer", "Viewer"])
                
                if st.form_submit_button("Create User"):
                    from auth import hash_password
                    if db.query(User).filter(User.username == new_user).first():
                        st.error("User already exists!")
                    else:
                        u = User(username=new_user, password_hash=hash_password(new_pass), role=new_role)
                        db.add(u)
                        db.commit()
                        st.success(f"User {new_user} created!")
                        time.sleep(1)
                        st.rerun()
    else:
        st.info("🔒 Only Commanders can add new users.")

    st.divider()

    
    st.subheader("🛠️ Database Tools")
    
    with st.expander("🌱 Initialize Demo Data (Use if App is Empty)"):
        st.warning("⚠️ This will add sample Locations and Movements to your system.")
        if st.button("🚀 Generate Demo Data"):
            try:
                
                locations = [
                    ("DXB-HQ", "Dubai Main Airbase", "main_base", "25.2532, 55.3657"),
                    ("RAK-FWD", "RAK Forward Base", "forward_base", "25.6092, 55.9367"),
                    ("FUJ-DEPOT", "Fujairah Naval Depot", "logistics_hub", "25.1288, 56.3265"),
                    ("AUH-AIR", "Abu Dhabi Airfield", "airfield", "24.4329, 54.6445")
                ]
                
                for code, name, ltype, coords in locations:
                    service.create_location(
                        code=code, name=name, location_type=ltype, 
                        coordinates=coords, max_capacity=5000
                    )
                
                
                initial_stock = [
                    ("DXB-HQ", 500, "Initial Stock"),
                    ("RAK-FWD", 150, "Deployment Stock"),
                    ("FUJ-DEPOT", 300, "Naval Supply")
                ]
                
                for loc, qty, note in initial_stock:
                    service.create_movement({
                        "mission": "INIT-001",
                        "from": "SYSTEM",
                        "to": loc,
                        "qty": qty,
                        "type": "Adjustment",
                        "priority": "Normal",
                        "notes": note,
                        "confirmed": st.session_state['username']
                    })

                st.success("✅ Demo Data Generated Successfully! Go to Dashboard.")
                time.sleep(2)
                st.rerun()
                
            except Exception as e:
                st.error(f"Error generating data: {e}")
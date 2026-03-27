import streamlit as st
import pandas as pd
from geopy.geocoders import Nominatim, Photon
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import time
import matplotlib.pyplot as plt
import io
import json
import folium
from streamlit_folium import folium_static # For displaying folium maps in Streamlit

# --- Page Configuration ---
st.set_page_config(
    page_title="Climate Physical Risk Analyzer",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Custom CSS for Styling ---
st.markdown("""
<style>
    .reportview-container .main .block-container {
        padding-top: 2rem;
        padding-right: 2rem;
        padding-left: 2rem;
        padding-bottom: 2rem;
    }
    .css-1d391kg { /* Overall sidebar style */
        background-color: #f0f2f6;
    }
    .stSelectbox, .stTextInput, .stMultiSelect, .stNumberInput, .stFileUploader {
        margin-bottom: 10px;
    }
    .stButton>button {
        background-color: #4CAF50;
        color: white;
        border-radius: 5px;
        padding: 10px 20px;
        font-size: 16px;
        border: none;
        cursor: pointer;
        margin-top: 10px;
    }
    .stButton>button:hover {
        background-color: #45a049;
    }
    h1 {
        color: #004d40;
    }
    h2 {
        color: #00695c;
    }
    .risk-score-card {
        border: 1px solid #ddd;
        border-radius: 8px;
        padding: 15px;
        text-align: center;
        margin-bottom: 20px;
        background-color: #ffffff;
        box-shadow: 2px 2px 8px rgba(0,0,0,0.1);
    }
    .risk-score-value {
        font-size: 3em;
        font-weight: bold;
        margin: 10px 0;
    }
    .risk-level-very-low { color: #28a745; } /* Green */
    .risk-level-low { color: #28a745; } /* Green */
    .risk-level-medium { color: #ffc107; } /* Yellow */
    .risk-level-high { color: #fd7e14; } /* Orange */
    .risk-level-very-high { color: #dc3545; } /* Red */
    .stTable {
        font-size: 0.9em;
    }
    /* Expander styling */
    .streamlit-expanderHeader {
        background-color: #e0f2f1;
        color: #004d40;
        border-radius: 5px;
        padding: 10px;
        margin-bottom: 5px;
        font-weight: bold;
    }
    .streamlit-expanderContent {
        background-color: #f9fcfc;
        border-left: 3px solid #004d40;
        padding: 10px;
    }
</style>
""", unsafe_allow_html=True)


# --- Geocoding Function ---
def geocode_location(location_str):
   cache_key = location_str.strip().lower()
    geocode_cache = st.session_state.setdefault("geocode_cache", {})
    if cache_key in geocode_cache:
        return geocode_cache[cache_key]

    providers = [
        ("Nominatim", Nominatim(user_agent="climate_risk_analyzer_app_v2")),
        ("Photon", Photon(user_agent="climate_risk_analyzer_app_v2")),
    ]
    max_retries = 3

    def _normalize_location(location_obj):
        address = location_obj.raw.get('address', {}) if isinstance(location_obj.raw, dict) else {}
        return {
            "city": address.get('city', address.get('town', address.get('county', 'N/A'))),
            "state_region": address.get('state', address.get('region', 'N/A')),
            "country": address.get('country', 'N/A'),
            "latitude": location_obj.latitude,
            "longitude": location_obj.longitude
        }

    for provider_name, geolocator in providers:
        retry_delay_seconds = 1.2
        for attempt in range(1, max_retries + 1):
            try:
                location = geolocator.geocode(location_str, timeout=10)
                if location:
                    normalized = _normalize_location(location)
                    geocode_cache[cache_key] = normalized  # Cache successful lookups only.
                    return normalized
                break  # Not found on this provider; move to next provider.
            except (GeocoderTimedOut, GeocoderServiceError) as e:
                is_rate_limit_error = "429" in str(e)
                can_retry = attempt < max_retries and (is_rate_limit_error or isinstance(e, GeocoderTimedOut))

                if can_retry:
                    time.sleep(retry_delay_seconds)
                    retry_delay_seconds *= 2
                    continue

                # If Nominatim is rate-limited, fall back to Photon before surfacing hard error.
                if provider_name == "Nominatim" and is_rate_limit_error:
                    st.warning("Nominatim is rate-limited right now; trying backup geocoding provider.")
                    break

                # For non-rate-limit issues, try next provider if available.
                break
            except Exception:
                break

    st.error("Geocoding failed across available providers. Please try again or use Latitude/Longitude.")
    return None

            if can_retry:
                time.sleep(retry_delay_seconds)
                retry_delay_seconds *= 2
                continue

            st.error(f"Geocoding service error: {e}. Please try again or use Latitude/Longitude.")
            return None
        except Exception as e:
            st.error(f"An unexpected error occurred during geocoding: {e}")
            return None

# --- Risk Assessment Logic (Simplified for demonstration) ---
# In a real application, this would involve complex models, data lookups from
# climate databases (e.g., Copernicus, NOAA, custom datasets), and scientific assessment.
# Here, we simulate based on general knowledge for London.
def perform_risk_assessment_for_asset(latitude, longitude, asset_type, time_horizons, scenario):
    # This is a highly simplified, rule-based simulation.
    # Real assessment would use specific climate model outputs and asset vulnerability profiles.

    # Base risks for London (generic asset, SSP2-4.5)
    # Scores are for 2030 initially, then adjusted for 2050.
    base_risks = {
        "River Flood": {"score": 40, "confidence": "Medium", "drivers": "Increased extreme rainfall, river flow.", "impact": "Ground floor/basement inundation, structural damage, service disruption."},
        "Pluvial Flood": {"score": 60, "confidence": "High", "drivers": "Increased frequency/intensity of extreme precipitation, drainage capacity.", "impact": "Surface water runoff, localized flooding, water ingress, damage to lower levels."},
        "Coastal Flood": {"score": 20, "confidence": "Medium", "drivers": "Sea level rise, storm surges, tidal influence.", "impact": "Long-term threat to low-lying areas, managed by defenses. Infrastructure may be impacted."},
        "Tropical Cyclone / Storm": {"score": 45, "confidence": "Medium", "drivers": "Increased intensity of extratropical storms, wind speeds.", "impact": "Wind damage to roof, facade, windows; power outages; debris impacts."},
        "Extreme Precipitation": {"score": 65, "confidence": "High", "drivers": "Higher intensity and frequency of heavy rainfall events.", "impact": "Water ingress, roof leaks, overloading of drainage, increased pluvial flood risk."},
        "Heatwaves": {"score": 80, "confidence": "High", "drivers": "Increasing frequency, intensity, duration; urban heat island.", "impact": "Building overheating, increased cooling demand/energy costs, HVAC strain, occupant discomfort."},
        "Wildfire": {"score": 15, "confidence": "Low", "drivers": "Longer dry spells, heat stress on urban green spaces.", "impact": "Localized smoke ingress, air quality issues, minor external asset damage."},
        "Rising Mean Temperature": {"score": 75, "confidence": "High", "drivers": "Global warming trends, urban heat island effect.", "impact": "Increased energy consumption for cooling, reduced comfort, strain on cooling systems."},
        "Drought / Water Stress": {"score": 35, "confidence": "Medium", "drivers": "Longer dry periods, increased evaporation, population demand.", "impact": "Potential water use restrictions, increased water costs, impact on landscaping."},
        "Sea Level Rise": {"score": 10, "confidence": "High", "drivers": "Thermal expansion of oceans, ice sheet melt.", "impact": "Exacerbates coastal flood risk, stresses existing defenses, affects regional infrastructure."},
        "Long-term Rainfall Change": {"score": 40, "confidence": "Medium", "drivers": "Shift to more intense events, longer dry spells.", "impact": "Increased stress on stormwater systems, potential for subsidence/heave issues."},
    }

    results = []
    overall_scores = {}

    for horizon in time_horizons:
        current_hazard_data = {}
        for hazard, data in base_risks.items():
            score_base = data["score"]
            
            # Simple progression over time
            if horizon == 2050: score_base += 10
            elif horizon == 2100: score_base += 20
            # No change for 2027, 2030 from base here, but could be added

            # Adjustments for asset type (simplified)
            adjusted_score = score_base
            if asset_type == "Port" and ("Coastal" in hazard or "Sea Level Rise" in hazard):
                adjusted_score += 20
            elif asset_type == "Solar Plant" and "Heatwaves" in hazard:
                adjusted_score += 15
            elif asset_type == "Data Centre" and ("Heatwaves" in hazard or "Rising Mean Temperature" in hazard):
                adjusted_score += 25
            elif asset_type == "Industrial Facility" and ("River Flood" in hazard or "Pluvial Flood" in hazard):
                adjusted_score += 10 # Higher flood impact for industrial

            final_score = min(100, max(0, adjusted_score)) # Ensure scores stay within 0-100

            current_hazard_data[hazard] = {
                "Risk Level": score_to_risk_level(final_score),
                "Score": final_score,
                "Key Drivers": data["drivers"],
                "Asset Impact": data["impact"],
                "Confidence": data["confidence"]
            }
        results.append({"time_horizon": horizon, "hazards": current_hazard_data})

        # Calculate overall score for each horizon
        total_score = sum(h_data["Score"] for h_data in current_hazard_data.values())
        overall_score = total_score / len(current_hazard_data)
        overall_scores[horizon] = overall_score

    return results, overall_scores

def score_to_risk_level(score):
    if score <= 20: return "Very Low"
    if score <= 40: return "Low"
    if score <= 60: return "Medium"
    if score <= 80: return "High"
    return "Very High"

def risk_level_to_color_code(risk_level):
    if risk_level in ["Very Low", "Low"]: return "#28a745" # Green
    if risk_level == "Medium": return "#ffc107" # Yellow
    if risk_level == "High": return "#fd7e14" # Orange
    if risk_level == "Very High": return "#dc3545" # Red
    return "#6c757d" # Grey for undefined

# --- Adaptation Recommendations (Asset Type Specific) ---
def get_adaptation_recommendations(asset_type, highest_hazard_name, highest_hazard_score):
    base_recs = {
        "Engineering Controls": [
            "Upgrade HVAC systems for higher cooling loads.",
            "Enhance building envelope insulation and install high-performance glazing.",
            "Improve on-site drainage capacity and implement permeable surfaces.",
            "Install deployable flood barriers for vulnerable entry points.",
            "Elevate critical equipment above potential flood levels.",
            "Reinforce roof structures and façade components against high winds."
        ],
        "Nature-Based Solutions": [
            "Implement green roofs/walls for temperature regulation and stormwater absorption.",
            "Integrate rain gardens and permeable paving in surrounding areas.",
            "Strategic urban tree planting for shading and local cooling."
        ],
        "Monitoring & Early Warning": [
            "Install smart building management systems for real-time environmental monitoring.",
            "Deploy flood sensors with automated alerts.",
            "Subscribe to local extreme weather alerts and flood warnings."
        ],
        "Insurance & Resilience Planning": [
            "Review and update insurance policies for comprehensive climate-related peril coverage.",
            "Develop and regularly test a robust Business Continuity Plan (BCP) for climate scenarios.",
            "Integrate climate risk assessment into long-term capital expenditure planning."
        ]
    }

    # Asset-specific adjustments (simplified)
    if asset_type == "Port":
        base_recs["Engineering Controls"].append("Elevate quay levels and critical infrastructure.")
        base_recs["Nature-Based Solutions"].append("Restore coastal wetlands/mangroves as natural buffers.")
        base_recs["Monitoring & Early Warning"].append("Implement advanced tide and storm surge monitoring systems.")
    elif asset_type == "Data Centre":
        base_recs["Engineering Controls"].append("Redundant cooling systems and robust uninterruptible power supplies (UPS).")
        base_recs["Engineering Controls"].append("Enhanced fire suppression systems and flood protection for critical hardware.")
        base_recs["Monitoring & Early Warning"].append("Advanced thermal monitoring with automated fail-safes.")
    elif asset_type == "Solar Plant":
        base_recs["Engineering Controls"].append("Optimize panel orientation and cooling for extreme heat.")
        base_recs["Engineering Controls"].append("Secure panel foundations against wind and flood erosion.")
        base_recs["Monitoring & Early Warning"].append("Monitor solar irradiance and temperature for performance degradation.")
    elif asset_type == "Industrial Facility":
        base_recs["Engineering Controls"].append("Implement robust containment systems for hazardous materials against floodwaters.")
        base_recs["Insurance & Resilience Planning"].append("Conduct regular safety audits considering climate hazard escalation.")


    # Prioritize recommendations based on highest risk
    if highest_hazard_name and highest_hazard_score > 60: # High or Very High
        if "Heatwaves" in highest_hazard_name or "Temperature" in highest_hazard_name:
            base_recs["Engineering Controls"].insert(0, f"Prioritize HVAC upgrades and passive cooling strategies to address {highest_hazard_name}.")
        if "Flood" in highest_hazard_name or "Precipitation" in highest_hazard_name:
            base_recs["Engineering Controls"].insert(0, f"Prioritize floodproofing and drainage improvements for {highest_hazard_name}.")

    return base_recs

# --- Value at Risk (VaR) Estimation (Simplified) ---
def estimate_var(asset_value, hazard_score, confidence_level=95):
    # This is a highly simplified, illustrative VaR estimation.
    # A real VaR calculation would involve probability distributions of losses.

    # Financial impact factor based on hazard score (illustrative)
    if hazard_score <= 20: # Very Low
        impact_factor_min, impact_factor_max = 0.001, 0.005 # 0.1% - 0.5%
    elif hazard_score <= 40: # Low
        impact_factor_min, impact_factor_max = 0.005, 0.02 # 0.5% - 2%
    elif hazard_score <= 60: # Medium
        impact_factor_min, impact_factor_max = 0.02, 0.07 # 2% - 7%
    elif hazard_score <= 80: # High
        impact_factor_min, impact_factor_max = 0.07, 0.15 # 7% - 15%
    else: # Very High
        impact_factor_min, impact_factor_max = 0.15, 0.30 # 15% - 30%

    # Adjust for confidence level (very rough scaling)
    if confidence_level == 99:
        impact_factor_min *= 1.2
        impact_factor_max *= 1.5
    
    var_min = asset_value * impact_factor_min
    var_max = asset_value * impact_factor_max

    return var_min, var_max

# --- Main Application Logic ---
def main():
    st.title("🌍 Climate Physical Risk Analyzer")
    st.write("Input asset details and location to get a comprehensive climate physical risk assessment. Upload a CSV for portfolio analysis.")

    col_input, col_output = st.columns([1, 2])

    with col_input:
        st.header("Input Section")

        analysis_mode = st.radio("Choose Analysis Mode:", ("Single Asset", "Portfolio Analysis (CSV Upload)"))

        assets_to_analyze = []

        if analysis_mode == "Single Asset":
            with st.expander("1. Location Input", expanded=True):
                location_option = st.radio("Choose Location Input Method:", ("City / State / Country", "Latitude & Longitude"), key="loc_radio")
                
                if location_option == "City / State / Country":
                    location_str = st.text_input("Enter City, State/Province, or Country (e.g., 'London, United Kingdom')", "London, United Kingdom", key="loc_text")
                    latitude = None
                    longitude = None
                else:
                    latitude = st.number_input("Enter Latitude (e.g., 51.50735)", value=51.50735, format="%.5f", key="lat_input")
                    longitude = st.number_input("Enter Longitude (e.g., -0.12776)", value=-0.12776, format="%.5f", key="lon_input")
                    location_str = None

            with st.expander("2. Asset Details", expanded=True):
                asset_type_options = ["Commercial Building", "Industrial Facility", "Port", "Solar Plant", "Data Centre", "Warehouse", "Other"]
                asset_type = st.selectbox("Asset Type:", asset_type_options, key="asset_type_single")
                
                asset_value = st.number_input("Asset Value (in GBP, optional):", min_value=0.0, format="%.2f", value=30000000.0, key="asset_value_single")

                time_horizons_options = [2027, 2030, 2050, 2100]
                default_time_horizons = [2030, 2050]
                time_horizons = st.multiselect("Time Horizon(s):", time_horizons_options, default=default_time_horizons, key="time_horizons_single")
                
                scenario_options = ["SSP1-2.6", "SSP2-4.5", "SSP5-8.5"]
                scenario = st.selectbox("Climate Scenario:", scenario_options, index=1, key="scenario_single") # Default to SSP2-4.5
            
            # Prepare single asset for processing
            assets_to_analyze.append({
                "asset_name": "Single Asset",
                "location_str": location_str,
                "latitude": latitude,
                "longitude": longitude,
                "asset_type": asset_type,
                "asset_value": asset_value,
                "time_horizons": time_horizons,
                "scenario": scenario
            })

        else: # Portfolio Analysis Mode
            st.subheader("Upload Asset Portfolio (CSV)")
            st.write("CSV must contain columns: `asset_name`, `location_str` (or `latitude`, `longitude`), `asset_type`, `asset_value` (optional), `time_horizons` (comma-separated, optional), `scenario` (optional).")
            st.write("Example `location_str`: 'New York, USA' or '34.0522,-118.2437'")
            st.write("Example `time_horizons`: '2030,2050'")
            
            uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
            if uploaded_file is not None:
                portfolio_df = pd.read_csv(uploaded_file)
                st.write("Uploaded Portfolio Preview:")
                st.dataframe(portfolio_df.head())

                # Validate required columns
                required_cols = ['asset_name', 'asset_type']
                if not all(col in portfolio_df.columns for col in required_cols):
                    st.error(f"Missing required columns in CSV. Ensure '{', '.join(required_cols)}' are present.")
                    st.stop()
                
                # Check for location data
                if not ('location_str' in portfolio_df.columns or ('latitude' in portfolio_df.columns and 'longitude' in portfolio_df.columns)):
                    st.error("CSV must contain either 'location_str' or both 'latitude' and 'longitude' columns.")
                    st.stop()

                # Populate assets_to_analyze from CSV
                for idx, row in portfolio_df.iterrows():
                    asset_loc_str = row.get('location_str')
                    asset_lat = row.get('latitude')
                    asset_lon = row.get('longitude')
                    
                    # Ensure time_horizons are a list of ints
                    th_raw = row.get('time_horizons', '2030,2050')
                    try:
                        asset_time_horizons = [int(x.strip()) for x in str(th_raw).split(',')] if pd.notna(th_raw) else default_time_horizons
                    except ValueError:
                        st.warning(f"Invalid time_horizons for asset {row.get('asset_name', idx)}. Using default: {default_time_horizons}")
                        asset_time_horizons = default_time_horizons

                    assets_to_analyze.append({
                        "asset_name": row['asset_name'],
                        "location_str": asset_loc_str if pd.notna(asset_loc_str) else None,
                        "latitude": asset_lat if pd.notna(asset_lat) else None,
                        "longitude": asset_lon if pd.notna(asset_lon) else None,
                        "asset_type": row['asset_type'],
                        "asset_value": row.get('asset_value', 0.0), # Default to 0 if not provided
                        "time_horizons": asset_time_horizons,
                        "scenario": row.get('scenario', 'SSP2-4.5') # Default scenario
                    })
            else:
                assets_to_analyze = [] # No file uploaded, no assets to analyze


        run_analysis = st.button("Run Climate Risk Analysis")

    with col_output:
        st.header("Analysis Results")

        if 'analysis_results_list' not in st.session_state:
            st.session_state['analysis_results_list'] = [] # Stores results for all assets
        if 'portfolio_summary' not in st.session_state:
            st.session_state['portfolio_summary'] = None

        if run_analysis and assets_to_analyze:
            st.session_state['analysis_results_list'] = []
            st.session_state['portfolio_summary'] = None
            
            all_asset_overall_risks = []

            with st.spinner(f"Geocoding and assessing risks for {len(assets_to_analyze)} asset(s)..."):
                for asset_num, asset_input in enumerate(assets_to_analyze):
                    st.info(f"Analyzing asset: {asset_input['asset_name']}")
                    loc_data = None
                    lat = None
                    lon = None

                    if asset_input['location_str']:
                        # Nominatim usage policy recommends spacing requests to avoid rate limits.
                        # This pause only applies on non-cached calls.
                        if analysis_mode == "Portfolio Analysis (CSV Upload)" and asset_num > 0:
                            time.sleep(1.1)
                        loc_data = geocode_location(asset_input['location_str'])
                        if loc_data:
                            lat = loc_data['latitude']
                            lon = loc_data['longitude']
                        else:
                            st.warning(f"Could not geocode location for asset {asset_input['asset_name']}. Skipping this asset.")
                            continue # Skip to next asset
                    elif asset_input['latitude'] is not None and asset_input['longitude'] is not None:
                        loc_data = {
                            "city": "N/A", "state_region": "N/A", "country": "N/A",
                            "latitude": asset_input['latitude'],
                            "longitude": asset_input['longitude']
                        }
                        lat = asset_input['latitude']
                        lon = asset_input['longitude']
                    else:
                        st.warning(f"No valid location provided for asset {asset_input['asset_name']}. Skipping this asset.")
                        continue # Skip to next asset
                    
                    if lat is not None and lon is not None:
                        results, overall_scores = perform_risk_assessment_for_asset(
                            lat, lon,
                            asset_input['asset_type'],
                            asset_input['time_horizons'],
                            asset_input['scenario']
                        )
                        st.session_state['analysis_results_list'].append({
                            "asset_name": asset_input['asset_name'],
                            "location_data": loc_data,
                            "asset_info": asset_input,
                            "hazard_assessment": results,
                            "overall_scores": overall_scores
                        })
                        
                        # For portfolio summary
                        if overall_scores:
                            latest_horizon = sorted(asset_input['time_horizons'])[-1] if asset_input['time_horizons'] else 2050
                            all_asset_overall_risks.append({
                                "asset_name": asset_input['asset_name'],
                                "location": loc_data.get('city', 'N/A'),
                                "asset_type": asset_input['asset_type'],
                                "overall_risk_score": overall_scores.get(latest_horizon, 0),
                                "risk_level": score_to_risk_level(overall_scores.get(latest_horizon, 0)),
                                "latitude": lat,
                                "longitude": lon
                            })
                    else:
                        st.warning(f"Invalid latitude/longitude for asset {asset_input['asset_name']}. Skipping.")
                
                if analysis_mode == "Portfolio Analysis (CSV Upload)" and all_asset_overall_risks:
                    st.session_state['portfolio_summary'] = pd.DataFrame(all_asset_overall_risks)


        # --- Display Results ---
        if st.session_state['analysis_results_list']:
            
            if analysis_mode == "Portfolio Analysis (CSV Upload)" and st.session_state['portfolio_summary'] is not None:
                st.subheader("Portfolio Summary")
                portfolio_df = st.session_state['portfolio_summary']
                st.dataframe(portfolio_df.style.apply(lambda x: [f"color: {risk_level_to_color_code(x['risk_level'])}" if x.name == 'risk_level' else '' for i in x], axis=1), use_container_width=True)

                avg_risk = portfolio_df['overall_risk_score'].mean()
                st.info(f"Average Overall Portfolio Risk Score (latest horizon): **{avg_risk:.0f} ({score_to_risk_level(avg_risk)})**")

                # Map for portfolio
                st.subheader("Map Visualization (Portfolio)")
                m = folium.Map(location=[portfolio_df['latitude'].mean(), portfolio_df['longitude'].mean()], zoom_start=4)
                for idx, row in portfolio_df.iterrows():
                    folium.Marker(
                        location=[row['latitude'], row['longitude']],
                        popup=f"<b>{row['asset_name']}</b><br>Type: {row['asset_type']}<br>Risk: {row['risk_level']} ({int(row['overall_risk_score'])})",
                        icon=folium.Icon(color={
                            "Very Low": "green", "Low": "green", "Medium": "orange", "High": "red", "Very High": "red"
                        }[row['risk_level']], icon='info-sign')
                    ).add_to(m)
                folium_static(m, width=700, height=500)

                st.markdown("---")
                st.subheader("Individual Asset Details")
                st.write("Scroll down to view detailed analysis for each asset in the portfolio.")


            for asset_res in st.session_state['analysis_results_list']:
                asset_name = asset_res['asset_name']
                loc_data = asset_res['location_data']
                asset_info = asset_res['asset_info']
                results = asset_res['hazard_assessment']
                overall_scores = asset_res['overall_scores']

                st.markdown(f"## Analysis for: {asset_name}")
                
                # --- Location Summary Card ---
                st.subheader("1. Location Summary")
                st.markdown(f"""
                **City:** {loc_data.get('city', 'N/A')}  
                **Country:** {loc_data.get('country', 'N/A')}  
                **Latitude:** {loc_data['latitude']:.5f}  
                **Longitude:** {loc_data['longitude']:.5f}
                """)

                # --- Overall Physical Risk Score ---
                st.subheader("2. Overall Physical Risk Score")
                latest_horizon = sorted(asset_info['time_horizons'])[-1] if asset_info['time_horizons'] else 2050
                latest_overall_score = overall_scores.get(latest_horizon, 0)
                latest_risk_level = score_to_risk_level(latest_overall_score)
                risk_color = risk_level_to_color_code(latest_risk_level)

                st.markdown(f"""
                <div class="risk-score-card">
                    <h3>Overall Risk ({latest_horizon})</h3>
                    <div class="risk-score-value" style="color: {risk_color};">{int(latest_overall_score)}</div>
                    <p style="font-size: 1.2em; font-weight: bold; color: {risk_color};">{latest_risk_level}</p>
                </div>
                """, unsafe_allow_html=True)
                
                # --- Map Visualization (Single Asset) ---
                if analysis_mode == "Single Asset":
                    st.subheader("Map Visualization (Single Asset)")
                    m = folium.Map(location=[loc_data['latitude'], loc_data['longitude']], zoom_start=10)
                    folium.Marker(
                        location=[loc_data['latitude'], loc_data['longitude']],
                        popup=f"<b>{asset_name}</b><br>Type: {asset_info['asset_type']}<br>Risk: {latest_risk_level} ({int(latest_overall_score)})",
                        icon=folium.Icon(color=risk_level_to_color_code(latest_risk_level), icon='info-sign')
                    ).add_to(m)
                    folium_static(m, width=700, height=500)


                # --- Hazard Risk Table ---
                st.subheader("3. Hazard Risk Table")
                for result_data in results:
                    horizon = result_data["time_horizon"]
                    st.markdown(f"**Time Horizon: {horizon}** (Scenario: {asset_info['scenario']})")
                    
                    hazard_df = pd.DataFrame([
                        {
                            "Hazard": h,
                            "Risk Level": d["Risk Level"],
                            "Score": d["Score"],
                            "Key Drivers": d["Key Drivers"],
                            "Asset Impact": d["Asset Impact"]
                        } for h, d in result_data["hazards"].items()
                    ])
                    st.dataframe(hazard_df.style.apply(lambda x: [f"color: {risk_level_to_color_code(x['Risk Level'])}" if x.name == 'Risk Level' else '' for i in x], axis=1), use_container_width=True)
                
                # --- Risk Score Comparison Across Time Horizons ---
                if len(asset_info['time_horizons']) > 1:
                    st.subheader("4. Risk Score Comparison Across Time Horizons")
                    comparison_df = pd.DataFrame({
                        "Time Horizon": list(overall_scores.keys()),
                        "Overall Score": [overall_scores[h] for h in list(overall_scores.keys())]
                    }).set_index("Time Horizon")

                    fig, ax = plt.subplots(figsize=(8, 4))
                    comparison_df["Overall Score"].plot(kind='bar', ax=ax, color=[risk_level_to_color_code(score_to_risk_level(s)) for s in comparison_df["Overall Score"]])
                    ax.set_ylabel("Overall Risk Score (0-100)")
                    ax.set_title(f"Overall Physical Risk Score Progression ({asset_info['scenario']})")
                    ax.tick_params(axis='x', rotation=0)
                    st.pyplot(fig)
                    plt.close(fig) # Close the figure to free up memory

                # --- Business Impact Panel ---
                st.subheader("5. Business Impact")
                with st.expander("Potential Business Impacts", expanded=True):
                    st.markdown("""
                    *   **Operational Disruption:** Risk of interruptions to daily operations due to extreme weather events (e.g., power outages, access restrictions from flooding, reduced productivity during heatwaves).
                    *   **Infrastructure Damage Potential:** High potential for physical damage to the building's structure, roof, facade, and internal systems (HVAC, electrical) from floods, storms, and long-term temperature changes.
                    *   **Insurance Implications:** Expect increasing insurance premiums and potential difficulties in securing comprehensive coverage for high-risk perils. Insurers may mandate resilience upgrades.
                    *   **Financial Exposure Estimate:**
                    """)
                    if asset_info['asset_value'] > 0:
                        st.markdown(f"""
                        For an asset valued at **{asset_info['asset_value']:,} GBP**, without significant adaptation, estimated financial exposure:
                        *   **By {sorted(asset_info['time_horizons'])[0]} ({score_to_risk_level(overall_scores.get(sorted(asset_info['time_horizons'])[0],0))} Risk):** ~5-15% of asset value (approx. {asset_info['asset_value'] * 0.05:,.0f} - {asset_info['asset_value'] * 0.15:,.0f} GBP)
                        *   **By {latest_horizon} ({score_to_risk_level(overall_scores.get(latest_horizon,0))} Risk):** ~10-25% of asset value (approx. {asset_info['asset_value'] * 0.10:,.0f} - {asset_info['asset_value'] * 0.25:,.0f} GBP)
                        *These are illustrative estimates and require detailed engineering and financial analysis for precision.*
                        """)
                    else:
                        st.info("Provide an asset value to see an estimated financial exposure.")

                # --- Value at Risk (VaR) Estimation ---
                if asset_info['asset_value'] > 0:
                    st.subheader("7. Value at Risk (VaR) Estimation")
                    with st.expander("Estimate Financial Loss for a Hazard", expanded=True):
                        hazards_list = list(results[0]['hazards'].keys())
                        var_hazard = st.selectbox("Select Hazard for VaR:", hazards_list, key=f"var_hazard_{asset_name}")
                        var_horizon = st.selectbox("Select Time Horizon for VaR:", sorted(asset_info['time_horizons']), key=f"var_horizon_{asset_name}")
                        var_confidence = st.slider("Confidence Level (%) for VaR:", 90, 99, 95, key=f"var_confidence_{asset_name}")

                        if st.button(f"Calculate VaR for {asset_name}", key=f"calc_var_{asset_name}"):
                            hazard_score_for_var = 0
                            for res_h in results:
                                if res_h['time_horizon'] == var_horizon:
                                    hazard_score_for_var = res_h['hazards'][var_hazard]['Score']
                                    break
                            
                            if hazard_score_for_var > 0:
                                var_min, var_max = estimate_var(asset_info['asset_value'], hazard_score_for_var, var_confidence)
                                st.success(f"Estimated VaR for **{var_hazard}** by **{var_horizon}** at **{var_confidence}%** confidence:")
                                st.markdown(f"**Potential Loss:** {var_min:,.0f} GBP - {var_max:,.0f} GBP")
                                st.info("This is a simplified estimation. Full VaR analysis requires detailed financial modeling and probability distributions.")
                            else:
                                st.warning("Please select a valid hazard and time horizon with a non-zero risk score.")
                else:
                    st.info("Provide an asset value to enable Value at Risk (VaR) estimation.")

                # --- Adaptation Recommendations Panel ---
                st.subheader("8. Adaptation Recommendations")
                highest_hazard_score_current = 0
                highest_hazard_name_current = "N/A"
                if len(results) > 0:
                    latest_hazard_data = results[-1]['hazards'] # Get data from latest horizon
                    highest_hazard_current = max(latest_hazard_data.items(), key=lambda item: item[1]['Score'])
                    highest_hazard_name_current = highest_hazard_current[0]
                    highest_hazard_score_current = highest_hazard_current[1]['Score']
                
                recs = get_adaptation_recommendations(asset_info['asset_type'], highest_hazard_name_current, highest_hazard_score_current)

                for category, recommendations_list in recs.items():
                    with st.expander(f"**{category}**", expanded=True):
                        for rec in recommendations_list:
                            st.write(f"- {rec}")
                
                st.markdown("---")
            
            # --- Reporting & Advanced Features ---
            st.subheader("Reporting & Advanced Features")

            # Generate JSON for export
            full_export_data = {
                "portfolio_summary": st.session_state['portfolio_summary'].to_dict(orient='records') if st.session_state['portfolio_summary'] is not None else [],
                "individual_asset_reports": st.session_state['analysis_results_list']
            }
            json_string = json.dumps(full_export_data, indent=2)
            st.download_button(
                label="Export Full Report (JSON)",
                data=json_string,
                file_name=f"climate_risk_report_full_{time.strftime('%Y%m%d-%H%M%S')}.json",
                mime="application/json"
            )
            st.warning("PDF export functionality requires additional libraries and is not included in this version.")


            st.markdown("---")
            st.subheader("Optional Next Steps:")
            st.markdown("""
            *   **1. Add another asset:** Use the 'Single Asset' mode for another asset.
            *   **2. Compare scenarios:** Rerun the analysis with a different Climate Scenario (SSP1-2.6 or SSP5-8.5).
            *   **3. Export JSON:** Download the current analysis data in JSON format.
            *   **4. Run portfolio analysis:** Upload a new CSV for a fresh portfolio assessment.
            *   **5. Estimate Value at Risk (VaR):** Available for individual assets in their respective sections.
            *   **6. Map visualization with pin:** Integrated for both single assets and portfolio view.
            """)
            st.info("To access advanced features like more complex portfolio aggregation or timeline graphs, further development would be needed.")


if __name__ == "__main__":
    main()

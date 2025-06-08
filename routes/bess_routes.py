# runtimes_app/routes/bess_routes.py

from flask import Blueprint, request, jsonify
import pandas as pd
import numpy as np
import numpy_financial as npf # Import numpy_financial

# --- Blueprint Definition ---
bess_bp = Blueprint('bess', __name__)

# --- BESS Financial Model Calculation Function ---
# (Copied directly from your previous app.py/main_routes.py)
def calculate_bess_financials(
    asset_life,
    BESS_size_MW,
    duration,
    overbuild,
    degradation,
    availability,
    rte,
    DoD,
    t4_usd_MWh,
    b4_usd_MWh,
    BESS_module_plus_PCS_unit_usd_kWh,
    epc_unit_usd_kWh,
    om_unit_kW_yr,
    opex_esc
):
    """
    Calculates BESS financial metrics based on provided inputs.
    """
    # ------------------------ Single value ------------------------
    # Size
    BESS_size_MWh_pre_overbuild = BESS_size_MW * duration
    BESS_size_MWh_post_overbuild = BESS_size_MWh_pre_overbuild * (1 + overbuild)

    # Annual discharge / charge (before degradation impact)
    annual_energy_discharge_MWh_base = BESS_size_MWh_post_overbuild * DoD * rte * 365 * availability
    annual_energy_charge_MWh_base = annual_energy_discharge_MWh_base / rte

    # CAPEX
    BESS_module_plus_PCS_total_usdk = BESS_module_plus_PCS_unit_usd_kWh * BESS_size_MWh_post_overbuild
    epc_total_usdk = epc_unit_usd_kWh * BESS_size_MWh_post_overbuild
    total_hard_cost_usdk = BESS_module_plus_PCS_total_usdk + epc_total_usdk

    # OPEX
    om_usdk = om_unit_kW_yr * BESS_size_MW
    total_opex_usdk = om_usdk

    # ------------------------ Time series ------------------------
    # df pre-configuration
    year_count = [i for i in range(asset_life + 1)]
    df = pd.DataFrame(index=year_count)
    df.index.name = 'Year'
    df['operation_flag'] = [1 if i > 0 else 0 for i in year_count]

    # Degradation factor time series
    degradation_factor_series = pd.Series([(1 - degradation)**year for year in year_count], index=year_count)

    # OPEX escalation time series / total OPEX time series
    opex_esc_series = pd.Series([(1 + opex_esc)**i for i in year_count], index=year_count)
    total_opex_series_usdk = total_opex_usdk * opex_esc_series

    # Energy arbitrage time series (adjusted by degradation factor)
    annual_energy_discharge_MWh_series = annual_energy_discharge_MWh_base * degradation_factor_series
    annual_energy_charge_MWh_series = annual_energy_charge_MWh_base * degradation_factor_series

    annaul_energy_sales_revenue_series_usdk = annual_energy_discharge_MWh_series * t4_usd_MWh / 1000
    annaul_energy_charging_cost_series_usdk = annual_energy_charge_MWh_series * b4_usd_MWh / 1000
    annaul_energy_arbitrage_series_usdk = annaul_energy_sales_revenue_series_usdk - annaul_energy_charging_cost_series_usdk

    # ------------------------ Dataframe buildup ------------------------
    df['energy arbitrage $000s'] = annaul_energy_arbitrage_series_usdk * df['operation_flag']
    df['OPEX $000s'] = -total_opex_series_usdk * df['operation_flag']
    df['CAPEX $000s'] = -total_hard_cost_usdk * (1 - df['operation_flag']) # CAPEX only in Year 0

    # Total Cash Flow
    df['Cash Flow $000s'] = df['energy arbitrage $000s'] + df['OPEX $000s'] + df['CAPEX $000s']

    # IRR calculation
    irr_series = []
    for i in df.index:
        cash_flows_for_irr = df.loc[0:i, 'Cash Flow $000s'].values
        try:
            current_irr = npf.irr(cash_flows_for_irr)
            if np.isinf(current_irr) or np.isnan(current_irr) or current_irr < -0:
                irr_series.append(0)
            else:
                irr_series.append(current_irr)
        except ValueError:
            irr_series.append(0)

    irr_series = pd.Series(irr_series, index=year_count).fillna(0) * 100
    df['IRR %'] = irr_series

    # Calculate final IRR (for the entire asset life)
    final_irr = npf.irr(df['Cash Flow $000s'].values) * 100
    if np.isinf(final_irr) or np.isnan(final_irr) or final_irr < -100:
        final_irr_display = "N/A"
    else:
        final_irr_display = f"{final_irr:.2f}%"

    return df, final_irr_display

# --- BESS IRR Calculation Endpoint ---
@bess_bp.route('/api/calculate', methods=['POST'])
def calculate_bess_api():
    data = request.get_json()
    case = data.get('case')

    # Define inputs for the good, base, and bad cases
    if case == 'good':
        inputs = {
            'asset_life': 25, 'BESS_size_MW': 12, 'duration': 4.5,
            'overbuild': 0.10, 'degradation': 0.015, 'availability': 0.99,
            'rte': 0.92, 'DoD': 0.95, 't4_usd_MWh': 150, 'b4_usd_MWh': 25,
            'BESS_module_plus_PCS_unit_usd_kWh': 100, 'epc_unit_usd_kWh': 60,
            'om_unit_kW_yr': 12, 'opex_esc': 0.02
        }
    elif case == 'bad':
        inputs = {
            'asset_life': 15, 'BESS_size_MW': 8, 'duration': 3.5,
            'overbuild': 0.20, 'degradation': 0.03, 'availability': 0.95,
            'rte': 0.88, 'DoD': 0.85, 't4_usd_MWh': 120, 'b4_usd_MWh': 40,
            'BESS_module_plus_PCS_unit_usd_kWh': 115, 'epc_unit_usd_kWh': 80,
            'om_unit_kW_yr': 18, 'opex_esc': 0.03
        }
    else: # Default to base case if 'case' is not provided or not recognized
        inputs = {
            'asset_life': 20, 'BESS_size_MW': 10, 'duration': 4,
            'overbuild': 0.15, 'degradation': 0.02, 'availability': 0.98,
            'rte': 0.90, 'DoD': 0.90, 't4_usd_MWh': 139, 'b4_usd_MWh': 30,
            'BESS_module_plus_PCS_unit_usd_kWh': 105, 'epc_unit_usd_kWh': 70,
            'om_unit_kW_yr': 15, 'opex_esc': 0.025
        }

    df, final_irr_display = calculate_bess_financials(
        inputs['asset_life'], inputs['BESS_size_MW'], inputs['duration'],
        inputs['overbuild'], inputs['degradation'], inputs['availability'],
        inputs['rte'], inputs['DoD'], inputs['t4_usd_MWh'], inputs['b4_usd_MWh'],
        inputs['BESS_module_plus_PCS_unit_usd_kWh'], inputs['epc_unit_usd_kWh'],
        inputs['om_unit_kW_yr'], inputs['opex_esc']
    )

    # Convert DataFrame to a list of dicts for JSON, ensuring 'Year' is included
    df_records = df.reset_index().to_dict('records')

    return jsonify({
        "final_irr": final_irr_display,
        "cash_flows_data": df_records
    })
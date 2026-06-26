# Deep Architectural Audit Report

## Animal Stock Entry
- **Missing Data Flow (Auto-Fetches):**
  - Potential missing fetch for manual field rate

## Biological Asset
- **Missing Data Flow (Auto-Fetches):**
  - Potential missing fetch for manual field initial_cost
  - Potential missing fetch for manual field cost_to_sell
  - Potential missing fetch for manual field capitalized_cost

## Biological Asset Valuation
- **Missing Data Flow (Auto-Fetches):**
  - Potential missing fetch for manual field cost_to_sell
  - Potential missing fetch for manual field previous_cost_to_sell

## Contract Farming Agreement
- **Missing Data Flow (Auto-Fetches):**
  - Potential missing fetch for manual field agreed_purchase_price_per_unit
- **Redundancies & Poor Practices:**
  - Child table Contract Farming Input repeats parent fields: unit

## Disease Incident
- **Missing Data Flow (Auto-Fetches):**
  - Potential missing fetch for manual field treatment_cost

## Farm Activity
- **Missing Data Flow (Auto-Fetches):**
  - Potential missing fetch for manual field actual_cost
  - Potential missing fetch for manual field estimated_cost

## Farm BOM
- **Missing Data Flow (Auto-Fetches):**
  - Potential missing fetch for manual field total_estimated_cost

## Farm BOM Item
- **Missing Data Flow (Auto-Fetches):**
  - Potential missing fetch for manual field total_cost

## Farm Pen
- **Missing Data Flow (Auto-Fetches):**
  - Potential missing fetch for manual field occupancy_rate

## Farm Type
- **Redundancies & Poor Practices:**
  - Child table Farm Type Managed Item repeats parent fields: is_active

## Field Management
- **Missing Data Flow (Auto-Fetches):**
  - Potential missing fetch for manual field cost_estimate

## Fish Batch
- **Missing Data Flow (Auto-Fetches):**
  - Potential missing fetch for manual field current_survival_rate

## Fowl Run
- **Missing Data Flow (Auto-Fetches):**
  - Potential missing fetch for manual field mortality_rate_percent

## Harvest Recovery
- **Missing Data Flow (Auto-Fetches):**
  - Potential missing fetch for manual field purchase_price_per_kg

## Livestock Health Event
- **Missing Data Flow (Auto-Fetches):**
  - Potential missing fetch for manual field cost

## Livestock Individual
- **Missing Data Flow (Auto-Fetches):**
  - Potential missing fetch for manual field purchase_price

## Standard Cost Calculation BOM
- **Missing Data Flow (Auto-Fetches):**
  - Potential missing fetch for manual field unit
- **Redundancies & Poor Practices:**
  - Child table Standard Cost Calculation BOM Item repeats parent fields: item


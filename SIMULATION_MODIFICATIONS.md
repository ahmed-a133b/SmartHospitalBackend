# Enhanced Hospital Data Simulation - Risk Pattern Generation

## Overview
The data simulation script has been modified to generate realistic vital sign patterns that can trigger your backend's prediction and anomaly detection systems without directly creating alerts in the simulation itself.

## Key Changes Made

### 1. Removed Direct Anomaly Generation
- Eliminated `AnomalyType`, `AlertLevel`, and `Alert` classes
- Removed all alert creation and Firebase alert storage functionality
- Removed environmental hazard generation that would create immediate alerts

### 2. Introduced Risk Scenario System
- **PatientState**: Enum defining patient states (stable, deteriorating, critical, recovering, at_risk)
- **RiskScenario**: Enum defining specific risk patterns that develop over time
- **VitalPatternGenerator**: Creates progressive vital sign patterns that indicate developing health risks

### 3. Risk Scenarios Implemented
The simulation now generates these realistic risk patterns:

#### Cardiac Risk Patterns
- **CARDIAC_STRESS**: Gradual increase in heart rate with blood pressure changes
- **TACHYCARDIC_PATTERN**: Progressive tachycardia (HR increasing over time)
- **BRADYCARDIC_PATTERN**: Progressive bradycardia (HR decreasing over time)

#### Blood Pressure Patterns
- **HYPERTENSIVE_PATTERN**: Gradual blood pressure elevation
- **HYPOTENSIVE_TREND**: Progressive blood pressure decline

#### Respiratory Patterns
- **RESPIRATORY_COMPROMISE**: Increasing respiratory rate with declining efficiency
- **OXYGEN_DESATURATION**: Progressive oxygen saturation decline

#### Metabolic Patterns
- **GLYCEMIC_INSTABILITY**: Fluctuating glucose levels (both hyper/hypoglycemia)
- **FEVER_PROGRESSION**: Gradual temperature rise with physiological responses
- **HYPOTHERMIC_TREND**: Progressive temperature drop

### 4. Realistic Pattern Progression
- **Time-based progression**: Scenarios develop over 30 minutes from 0% to 100% completion
- **Mathematical variation**: Uses sine waves and other functions for natural fluctuation
- **Patient-specific triggers**: Risk factors and medical conditions influence scenario probability
- **Automatic resolution**: Scenarios end naturally, allowing for recovery periods

### 5. Backend Integration Benefits
The modified simulation creates patterns that your backend can detect through:

#### Vital Sign Trends
- Gradual changes that ML models can identify as concerning patterns
- Realistic progression that matches actual medical deterioration
- Multi-parameter correlations (e.g., fever causing increased HR and RR)

#### Risk Factor Correlation
- Patients with diabetes are more likely to have glycemic instability
- Cardiac patients have increased cardiac stress scenarios
- Age-based risk adjustments match real medical patterns

#### Pattern Recognition Opportunities
- **Early Warning Scores**: Gradual vital changes that can trigger EWS algorithms
- **Trend Analysis**: Multi-point data trends your prediction models can analyze
- **Correlation Detection**: Multiple vital signs changing together in realistic patterns

## Example Risk Scenario Flow

```
Patient with diabetes and hypertension:
Time 0: Normal vitals (baseline)
Time 5min: GLYCEMIC_INSTABILITY starts, glucose begins rising
Time 10min: Glucose at 180 mg/dL, slight HR increase
Time 15min: Glucose at 220 mg/dL, HR and RR elevated
Time 20min: Glucose at 280 mg/dL, clear deterioration pattern
Time 25min: Peak values, multiple vital signs affected
Time 30min: Scenario completion, ready for backend detection
```

## Backend Detection Points
Your prediction and anomaly detection systems can now identify:

1. **Early Warning Indicators**: Subtle changes in the first 10-15 minutes
2. **Pattern Recognition**: Multi-vital correlations as scenarios progress
3. **Risk Stratification**: Different patterns based on patient conditions
4. **Trend Analysis**: 30-minute progression curves for ML training

## Monitoring and Debugging
- Risk scenario starts are logged with patient ID and scenario type
- Vital values are logged during scenarios for debugging
- Scenario progression (0.0-1.0) is tracked and logged
- Natural scenario resolution is logged

This approach provides your backend with realistic data patterns that closely mimic actual patient deterioration, allowing for proper testing and validation of your prediction and anomaly detection algorithms.

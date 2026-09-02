from analysis.mosca import calculate_mosca_risk


result = calculate_mosca_risk(
    data_lifetime=12,
    migration_time=4,
    quantum_horizon=10,
    business_criticality="Critical"
)


for key, value in result.items():
    print(f"{key:25}: {value}")
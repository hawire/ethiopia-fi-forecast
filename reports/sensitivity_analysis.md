# Sensitivity Analysis

One-at-a-time (OAT) sweeps around the base scenario for 2027 forecasts.

## Tornado ranking (parameter influence)

indicator      parameter  min_forecast  max_forecast     range  base_forecast  target_year
   access   growth_scale     55.894879     66.550052 10.655172      61.222465         2027
   access    event_scale     59.422465     63.022465  3.600000      61.222465         2027
   access   decay_factor     60.822465     61.422465  0.600000      61.222465         2027
   access      lag_years     61.042465     61.422465  0.380000      61.222465         2027
   access residual_scale     60.989758     61.338819  0.349061      61.222465         2027
    usage   growth_scale     47.491942     63.491942 16.000000      55.491942         2027
    usage    event_scale     50.991942     59.991942  9.000000      55.491942         2027
    usage   decay_factor     54.491942     55.991942  1.500000      55.491942         2027
    usage      lag_years     55.041942     55.991942  0.950000      55.491942         2027
    usage residual_scale     55.483883     55.495971  0.012088      55.491942         2027

## Interpretation

- Larger `range` means the 2027 point forecast is more sensitive to that assumption.
- `growth_scale` scales the trend change relative to the last observation.
- `event_scale` scales additive event boosts; `lag_years` and `decay_factor` control timing.

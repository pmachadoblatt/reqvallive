package CriterionEvaluator {
    // Documentation holds only _go_to_verification.
    // Each success criterion is an item SuccessCriteria under the requirement.
    // After the measurement, Criterion Evaluator writes VerificationResult_PASS_* or VerificationResult_FAIL_*.
    //
    // Desk publisher: python scripts/publish_three_drones.py --mode both --altitude-span 2.5
    //   RQ_BAT_001      batteryLevel >= 20 percent          typically FAIL, then latched
    //   RQ_ALT_BAND_001 altitudeAGL between 20 m and 30 m   typically PASS
    //   RQ_ALT_VAR_001  altitude swing <= 1 m               typically FAIL (span 2.5 m)
    //   RQ_SEP_001      smallest separation >= 20 m         typically PASS
    //   RQ_BAT_RATE_001 |d(battery)/dt| <= 30 percent/min   typically FAIL
    //   RQ_BAT_DWELL_001 below 20 percent for at most 2 s   typically FAIL
    // RQ_01 repeats the battery criterion. Delete it in SysON before the dissertation screenshots.

    requirement RQ_BAT_001 {
        doc /*
        _go_to_verification
        */

        item SuccessCriteria {
            attribute scType = "threshold";
            attribute metric = "batteryLevel";
            attribute operator = ">=";
            attribute value = 20.0;
            attribute unit = "percent";
            attribute scope = "all_entities";
            attribute tolerance = 0.0;
        }
    }

    // Alias pedagógico / UI rápida (mesmo SC de bateria).
    requirement RQ_01 {
        doc /*
        _go_to_verification
        */

        item SuccessCriteria {
            attribute scType = "threshold";
            attribute metric = "batteryLevel";
            attribute operator = ">=";
            attribute value = 20.0;
            attribute unit = "percent";
            attribute scope = "all_entities";
            attribute tolerance = 0.0;
        }
    }

    requirement RQ_ALT_BAND_001 {
        doc /*
        _go_to_verification
        */

        item SuccessCriteria {
            attribute scType = "range";
            attribute metric = "altitudeAGL";
            attribute min_value = 20.0;
            attribute max_value = 30.0;
            attribute unit = "meters";
            attribute scope = "all_entities";
        }
    }

    requirement RQ_ALT_VAR_001 {
        doc /*
        _go_to_verification
        */

        item SuccessCriteria {
            attribute scType = "statistical";
            attribute metric = "altitudeAGL";
            attribute aggregation = "range";
            attribute operator = "<=";
            attribute value = 1.0;
            attribute unit = "meters";
        }
    }

    requirement RQ_SEP_001 {
        doc /*
        _go_to_verification
        */

        item SuccessCriteria {
            attribute scType = "threshold";
            attribute metric = "min_separation_m";
            attribute operator = ">=";
            attribute value = 20.0;
            attribute unit = "meters";
            attribute scope = "all_timesteps";
            attribute tolerance = 0.0;
        }
    }

    requirement RQ_BAT_RATE_001 {
        doc /*
        _go_to_verification
        */

        item SuccessCriteria {
            attribute scType = "rate";
            attribute metric = "batteryLevel";
            attribute operator = "<=";
            attribute value = 30.0;
            attribute unit = "percent/min";
            attribute scope = "all_entities";
            attribute abs_rate = true;
        }
    }

    requirement RQ_BAT_DWELL_001 {
        doc /*
        _go_to_verification
        */

        item SuccessCriteria {
            attribute scType = "dwell";
            attribute metric = "batteryLevel";
            attribute operator = "<";
            attribute value = 20.0;
            attribute unit = "percent";
            attribute scope = "all_entities";
            attribute max_duration_ms = 2000.0;
        }
    }
}

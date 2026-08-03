package ReqValLiveDemo {
    // Contrato: docs/SYSON_CONTRATO_DOC.md
    // Documentation = só _go_to_verification
    // Success Criteria = item SuccessCriteria no modelo
    // Após medição: ReqValLive cria VerificationResult_PASS_* / VerificationResult_FAIL_*
    //
    // Cenário demo com publish_three_drones.py --mode both (altitude_span=2.5):
    //   RQ_BAT_001     threshold battery  → tipicamente FAIL (charlie < 20%)
    //   RQ_ALT_BAND_001 range altitudeAGL → tipicamente PASS (banda 20–30 m)
    //   RQ_ALT_VAR_001 statistical range  → tipicamente FAIL (span ~2.5 > 1.0)
    //   RQ_SEP_001     threshold separação → tipicamente PASS (órbita ~60 m)

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
}

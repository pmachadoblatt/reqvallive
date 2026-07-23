package Model {
    // Exemplo de export textual SysML v2 (estilo CATIA Magic).
    // O APP só verifica requisitos cujo doc contém _go_to_verification.

    part partBattery {
        satisfy RQ_BAT_001;
    }

    requirement RQ_BAT_001 {
        doc /*
        _go_to_verification

        O sistema deve manter batteryLevel >= 20 percent em cada drone durante a operação.

        vv_method: test
        level: system
        priority: high

        ```json
        {
          "type": "threshold",
          "metric": "batteryLevel",
          "operator": ">=",
          "value": 20.0,
          "unit": "percent",
          "scope": "all_entities",
          "tolerance": 0.0
        }
        ```
        */
    }

    // Sem a tag → o APP ignora (não entra na verificação live)
    requirement RQ_IGNORED_UI {
        doc /*
        Requisito só de interface — não medir via MQTT.
        */
    }
}

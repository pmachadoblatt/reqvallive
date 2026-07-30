package ReqValLiveDemo {
    // Documentation = só marcador (_go_to_verification).
    // Success Criteria = item no modelo (visível no explorador).
    // Após medição o app cria item VerificationResult sob cada RQ
    // (status, reason, failedAt, extremeValue…) — não copiar laudo no doc.

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
        // VerificationResult é escrito pelo ReqValLive após a corrida, ex.:
        // item VerificationResult {
        //     attribute status = "FAIL";
        //     attribute reason = "...";
        //     attribute failedAt = "2026-07-30T17:55:00Z";
        //     attribute extremeValue = 15.2;
        //     attribute extremeKind = "min";
        // }
    }

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
}

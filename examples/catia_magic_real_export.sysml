package Model {
    requirement <RQ_BAT_001> RQ_BAT_001 {
        doc
        /* _go_to_verification
         *
         * O sistema deve manter batteryLevel >= 20 percent em cada drone durante a operação.
         *
         * vv_method: test
         * level: system
         * priority: high
         *
         * ```json
         * {
         *   "type": "threshold",
         *   "metric": "batteryLevel",
         *   "operator": ">=",
         *   "value": 20.0,
         *   "unit": "percent",
         *   "scope": "all_entities",
         *   "tolerance": 0.0
         * }*/
    }
    view ModelTable : DS_Views::TabularViews::rt {
        expose RQ_BAT_001;
    }
}

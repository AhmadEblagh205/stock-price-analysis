from audit import regime_correlation_audit, tail_risk_audit


def test_tail_audit_schema_and_expected_tail_pattern():
    out = tail_risk_audit(n_worlds=20, n_days=1200, seed=5)
    assert len(out) == 4
    assert set(out["level"]) == {0.95, 0.99}
    t99 = out[(out.distribution == "Student-t(5)") & (out.level == 0.99)].iloc[0]
    assert t99.hist_es_loss_median > t99.gaussian_es_loss_median


def test_regime_audit_recovers_known_correlation_shift():
    out = regime_correlation_audit(n_worlds=12, window=60, seed=12)
    corr = out[out.metric == "mean_pairwise_corr"].iloc[0]
    vol = out[out.metric == "equal_weight_ann_vol"].iloc[0]
    assert corr.stress_median > corr.calm_median + 0.4
    assert vol.stress_median > vol.calm_median

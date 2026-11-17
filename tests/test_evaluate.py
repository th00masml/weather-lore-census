"""Pin the two evaluator bugs fixed in 2026-11 and the skill statistic itself."""
import json
from pathlib import Path

import numpy as np
import pytest

import evaluate as E

ROOT = Path(__file__).resolve().parents[1]


def test_window_crossing_new_year_has_its_own_length():
    days, wrapped = E.window_days("12-01", "02-28")
    assert wrapped and len(days) == 90 and days[0] == (12, 1) and days[-1] == (2, 28)


def test_plain_and_single_day_windows():
    assert len(E.window_days("09-01", "09-30")[0]) == 30
    assert E.window_days("11-25", "11-25")[0] == [(11, 25)]


def test_outcome_before_condition_in_calendar_is_next_year():
    r = {"cond": {"start": "12-01", "end": "12-31"}, "out": {"start": "03-01", "end": "04-30"}}
    assert E.out_year_offset(r) == 1
    r = {"cond": {"start": "02-24", "end": "02-24"}, "out": {"start": "02-25", "end": "03-25"}}
    assert E.out_year_offset(r) == 0


def test_wrapped_window_value_reads_into_next_year():
    series = {(2000, 12, d): 1.0 for d in range(1, 32)}
    series.update({(2001, 1, d): 3.0 for d in range(1, 32)})
    days, wrapped = E.window_days("12-01", "01-31")
    assert E.window_value(series, 2000, days, wrapped, "mean") == pytest.approx(2.0)


@pytest.mark.skipif(not (ROOT / "data" / "raw" / "cet_daily.txt").exists(), reason="Met Office series not downloaded")
def test_baselines_reproduce_the_census():
    b = json.loads((ROOT / "outputs" / "baselines.json").read_text())
    assert b["summary"]["census_vs_recomputed_max_abs_diff"] < 1e-3


def test_census_has_no_whole_year_artefact():
    """Before the fix, Dec-Feb outcome windows were read as 367-day windows."""
    census = json.loads((ROOT / "outputs" / "census.json").read_text())
    assert len(census) == 76 and sum(r.get("fdr_significant", False) for r in census) == 10

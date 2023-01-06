from cycling_cadence_display.app import *
import pytest
import numpy as np
import mock
import re
import freezegun
from datetime import datetime as dt, timedelta

START_DT = dt(2023, 1, 5)


@pytest.fixture
def ctx() -> CycleContext:
    x = np.linspace(0, 2 * np.pi, 100)
    y = np.sin(x) + x

    dt_offset = float(START_DT.strftime("%s"))
    measurements = pd.DataFrame(
        {"cumulative_crank_revs": np.arange(0.0, len(y)), "last_crank_event_time": y},
        index=(np.arange(100.0) + dt_offset),
    )

    return CycleContext(
        device_address="1.2.3.4",
        device_name="XYZ",
        cumulative_crank_revs=1,
        last_crank_event_time=1,
        measurements=measurements,
    )


def test_ctx_layout(ctx):
    res = ctx.get_layout()
    assert len(res.children) == 3

    lower = res.children[-2]
    assert lower.name == "lower"
    assert len(lower.children) == 3


def test_ctx_get_plot(ctx):
    next_ts = ctx.measurements["last_crank_event_time"].max() * 1000 + 1000.0
    evt = mock.Mock(cumulative_crank_revs=101.0, last_crank_event_time=next_ts)
    ctx.update(evt)
    fig = ctx.get_plot()
    console = mock.MagicMock(max_width=40, max_height=10)
    plt: str = fig.__rich_console__(fig, console)[0]
    expected_plt = (
        "  6e+06 +---------------------------+\n"
        "  5e+06 |                           |\n"
        "  4e+06 |                           |\n"
        "  2e+06 |                           |\n"
        "  1e+06 |                           |\n"
        "      0 +---------------------------+\n"
        "        0    500  1000  1500 2000  2500\n"
        "                    mins"
    )
    assert expected_plt == plt


@freezegun.freeze_time(START_DT + timedelta(seconds=102))
def test_ctx_update(ctx):
    assert ctx.mean_rpm == ctx.last_instant_rpm == ctx.duration == "N/A"
    assert ctx.cumulative_crank_revs == 1
    assert ctx.last_crank_event_time == 1
    prev_measurements = ctx.measurements.copy()
    assert len(prev_measurements) == 100
    next_ts = ctx.measurements["last_crank_event_time"].max() * 1000 + 1000.0
    evt = mock.Mock(cumulative_crank_revs=101.0, last_crank_event_time=next_ts)
    ctx.update(evt)
    assert ctx.cumulative_crank_revs == 101.0
    assert np.isclose(ctx.last_crank_event_time, 7283.185307179586)
    assert len(ctx.measurements) == 101.0

    pd.util.testing.assert_frame_equal(ctx.measurements.iloc[:-1], prev_measurements)
    assert np.isclose(ctx.mean_rpm, 70989.9)
    assert np.isclose(ctx.last_instant_rpm, 120.0)
    assert re.match("\d+ min, \d+ sec", ctx.duration) is not None

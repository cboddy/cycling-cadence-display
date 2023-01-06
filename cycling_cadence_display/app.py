import asyncio
from bleak import BleakClient

from pycycling.cycling_speed_cadence_service import CyclingSpeedCadenceService, CSCMeasurement
from dataclasses import dataclass
import argparse
import os
import logging
import pandas as pd
import time
import termplotlib as tpl  # TODO
import json
import os
import os.path
from typing import List, Optional, Dict, Iterable
import rich
from rich import print
from rich.live import Live
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.layout import Layout
from rich.console import Console

LOG = logging.getLogger(__name__)


@dataclass
class CycleContext:
    device_address: str
    device_name: str
    cumulative_crank_revs: int = 0
    last_crank_event_time: int = 0
    instant_rpm: str = "N/A"
    mean_rpm: str = "N/A"
    duration: str = "N/A"
    last_instant_rpm: str = "N/A"
    measurements: pd.DataFrame = pd.DataFrame(columns=["cumulative_crank_revs", "last_crank_event_time"])
    instant_rpm: pd.DataFrame = pd.DataFrame()

    def update(self, event: CSCMeasurement):
        cumulative_crank_revs = event.cumulative_crank_revs
        last_crank_event_time = event.last_crank_event_time

        if self.cumulative_crank_revs >= cumulative_crank_revs or self.last_crank_event_time >= last_crank_event_time:
            # duplicate or out-of-order BLE event - ignore
            return

        self.cumulative_crank_revs = cumulative_crank_revs
        self.last_crank_event_time = last_crank_event_time

        self.measurements.loc[time.time()] = {
            "cumulative_crank_revs": cumulative_crank_revs,
            "last_crank_event_time": last_crank_event_time / 1000,
        }
        self.diff = self.measurements.diff().tail(-1).ffill()
        self.instant_rpm = (self.diff["cumulative_crank_revs"] / self.diff["last_crank_event_time"] * 60).ffill()

        self.mean_rpm = round(self.instant_rpm.mean(), 2)

        duration = self.measurements.index.max() - self.measurements.index.min()
        self.duration = f"{int(duration//60)} min, {int(duration % 60)} sec"
        self.last_instant_rpm = round(self.instant_rpm.iloc[-1], 2)

    def get_plot(self) -> "Figure":
        fig = tpl.Figure()
        fig.string_cache = None
        if len(self.measurements) < 2:
            return fig

        x_vals = ((self.measurements.index - self.measurements.index[0]) / 60).values[1:]

        def plt(_self, console: Console, *args, **kwargs) -> Iterable:
            """implement __rich_console__ method that is aware
            of the size of the console object pane, which should
            return an iterable of renderable objects, in this case
            just one `str`.
            """
            # __rich_console__ get's called more than once so cache the result. Otherwise it cats
            # together the plots as many times as __rich_console__ is called
            if fig.string_cache is None:
                fig.plot(
                    x_vals, self.instant_rpm.values, width=console.max_width, height=console.max_height, xlabel="mins"
                )
                fig.string_cache = fig.get_string()
            return (fig.string_cache,)

        fig.__rich_console__ = plt
        return fig

    def get_layout(self) -> Layout:

        layout = Layout()
        layout.split_column(Layout(name="upper"), Layout(name="lower"), Layout(name="bottom"))
        layout["lower"].split_row(
            Layout(name="left"),
            Layout(name="middle"),
            Layout(name="right"),
        )

        for key in ["upper", "lower"]:
            # fix the height of these panes to three rows
            # sine  they only display a few words
            layout[key].size = 3

        layout["upper"].update(Panel(Text(f"{self.device_name}'s Bike Crank Revolutions per Minute", justify="center")))
        for panel_key, state, title in (
            ("left", self.duration, "Time Cycling"),
            ("middle", self.mean_rpm, "Average RPM"),
            ("right", self.last_instant_rpm, "Instant RPM"),
        ):
            layout[panel_key].update(Panel(Text(str(state), justify="center"), title=title))

        layout["bottom"].update(Panel(self.get_plot(), title="RPM"))
        # return layout["bottom"]
        return layout


async def run(device_address: str, device_name: str):
    cycle_context = CycleContext(device_address=device_address, device_name=device_name)

    async with BleakClient(device_address, timeout=30) as client:

        await client.is_connected()

        with Live(cycle_context.get_layout(), refresh_per_second=4) as live:

            def my_page_handler(data):
                cycle_context.update(data)
                live.update(cycle_context.get_layout())
                # live.update(str(cycle_context))

            trainer = CyclingSpeedCadenceService(client)
            trainer.set_csc_measurement_handler(my_page_handler)
            await trainer.enable_csc_measurement_notifications()
            try:
                await asyncio.sleep(1000.0)
            finally:
                await trainer.disable_csc_measurement_notifications()


def main():
    os.environ["PYTHONASYNCIODEBUG"] = str(1)
    parser = argparse.ArgumentParser(
        """A TUI to display a dashboard of information about a  cycling cadence meter including the RPM over time"""
    )
    parser.add_argument("--device-address", default="E9:71:30:2B:BA:BF", required=True)  # TODO REMOVE
    args = parser.parse_args()
    LOG.info(f"Starting display with {args}")
    loop = asyncio.get_event_loop()
    device_name = "SENSOR"  # TODO use Bleak to get the name from device_address
    loop.run_until_complete(run(device_address=args.device_address, device_name=device_name))


if __name__ == "__main__":
    main()

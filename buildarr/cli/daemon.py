# Copyright (C) 2023 Callum Dickinson
#
# Buildarr is free software: you can redistribute it and/or modify it under the terms of the
# GNU General Public License as published by the Free Software Foundation,
# either version 3 of the License, or (at your option) any later version.
#
# Buildarr is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with Buildarr.
# If not, see <https://www.gnu.org/licenses/>.


"""
`buildarr daemon` CLI command.
"""


from __future__ import annotations

import itertools
import signal

from contextlib import contextmanager
from datetime import datetime, time
from logging import getLogger
from pathlib import Path
from threading import Lock, current_thread
from time import sleep
from typing import TYPE_CHECKING, cast

import click

from schedule import Job as SchedulerJob, Scheduler  # type: ignore[import]
from watchdog.events import FileSystemEventHandler
from watchdog.observers.polling import PollingObserver

from .. import __version__
from ..config import load_config
from ..logging import get_log_level
from ..state import state
from ..types import DayOfWeek
from ..util import get_absolute_path
from . import cli
from .run import _run as run_apply

if TYPE_CHECKING:
    from types import FrameType
    from typing import Dict, Generator, Iterable, List, Optional, Set, Tuple, Union

    from watchdog.events import DirModifiedEvent, FileModifiedEvent


logger = getLogger(__name__)


class Daemon:
    """
    Buildarr daemon object.

    Runs a job scheduler in the main thread, config file monitoring in a separate thread,
    and signal handlers to reload runtime state and interrupt the main thread as necessary.
    """

    def __init__(
        self,
        config_path: Path,
        secrets_file_path: Optional[Path],
        watch_config: Optional[bool],
        update_days: Iterable[DayOfWeek],
        update_times: Iterable[time],
    ) -> None:
        """
        Initialise the daemon object.

        Loads configuration from the given file, and determines appropriate values
        for daemon configuration fields.

        Args:
            config_path (Path): Buildarr configuration file to load
            watch_config (Optional[bool]): Override `watch_config` setting
            update_days (Iterable[DayOfWeek]): Override `update_days` setting
            update_times (Iterable[time]): Override `update_times` setting
        """
        # Set static configuration and override field values.
        self.config_path = config_path
        self.default_secrets_file_path = secrets_file_path
        self.default_watch_config = watch_config
        self.default_update_days = set(update_days)
        self.default_update_times = set(update_times)
        # Internal variables for tracking daemon state.
        self._stopped = False
        self._lock = Lock()
        self._secrets_file_path: Path = None  # type: ignore[assignment]
        self._watch_config = False
        self._update_days: Set[DayOfWeek] = set()
        self._update_times: Set[time] = set()
        self._update_daytimes: List[Tuple[DayOfWeek, time]] = []
        self._old_secrets_file_path: Optional[Path] = None
        self._old_watch_config = False
        self._old_update_days: Set[DayOfWeek] = set()
        self._old_update_times: Set[time] = set()
        self._old_update_daytimes: List[Tuple[DayOfWeek, time]] = []
        self._observer = PollingObserver()
        self._scheduler = Scheduler()

    def start(self) -> None:
        """
        Start the Buildarr daemon main loop.
        """
        with self._run_lock():
            self._initial_run()
            self._setup_signal_handlers()
            self._log_next_run()
            logger.info("Buildarr ready.")
        # Enter the update job schedule main loop.
        # This is a non-blocking process, so if there are no jobs to run,
        # it returns and sleeps for a pre-determined amount of time.
        # If the daemon has been signaled to stop, exit the loop.
        run_once = False
        while not self._stopped:
            if run_once:
                sleep(1)
            self._scheduler.run_pending()
            run_once = True
        logger.info("Finished stopping daemon")

    def stop(self) -> None:
        """
        Signal the daemon to stop, and shutdown job schedulers and monitors.

        This method is called by the SIGINT and SIGHUP handlers.
        """
        logger.info("Stopping daemon")
        self._stopped = True
        self._stop_handlers()

    @contextmanager
    def _run_lock(self) -> Generator[None, None, None]:
        """
        Control Buildarr run jobs using a lock, ensuring only one job runs at a given time.
        """
        thread = current_thread()
        self._lock.acquire()
        try:
            logger.debug("Thread '%s' acquired daemon run lock", thread.name)
            yield
        finally:
            logger.debug("Thread '%s' releasing daemon run lock", thread.name)
            self._lock.release()

    def _load_config(self) -> None:
        """
        Load the daemon configuration from the command line arguments
        and the Buildarr configuration.
        """
        # Load the Buildarr configuration, and save the list of files loaded.
        logger.info("Loading configuration file '%s'", self.config_path)
        load_config(self.config_path)
        logger.info("Finished loading configuration file")
        # Fetch the new configuration values, from the command line overrides,
        # then the Buildarr configuration, in that order.
        buildarr_config = state.config.buildarr
        secrets_file_path = (
            self.default_secrets_file_path
            if self.default_secrets_file_path
            else buildarr_config.secrets_file_path
        )
        watch_config = (
            self.default_watch_config
            if self.default_watch_config is not None
            else buildarr_config.watch_config
        )
        update_days = (
            self.default_update_days if self.default_update_days else buildarr_config.update_days
        )
        update_times = (
            self.default_update_times if self.default_update_times else buildarr_config.update_times
        )
        # Record whether or not the values were updated.
        self._old_secrets_file_path = self._secrets_file_path
        self._old_watch_config = self._watch_config
        self._old_update_days = self._update_days
        self._old_update_times = self._update_times
        self._old_update_daytimes = self._update_daytimes
        # Set the new values.
        self._secrets_file_path = secrets_file_path
        self._watch_config = watch_config
        self._update_days = update_days
        self._update_times = update_times
        # Generate the update job schedule.
        self._update_daytimes = [
            (update_day, update_time)
            for update_day, update_time in itertools.product(
                sorted(self._update_days),
                sorted(self._update_times),
            )
        ]

    def _initial_run(self) -> None:
        """
        Perform an initial Buildarr run under this configuration.

        Push initial updates to their configuration to all defined instances.
        """
        # Load the latest Buildarr configuration.
        self._load_config()
        # Print the daemon-specific configuration to the log.
        logger.info("Daemon configuration:")
        logger.info(" - Watch configuration files: %s", "Yes" if self._watch_config else "No")
        if self._watch_config:
            logger.info(" - Configuration files to watch:")
            for config_file in state.config_files:
                logger.info("   - %s", config_file)
        logger.info(" - Update at:")
        for update_day, update_time in self._update_daytimes:
            logger.info("   - %s %s", update_day.name.capitalize(), update_time.strftime("%H:%M"))
        # Setup update schedule.
        self._setup_update_schedule()
        # Setup configuration file watching, if enabled.
        self._setup_watch_config()
        # Apply initial configuration to all defined remote instances.
        logger.info("Applying initial configuration")
        try:
            run_apply(secrets_file_path=self._secrets_file_path)
        finally:
            state._reset()
        logger.info("Finished applying initial configuration")

    def _setup_update_schedule(self) -> None:
        """
        Schedule configuration update jobs according to the configuration,
        so that remote instances are automatically updated periodically.
        """
        logger.info("Scheduling update jobs")
        self._scheduler.clear()
        for update_day, update_time in self._update_daytimes:
            logger.debug(
                "Scheduling update job for %s %s",
                update_day.name.capitalize(),
                update_time.strftime("%H:%M"),
            )
            cast(SchedulerJob, getattr(self._scheduler.every().week, update_day.name)).at(
                update_time.strftime("%H:%M"),
            ).do(self._update)
        logger.info("Finished scheduling update jobs")

    def _update(self) -> None:
        """
        Perform a scheduled update of the remote instances.

        This method is called by the scheduled automatic update jobs.
        """
        with self._run_lock():
            logger.info("Running scheduled update of remote instances")
            try:
                run_apply(secrets_file_path=self._secrets_file_path)
            finally:
                state._reset()
            logger.info("Finished running scheduled update of remote instances")
            self._log_next_run()
            logger.info("Buildarr ready.")

    def _log_next_run(self) -> None:
        """
        Print a log alerting the user to the next scheduled run time.
        """
        logger.info(
            "The next run will be at %s",
            self._scheduler.next_run.strftime("%Y-%m-%d %H:%M"),
        )

    def _setup_watch_config(self) -> None:
        """
        Start configuration watching, if enabled and the schedule has changed.
        If disabled and was previously enabled, stop configuration watching.
        """
        if self._watch_config == self._old_watch_config:
            logger.info(
                "Config file monitoring is already %s",
                "enabled" if self._watch_config else "disabled",
            )
            return
        if self._watch_config:
            logger.info("Enabling config file monitoring")
            self._observer = PollingObserver()
            config_dirs: Dict[Path, Set[str]] = {}
            for config_file in state.config_files:
                if config_file.parent not in config_dirs:
                    config_dirs[config_file.parent] = set()
                config_dirs[config_file.parent].add(config_file.name)
            for config_dir, filenames in config_dirs.items():
                logger.debug(
                    "Scheduling event handler for directory '%s' with config files %s",
                    config_dir,
                    ", ".join(repr(filename) for filename in filenames),
                )
                self._observer.schedule(
                    ConfigDirEventHandler(self, config_dir, filenames),
                    config_dir,
                )
                logger.debug("Finished scheduling event handler for directory '%s'", config_dir)
            logger.debug("Starting config file observer")
            self._observer.start()
            logger.debug("Finished starting config file observer")
            logger.info("Finished enabling config file monitoring")
        else:
            logger.info("Disabling config file monitoring")
            self._observer.stop()
            self._observer = PollingObserver()
            logger.info("Finished disabling config file monitoring")

    def _watch_config_reload(self, changed_file: str, action: str) -> None:
        """
        Reload the Buildarr configuration, and re-run the initial run.

        This method is called by the config file monitor.
        Because this runs in a different thread, add extra handling to make sure
        that thread does not stop when an error occurs.
        """
        with self._run_lock():
            try:
                logger.info("Config file '%s' has been %s", changed_file, action)
                logger.info("Reloading config")
                self._initial_run()
                logger.info("Finished reloading config")
                self._log_next_run()
            except Exception as err:
                logger.exception(
                    "Unexpected exception occurred while handling config file event: %s",
                    err,
                )
            finally:
                logger.info("Buildarr ready.")

    def _setup_signal_handlers(self) -> None:
        """
        Setup `SIGINT`, `SIGTERM` and `SIGHUP` signal handers.

        SIGHUP can be used to reload the configuration, even if `watch_config` is disabled.
        """
        logger.info("Setting up signal handlers")
        logger.debug("Setting up SIGINT signal handler")
        signal.signal(signal.SIGINT, self._sigterm_handler)
        logger.debug("Setting up SIGTERM signal handler")
        signal.signal(signal.SIGTERM, self._sigterm_handler)
        if hasattr(signal, "SIGHUP"):
            logger.debug("Setting up SIGHUP signal handler")
            signal.signal(signal.SIGHUP, self._sighup_handler)  # type: ignore[attr-defined]
        else:
            logger.debug("SIGHUP is not available on this platform")
        logger.info("Finished setting up signal handlers")

    def _stop_handlers(self) -> None:
        """
        Shutdown the config file monitors and clear the automatic update job schedule.
        """
        logger.info("Stopping config file observer")
        self._observer.stop()
        logger.info("Finished stopping config file observer")
        logger.info("Clearing update job schedule")
        self._scheduler.clear()
        logger.info("Finished clearing update job schedule")

    def _sigterm_handler(self, signalnum: int, frame: Optional[FrameType]) -> None:
        """
        SIGTERM/SIGINT handler callback method.
        """
        logger.info("%s received", signal.Signals(signalnum).name)
        self.stop()

    def _sighup_handler(self, signalnum: int, frame: Optional[FrameType]) -> None:
        """
        SIGHUP handler callback method.
        """
        logger.info("%s received", signal.Signals(signalnum).name)
        with self._run_lock():
            logger.info("Reloading config")
            self._initial_run()
            logger.info("Finished reloading config")
            self._log_next_run()
            logger.info("Buildarr ready.")


class ConfigDirEventHandler(FileSystemEventHandler):
    """
    Config directory event handler.

    When a file being watched under the given directory has been modified,
    alert the Buildarr daemon.
    """

    def __init__(self, daemon: Daemon, config_dir: Path, filenames: Set[str]) -> None:
        """
        Initialise the config directory event handler.

        Args:
            daemon (Daemon): Buildarr daemon object
            config_dir (Path): Directory containing config files
            filenames (Set[str]): Names of config files to monitor
        """
        self.daemon = daemon
        self.config_dir = config_dir
        self.filenames = filenames
        super().__init__()

    def on_created(self, event: Union[DirModifiedEvent, FileModifiedEvent]) -> None:
        """
        On recreation of a config file within the monitored directory,
        reload the Buildarr daemon.

        Args:
            event (Union[DirModifiedEvent, FileModifiedEvent]): Event metadata
        """
        if not event.is_directory and Path(event.src_path) in (
            (self.config_dir / filename) for filename in self.filenames
        ):
            self.daemon._watch_config_reload(event.src_path, "recreated")

    def on_modified(self, event: Union[DirModifiedEvent, FileModifiedEvent]) -> None:
        """
        On modification of a config file within the monitored directory,
        reload the Buildarr daemon.

        Args:
            event (Union[DirModifiedEvent, FileModifiedEvent]): Event metadata
        """
        if not event.is_directory and Path(event.src_path) in (
            (self.config_dir / filename) for filename in self.filenames
        ):
            self.daemon._watch_config_reload(event.src_path, "modified")


def parse_time(
    ctx: click.Context,
    param: click.Parameter,
    time_strs: Tuple[str, ...],
) -> Tuple[time, ...]:
    """
    Parse a list of 24-hour time strings into `datetime.time` objects.

    Args:
        ctx (click.Context): `click` execution context
        param (click.Parameter): Parameter context
        time_strs (Tuple[str, ...]): Sequence of time strings to parse

    Raises:
        click.BadParameter: When an invalid time string has been supplied

    Returns:
        Tuple[time, ...]: Sequence of `datetime.time` objects
    """

    times: List[time] = []
    for time_str in time_strs:
        try:
            times.append(datetime.strptime(time_str, "%H:%M").time())
        except ValueError:
            raise click.BadParameter(f"Invalid 24 hour time '{time_str}'") from None
    return tuple(times)


@cli.command(
    help=(
        "Run as a daemon and periodically update defined instances.\n\n"
        "If CONFIG-PATH is not defined, use `buildarr.yml' from the current directory."
    ),
)
@click.argument(
    "config_path",
    metavar="[CONFIG-PATH]",
    type=click.Path(
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        path_type=Path,
    ),
    default=Path.cwd() / "buildarr.yml",
    # Get absolute path, but do NOT resolve symlinks in daemon mode.
    callback=lambda ctx, params, path: get_absolute_path(path),
)
@click.option(
    "-s",
    "--secrets-file",
    "secrets_file_path",
    metavar="SECRETS-JSON",
    type=click.Path(
        # The secrets file does not need to exist (it will be created in that case).
        file_okay=True,
        dir_okay=False,
        readable=True,
        path_type=Path,
    ),
    default=None,
    # Get absolute path, but do NOT resolve symlinks in daemon mode.
    callback=lambda ctx, params, path: get_absolute_path(path) if path else None,
    help=(
        "Read secrets metadata from (and write back to) the specified JSON file. "
        "If unspecified, use the value from the configuration file, "
        "and if undefined there, default to `secrets.json'."
    ),
)
@click.option(
    "-w/-W",
    "--watch/--no-watch",
    "watch_config",
    default=None,
    help=(
        "If `--watch' is defined, reload the config files if they are updated while running. "
        "If `--no-watch' is defined, disable watching the config files. "
        "Overrides the `buildarr.watch_config' config field."
    ),
)
@click.option(
    "-d",
    "--update-day",
    "update_days",
    metavar="DAY",
    type=click.Choice([day.name for day in DayOfWeek], case_sensitive=False),
    callback=lambda ctx, param, days: tuple(DayOfWeek(day) for day in days),
    multiple=True,
    help=(
        "Update defined instances on the specified day. "
        "Overrides the `buildarr.update_days' config field. "
        "(can be defined multiple times)"
    ),
)
@click.option(
    "-t",
    "--update-time",
    "update_times",
    metavar="TIME",
    callback=parse_time,
    multiple=True,
    help=(
        "Update defined instances at the specified 24-hour time. "
        "Overrides the `buildarr.update_times' config field. "
        "(can be defined multiple times)"
    ),
)
def daemon(
    config_path: Path,
    secrets_file_path: Optional[Path],
    watch_config: Optional[bool],
    update_days: Tuple[DayOfWeek, ...],
    update_times: Tuple[time, ...],
) -> None:
    """
    `buildarr daemon` command main routine.

    Args:
        config_path (Path): Buildarr configuration file to load
        watch_config (Optional[bool]): Override `watch_config` setting
        update_days (Tuple[DayOfWeek, ...]): Override `update_days` setting
        update_times (Tuple[time, ...]): Override `update_times` setting
    """

    logger.info("Buildarr version %s (log level: %s)", __version__, get_log_level())

    Daemon(
        config_path=config_path,
        secrets_file_path=secrets_file_path,
        watch_config=watch_config,
        update_days=update_days,
        update_times=update_times,
    ).start()

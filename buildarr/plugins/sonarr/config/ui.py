# -*- coding: utf-8 -*-

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
Sonarr plugin UI settings configuration object.
"""


from __future__ import annotations

from typing import List, cast

from buildarr.config import ConfigBase, ConfigEnum, RemoteMapEntry
from buildarr.secrets import SecretsPlugin

from ..secrets import SonarrSecrets
from ..util import api_get, api_put


class FirstDayOfWeek(ConfigEnum):
    """
    First day of the week enumeration for Sonarr.
    """

    sunday = 0
    monday = 1


class WeekColumnHeader(ConfigEnum):
    """
    Week column header enumeration for Sonarr.
    """

    month_first = "ddd M/D"
    month_first_padded = "ddd MM/DD"
    day_first = "ddd D/M"
    day_first_padded = "ddd DD/MM"


class ShortDateFormat(ConfigEnum):
    """
    Short date format enumeration for Sonarr.
    """

    word_month_first = "MMM D YYYY"
    word_month_second = "DD MMM YYYY"
    slash_month_first = "MM/D/YYYY"
    slash_month_first_day_padded = "MM/DD/YYYY"
    slash_day_first = "DD/MM/YYYY"
    iso8601 = "YYYY-MM-DD"


class LongDateFormat(ConfigEnum):
    """
    Long date format enumeration for SOnarr.
    """

    month_first = "dddd, MMMM D YYYY"
    day_first = "dddd, D MMMM YYYY"


class TimeFormat(ConfigEnum):
    """
    Time format enumeration for Sonarr.
    """

    twelve_hour = "h(:mm)a"
    twentyfour_hour = "HH:mm"


class SonarrUISettingsConfig(ConfigBase):
    """
    Sonarr user interface configuration can also be set directly from Buildarr.

    ```yaml
    sonarr:
      settings:
        ui:
          first_day_of_week: "monday"
          week_column_header: "day-first"
          short_date_format: "word-month-second"
          long_date_format: "day-first"
          time_format: "twentyfour-hour"
          show_relative_dates: true
          enable_color_impaired_mode: false
    ```
    """

    # Calendar
    first_day_of_week: FirstDayOfWeek = FirstDayOfWeek.sunday
    """
    The first day of the week that Sonarr will show in the calendar.

    Values:

    * `sunday` - Sunday
    * `monday` - Monday
    """

    week_column_header: WeekColumnHeader = WeekColumnHeader.month_first
    """
    The format of the date in columns when "Week" is the active view in the calendar.

    Values:

    * `month-first` - Print month first (e.g. Tue 3/25)
    * `month-first-padded` - Print month first with padded numbers (e.g. Tue 03/25)
    * `day-first` - Print day first with padded numbers (e.g. Tue 25/3)
    * `day-first-padded` - Print day first with padded numbers (e.g. Tue 25/03)
    """

    # Dates
    short_date_format: ShortDateFormat = ShortDateFormat.word_month_first
    """
    The format of short dates in the user interface.

    Values:

    * `word-month-first` - Month as word, print month first (e.g. Mar 4 2014)
    * `word-month-second` - Month as word, print month second (e.g. 4 Mar 2014)
    * `slash-month-first` - Slash-separated date, print month first (e.g. 03/4/2014)
    * `slash-month-first-padded` - Slash-separated date, print month first (e.g. 03/04/2014)
    * `slash-day-first` - Slash-separated date, print day first (e.g. 04/03/2014)
    * `iso8601` - ISO-8601 date (e.g. 2014-03-04)
    """

    long_date_format: LongDateFormat = LongDateFormat.month_first
    """
    The format of long dates in the user interface.

    Values:

    * `month-first` - Print month first (e.g. Tuesday, March 4 2014)
    * `day-first` - Print day first (e.g. Tuesday, 4 March 2014)
    """

    time_format: TimeFormat = TimeFormat.twelve_hour
    """
    The format of time in the user information.

    Values:

    * `twelve-hour` - 12-hour time (e.g. 5pm/5:30pm)
    * `twentyfour-hour` - 24-hour time (e.g. 17:00/17:30)
    """

    show_relative_dates: bool = True
    """
    When set to `True`, Sonarr will show relative dates (e.g. today, yesterday)
    instead of absolute dates (e.g. Monday, Tuesday ...).
    """

    # Style
    enable_color_impaired_mode: bool = False
    """
    Enable an altered view style to allow colour-impaired users to better distinguish
    colour-coded information.
    """

    _remote_map: List[RemoteMapEntry] = [
        ("first_day_of_week", "firstDayOfWeek", {}),
        ("week_column_header", "calendarWeekColumnHeader", {}),
        ("short_date_format", "shortDateFormat", {}),
        ("long_date_format", "longDateFormat", {}),
        ("time_format", "timeFormat", {}),
        ("show_relative_dates", "showRelativeDates", {}),
        ("enable_color_impaired_mode", "enableColorImpairedMode", {}),
    ]

    @classmethod
    def from_remote(cls, secrets: SecretsPlugin) -> SonarrUISettingsConfig:
        return cls(
            **cls.get_local_attrs(
                cls._remote_map,
                api_get(cast(SonarrSecrets, secrets), "/api/v3/config/ui"),
            ),
        )

    def update_remote(
        self,
        tree: str,
        secrets: SecretsPlugin,
        remote: SonarrUISettingsConfig,
        check_unmanaged: bool = False,
    ) -> bool:
        sonarr_secrets = cast(SonarrSecrets, secrets)
        updated, remote_attrs = self.get_update_remote_attrs(
            tree,
            remote,
            self._remote_map,
            check_unmanaged=check_unmanaged,
        )
        if updated:
            api_put(
                sonarr_secrets,
                f"/api/v3/config/ui/{api_get(sonarr_secrets, '/api/v3/config/ui')['id']}",
                remote_attrs,
            )
            return True
        return False

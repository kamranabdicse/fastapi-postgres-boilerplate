import uuid
import pandas as pd
from pandas import ExcelWriter
from typing import Tuple

import jdatetime


def last_jmonth_period(
    j_now: jdatetime.datetime,
) -> Tuple[jdatetime.datetime, jdatetime.datetime]:
    if j_now.month == 1:
        last_month = 12
        last_year = j_now.year - 1
    else:
        last_month = j_now.month - 1
        last_year = j_now.year
    last_month_start = jdatetime.datetime(last_year, last_month, 1)
    last_day_of_month = jdatetime.j_days_in_month[last_month - 1]
    last_month_end = jdatetime.datetime(last_year, last_month, last_day_of_month)
    return last_month_start, last_month_end


def generate_excel_file(path, data: dict, title: str = "Report") -> Tuple[str, str]:
    file_name = "{}-{}.xlsx".format(title, str(uuid.uuid4()))
    file_path = path + file_name
    df = pd.DataFrame(data)
    writer = ExcelWriter(file_path)
    df.to_excel(writer, title, index=False)
    writer.save()
    return file_path, file_name

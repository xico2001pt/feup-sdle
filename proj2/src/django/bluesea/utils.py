import ntplib
from datetime import datetime, timezone


def get_datetime():
    c = ntplib.NTPClient()
    # Provide the respective ntp server ip in below function
    response = c.request('pt.pool.ntp.org', version=3)
    return datetime.fromtimestamp(response.tx_time, timezone.utc)
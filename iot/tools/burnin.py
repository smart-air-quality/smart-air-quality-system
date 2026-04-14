"""
30-minute burn-in: CSV to UART. Copy to device root beside `aqmon/` + `config.py`.

  import burnin
  burnin.run()
"""

import time

try:
    import config
except ImportError:
    raise SystemExit("Add config.py on device (copy from iot/config/config.example.py)")

from aqmon import timeutil
from aqmon.drivers import KY015, MQ9, PMS7003

BURN_MINUTES = 30
SAMPLE_S = 10


def run():
    timeutil.sync_ntp()
    pms = PMS7003(
        config.PMS_UART_ID,
        config.PMS_TX_PIN,
        config.PMS_RX_PIN,
        config.PMS_BAUD,
    )
    ky = KY015(config.KY015_PIN, config.KY015_DHT_TYPE)
    mq = MQ9(config.MQ9_ADC_PIN, config.MQ9_ADC_ATTN)

    end = time.time() + BURN_MINUTES * 60
    print("utc,pm1,pm25,pm10,temp_c,hum_pct,raw_adc,co_ppm_est,preheat_s")
    while time.time() < end:
        pm1, pm25, pm10 = pms.read()
        tc, hum = ky.read()
        adc = mq.raw_adc()
        co = mq.co_ppm_estimate()
        pre = mq.preheat_remaining_s()
        ts = timeutil.utc_iso()
        print(
            "{},{},{},{},{},{},{},{},{}".format(
                ts,
                pm1,
                pm25,
                pm10,
                tc,
                hum,
                adc,
                co,
                pre,
            )
        )
        time.sleep(SAMPLE_S)
    print("# burn-in complete")


if __name__ == "__main__":
    run()

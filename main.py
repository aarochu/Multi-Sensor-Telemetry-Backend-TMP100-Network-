import argparse
from multi_tmpsensor import MultiTMPSensors
from tmpsensor import TMPSensor
from fake_tmpsensor import FakeTMPSensor
import smbus
import RPi.GPIO as GPIO
import time
from datetime import datetime
import csv

'''main.py --single --address 0x4f  main.py --single --fake  main.py --csv --rows 100 --outfile multi_tmp100_log.csv  main.py --single --fake --csv --rows 50 --outfile single_fake.csv'''
def main():

    TEMP_REG = 0x00
    CONFIG_REG = 0x01
    TLOW_REG = 0x10
    HIGH_REG = 0x11
    CHANNEL = 1

    parser = argparse.ArgumentParser()
    parser.add_argument("--address", type=lambda x: int(x, 0), default=0x4f, help="I2C address of sensor (e.g. 0x4f or 79)")
    parser.add_argument("--fake", action="store_true", help="Use fake sensors")
    parser.add_argument("--single", action="store_true", help="Run single TMPSensor + FakeTMPSensor instead of MultiTMPSensors")
    parser.add_argument("--multi", action="store_true", help="Run MultiTMPSensors instead of single TMPSensor + FakeTMPSensor")
    parser.add_argument("--csv", action="store_true", help="Save telemetry rows to CSV")
    parser.add_argument("--rows", type=int, default=100, help="How many rows to save in CSV mode")
    parser.add_argument("--outfile", default="multi_tmp100_log.csv", help="CSV output filename")
    parser.add_argument("--interval", type=float, default=1.0, help="Print/sample interval in seconds")
    args = parser.parse_args()
    ADDRESS = args.address

    if args.single:
        if not args.fake:
            bus = smbus.SMBus(CHANNEL)
            bus.write_byte_data(ADDRESS, CONFIG_REG, 0b1100000)
            testtmp = TMPSensor(addr=ADDRESS, bus=bus, reg=TEMP_REG, interval=0.5)
            testtmp.start()
        testfake = FakeTMPSensor(addr=0x00, reg=TEMP_REG, interval=0.5, baseline=70.0)
        testfake.start()
        rows = []
        try:
            while True:
                ts = datetime.now().isoformat()
                if not args.fake:
                    real_t = testtmp.get_latest()
                    fake_t = testfake.get_latest()
                    print("real:", real_t, "fake:", fake_t)
                    if args.csv:
                        rows.append({"timestamp": ts, "real": real_t, "fake": fake_t})
                else:
                    fake_t = testfake.get_latest()
                    print("fake:", fake_t)
                    if args.csv:
                        rows.append({"timestamp": ts, "fake": fake_t})
                if args.csv and len(rows) >= args.rows:
                    break
                time.sleep(args.interval)
        except KeyboardInterrupt:
            pass
        finally:
            if args.csv and rows:
                with open(args.outfile, "a", newline="") as f:
                    w = csv.DictWriter(f, fieldnames=rows[0].keys())
                    if f.tell() == 0:
                        w.writeheader()
                    w.writerows(rows)
                print("saved", len(rows), "rows to", args.outfile)
            if not args.fake:
                testtmp.stop()
                bus.close()
            testfake.stop()
    else:
       ## if not args.fake:
        ##    bus = smbus.SMBus(CHANNEL)
         ##   bus.write_byte_data(ADDRESS, CONFIG_REG, 0b1100000)
       ##     bus.close()
        m = MultiTMPSensors(use_fake=args.fake)
        m.start()
        rows = []
        try:
            while True:
                latest = m.get_latest()
                print(latest)
                if args.csv:
                    row = {"timestamp": datetime.now().isoformat()}
                    row.update(latest)
                    rows.append(row)
                    if len(rows) >= args.rows:
                        break
                time.sleep(args.interval)
        except KeyboardInterrupt:
            pass
        finally:
            if args.csv and rows:
                m.write_csv(rows, filename=args.outfile)
                print("saved", len(rows), "rows to", args.outfile)
            m.stop()


if __name__ == "__main__":
    main()

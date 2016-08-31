#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import graceful_exit
import psycopg2
import sys
import time

import logging
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
log_formatter = logging.Formatter("%(asctime)s: [%(levelname)s] %(message)s")
log_file_handler = logging.FileHandler(filename="send_temps.log", mode="w")
log_file_handler.setFormatter(log_formatter)
log_file_handler.setLevel(logging.INFO)
stderr_handler = logging.StreamHandler()
stderr_handler.setFormatter(log_formatter)
stderr_handler.setLevel(logging.WARNING)
logger.addHandler(log_file_handler)
logger.addHandler(stderr_handler)

IN_SENSOR = "28-xxxxxxxxxxxx"
OUT_SENSOR = "28-xxxxxxxxxxxx"
DB_NAME = "weatherman"
DB_USER = "weatherman"
UPDATE_INTERVAL = 599


def db_connect(name, user):
    try:
        conn = psycopg2.connect("dbname='{0}' user='{1}'".format(name, user))
        return conn
    except Exception as err:
        logger.critical("Could not connect to database: {0}".format(err))
        return False


def db_push(temps, db_conn):
    try:
        cur = db_conn.cursor()
        stamp = time.strftime("%Y-%m-%d %H:%M:%S")

        for sensor, temp in temps.items():
            if sensor == "in":
                cur.execute("INSERT INTO inside_temp VALUES('{0}', {1})"
                            .format(stamp, temp))
            if sensor == "out":
                cur.execute("INSERT INTO outside_temp VALUES('{0}', {1})"
                            .format(stamp, temp))
        db_conn.commit()
        cur.close()
    except Exception as err:
        logger.error("Could not push data to database: {0}".format(err))


def read_temps(sensor_files):
    temps = {}

    for sensor, sensor_file in sensor_files.items():
        try:
            handle = open("/sys/bus/w1/devices/{}/w1_slave"
                          .format(sensor_file), "r")
        except FileNotFoundError as err:
            logger.warning("Probe '{0}': {1}".format(sensor, err))
        else:
            cat = handle.read().split("\n")
            if cat[0].endswith("YES"):
                temps[sensor] = round(float(cat[1][-5:])/1000, 1)
            handle.close()

    return temps


def main():
    ge = graceful_exit.GracefulExit()
    db_conn = db_connect(DB_NAME, DB_USER)

    if not db_conn:
        sys.exit(1)

    logger.info("Started sending weather data.")
    while True:
        if ge.kill:
            break
        db_push(read_temps({"in": IN_SENSOR, "out": OUT_SENSOR}), db_conn)
        time.sleep(UPDATE_INTERVAL)

    db_conn.close()
    logger.info("Stopped sending weather data.")


if __name__ == "__main__":
    main()

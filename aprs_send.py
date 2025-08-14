# coding: utf-8
# aprs_send by N1k0droid\\IT9KVB update 14.08.25

import aprslib
import json
import configparser
from datetime import datetime
import sys
import os
import logging
import time
import shutil

CONFIG_FILE = "/config/aprs_config.ini"
DEFAULT_CONFIG_FILE = "/defaults/aprs_config.ini"
METEO_FILE = "/config/meteo.json"

def create_default_config():
    """
    Create default configuration file if it doesn't exist.
    If DEFAULT_CONFIG_FILE exists, copy it. Otherwise, generate hardcoded defaults.
    """
    if os.path.exists(CONFIG_FILE):
        return

    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)

    if os.path.exists(DEFAULT_CONFIG_FILE):
        print(f"[CONFIG] Copying default config from {DEFAULT_CONFIG_FILE}")
        shutil.copy(DEFAULT_CONFIG_FILE, CONFIG_FILE)
        return

    print(f"[CONFIG] Creating default config file: {CONFIG_FILE}")
    config = configparser.ConfigParser()
    config['APRS'] = {
        'callsign': 'NOCALL',
        'ssid': '13',
        'passcode': '00000',
        'server': 'euro.aprs2.net',
        'port': '14580',
        'comment_prefix': '',
        'comment': '',
        'comment_wx': 'Python APRS Weather Station',
        'test_message': 'TEST',
        'send_weather': 'no',
        'wx_format': 'text',
        'restore_icon': 'no',
        'symbol_table': '/',
        'symbol_code': '<'
    }
    config['Station'] = {
        'lat': '42.0000',
        'lon': '12.0000'
    }
    with open(CONFIG_FILE, 'w') as configfile:
        config.write(configfile)
    print("[CONFIG] Default configuration created.")

def read_config():
    """
    Load configuration, apply environment variable overrides, and save if modified.
    """
    create_default_config()

    config = configparser.ConfigParser()
    config.read(CONFIG_FILE)

    try:
        if 'APRS' not in config:
            raise configparser.NoSectionError('APRS')
        if 'Station' not in config:
            raise configparser.NoSectionError('Station')
    except configparser.NoSectionError as e:
        print(f"[CONFIG] Missing section: {e}")
        sys.exit(1)

    override_applied = False

    for key in config['APRS']:
        env_key = f"APRS_{key.upper()}"
        if env_key in os.environ:
            config['APRS'][key] = os.environ[env_key]
            print(f"[CONFIG] Override from ENV: {env_key}={os.environ[env_key]}")
            override_applied = True

    for key in config['Station']:
        env_key = f"STATION_{key.upper()}"
        if env_key in os.environ:
            config['Station'][key] = os.environ[env_key]
            print(f"[CONFIG] Override from ENV: {env_key}={os.environ[env_key]}")
            override_applied = True

    if override_applied:
        with open(CONFIG_FILE, 'w') as f:
            config.write(f)
        print("[CONFIG] Saved updated config with ENV overrides.")
    else:
        print("[CONFIG] No ENV overrides detected, using existing config unchanged.")

    try:
        callsign = config['APRS']['callsign'].strip()
        ssid = config['APRS'].get('ssid', '').strip()
        passcode = config['APRS']['passcode'].strip()
        server = config['APRS'].get('server', 'euro.aprs2.net').strip()
        port = int(config['APRS'].get('port', 14580))
        comment_prefix = config['APRS'].get('comment_prefix', '').strip()
        comment = config['APRS'].get('comment', '').strip() or f"73 de {callsign}"
        comment_wx = config['APRS'].get('comment_wx', '').strip() or "Weather Station"
        test_message = config['APRS'].get('test_message', '').strip() or "TEST"
        send_weather = config['APRS'].get('send_weather', 'yes').strip().lower()
        wx_format = config['APRS'].get('wx_format', 'text').strip().lower()
        restore_icon = config['APRS'].get('restore_icon', 'no').strip().lower()
        symbol_table = config['APRS'].get('symbol_table', '/').strip()
        symbol_code = config['APRS'].get('symbol_code', '<').strip()
        lat = float(config['Station']['lat'])
        lon = float(config['Station']['lon'])

        return {
            'callsign': callsign, 'ssid': ssid, 'passcode': passcode,
            'server': server, 'port': port, 'comment_prefix': comment_prefix,
            'comment': comment, 'comment_wx': comment_wx, 'test_message': test_message,
            'send_weather': send_weather, 'wx_format': wx_format, 'restore_icon': restore_icon,
            'symbol_table': symbol_table, 'symbol_code': symbol_code,
            'lat': lat, 'lon': lon
        }

    except (configparser.NoOptionError, KeyError, ValueError) as e:
        print(f"[CONFIG] Configuration file error: {e}")
        sys.exit(1)

def get_tocall(wx_format, is_test=False):
    return 'APRS' if is_test else 'APTKVB'

def aprs_coord(deg, is_lat=True):
    degrees = int(abs(deg))
    minutes = (abs(deg) - degrees) * 60
    hemi = 'N' if is_lat and deg >= 0 else 'S' if is_lat else 'E' if deg >= 0 else 'W'
    return f"{degrees:02d}{minutes:05.2f}{hemi}" if is_lat else f"{degrees:03d}{minutes:05.2f}{hemi}"

def format_wx_standard(meteo):
    parts = []
    wind_direction = int(round(meteo.get('wind_direction', 0))) % 360
    parts.append(f"c{wind_direction:03d}")
    wind_speed = int(round(meteo.get('wind_speed', 0) * 2.237))
    parts.append(f"s{wind_speed:03d}")
    wind_gust = int(round(meteo.get('wind_gust', 0) * 2.237))
    parts.append(f"g{wind_gust:03d}")
    if 'temperature' in meteo:
        temp_f = int(meteo['temperature'] * 9/5 + 32)
        parts.append(f"t{temp_f:03d}")
    rain_1h = int(round(meteo.get('rain_1h', 0) / 25.4 * 100))
    parts.append(f"r{rain_1h:03d}")
    rain_24h = int(round(meteo.get('rain_24h', 0) / 25.4 * 100))
    parts.append(f"p{rain_24h:03d}")
    parts.append(f"P{rain_24h:03d}")
    if 'humidity' in meteo:
        humidity = int(round(meteo['humidity']))
        if humidity == 100:
            humidity = 0
        parts.append(f"h{humidity:02d}")
    if 'pressure' in meteo:
        pressure = int(round(meteo['pressure'] * 10))
        parts.append(f"b{pressure:05d}")
    return "".join(parts)

def send_aprs_packet_raw(cfg, packet):
    callsign_full = cfg['callsign']
    if cfg['ssid']:
        try:
            n = int(cfg['ssid'])
            if 0 <= n <= 15:
                callsign_full = f"{cfg['callsign']}-{n}"
        except ValueError:
            pass
    try:
        ais = aprslib.IS(callsign_full, cfg['passcode'], host=cfg['server'], port=cfg['port'])
        ais.connect()
        ais.sendall(packet)
        ais.close()
        print("APRS packet sent:", packet)
        return True
    except Exception as e:
        print("APRS-IS error:", e)
        return False

def send_aprs_packet(cfg, meteo, is_test=False):
    callsign = cfg['callsign']
    ssid = cfg['ssid']
    comment_prefix = cfg['comment_prefix']
    comment = cfg['comment']
    comment_wx = cfg['comment_wx']
    test_message = cfg['test_message']
    send_weather = cfg['send_weather']
    wx_format = cfg['wx_format']
    restore_icon = cfg['restore_icon']
    symbol_table = cfg['symbol_table']
    symbol_code = cfg['symbol_code']
    lat = cfg['lat']
    lon = cfg['lon']

    callsign_full = callsign
    if ssid:
        try:
            n = int(ssid)
            if 0 <= n <= 15:
                callsign_full = f"{callsign}-{n}"
            else:
                print(f"SSID {ssid} out of range, ignored.")
        except ValueError:
            print(f"SSID '{ssid}' invalid, ignored.")

    tocall = get_tocall(wx_format, is_test)
    now = datetime.utcnow().strftime("%d%H%M")
    lat_aprs = aprs_coord(lat, True)
    lon_aprs = aprs_coord(lon, False)

    if is_test:
        msg = f"{comment_prefix} {test_message}" if comment_prefix else test_message
        packet = f"{callsign_full}>{tocall},TCPIP*:@{now}z{lat_aprs}{symbol_table}{lon_aprs}{symbol_code} {msg}"
        print(f"TEST mode active (TOCALL: {tocall})")
        send_aprs_packet_raw(cfg, packet)
        return

    if send_weather == 'yes' and wx_format == 'wx-text' and meteo:
        print(f"WX-TEXT mode active (TOCALL: {tocall})")
        comment_packet = f"{callsign_full}>{tocall},TCPIP*:@{now}z{lat_aprs}{symbol_table}{lon_aprs}{symbol_code} {comment_wx}"
        if send_aprs_packet_raw(cfg, comment_packet):
            print("Comment sent, waiting 15 seconds...")
            time.sleep(15)
            now = datetime.utcnow().strftime("%d%H%M")
            lat_aprs = aprs_coord(lat, True)
            lon_aprs = aprs_coord(lon, False)
            wx_data = format_wx_standard(meteo)
            wx_packet = f"{callsign_full}>{tocall},TCPIP*:@{now}z{lat_aprs}/{lon_aprs}_{wx_data}"
            print("Sending WX data...")
            if send_aprs_packet_raw(cfg, wx_packet) and restore_icon == 'yes':
                print("WX data sent, restoring icon...")
                time.sleep(15)
                now = datetime.utcnow().strftime("%d%H%M")
                restore_packet = f"{callsign_full}>{tocall},TCPIP*:@{now}z{lat_aprs}{symbol_table}{lon_aprs}{symbol_code}"
                send_aprs_packet_raw(cfg, restore_packet)
        return

    if send_weather == 'yes' and wx_format == 'wx' and meteo:
        now = datetime.utcnow().strftime("%d%H%M")
        lat_aprs = aprs_coord(lat, True)
        lon_aprs = aprs_coord(lon, False)
        wx_data = format_wx_standard(meteo)
        packet = f"{callsign_full}>{tocall},TCPIP*:@{now}z{lat_aprs}/{lon_aprs}_{wx_data}"
        print(f"WX station mode active (TOCALL: {tocall})")
        send_aprs_packet_raw(cfg, packet)
        return

    parts = []
    if send_weather == 'yes':
        if meteo:
            if 'temperature' in meteo: parts.append(f"Temp: {meteo['temperature']:.1f}C")
            if 'dewpoint' in meteo: parts.append(f"DewPt: {meteo['dewpoint']:.1f}C")
            if 'humidity' in meteo: parts.append(f"Hum: {int(round(meteo['humidity']))}%")
            if 'pressure' in meteo: parts.append(f"Press: {meteo['pressure']:.1f}hPa")
            if 'wind_speed' in meteo: parts.append(f"WindSpd: {meteo['wind_speed']:.1f}m/s")
            if 'wind_direction' in meteo: parts.append(f"WindDir: {meteo['wind_direction']}")
            if 'wind_gust' in meteo: parts.append(f"WindGust: {meteo['wind_gust']:.1f}m/s")
            if 'rain_1h' in meteo: parts.append(f"Rain1h: {meteo['rain_1h']:.1f}mm")
            if 'rain_24h' in meteo: parts.append(f"Rain24h: {meteo['rain_24h']:.1f}mm")
            known = {'temperature','dewpoint','humidity','pressure',
                     'wind_speed','wind_direction','wind_gust','rain_1h','rain_24h'}
            for k, v in meteo.items():
                if k not in known and isinstance(v, (int, float)):
                    parts.append(f"{k.title()}: {v:.1f}" if isinstance(v, float) else f"{k.title()}: {v}")
    msg = " ".join(parts) if parts else comment
    if comment_prefix:
        msg = f"{comment_prefix} {msg}"
    packet = f"{callsign_full}>{tocall},TCPIP*:@{now}z{lat_aprs}{symbol_table}{lon_aprs}{symbol_code} {msg}"
    send_aprs_packet_raw(cfg, packet)

def main():
    cfg = read_config()
    is_test = '--test' in sys.argv
    debug = '--debug' in sys.argv
    logging.basicConfig(level=logging.DEBUG if debug else logging.INFO)
    if debug:
        print("DEBUG mode active")
    if os.path.exists(METEO_FILE):
        with open(METEO_FILE) as f:
            meteo = json.load(f)
        print(f"Weather file loaded: {len(meteo)} parameters")
    else:
        meteo = {}
        print("Weather file not found - using empty data")
    send_aprs_packet(cfg, meteo, is_test=is_test)

if __name__ == "__main__":
    main()

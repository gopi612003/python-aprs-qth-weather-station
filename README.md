# Python APRS QTH Weather Station

Small Python Docker container to send APRS QTH position or weather data.  
It receives weather measurements via HTTP requests (GET or POST) from any device capable of sending data over the network, then forwards them to APRS-IS (e.g., APRS.fi) in APRS/WX format.  
Ideal for amateur radio operators as an APRS client or automatic weather station.

---

## Features

- **QTH Position Update** — Send your station's position to APRS-IS.
- **Automatic Weather Station** — Transmit weather data received via HTTP to APRS.
- **HTTP GET/POST Data Input** — Accepts JSON or URL-parameter formatted data.
- **Multiple APRS Modes**:
  - **TEXT**: Human-readable weather comment.
  - **WX**: APRS weather packet format with standard WX symbols.
  - **WX-TEXT**: Text comment followed by WX packet (optional icon restore).
  - **TEST**: Send test packets for diagnostics.
- **Configurable** — All parameters via `aprs_config.ini` or ENV variables (ENV has priority).
- **Dockerized** — Portable, isolated environment.
- **Status & Health Endpoints** via HTTP.

---

## Installation

### Requirements
- [Docker](https://docs.docker.com/get-docker/) installed.
- APRS Passcode (see section *How to Obtain Your APRS Passcode*).

---

## Prepare the Configuration

You can configure the container in three ways:

1. **File only** (included in image):  
   Prepare `aprs_config.ini` in the repo before build — it will be included in `/defaults` and `/config` inside the image.

2. **File + Persistent Volume** (**recommended**):  
   Mount a host directory to `/config` — if `aprs_config.ini` is absent, it will be copied from `/defaults`.

3. **File + ENV Variables override**:  
   Pass any supported ENV variable (see *Environment Variables*).  
   ENV values always take priority and are written to the `.ini` file in use.

---

## Configuration File (`aprs_config.ini`)

Complete parameter list (defaults in build or generated if missing):

| Section     | Key            | Description | Allowed Values / Examples | Default |
|-------------|---------------|-------------|---------------------------|---------|
| `[APRS]`    | `callsign`     | Your amateur radio callsign (without SSID) | Example: `IT9KVB` | `NOCALL` |
| `[APRS]`    | `ssid`         | SSID (station identifier) | `0`-`15` | `13` |
| `[APRS]`    | `passcode`     | APRS-IS passcode | numeric | `00000` |
| `[APRS]`    | `server`       | APRS-IS server address | hostname | `euro.aprs2.net` |
| `[APRS]`    | `port`         | APRS-IS port | integer | `14580` |
| `[APRS]`    | `comment_prefix` | Optional prefix for comments | string | *(empty)* |
| `[APRS]`    | `comment`      | Comment text for TEXT mode | string | *(empty)* If you leave it blank, it will always be the default: `73 de` your `callsign` |
| `[APRS]`    | `comment_wx`   | Comment before WX packet in wx-text mode | string | `Python APRS Weather Station` |
| `[APRS]`    | `test_message` | Message in TEST mode | string | `TEST` |
| `[APRS]`    | `send_weather` | Enable/disable WX sending | `yes` / `no` | `yes` |
| `[APRS]`    | `wx_format`    | Weather mode | `text`, `wx`, `wx-text` | `text` |
| `[APRS]`    | `restore_icon` | Restore icon in wx-text mode | `yes` / `no` | `no` |
| `[APRS]`    | `symbol_table` | Symbol table code | `/` or `\` | `/` |
| `[APRS]`    | `symbol_code`  | Symbol code | e.g. `<`, `_`, `>` | `<` |
| `[Station]` | `lat`          | Latitude (decimal degrees, dot) | -90 to 90 | `42.0000` |
| `[Station]` | `lon`          | Longitude (decimal degrees, dot) | -180 to 180 | `12.0000` |

---

## Build & Run Docker

### Steps to build image

1. Clone the repository and enter in the subfolder:
<pre>
git clone https://github.com/N1k0droid/python-aprs-qth-weather-station.git

cd python-aprs-qth-weather-station</pre>

2. Copy the example configuration:
<pre>cp aprs_config.ini.example aprs_config.ini</pre>

3. Edit `aprs_config.ini` to set your callsign, passcode, location, and settings.

4. Build the docker image:
<pre>docker build -t aprs-weather-station </pre>

### Run without persistent configuration
Uses `aprs_config.ini` included in the image (modified ENV values are not persisted after container removal):
<pre>docker run -d
--name aprs-weather-station
-p 5000:5000
aprs-weather-station </pre>

### Run with persistent configuration (**recommended**)
<pre>docker run -d
--name aprs-weather-station
-p 5000:5000
-v your-own-path/config:/config
aprs-weather-station</pre>

### Run with Environment Variables (INI overrides)

You can pass environment variables to the container to **override the values** in the active `/config/aprs_config.ini`.  
Overrides are **also saved** in the `.ini` file so they persist if you are using a mapped volume.

- **Without volume:** overrides are applied for the session only and are lost when the container is removed.
- **With volume:** overrides are saved inside the INI in `/config` and persist across restarts.

#### Full example (ENV + persistent volume)
<pre>docker run -d
--name aprs-weather-station
-p 5000:5000
-v your-own-path/config:/config
-e APRS_CALLSIGN=NOCALL
-e APRS_SSID=13
-e APRS_PASSCODE=12345
-e APRS_SERVER=euro.aprs2.net
-e APRS_PORT=14580
-e APRS_COMMENT_PREFIX=QTH
-e APRS_COMMENT="Python APRS Weather Station"
-e APRS_COMMENT_WX="WX Beacon"
-e APRS_TEST_MESSAGE="TEST"
-e APRS_SEND_WEATHER=yes
-e APRS_WX_FORMAT=wx-text
-e APRS_RESTORE_ICON=yes
-e APRS_SYMBOL_TABLE=/
-e APRS_SYMBOL_CODE="<"
-e STATION_LAT=37.499
-e STATION_LON=15.083
-e APRS_AUTO_ENABLED=on
-e APRS_UPDATE_INTERVAL=900
-e APRS_DEBUG=yes
aprs-weather-station</pre>

Behavior:
- If INI is missing on volume → copied from `/defaults` (image default)
- If ENV variables provided → values override INI and are written back to the file
- Config changes persist across restarts

---

## How to Obtain Your APRS Passcode

Generate it online with the **APRS Passcode Generator**:  🔗 [https://apps.magicbug.co.uk/passcode/](https://apps.magicbug.co.uk/passcode/)  

Enter your **callsign without SSID** — use result in `aprs_config.ini`:

---

## Runtime daemon controls (not saved to .INI)

| Variable               | Description                              | Values       | Default |
|------------------------|------------------------------------------|--------------|---------|
| `APRS_AUTO_ENABLED`    | Enable/disable automatic APRS send       | `on` / `off` | `off`   |
| `APRS_UPDATE_INTERVAL` | Interval (seconds) for auto send         | integer      | `3600`  |
| `APRS_DEBUG`           | Enable debug logs                        | `yes` / `no` | `yes`   |

> **Note:**  
> If `APRS_AUTO_ENABLED` is `off` (default), the station will **not send any APRS data automatically**.  
> To send data you must trigger it manually from the command line inside the container.

**Example run with automatic APRS enabled (every 15 min):**
<pre>docker run -d
--name aprs-weather-station
-p 5000:5000
-e APRS_AUTO_ENABLED=on
-e APRS_UPDATE_INTERVAL=900
-e APRS_DEBUG=yes
aprs-weather-station</pre>

**Manual send example (auto APRS disabled):**
Start container without auto APRS
<pre>docker run -d
--name aprs-weather-station
-p 5000:5000
aprs-weather-station</pre>

Manually send current data (reads /config/aprs_config.ini and /config/meteo.json)
<pre>docker exec -it aprs-weather-station python3 /app/aprs_send.py</pre>

**Send a test packet (does not require weather data):**
<pre>docker exec -it aprs-weather-station python3 /app/aprs_send.py --test</pre>

---

## Sending Weather Data

### Supported parameters
| Name            | Unit     | Range              | Description |
|-----------------|----------|--------------------|-------------|
| temperature     | °C       | -50..70            | Air temp |
| humidity        | %        | 0..100             | Relative humidity |
| pressure        | hPa      | 800..1200          | Atmospheric pressure |
| wind_speed      | m/s      | 0..100             | Wind speed |
| wind_direction  | degrees  | 0..360             | Wind dir |
| wind_gust       | m/s      | 0..150             | Max gust |
| rain_1h         | mm       | 0..200             | Rain in 1h |
| rain_24h        | mm       | 0..1000            | Rain in 24h |
| dewpoint        | °C       | -60..50            | Dew point |

**Notes:** unknown numeric params accepted, out-of-range → rejected.

---
## Examples:
> 💡 **Note:** In the example commands, replace `localhost` with the IP address or hostname of the server running the Docker container if the command is executed from a remote client.

### GET examples
Full sample
<pre>curl "http://localhost:5000/meteo?temperature=22.5&humidity=65.8&pressure=1013.2&wind_speed=5.4&wind_direction=210&wind_gust=8.2&rain_1h=0.0&rain_24h=2.5&dewpoint=12.3" </pre>

Minimal sample
<pre>curl "http://localhost:5000/meteo?temperature=22,5&humidity=65" </pre>

### POST examples (JSON)
Full sample
<pre>curl -X POST -H "Content-Type: application/json"
-d '{
"temperature": 22.5,
"humidity": 65.8,
"pressure": 1013.2,
"wind_speed": 5.4,
"wind_direction": 210,
"wind_gust": 8.2,
"rain_1h": 0.0,
"rain_24h": 2.5,
"dewpoint": 12.3
}'
http://localhost:5000/meteo </pre>

Minimal sample

<pre>curl -X POST -H "Content-Type: application/json"
-d '{"temperature": "22,5", "pressure": "1013,2"}'
http://localhost:5000/meteo </pre>

### Decimal formats
- Dot (`.`) and comma (`,`) are both accepted and auto-converted.

---

## Manual Tests & Health

**Send APRS test packet:**
<pre>docker exec -it aprs-weather-station python3 /app/aprs_send.py --test</pre>

**Health check:**
<pre>curl http://localhost:5000/health </pre>

**Status (last data & uptime):**
<pre>curl http://localhost:5000/status </pre>

---

## License

MIT License — see the [LICENSE](LICENSE) file.  
Third-party:
- Flask (BSD 3-Clause)
- aprslib (GPL-2.0) — if redistributing with aprslib, comply with GPLv2 by providing source code.

---

## Credits

Developed by an amateur radio operator for the ham community.  

## Contributing

Contributions, bug reports, and feature requests are welcome!


**73 de IT9KVB**

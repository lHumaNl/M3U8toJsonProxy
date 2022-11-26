# M3U8toJsonProxy

This utility is a web server that parses IPTV(m3u8) and EPG playlists and returns a JSON response.

## Utility Features

1. Substring video stream link by regEx
2. Formatting JSON response from template
3. Get EPG list from now or for the whole period
4. Update data for playlist and EPG by scheduler (`!WIP!`)
5. Mocking responses by request path

## Console arguments

Arg | Required | Default value | Description
-|-|-|-
`--util_port` | False | 9120 | Port on which the proxy web server will start
`--m3u8_config` | False | `m3u8_config.json` | File name with M3U8 configs. File must be placed in `config` folder
near `main.py`
`--epg_config` | False | `epg_config.json` | File name with EPG configs. File must be placed in `config` folder
near `main.py`
`--mock_config` | False | `mock_config.json` | File name with MOCK configs. File must be placed in `config` folder
near `main.py`

## Instruction for JSON config file

First of all, you need to create `config` folder near `main.py` file.
Then create inside this folder blank new file. Strongly recommended to create file with name `m3u8_config.json` for M3U8
config,
`epg_config.json` for EPG config and `mock_config.json` for MOCK config because in the future it is not
expected to enter a console arguments `--m3u8_config`, `--epg_config` and `--mock_config`.

### M3U8 JSON config keys

Key | Required | Default value | Type | Description | Example
-|-|-|-|-|-
`link` | True | Null | String | Link to m3u8 playlist | `"link": "https://<host>/****.m3u8"`
`regex_endpoint` | True | Null | String | Endpoint(regEx) for taking json response with channels data
| `"regex_endpoint": "/tvPL"`
`regex_source_substring` | False | Null | String | Search string in video stream link by regEx and replace with custom
string | `"regex_source_substring": {"\\?q=\\d*": ""}`
`update_schedule` | False | Null | JsonArray\[String] | Playlist update scheduler. Time format: HH:MM
| `"update_schedule": ["08:30", "23:30"]`
`template_channels` | True | Null | JsonObject{String(`template key`): String(`name of channel data to replace`)} |
Template for channel data list. Contains `template key` and `name of channel data to replace`. Channel name keys in
table `Channel keys`
| `"template_channels": {"group": "group", "id": "id", "name": "name", "picture": "logo_url", "video": "stream_url"}`
`template_group` | False | Null | JsonObject{String(`template key`): String(`name of group data to replace`)} | Template
for group data list. Contains `template key` and `name of group data to replace`. Group name keys in table `Group keys`
| `"template_group": {"count": "count", "name": "group"}`
`template` | False | Null | JsonObject{AnyType} | General template for response. Must have a key
value `template_channels` to replace it with Json channel data list and (`optional`) `template_group` to replace it with
Json group data list | `"template": {"channels": "template_channels", "groups": "template_group"}`

#### Channel keys

Channel key | Description
-|-
group | Channel group name
id | Channel ID
name | Channel name
logo_url | Link to logo
stream_url | Link to video stream

#### Group keys

Group key | Description
-|-
group | Group name
count | Count channels in group

#### M3U8 JSON config Example

```
{
  "link": "http://10.10.0.21:34300/playlist.m3u8",
  "regex_endpoint": "/tvPL",
  "regex_source_substring": {
    "\\?q=\\d*": ""
  },
  "update_schedule": [
    "08:00"
  ],
  "template_channels": {
    "group": "group",
    "id": "id",
    "name": "name",
    "picture": "logo_url",
    "video": "stream_url"
  },
  "template_group": {
    "count": "count",
    "name": "group"
  },
  "template": {
    "channels": "template_channels",
    "groups": "template_group"
  }
}
```

### EPG JSON config keys

Key | Required | Default value | Type | Description | Example
-|-|-|-|-|-
`link` | False | Null | String | Link to EPG. Not required if the link is in the playlist or if it doesn't need
| `"link": "https://<host>/****.epg.xml.gz"`
`regex_endpoint` | True | Null | String | Endpoint(regEx) for taking json response with program data
| `"regex_endpoint": "/EPG"`
`path_channel_regex` | False | Null | String | RegEx for taking channel name\channel id from request path
| `"path_channel_regex": "/api/iptv/program/(\\d*)/\\d*"`
`post_param_key` | False | Null | String | Key for taking channel name\channel id from body POST param
| `"post_param_key": "name""`
`update_schedule` | False | Null | JsonArray\[String] | Playlist update scheduler. Time format: HH:MM
| `"update_schedule": ["08:30", "23:30"]`
`is_program_from_now` | False | False | Boolean | Return program list from now | `"is_program_from_now": true`
`template_program` | True | Null | JsonObject{String(`template key`): String(`name of program data to replace`)} |
Template for program data list. Contains `template key` and `name of program data to replace`. Program name keys in
table `Program keys`
| `"template_channels": {"group": "group", "id": "id", "name": "name", "picture": "logo_url", "video": "stream_url"}`
`template` | False | Null | JsonObject{AnyType} | General template for response. Must have a key
value `template_program` to replace it with Json program data list | `"template": {"epg_data": "template_program"}`

#### Program keys

Program key | Description
-|-
group | Group name
channel | Channel name
tvg | TVG ID
start | Program start time(timestamp)
stop | Program end time(timestamp)
title | Program title
description | Program description

#### EPG JSON config Example

```
{
  "link": "http://10.10.0.21:34300/epg.xml.gz",
  "regex_endpoint": "/EPG",
  "post_param_key": "name",
  "is_program_from_now": true,
  "update_schedule": [
    "08:30",
    "23:30"
  ],
  "template_program": {
    "descr": "description",
    "name": "title",
    "time": "start",
    "time_to": "stop"
  },
  "template": {
    "epg_data": "template_program"
  }
}
```

### Mock JSON config keys

Yoy may create this config for mocking some responses if it needed. Json config consists of an `endpoint(regEx)` that
needs to be mocked and `template` for response.

#### Mock JSON config Example

```
{
  "/api/iptv/list": {
    "secuses": true,
    "list": [
      {
        "id": 1,
        "cid": 1,
        "url": "",
        "name": "",
        "status": 1,
        "profiles": ""
      }
    ]
  }
}
```

## Installation using Docker

1. Build image `docker build -t m3u8-to-json-proxy .`
2. Run container ```docker run -d
   --restart always
   -p 9120:9120
   -v <path-to-config-folder>:/app/config
   -it
   --name m3u8-to-json-proxy
   m3u8-to-json-proxy```
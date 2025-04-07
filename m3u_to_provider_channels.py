import requests
import json
import re
import sys
from urllib.parse import urlparse


def download_m3u(url):
    """Download M3U content from URL."""
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"Error downloading M3U file: {e}")
        sys.exit(1)


def parse_m3u(content):
    """Parse M3U content and extract channel information."""
    channels = []
    lines = content.strip().split('\n')

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Skip header or empty lines
        if line.startswith("#EXTM3U") or not line:
            i += 1
            continue

        # Look for EXTINF line
        if line.startswith('#EXTINF:'):
            tvg_id = re.search(r'tvg-id="([^"]*)"', line)
            tvg_name = re.search(r'tvg-name="([^"]*)"', line)
            tvg_logo = re.search(r'tvg-logo="([^"]*)"', line)
            tvg_group = re.search(r'group-title="([^"]*)"', line)

            chars_to_replace = [' ', ',', '.', '!', '-', '(', ')']
            # 转义特殊字符并构建正则模式
            pattern = '[{}]'.format(re.escape(''.join(chars_to_replace)))

            # Get URL from next line
            i += 1
            if i < len(lines):
                url = lines[i].strip()

                channel = {
                    'id': tvg_id.group(1) if tvg_id else "",
                    'name': re.sub(pattern, '', tvg_name.group(1)) if tvg_name else "",
                    'logo': tvg_logo.group(1) if tvg_logo else "",
                    'url': url,
                    'group': tvg_group.group(1) if tvg_group else "Ungrouped",
                }
                channels.append(channel)
        i += 1

    return channels


def create_channel_object(channel):
    """Create channel object in the required format."""
    return {
        "Name": f"{channel['group']} - {channel['name']}",
        "Id": channel['id'],
        "LogoUrl": channel['logo'],
        "IsEvent": False,
        "RecordEvent": False,
        "Start": 0,
        "End": 0,
        "Mode": "live",
        "RunningMode": "internalremuxer",
        "OutputMode": "directhls",
        "Proxy": "",
        "Bind": "",
        "Doh": "",
        "NetworkScope": "script,manifest,media",
        "OnDemand": True,
        "Autostart": False,
        "PipeOutputParams": "",
        "ProtoOutputParams": "",
        "SessionManifest": False,
        "SpeedUp": True,
        "UseCdm": False,
        "Cdm": "",
        "CdmType": "widevine",
        "CdmMode": "internal",
        "PRLAVersion": "",
        "PRClientVersion": "",
        "PRCustomData": "",
        "NetworkOverride": False,
        "ModeOverride": False,
        "IgnoreUpdate": False,
        "FixIvSize": False,
        "TimeRange": False,
        "ManifestScript": "",
        "Manifest": channel['url'],
        "ManifestType": "",
        "ManifestInfo": "",
        "Video": "best",
        "Audio": "",
        "Subtitles": "",
        "VideoList": None,
        "AudioList": None,
        "SubtitlesList": None,
        "Keys": None,
        "Drm": {
            "Vendor": None
        },
        "RangeStartTime": "",
        "RangeEndTime": "",
        "Heartbeat": {
            "Url": "",
            "Params": "",
            "PeriodMs": 0,
            "RandomMs": 0
        },
        "Headers": {
            "Manifest": None,
            "Media": None
        }
    }


def create_provider_object(name, channels):
    """Create provider object with channels."""
    return {
        "Name": name,
        "Id": name,
        "RunningMode": "internalremuxer",
        "OutputMode": "directhls",
        "Script": "",
        "LogoUrl": "",
        "Proxy": "",
        "Bind": "",
        "Doh": "",
        "NetworkScope": "script,manifest,media",
        "UserAgent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36 Edg/134.0.0.0",
        "XForwardedFor": "",
        "EventsAutorefresh": False,
        "EventsAutoremove": False,
        "ChannelsAutoremove": False,
        "MaxConcurrentStreams": 0,
        "LastEventIndex": 0,
        "AlwaysResetSession": False,
        "RestartDelay": 30,
        "PipeOutputCmdFormated": "tsplay -pace-pcr2-pmt -stdin %s",
        "NbAnnouncedFragments": 0,
        "HlsFragmentsDuration": 0,
        "PlaylistDuration": 15,
        "AutorestartPeriod": 0,
        "NoRestartOnError": False,
        "RestartFinished": False,
        "NoRestartOnTrackChange": False,
        "PlaybackDelay": 0,
        "RandomAutostartPeriod": 0,
        "SequencialAutostartPeriod": 0,
        "EpgTimezone": "",
        "ReuseEventIndex": False,
        "EventsRefreshPeriod": 3600,
        "HttpGetRetries": 2,
        "NoWaitFullPlaylist": False,
        "ContinuousPlayback": False,
        "IgnoreStaticDash": False,
        "UseDashDelay": False,
        "StallDetectTimeout": 60,
        "Headers": None,
        "VmxUniqueId": "",
        "Channels": channels
    }


def m3u_to_provider_channels(m3u_url, provider_name, output_file=None):
    """Convert M3U to provider channels JSON format."""
    # Download M3U content
    content = download_m3u(m3u_url)

    # Parse M3U content
    channels = parse_m3u(content)

    # Transform channels to required format
    provider_channels = [create_channel_object(channel) for channel in channels]

    # Create provider object
    provider = create_provider_object(provider_name, provider_channels)

    # Output JSON
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(provider, f, ensure_ascii=False, indent=4)
        print(f"Output saved to {output_file}")
    else:
        print(json.dumps(provider, ensure_ascii=False, indent=4))


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python m3u_to_provider_channels.py <m3u_url> <provider_name> [output_file]")
        sys.exit(1)

    m3u_url = sys.argv[1]
    provider_name = sys.argv[2]
    output_file = sys.argv[3] if len(sys.argv) > 3 else None

    m3u_to_provider_channels(m3u_url, provider_name, output_file)
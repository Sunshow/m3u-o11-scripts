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


def parse_mytvsuper_m3u(content):
    """Parse MyTV Super M3U content and extract channel information."""
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

            channel = {
                'id': tvg_id.group(1) if tvg_id else "",
                'name': tvg_name.group(1) if tvg_name else "",
                'logo': tvg_logo.group(1) if tvg_logo else "",
                'manifest_type': "",
                'license_type': "",
                'license_key': "",
                'url': ""
            }

            # Move to next line
            i += 1

            # Look for KODIPROP lines
            while i < len(lines) and lines[i].startswith('#KODIPROP:'):
                kodiprop_line = lines[i]

                if 'inputstream.adaptive.manifest_type=' in kodiprop_line:
                    manifest_type = kodiprop_line.split('=')[1].strip()
                    channel['manifest_type'] = manifest_type

                if 'inputstream.adaptive.license_type=' in kodiprop_line:
                    license_type = kodiprop_line.split('=')[1].strip()
                    channel['license_type'] = license_type

                if 'inputstream.adaptive.license_key=' in kodiprop_line:
                    license_key = kodiprop_line.split('=')[1].strip()
                    channel['license_key'] = license_key

                i += 1

            # Get URL from current line
            if i < len(lines) and not lines[i].startswith('#'):
                channel['url'] = lines[i].strip()
                channels.append(channel)
                i += 1
            else:
                # No URL found, skip this channel
                i += 1
        else:
            i += 1

    return channels


def create_mytvsuper_channel_object(channel):
    """Create channel object in the required format for MyTV Super."""
    # Determine manifest type
    manifest_type = ""
    if channel.get('manifest_type') == "mpd":
        manifest_type = "dash"

    # Set keys from license_key if available
    keys = []
    if channel.get('license_key'):
        keys.append(channel['license_key'])

    # Create video, audio, and subtitles lists for dash streams
    video_list = None
    audio_list = None
    subtitles_list = None

    if manifest_type == "dash":
        # Extract the KID from the license key if available
        kid = ""
        if channel.get('license_key'):
            kid = channel['license_key'].split(':')[0]

        video_list = [
            {
                "Id": "v15000000_33",
                "Desc": "2160p50 (hev1.2.4.L153.b0, 14648Kb/s)",
                "Kid": kid
            }
        ]

        audio_list = [
            {
                "Id": "au1_345",
                "Desc": "au1 (mp4a.40.2, 48Khz, 125Kb/s)",
                "Kid": kid
            },
            {
                "Id": "au2_355",
                "Desc": "au2 (mp4a.40.2, 48Khz, 125Kb/s)",
                "Kid": kid
            }
        ]

        subtitles_list = [
            {
                "Id": "s10000_chi",
                "Desc": "chi",
                "Kid": ""
            },
            {
                "Id": "s10000_chs",
                "Desc": "chs",
                "Kid": ""
            },
            {
                "Id": "s10000_eng",
                "Desc": "eng",
                "Kid": ""
            }
        ]

    # Create manifest info
    manifest_info = ""
    if manifest_type == "dash":
        manifest_info = "Format: <i><b>dash (live)</b></i><br>Best video: <i><b>2160p50</b></i><br>Duration: <i><b>2h59m52s</b></i><br>\nDRM: <i><b>widevine playready </b></i><br>"

    return {
        "Name": channel['name'],
        "Id": channel['name'],
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
        "SpeedUp": True if manifest_type == "dash" else False,
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
        "ManifestType": manifest_type,
        "ManifestInfo": manifest_info,
        "Video": "best",
        "Audio": "au1_345" if manifest_type == "dash" else "",
        "Subtitles": "",
        "VideoList": video_list,
        "AudioList": audio_list,
        "SubtitlesList": subtitles_list,
        "Keys": keys if keys else None,
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
        "UserAgent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36",
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
    """Convert MyTV Super M3U to provider channels JSON format."""
    # Download M3U content
    content = download_m3u(m3u_url)

    # Parse M3U content
    channels = parse_mytvsuper_m3u(content)

    # Transform channels to required format
    provider_channels = [create_mytvsuper_channel_object(channel) for channel in channels]

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
        print("Usage: python m3u_to_provider_channels_mytvsuper.py <m3u_url> <provider_name> [output_file]")
        sys.exit(1)

    m3u_url = sys.argv[1]
    provider_name = sys.argv[2]
    output_file = sys.argv[3] if len(sys.argv) > 3 else None

    m3u_to_provider_channels(m3u_url, provider_name, output_file)
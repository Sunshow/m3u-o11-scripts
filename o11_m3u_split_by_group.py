import sys
import os
import re


def read_m3u_file(filepath):
    """Read M3U file content."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except UnicodeDecodeError:
        try:
            with open(filepath, 'r', encoding='latin-1') as f:
                return f.read()
        except Exception as e:
            print(f"Error reading M3U file: {e}")
            sys.exit(1)
    except Exception as e:
        print(f"Error reading M3U file: {e}")
        sys.exit(1)


def extract_channel_info(extinf_line, url):
    """Extract provider and reformat channel info."""
    # Extract provider
    provider_match = re.search(r'provider="([^"]*)"', extinf_line)
    provider = provider_match.group(1) if provider_match else "unknown"

    # Extract channel name
    channel_match = re.search(r',(.*?)$', extinf_line)
    if channel_match:
        full_name = channel_match.group(1).strip()

        # Remove provider prefix (e.g., "[hami] ")
        clean_name = re.sub(r'^\[.*?\]\s*', '', full_name)

        # Extract new group and channel name
        if ' - ' in clean_name:
            new_group, channel_name = clean_name.split(' - ', 1)
            new_group = new_group.strip()
            channel_name = channel_name.strip()
        else:
            new_group = "Ungrouped"
            channel_name = clean_name

        # Create new EXTINF line with modified group-title
        new_extinf = extinf_line.split(',', 1)[0]  # Keep all tags
        new_extinf = re.sub(r'group-title="[^"]*"', f'group-title="{new_group}"', new_extinf)
        new_extinf += f',{channel_name}'
    else:
        new_extinf = extinf_line
        provider = "unknown"

    return provider, new_extinf, url


def parse_m3u_by_provider(content):
    """Parse M3U content and organize channels by provider."""
    providers = {}
    lines = content.strip().split('\n')

    header = None
    if lines and lines[0].startswith('#EXTM3U'):
        header = lines[0]
        lines = lines[1:]

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        if not line:
            i += 1
            continue

        if line.startswith('#EXTINF:'):
            i += 1
            if i < len(lines):
                url = lines[i].strip()

                if not url or url.startswith('#'):
                    i += 1
                    continue

                provider, new_extinf, url = extract_channel_info(line, url)

                if provider not in providers:
                    providers[provider] = []

                providers[provider].append((new_extinf, url))
        i += 1

    return header, providers


def sanitize_filename(name):
    """Convert a string to a valid filename."""
    sanitized = re.sub(r'[\\/*?:"<>|]', '_', name)
    sanitized = sanitized.strip('. ')
    if not sanitized:
        sanitized = "unknown"
    return sanitized


def write_provider_m3u_files(header, providers, output_dir='.'):
    """Write separate M3U files for each provider."""
    os.makedirs(output_dir, exist_ok=True)
    provider_counts = {}

    for provider, channels in providers.items():
        safe_provider_name = sanitize_filename(provider)
        output_path = os.path.join(output_dir, f"{safe_provider_name}.m3u")

        with open(output_path, 'w', encoding='utf-8') as f:
            if header:
                f.write(f"{header}\n")
            else:
                f.write("#EXTM3U\n")

            for extinf, url in channels:
                f.write(f"{extinf}\n{url}\n")

        provider_counts[safe_provider_name] = len(channels)
        print(f"Created {output_path} with {len(channels)} channels")

    return provider_counts


def main():
    if len(sys.argv) != 2:
        print("Usage: python o11_m3u_split_by_provider.py <input_m3u_file>")
        sys.exit(1)

    input_file = sys.argv[1]
    content = read_m3u_file(input_file)

    header, providers = parse_m3u_by_provider(content)
    output_dir = "output"

    header = f'#EXTM3U\n#EXTM3U x-tvg-url="https://assets.livednow.com/epg.xml"\n'

    provider_counts = write_provider_m3u_files(header, providers, output_dir)

    total_channels = sum(provider_counts.values())
    print(f"\nSummary:")
    print(f"Total providers: {len(providers)}")
    print(f"Total channels: {total_channels}")

    print("\nChannels per provider:")
    for provider, count in sorted(provider_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {provider}: {count} channels")

    print(f"\nOutput directory: {output_dir}")


if __name__ == "__main__":
    main()
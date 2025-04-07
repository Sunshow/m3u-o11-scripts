import sys
import os
import re


def read_m3u_file(filepath):
    """Read M3U file content."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except UnicodeDecodeError:
        # Try another common encoding
        try:
            with open(filepath, 'r', encoding='latin-1') as f:
                return f.read()
        except Exception as e:
            print(f"Error reading M3U file: {e}")
            sys.exit(1)
    except Exception as e:
        print(f"Error reading M3U file: {e}")
        sys.exit(1)


def parse_m3u_by_group(content):
    """Parse M3U content and organize channels by group."""
    groups = {}
    lines = content.strip().split('\n')

    header = None
    # Check for header line
    if lines and lines[0].startswith('#EXTM3U'):
        header = lines[0]
        lines = lines[1:]

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Skip empty lines
        if not line:
            i += 1
            continue

        # Look for EXTINF line
        if line.startswith('#EXTINF:'):
            # Extract group-title
            group_match = re.search(r'group-title="([^"]*)"', line)
            group = group_match.group(1) if group_match else "Ungrouped"

            # Get URL from next line
            i += 1
            if i < len(lines):
                url = lines[i].strip()

                # Skip if URL is empty or another EXTINF
                if not url or url.startswith('#'):
                    i += 1
                    continue

                # Add channel to group
                if group not in groups:
                    groups[group] = []

                groups[group].append((line, url))
        i += 1

    return header, groups


def sanitize_filename(name):
    """Convert a string to a valid filename."""
    # Replace invalid file characters
    sanitized = re.sub(r'[\\/*?:"<>|]', '_', name)
    # Remove leading/trailing spaces and dots
    sanitized = sanitized.strip('. ')
    # Use "Ungrouped" if the name becomes empty
    if not sanitized:
        sanitized = "Ungrouped"
    return sanitized


def write_group_m3u_files(header, groups, output_dir='.'):
    """Write separate M3U files for each group."""
    os.makedirs(output_dir, exist_ok=True)

    group_counts = {}

    for group, channels in groups.items():
        # Create a valid filename
        safe_group_name = sanitize_filename(group)

        output_path = os.path.join(output_dir, f"{safe_group_name}.m3u")

        with open(output_path, 'w', encoding='utf-8') as f:
            # Write header
            if header:
                f.write(f"{header}\n")
            else:
                f.write("#EXTM3U\n")

            # Write channels
            for extinf, url in channels:
                f.write(f"{extinf}\n{url}\n")

        group_counts[safe_group_name] = len(channels)
        print(f"Created {output_path} with {len(channels)} channels")

    return group_counts


def main():
    if len(sys.argv) != 2:
        print("Usage: python o11_m3u_split_by_group.py <input_m3u_file>")
        sys.exit(1)

    input_file = sys.argv[1]

    # Read input file
    content = read_m3u_file(input_file)

    # Parse content by group
    header, groups = parse_m3u_by_group(content)

    # Create output directory based on input file name
    base_name = os.path.splitext(os.path.basename(input_file))[0]
    output_dir = f"output"

    header = f'#EXTM3U\n#EXTM3U x-tvg-url="https://assets.livednow.com/epg.xml"\n'

    # Write group files
    group_counts = write_group_m3u_files(header, groups, output_dir)

    # Print summary
    total_channels = sum(group_counts.values())
    print(f"\nSummary:")
    print(f"Total groups: {len(groups)}")
    print(f"Total channels: {total_channels}")

    # Print channel count by group
    print("\nChannels per group:")
    for group, count in sorted(group_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {group}: {count} channels")

    print(f"\nOutput directory: {output_dir}")


if __name__ == "__main__":
    main()
#!/usr/bin/env python3
# Merge multiple XMLTV (.xml/.xml.gz; local paths or HTTP URLs) into ONE file.
# Usage examples:
#   python xmltv_merge.py epg1.xml epg2.xml -o merged.xml.gz
#     https://jackieboii.github.io/iptv/merged.xml.gz
#   python xmltv_merge.py https://example.com/epg1.xml.gz https://example.com/epg2.xml -o merged.xml
import io, gzip, argparse, urllib.request
import xml.etree.ElementTree as ET

def open_source(src: str) -> bytes:
    if src.startswith(("http://","https://")):
        with urllib.request.urlopen(src, timeout=60) as r:
            return r.read()
    with open(src, "rb") as f:
        return f.read()

def xml_from_bytes(raw: bytes, name_hint: str):
    if name_hint.endswith(".gz"):
        raw = gzip.decompress(raw)
    return ET.fromstring(raw)

def merge_xmltv(sources):
    out_root = ET.Element("tv")
    seen_channels = set()               # channel ids we already added
    seen_programmes = set()             # (channel_id, start_time) pairs
    for src in sources:
        raw = open_source(src)
        root = xml_from_bytes(raw, src)
        # channels
        for ch in root.findall("./channel"):
            cid = (ch.attrib.get("id") or "").strip()
            if cid and cid not in seen_channels:
                seen_channels.add(cid)
                out_root.append(ch)
        # programmes
        for pr in root.findall("./programme"):
            key = ((pr.attrib.get("channel") or "").strip(),
                   (pr.attrib.get("start") or "").strip())
            if key[0] and key[1] and key not in seen_programmes:
                seen_programmes.add(key)
                out_root.append(pr)
    return ET.ElementTree(out_root)

def main():
    ap = argparse.ArgumentParser(description="Merge multiple XMLTV feeds into one file")
    ap.add_argument("inputs", nargs="+", help="EPG inputs (.xml or .xml.gz; files or URLs)")
    ap.add_argument("-o", "--out", required=True, help="Output path (.xml or .xml.gz)")
    args = ap.parse_args()

    tree = merge_xmltv(args.inputs)
    buf = io.BytesIO()
    tree.write(buf, encoding="utf-8", xml_declaration=True)
    data = buf.getvalue()

    if args.out.endswith(".gz"):
        with gzip.open(args.out, "wb", compresslevel=9) as f:
            f.write(data)
    else:
        with open(args.out, "wb") as f:
            f.write(data)
    print(f"[OK] Wrote {args.out}")

if __name__ == "__main__":
    main()

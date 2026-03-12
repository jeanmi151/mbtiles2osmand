#!/usr/bin/env python3
import io
import sqlite3
from PIL import Image
import os

# See:
# * https://github.com/osmandapp/Osmand/blob/master/OsmAnd/src/net/osmand/plus/SQLiteTileSource.java


def to_jpg(raw_bytes, quality):
    im = Image.open(io.BytesIO(raw_bytes))
    im = im.convert("RGB")
    stream = io.BytesIO()
    im.save(stream, format="JPEG", subsampling=0, quality=quality)
    return stream.getvalue()


# Converts mbtiles format to sqlitedb format suitable for OsmAnd
# force_overwrite : override output file if exists
# jpeg_quality : 'convert tiles to JPEG with specified quality'
def mbtiles2osmand_convertion(
    intput_file, output_file, force_overwrite=False, jpeg_quality=None
):
    if os.path.isfile(output_file):
        if force_overwrite:
            os.remove(output_file)
        else:
            print("Output file already exists. Add -f option for overwrite")
            exit(1)
    source = sqlite3.connect(intput_file)
    dest = sqlite3.connect(output_file)

    scur = source.cursor()
    dcur = dest.cursor()

    dcur.execute(
        """CREATE TABLE tiles (x int, y int, z int, s int, image blob, PRIMARY KEY (x,y,z,s));"""
    )
    dcur.execute("""CREATE TABLE info (maxzoom Int, minzoom Int);""")

    for row in scur.execute(
        "SELECT zoom_level, tile_column, tile_row, tile_data FROM tiles"
    ):
        image = row[3]
        if jpeg_quality != None:
            image = to_jpg(image, int(jpeg_quality))
        z, x, y, s = int(row[0]), int(row[1]), int(row[2]), 0
        y = 2**z - 1 - y
        z = 17 - z
        dcur.execute(
            "INSERT INTO tiles (x, y, z, s, image) VALUES (?, ?, ?, ?, ?)",
            [x, y, z, s, sqlite3.Binary(image)],
        )

    dcur.execute("INSERT INTO info (maxzoom, minzoom) SELECT max(z),min(z) from tiles")

    dest.commit()
    source.close()
    dest.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Converts mbtiles format to sqlitedb format suitable for OsmAnd"
    )

    parser.add_argument("input", help="input file")
    parser.add_argument("output", help="output file")
    parser.add_argument(
        "-f", "-force", action="store_true", help="override output file if exists"
    )
    parser.add_argument(
        "--jpg",
        dest="jpeg_quality",
        action="store",
        help="convert tiles to JPEG with specified quality",
    )
    args = parser.parse_args()

    if os.path.isfile(args.output):
        if args.f:
            os.remove(args.output)
        else:
            print("Output file already exists. Add -f option for overwrite")
            exit(1)

    mbtiles2osmand_convertion(
        args.input, args.output, force_overwrite=args.f, jpeg_quality=args.jpeg_quality
    )

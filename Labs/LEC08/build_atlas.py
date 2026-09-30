"""Pack AI-generated poses into a variable-size atlas (development tool).

The game itself needs only pico2d. To rebuild this asset install Pillow and run
python build_atlas.py. Cropping and packing preserve the source RGBA pixels.
"""
from pathlib import Path
import json
from PIL import Image

ASSETS = Path(__file__).resolve().parent / 'assets'
SOURCE = ASSETS / 'generated_source.png'
SELECTIONS = [
    ('walk', 'Walk', 0.12, 0, [0, 1, 2, 4, 5, 6]),
    ('run', 'Run', 0.085, 1, list(range(8))),
    ('jump', 'Jump', 0.13, 2, [0, 1, 2, 4, 5, 6, 7]),
    ('attack', 'Attack', 0.12, 3, [0, 2, 4, 6, 7]),
]


def main():
    image = Image.open(SOURCE).convert('RGBA')
    cell_width, cell_height = image.width / 8, image.height / 4
    rows = []
    gap = 12
    for name, label, seconds, row, columns in SELECTIONS:
        frames = []
        y0, y1 = round(row * cell_height), round((row + 1) * cell_height)
        alpha = image.crop((0, y0, image.width, y1)).getchannel('A')
        # AI 시트는 지정 크기와 다를 수 있으므로 투명한 간격을 찾아 칸 경계를 보정한다.
        # A zero-alpha vertical strip is a safe cut between two neighboring poses.
        occupied = [any(alpha.getpixel((x, y)) >= 32 for y in range(alpha.height))
                    for x in range(alpha.width)]
        boundaries = [0]
        for edge in range(1, 8):
            ideal = round(edge * cell_width)
            candidates = [x for x in range(max(3, ideal - 30), min(image.width - 3, ideal + 31))
                          if not any(occupied[x-2:x+3])]
            if not candidates:
                raise ValueError(f'Overlapping generated poses in row {row}, edge {edge}')
            boundaries.append(min(candidates, key=lambda x: abs(x - ideal)))
        boundaries.append(image.width)
        for column in columns:
            x0, x1 = boundaries[column], boundaries[column + 1]
            source_rect = (x0, y0, x1, y1)
            cell = image.crop(source_rect)
            silhouette = cell.getchannel('A').point(lambda a: 255 if a >= 64 else 0)
            box = silhouette.getbbox()
            if box is None:
                raise ValueError(f'Empty pose: {name}/{column}')
            left, top, right, bottom = box
            box = (max(0, left - 2), max(0, top - 2),
                   min(cell.width, right + 2), min(cell.height, bottom + 2))
            pose = cell.crop(box)
            anchor = round((column + 0.5) * cell_width)
            pivot_x = min(pose.width, max(0, anchor - x0 - box[0]))
            lift = max(0, cell_height - 10 - box[3]) if name == 'jump' else 0
            frames.append((pose, pivot_x, lift, source_rect, box))
        rows.append((name, label, seconds, frames))
    atlas_width = max(sum(frame[0].width + gap for frame in row[3]) + gap for row in rows)
    row_heights = [max(frame[0].height for frame in row[3]) + gap * 2 for row in rows]
    atlas = Image.new('RGBA', (atlas_width, sum(row_heights)), (0, 0, 0, 0))
    metadata = {'schema_version': 1, 'image': 'sprite_atlas.png',
                'size': list(atlas.size), 'animations': []}
    provenance = []
    y = 0
    for (name, label, seconds, frames), row_height in zip(rows, row_heights):
        animation = {'name': name, 'label': label, 'frame_seconds': seconds, 'frames': []}
        x = gap
        for pose, pivot_x, lift, source_rect, crop in frames:
            target_y = y + gap
            atlas.paste(pose, (x, target_y))
            animation['frames'].append({'x': x, 'y': target_y, 'width': pose.width,
                                        'height': pose.height, 'pivot_x': pivot_x,
                                        'pivot_y': pose.height, 'offset_y': lift})
            provenance.append({'animation': name, 'source_rect': source_rect, 'crop': crop})
            x += pose.width + gap
        metadata['animations'].append(animation)
        y += row_height
    atlas.save(ASSETS / 'sprite_atlas.png')
    (ASSETS / 'sprite_atlas.json').write_text(json.dumps(metadata, indent=2) + '\n', encoding='utf-8')
    (ASSETS / 'packing_provenance.json').write_text(json.dumps(provenance, indent=2) + '\n', encoding='utf-8')
    print(f'Atlas: {atlas.size}; counts: {[len(a[3]) for a in rows]}')


if __name__ == '__main__':
    main()

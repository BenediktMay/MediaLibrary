#!/usr/bin/env python3
import sys
sys.path.insert(0, r'c:\Torrent\MediaLibrary')
from app import scan_media_library

library = scan_media_library()

print('=== SERIES ===')
for series_name in sorted(library['series'].keys())[:10]:
    seasons = library['series'][series_name]
    total_eps = sum(len(eps) for eps in seasons.values())
    print(f'{series_name}:')
    for season_num in sorted(seasons.keys()):
        print(f'  Season {season_num}: {len(seasons[season_num])} episodes')

print()
print('=== MOVIES ===')
movies = library['movies']
print(f'Total movies: {len(movies)}')
if movies:
    for m in movies[:5]:
        name = m.get('name', 'Unknown')
        print(f'  - {name}')

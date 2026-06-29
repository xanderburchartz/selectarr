// Mock data for Selectarr UI prototype.
// Titles are intentionally generic to avoid implying real catalog items.

window.SELECTARR_DATA = (function () {
  const users = [
    { id: 'u1', name: 'sven' },
    { id: 'u2', name: 'nora' },
    { id: 'u3', name: 'roel' },
  ];

  // helper — watch_status.per_user keyed by user.id with bool values
  const ws = (s, n, r) => ({ per_user: { u1: s, u2: n, u3: r } });

  const movies = [
    { radarr_id: 101, title: 'Solaris Drift',        year: 2024, file_size_bytes: 8.7e9,  has_file: true,  watch_status: ws(true,  true,  true)  },
    { radarr_id: 102, title: 'The Glass Cathedral',  year: 2019, file_size_bytes: 4.2e9,  has_file: true,  watch_status: ws(true,  false, false) },
    { radarr_id: 103, title: 'Northbound',           year: 2022, file_size_bytes: 12.1e9, has_file: true,  watch_status: ws(false, false, false) },
    { radarr_id: 104, title: 'Echoes Beneath',       year: 2018, file_size_bytes: 6.8e9,  has_file: true,  watch_status: ws(true,  true,  false) },
    { radarr_id: 105, title: 'Aurora Protocol',      year: 2024, file_size_bytes: 18.4e9, has_file: true,  watch_status: ws(false, false, false) },
    { radarr_id: 106, title: 'Pale Light District',  year: 2021, file_size_bytes: 5.5e9,  has_file: true,  watch_status: ws(true,  false, true)  },
    { radarr_id: 107, title: 'Tundra Boys',          year: 2017, file_size_bytes: 3.1e9,  has_file: false, watch_status: null },
    { radarr_id: 108, title: 'Midnight Atlas',       year: 2023, file_size_bytes: 9.6e9,  has_file: true,  watch_status: ws(true,  true,  true)  },
    { radarr_id: 109, title: 'The Long Saturday',    year: 2020, file_size_bytes: 4.9e9,  has_file: true,  watch_status: ws(false, true,  false) },
    { radarr_id: 110, title: 'Halcyon Drive',        year: 2024, file_size_bytes: 15.2e9, has_file: true,  watch_status: ws(true,  true,  false) },
    { radarr_id: 111, title: 'Lantern in the Field', year: 2016, file_size_bytes: 2.8e9,  has_file: true,  watch_status: null },
    { radarr_id: 112, title: 'Driftwood Country',    year: 2022, file_size_bytes: 7.4e9,  has_file: true,  watch_status: ws(true,  true,  true)  },
  ];

  const series = [
    {
      sonarr_id: 201, title: 'Lighthouse Bay', year: 2021, total_size_bytes: 42.6e9,
      watch_status: ws(true, true, false),
      seasons: [
        { number: 1, episode_count: 8, episode_file_count: 8, episodes: [
          { episode_number: 1, title: 'The Keeper',          episode_file_id: 9001, has_file: true },
          { episode_number: 2, title: 'Salt and Iron',       episode_file_id: 9002, has_file: true },
          { episode_number: 3, title: 'Underwater Bells',    episode_file_id: 9003, has_file: true },
          { episode_number: 4, title: 'A Quiet Morning',     episode_file_id: 9004, has_file: true },
          { episode_number: 5, title: 'Stormglass',          episode_file_id: 9005, has_file: true },
          { episode_number: 6, title: 'Departures',          episode_file_id: 9006, has_file: true },
          { episode_number: 7, title: 'The Last Watch',      episode_file_id: 9007, has_file: true },
          { episode_number: 8, title: 'Homecoming',          episode_file_id: 9008, has_file: true },
        ]},
        { number: 2, episode_count: 8, episode_file_count: 7, episodes: [
          { episode_number: 1, title: 'New Beacon',          episode_file_id: 9101, has_file: true },
          { episode_number: 2, title: 'Cartography',         episode_file_id: 9102, has_file: true },
          { episode_number: 3, title: 'Northern Lights',     episode_file_id: 9103, has_file: true },
          { episode_number: 4, title: 'Driftwood',           episode_file_id: 9104, has_file: true },
          { episode_number: 5, title: 'Signal Lost',         episode_file_id: null, has_file: false },
          { episode_number: 6, title: 'The Replacement',     episode_file_id: 9106, has_file: true },
          { episode_number: 7, title: 'Two Lighthouses',     episode_file_id: 9107, has_file: true },
          { episode_number: 8, title: 'Tide Returns',        episode_file_id: 9108, has_file: true },
        ]},
        { number: 3, episode_count: 6, episode_file_count: 6, episodes: [] },
      ]
    },
    { sonarr_id: 202, title: 'The Cartographer',     year: 2019, total_size_bytes: 28.4e9, watch_status: ws(true, false, false), seasons: [{ number: 1, episode_count: 10, episode_file_count: 10, episodes: [] }, { number: 2, episode_count: 10, episode_file_count: 10, episodes: [] }] },
    { sonarr_id: 203, title: 'Last Frequency',       year: 2023, total_size_bytes: 19.8e9, watch_status: ws(false, false, false), seasons: [{ number: 1, episode_count: 6, episode_file_count: 6, episodes: [] }] },
    { sonarr_id: 204, title: 'Iron Coast',           year: 2017, total_size_bytes: 56.2e9, watch_status: ws(true, true, true), seasons: [{number:1,episode_count:13,episode_file_count:13,episodes:[]},{number:2,episode_count:13,episode_file_count:13,episodes:[]},{number:3,episode_count:13,episode_file_count:13,episodes:[]},{number:4,episode_count:13,episode_file_count:13,episodes:[]}] },
    { sonarr_id: 205, title: 'Pelagic',              year: 2024, total_size_bytes: 12.3e9, watch_status: ws(false, true, false), seasons: [{number:1,episode_count:8,episode_file_count:8,episodes:[]}] },
    { sonarr_id: 206, title: 'Cold Open',            year: 2020, total_size_bytes: 34.1e9, watch_status: null, seasons: [{number:1,episode_count:10,episode_file_count:10,episodes:[]},{number:2,episode_count:10,episode_file_count:9,episodes:[]}] },
  ];

  const artists = [
    {
      lidarr_id: 301, name: 'Hold Wave', album_count: 4, mb_id: 'mb-301',
      albums: [
        { lidarr_id: 401, title: 'Sea Static',     year: 2019, track_count: 11, has_files: true,
          tracks: [
            { id: 501, title: 'Open Window',   track_number: 1 },
            { id: 502, title: 'Drift Code',    track_number: 2 },
            { id: 503, title: 'Pale Wires',    track_number: 3 },
            { id: 504, title: 'Slow Aurora',   track_number: 4 },
          ]},
        { lidarr_id: 402, title: 'Long Year',      year: 2021, track_count: 9,  has_files: true,  tracks: [] },
        { lidarr_id: 403, title: 'Northern Halls', year: 2023, track_count: 12, has_files: true,  tracks: [] },
        { lidarr_id: 404, title: 'Quiet Engines',  year: 2024, track_count: 10, has_files: false, tracks: [] },
      ]
    },
    { lidarr_id: 302, name: 'mira oka',        album_count: 2, mb_id: 'mb-302', albums: [{lidarr_id:411,title:'Soft Static',year:2022,track_count:8,has_files:true,tracks:[]},{lidarr_id:412,title:'Map of Sleep',year:2024,track_count:9,has_files:true,tracks:[]}] },
    { lidarr_id: 303, name: 'Pelagic Drift',   album_count: 3, mb_id: 'mb-303', albums: [] },
    { lidarr_id: 304, name: 'Foundry',         album_count: 5, mb_id: null, albums: [] },
    { lidarr_id: 305, name: 'OBSERVER',        album_count: 1, mb_id: 'mb-305', albums: [] },
    { lidarr_id: 306, name: 'Field Recordings of an Empty Room', album_count: 7, mb_id: 'mb-306', albums: [] },
  ];

  const logs = [
    { timestamp: '2026-05-16T14:22:01', media_type: 'movie',   title: 'The Glass Cathedral',         level: 'movie',   dry_run: false, success: true,  message: 'Deleted (4.2 GB freed)' },
    { timestamp: '2026-05-16T14:21:47', media_type: 'movie',   title: 'Tundra Boys',                 level: 'movie',   dry_run: false, success: false, message: 'Radarr returned 404 — id not found' },
    { timestamp: '2026-05-16T13:08:12', media_type: 'episode', title: 'Lighthouse Bay · S02E05',     level: 'episode', dry_run: true,  success: true,  message: 'Would delete 1 file (0.9 GB)' },
    { timestamp: '2026-05-16T12:55:30', media_type: 'season',  title: 'Iron Coast · Season 4',       level: 'season',  dry_run: true,  success: true,  message: 'Would delete 13 files (5.8 GB)' },
    { timestamp: '2026-05-16T11:14:09', media_type: 'album',   title: 'Hold Wave — Quiet Engines',   level: 'album',   dry_run: false, success: true,  message: 'Deleted 10 tracks (124 MB)' },
    { timestamp: '2026-05-16T10:42:18', media_type: 'movie',   title: 'Lantern in the Field',        level: 'movie',   dry_run: true,  success: true,  message: 'Would delete 1 file (2.8 GB)' },
    { timestamp: '2026-05-15T22:31:55', media_type: 'series',  title: 'Cold Open',                   level: 'series',  dry_run: false, success: true,  message: 'Deleted (34.1 GB freed, 20 files)' },
    { timestamp: '2026-05-15T21:09:02', media_type: 'track',   title: 'mira oka — Drift Code',       level: 'track',   dry_run: false, success: true,  message: 'Deleted (11.4 MB)' },
    { timestamp: '2026-05-15T19:48:41', media_type: 'movie',   title: 'Halcyon Drive',               level: 'movie',   dry_run: false, success: false, message: 'Permission denied on /media/movies/halcyon-drive' },
    { timestamp: '2026-05-15T18:02:19', media_type: 'episode', title: 'Lighthouse Bay · S01E03',     level: 'episode', dry_run: true,  success: true,  message: 'Would delete 1 file (1.1 GB)' },
    { timestamp: '2026-05-15T17:30:00', media_type: 'movie',   title: 'Pale Light District',         level: 'movie',   dry_run: true,  success: true,  message: 'Would delete 1 file (5.5 GB)' },
    { timestamp: '2026-05-15T16:11:44', media_type: 'season',  title: 'The Cartographer · Season 1', level: 'season',  dry_run: false, success: true,  message: 'Deleted 10 files (14.2 GB)' },
  ];

  return { users, movies, series, artists, logs };
})();

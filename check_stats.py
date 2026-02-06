import duckdb

conn = duckdb.connect('data/superbowl.db')

print('Jaxon Smith-Njigba - First 10 games:')
result = conn.execute("""
    SELECT week, receptions, receiving_yards
    FROM player_game_logs
    WHERE player_name = 'Jaxon Smith-Njigba' AND season = 2025
    ORDER BY week
    LIMIT 10
""").fetchall()

for week, rec, yds in result:
    print(f'  Week {week}: {rec} rec, {yds} yds')

print('\nSeason totals and averages:')
result = conn.execute("""
    SELECT
        COUNT(*) as games,
        SUM(receptions) as total_rec,
        SUM(receiving_yards) as total_yds,
        AVG(receptions) as avg_rec,
        AVG(receiving_yards) as avg_yds
    FROM player_game_logs
    WHERE player_name = 'Jaxon Smith-Njigba' AND season = 2025
""").fetchone()

print(f'  Games: {result[0]}')
print(f'  Total receptions: {result[1]}')
print(f'  Total yards: {result[2]}')
print(f'  Average rec/game: {result[3]:.1f}')
print(f'  Average yds/game: {result[4]:.1f}')

print('\n' + '='*60)
print('All Seattle players - Averages vs Totals:')
print('='*60)

result = conn.execute("""
    SELECT
        player_name,
        COUNT(*) as games,
        SUM(receptions) as total_rec,
        AVG(receptions) as avg_rec,
        SUM(receiving_yards) as total_yds,
        AVG(receiving_yards) as avg_yds
    FROM player_game_logs
    WHERE season = 2025
    GROUP BY player_name
    ORDER BY player_name
""").fetchall()

for name, games, tot_rec, avg_rec, tot_yds, avg_yds in result:
    print(f'\n{name}: {games} games')
    print(f'  Total: {tot_rec} rec, {tot_yds} yds')
    print(f'  Average: {avg_rec:.1f} rec/game, {avg_yds:.1f} yds/game')

conn.close()

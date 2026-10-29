-- Candidate sales lines (B), read by the new engine
SELECT *
FROM read_csv('data/b_raw.csv', header = true)

ALTER TABLE gym_sets ADD COLUMN time_seconds INTEGER;
INSERT OR IGNORE INTO schema_version (version) VALUES (2);

CREATE TABLE IF NOT EXISTS file_upload_log (
  upload_time TIMESTAMPTZ NOT NULL,
  file_name TEXT NOT NULL,
  PRIMARY KEY(upload_time, file_name)
);
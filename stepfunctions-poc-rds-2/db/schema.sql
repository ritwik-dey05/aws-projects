CREATE TABLE IF NOT EXISTS questions (
  question_id VARCHAR(36) PRIMARY KEY,
  title TEXT NOT NULL,
  content TEXT,
  created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS approval_tasks (
  task_id VARCHAR(36) PRIMARY KEY,
  question_id VARCHAR(36) NOT NULL REFERENCES questions(question_id) ON DELETE CASCADE,
  assessor_email TEXT NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('PENDING','APPROVED','REJECTED','TIMED_OUT','FAILED')),
  task_token TEXT NULL,
  comments TEXT NULL,
  created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_approval_tasks_token ON approval_tasks(task_token);
CREATE INDEX IF NOT EXISTS idx_approval_tasks_qid ON approval_tasks(question_id);

BEGIN;

-- Sample questions
INSERT INTO questions (question_id, title, content, created_at)
VALUES
  ('11111111-1111-1111-1111-111111111111', 'Algebra Midterm',        'Set A - Algebra QP',            NOW()),
  ('22222222-2222-2222-2222-222222222222', 'Physics Midterm',        'Set A - Physics QP',            NOW()),
  ('33333333-3333-3333-3333-333333333333', 'Chemistry Quiz',         'Organic I topics',              NOW()),
  ('44444444-4444-4444-4444-444444444444', 'Biology Final',          'Human Anatomy Section',         NOW()),
  ('55555555-5555-5555-5555-555555555555', 'Computer Science Lab',   'DSA practical assessment',      NOW())
ON CONFLICT (question_id) DO NOTHING;

-- Sample approval tasks (statuses cover PENDING/APPROVED/REJECTED/TIMED_OUT/FAILED)
INSERT INTO approval_tasks (task_id, question_id, assessor_email, status, task_token, comments, created_at, updated_at)
VALUES
  -- Pending (no token yet; will be set by SQS consumer)
  ('aaaaaaa1-aaaa-aaaa-aaaa-aaaaaaaaaaa1', '11111111-1111-1111-1111-111111111111',
   'assessor1@example.com', 'PENDING', NULL, NULL, NOW(), NOW()),

  -- Approved
  ('aaaaaaa2-aaaa-aaaa-aaaa-aaaaaaaaaaa2', '22222222-2222-2222-2222-222222222222',
   'assessor2@example.com', 'APPROVED', NULL, 'Approved as-is', NOW() - INTERVAL '2 days', NOW() - INTERVAL '1 day'),

  -- Rejected
  ('aaaaaaa3-aaaa-aaaa-aaaa-aaaaaaaaaaa3', '33333333-3333-3333-3333-333333333333',
   'assessor3@example.com', 'REJECTED', NULL, 'Revise Q3 and resubmit', NOW() - INTERVAL '3 days', NOW() - INTERVAL '2 days'),

  -- Timed out
  ('aaaaaaa4-aaaa-aaaa-aaaa-aaaaaaaaaaa4', '44444444-4444-4444-4444-444444444444',
   'assessor4@example.com', 'TIMED_OUT', NULL, 'No response from approver', NOW() - INTERVAL '5 days', NOW() - INTERVAL '3 days'),

  -- Failed (represents a workflow/system error)
  ('aaaaaaa5-aaaa-aaaa-aaaa-aaaaaaaaaaa5', '55555555-5555-5555-5555-555555555555',
   'assessor5@example.com', 'FAILED', NULL, 'Workflow error during callback', NOW() - INTERVAL '1 day', NOW() - INTERVAL '1 day'),

  -- Another pending for the same assessor to show multiples
  ('aaaaaaa6-aaaa-aaaa-aaaa-aaaaaaaaaaa6', '22222222-2222-2222-2222-222222222222',
   'assessor2@example.com', 'PENDING', NULL, NULL, NOW(), NOW())
ON CONFLICT (task_id) DO NOTHING;

COMMIT;

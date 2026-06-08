IF OBJECT_ID('teacher_leave_applications', 'U') IS NOT NULL
BEGIN
    IF COL_LENGTH('teacher_leave_applications', 'admin_remarks') IS NULL
        ALTER TABLE teacher_leave_applications ADD admin_remarks NVARCHAR(500) NULL;

    IF COL_LENGTH('teacher_leave_applications', 'cancel_reason') IS NULL
        ALTER TABLE teacher_leave_applications ADD cancel_reason NVARCHAR(500) NULL;

    IF COL_LENGTH('teacher_leave_applications', 'decided_by') IS NULL
        ALTER TABLE teacher_leave_applications ADD decided_by NVARCHAR(150) NULL;

    IF COL_LENGTH('teacher_leave_applications', 'decided_at') IS NULL
        ALTER TABLE teacher_leave_applications ADD decided_at DATETIME2 NULL;

    IF COL_LENGTH('teacher_leave_applications', 'updated_at') IS NULL
        ALTER TABLE teacher_leave_applications ADD updated_at DATETIME2 NULL;
END;

IF OBJECT_ID('notifications', 'U') IS NULL
BEGIN
    CREATE TABLE notifications (
        notification_id NVARCHAR(80) NOT NULL PRIMARY KEY,
        school_id NVARCHAR(50) NOT NULL,
        recipient_role NVARCHAR(30) NOT NULL,
        recipient_id NVARCHAR(50) NULL,
        title NVARCHAR(200) NOT NULL,
        message NVARCHAR(1000) NOT NULL,
        [type] NVARCHAR(50) NULL,
        reference_id NVARCHAR(80) NULL,
        is_read BIT NOT NULL DEFAULT 0,
        created_at DATETIME2 NOT NULL
    );
END;

IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE name = 'ix_notifications_recipient'
      AND object_id = OBJECT_ID('notifications')
)
BEGIN
    CREATE INDEX ix_notifications_recipient
    ON notifications(school_id, recipient_role, recipient_id, is_read);
END;

CREATE TABLE schools (
    school_id NVARCHAR(50) NOT NULL PRIMARY KEY,
    name NVARCHAR(200) NOT NULL,
    address NVARCHAR(500) NULL,
    contact NVARCHAR(20) NULL,
    latitude DECIMAL(10, 7) NULL,
    longitude DECIMAL(10, 7) NULL,
    logo_path NVARCHAR(500) NULL,
    created_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    updated_at DATETIME2 NULL
);

CREATE TABLE super_admins (
    super_admin_id NVARCHAR(50) NOT NULL PRIMARY KEY,
    name NVARCHAR(150) NOT NULL,
    email NVARCHAR(150) NULL,
    contact NVARCHAR(20) NULL,
    password NVARCHAR(200) NOT NULL,
    role NVARCHAR(30) NOT NULL DEFAULT 'SUPER_ADMIN',
    is_active BIT NOT NULL DEFAULT 1,
    created_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);

INSERT INTO super_admins(
    super_admin_id,
    name,
    email,
    contact,
    password,
    role,
    is_active
)
SELECT
    'SUPER001',
    'Super Admin',
    'superadmin@attendancepro.local',
    '',
    'Super@123',
    'SUPER_ADMIN',
    1
WHERE NOT EXISTS (
    SELECT 1 FROM super_admins WHERE super_admin_id = 'SUPER001'
);

CREATE TABLE admins (
    admin_id NVARCHAR(50) NOT NULL PRIMARY KEY,
    school_id NVARCHAR(50) NOT NULL,
    name NVARCHAR(150) NOT NULL,
    email NVARCHAR(150) NULL,
    contact NVARCHAR(20) NULL,
    address NVARCHAR(500) NULL,
    role NVARCHAR(30) NOT NULL DEFAULT 'ADMIN',
    password NVARCHAR(200) NOT NULL,
    created_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    CONSTRAINT fk_admins_school FOREIGN KEY (school_id) REFERENCES schools(school_id)
);

CREATE TABLE school_subscriptions (
    school_id NVARCHAR(50) NOT NULL PRIMARY KEY,
    start_date DATE NULL,
    end_date DATE NULL,
    status NVARCHAR(30) NOT NULL DEFAULT 'Active',
    updated_at DATETIME2 NULL,
    CONSTRAINT fk_school_subscriptions_school FOREIGN KEY (school_id) REFERENCES schools(school_id)
);

CREATE TABLE school_feature_settings (
    setting_id INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    school_id NVARCHAR(50) NOT NULL,
    audience NVARCHAR(30) NOT NULL,
    feature_code NVARCHAR(80) NOT NULL,
    enabled BIT NOT NULL DEFAULT 1,
    updated_at DATETIME2 NULL,
    CONSTRAINT uq_school_feature_settings UNIQUE (school_id, audience, feature_code),
    CONSTRAINT fk_school_feature_settings_school FOREIGN KEY (school_id) REFERENCES schools(school_id)
);

CREATE TABLE class_master (
    class_id INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    school_id NVARCHAR(50) NOT NULL,
    class_name NVARCHAR(30) NOT NULL,
    display_order INT NULL,
    CONSTRAINT uq_class_master UNIQUE (school_id, class_name),
    CONSTRAINT fk_class_school FOREIGN KEY (school_id) REFERENCES schools(school_id)
);

CREATE TABLE section_master (
    section_id INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    school_id NVARCHAR(50) NOT NULL,
    section_name NVARCHAR(20) NOT NULL,
    CONSTRAINT uq_section_master UNIQUE (school_id, section_name),
    CONSTRAINT fk_section_school FOREIGN KEY (school_id) REFERENCES schools(school_id)
);

CREATE TABLE subjects (
    subject_id INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    school_id NVARCHAR(50) NOT NULL,
    name NVARCHAR(120) NOT NULL,
    created_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    CONSTRAINT uq_subjects UNIQUE (school_id, name),
    CONSTRAINT fk_subjects_school FOREIGN KEY (school_id) REFERENCES schools(school_id)
);

CREATE TABLE teachers (
    teacher_id NVARCHAR(50) NOT NULL PRIMARY KEY,
    school_id NVARCHAR(50) NOT NULL,
    name NVARCHAR(150) NOT NULL,
    email NVARCHAR(150) NULL,
    contact NVARCHAR(20) NULL,
    address NVARCHAR(500) NULL,
    role NVARCHAR(30) NOT NULL DEFAULT 'TEA',
    subject NVARCHAR(120) NULL,
    qualification NVARCHAR(150) NULL,
    face_embedding NVARCHAR(MAX) NULL,
    password NVARCHAR(200) NOT NULL,
    created_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    CONSTRAINT fk_teachers_school FOREIGN KEY (school_id) REFERENCES schools(school_id)
);

CREATE TABLE students (
    student_id NVARCHAR(50) NOT NULL PRIMARY KEY,
    school_id NVARCHAR(50) NOT NULL,
    admission_no NVARCHAR(50) NULL,
    admission_date DATETIME2 NULL,
    first_name NVARCHAR(100) NOT NULL,
    middle_name NVARCHAR(100) NULL,
    last_name NVARCHAR(100) NULL,
    full_name NVARCHAR(220) NOT NULL,
    father_name NVARCHAR(150) NULL,
    mother_name NVARCHAR(150) NULL,
    address NVARCHAR(500) NULL,
    gender NVARCHAR(20) NULL,
    dob DATETIME2 NULL,
    [class] NVARCHAR(30) NOT NULL,
    section NVARCHAR(20) NOT NULL,
    session NVARCHAR(20) NOT NULL,
    class_teacher NVARCHAR(150) NULL,
    photo_path NVARCHAR(500) NULL,
    face_embedding NVARCHAR(MAX) NULL,
    created_at DATETIME2 NULL,
    CONSTRAINT uq_students_admission UNIQUE (school_id, admission_no),
    CONSTRAINT fk_students_school FOREIGN KEY (school_id) REFERENCES schools(school_id)
);

CREATE TABLE class_teacher_assignments (
    assignment_id INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    school_id NVARCHAR(50) NOT NULL,
    class_name NVARCHAR(30) NOT NULL,
    section NVARCHAR(20) NOT NULL,
    teacher_id NVARCHAR(50) NOT NULL,
    teacher_name NVARCHAR(150) NOT NULL,
    assigned_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    CONSTRAINT uq_class_teacher UNIQUE (school_id, class_name, section),
    CONSTRAINT fk_assignment_school FOREIGN KEY (school_id) REFERENCES schools(school_id),
    CONSTRAINT fk_assignment_teacher FOREIGN KEY (teacher_id) REFERENCES teachers(teacher_id)
);

CREATE TABLE student_attendance (
    attendance_id BIGINT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    student_id NVARCHAR(50) NOT NULL,
    school_id NVARCHAR(50) NOT NULL,
    [date] DATE NOT NULL,
    status NVARCHAR(20) NOT NULL,
    [timestamp] DATETIME2 NOT NULL,
    CONSTRAINT uq_student_attendance UNIQUE (student_id, school_id, [date]),
    CONSTRAINT fk_student_attendance_student FOREIGN KEY (student_id) REFERENCES students(student_id),
    CONSTRAINT fk_student_attendance_school FOREIGN KEY (school_id) REFERENCES schools(school_id)
);

CREATE TABLE teacher_attendance (
    attendance_id BIGINT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    teacher_id NVARCHAR(50) NOT NULL,
    school_id NVARCHAR(50) NOT NULL,
    [date] DATE NOT NULL,
    status NVARCHAR(20) NOT NULL,
    [timestamp] DATETIME2 NOT NULL,
    CONSTRAINT uq_teacher_attendance UNIQUE (teacher_id, school_id, [date]),
    CONSTRAINT fk_teacher_attendance_teacher FOREIGN KEY (teacher_id) REFERENCES teachers(teacher_id),
    CONSTRAINT fk_teacher_attendance_school FOREIGN KEY (school_id) REFERENCES schools(school_id)
);

CREATE TABLE holidays (
    holiday_id INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    school_id NVARCHAR(50) NULL,
    holiday_date DATE NOT NULL,
    name NVARCHAR(150) NOT NULL,
    CONSTRAINT uq_holidays UNIQUE (school_id, holiday_date)
);

CREATE TABLE leave_types (
    leave_type_id INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    school_id NVARCHAR(50) NOT NULL,
    name NVARCHAR(120) NOT NULL,
    code NVARCHAR(20) NOT NULL,
    CONSTRAINT uq_leave_types UNIQUE (school_id, code),
    CONSTRAINT fk_leave_types_school FOREIGN KEY (school_id) REFERENCES schools(school_id)
);

CREATE TABLE teacher_leave_allocations (
    allocation_id INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    school_id NVARCHAR(50) NOT NULL,
    teacher_id NVARCHAR(50) NULL,
    leave_type_code NVARCHAR(20) NOT NULL,
    [year] NVARCHAR(10) NOT NULL,
    total_days DECIMAL(6,2) NOT NULL,
    CONSTRAINT fk_leave_allocations_school FOREIGN KEY (school_id) REFERENCES schools(school_id),
    CONSTRAINT fk_leave_allocations_teacher FOREIGN KEY (teacher_id) REFERENCES teachers(teacher_id)
);

CREATE TABLE teacher_leave_applications (
    leave_id BIGINT NOT NULL PRIMARY KEY,
    school_id NVARCHAR(50) NOT NULL,
    teacher_id NVARCHAR(50) NOT NULL,
    leave_type_code NVARCHAR(20) NOT NULL,
    from_date DATE NOT NULL,
    to_date DATE NOT NULL,
    days DECIMAL(6,2) NOT NULL,
    reason NVARCHAR(500) NULL,
    status NVARCHAR(30) NOT NULL,
    admin_remarks NVARCHAR(500) NULL,
    cancel_reason NVARCHAR(500) NULL,
    decided_by NVARCHAR(150) NULL,
    decided_at DATETIME2 NULL,
    updated_at DATETIME2 NULL,
    created_at DATETIME2 NOT NULL,
    CONSTRAINT fk_leave_applications_school FOREIGN KEY (school_id) REFERENCES schools(school_id),
    CONSTRAINT fk_leave_applications_teacher FOREIGN KEY (teacher_id) REFERENCES teachers(teacher_id)
);

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
    created_at DATETIME2 NOT NULL,
    CONSTRAINT fk_notifications_school FOREIGN KEY (school_id) REFERENCES schools(school_id)
);

CREATE TABLE sync_events (
    sync_event_id BIGINT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    entity NVARCHAR(80) NOT NULL,
    action NVARCHAR(30) NOT NULL,
    payload_json NVARCHAR(MAX) NOT NULL,
    created_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);

CREATE INDEX ix_students_school_class_section ON students(school_id, [class], section);
CREATE INDEX ix_teachers_school ON teachers(school_id);
CREATE INDEX ix_student_attendance_school_date ON student_attendance(school_id, [date]);
CREATE INDEX ix_teacher_attendance_school_date ON teacher_attendance(school_id, [date]);
CREATE INDEX ix_teacher_leave_applications_teacher ON teacher_leave_applications(school_id, teacher_id, from_date);
CREATE INDEX ix_school_feature_settings_school ON school_feature_settings(school_id, audience);
CREATE INDEX ix_notifications_recipient ON notifications(school_id, recipient_role, recipient_id, is_read);

GO

CREATE VIEW vw_student_attendance_monthly AS
SELECT
    s.school_id,
    s.student_id,
    s.full_name,
    s.father_name,
    s.mother_name,
    s.gender,
    s.dob,
    s.[class],
    s.section,
    s.session,
    YEAR(sa.[date]) AS attendance_year,
    MONTH(sa.[date]) AS attendance_month,
    MAX(CASE WHEN DAY(sa.[date]) = 1 THEN sa.status END) AS day_1,
    MAX(CASE WHEN DAY(sa.[date]) = 2 THEN sa.status END) AS day_2,
    MAX(CASE WHEN DAY(sa.[date]) = 3 THEN sa.status END) AS day_3,
    MAX(CASE WHEN DAY(sa.[date]) = 4 THEN sa.status END) AS day_4,
    MAX(CASE WHEN DAY(sa.[date]) = 5 THEN sa.status END) AS day_5,
    MAX(CASE WHEN DAY(sa.[date]) = 6 THEN sa.status END) AS day_6,
    MAX(CASE WHEN DAY(sa.[date]) = 7 THEN sa.status END) AS day_7,
    MAX(CASE WHEN DAY(sa.[date]) = 8 THEN sa.status END) AS day_8,
    MAX(CASE WHEN DAY(sa.[date]) = 9 THEN sa.status END) AS day_9,
    MAX(CASE WHEN DAY(sa.[date]) = 10 THEN sa.status END) AS day_10,
    MAX(CASE WHEN DAY(sa.[date]) = 11 THEN sa.status END) AS day_11,
    MAX(CASE WHEN DAY(sa.[date]) = 12 THEN sa.status END) AS day_12,
    MAX(CASE WHEN DAY(sa.[date]) = 13 THEN sa.status END) AS day_13,
    MAX(CASE WHEN DAY(sa.[date]) = 14 THEN sa.status END) AS day_14,
    MAX(CASE WHEN DAY(sa.[date]) = 15 THEN sa.status END) AS day_15,
    MAX(CASE WHEN DAY(sa.[date]) = 16 THEN sa.status END) AS day_16,
    MAX(CASE WHEN DAY(sa.[date]) = 17 THEN sa.status END) AS day_17,
    MAX(CASE WHEN DAY(sa.[date]) = 18 THEN sa.status END) AS day_18,
    MAX(CASE WHEN DAY(sa.[date]) = 19 THEN sa.status END) AS day_19,
    MAX(CASE WHEN DAY(sa.[date]) = 20 THEN sa.status END) AS day_20,
    MAX(CASE WHEN DAY(sa.[date]) = 21 THEN sa.status END) AS day_21,
    MAX(CASE WHEN DAY(sa.[date]) = 22 THEN sa.status END) AS day_22,
    MAX(CASE WHEN DAY(sa.[date]) = 23 THEN sa.status END) AS day_23,
    MAX(CASE WHEN DAY(sa.[date]) = 24 THEN sa.status END) AS day_24,
    MAX(CASE WHEN DAY(sa.[date]) = 25 THEN sa.status END) AS day_25,
    MAX(CASE WHEN DAY(sa.[date]) = 26 THEN sa.status END) AS day_26,
    MAX(CASE WHEN DAY(sa.[date]) = 27 THEN sa.status END) AS day_27,
    MAX(CASE WHEN DAY(sa.[date]) = 28 THEN sa.status END) AS day_28,
    MAX(CASE WHEN DAY(sa.[date]) = 29 THEN sa.status END) AS day_29,
    MAX(CASE WHEN DAY(sa.[date]) = 30 THEN sa.status END) AS day_30,
    MAX(CASE WHEN DAY(sa.[date]) = 31 THEN sa.status END) AS day_31,
    SUM(CASE WHEN sa.status = 'Present' THEN 1 ELSE 0 END) AS present_days
FROM students s
LEFT JOIN student_attendance sa
    ON sa.student_id = s.student_id
    AND sa.school_id = s.school_id
GROUP BY
    s.school_id, s.student_id, s.full_name, s.father_name, s.mother_name,
    s.gender, s.dob, s.[class], s.section, s.session,
    YEAR(sa.[date]), MONTH(sa.[date]);

GO

CREATE VIEW vw_teacher_attendance_monthly AS
SELECT
    t.school_id,
    t.teacher_id,
    t.name,
    t.subject,
    YEAR(ta.[date]) AS attendance_year,
    MONTH(ta.[date]) AS attendance_month,
    SUM(CASE WHEN ta.status = 'Present' THEN 1 ELSE 0 END) AS present_days
FROM teachers t
LEFT JOIN teacher_attendance ta
    ON ta.teacher_id = t.teacher_id
    AND ta.school_id = t.school_id
GROUP BY t.school_id, t.teacher_id, t.name, t.subject, YEAR(ta.[date]), MONTH(ta.[date]);

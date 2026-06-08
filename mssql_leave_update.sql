IF OBJECT_ID('leave_types', 'U') IS NULL
BEGIN
    CREATE TABLE leave_types (
        leave_type_id INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
        school_id NVARCHAR(50) NOT NULL,
        name NVARCHAR(120) NOT NULL,
        code NVARCHAR(20) NOT NULL,
        CONSTRAINT uq_leave_types UNIQUE (school_id, code),
        CONSTRAINT fk_leave_types_school FOREIGN KEY (school_id) REFERENCES schools(school_id)
    );
END;

IF OBJECT_ID('teacher_leave_allocations', 'U') IS NULL
BEGIN
    CREATE TABLE teacher_leave_allocations (
        allocation_id INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
        school_id NVARCHAR(50) NOT NULL,
        teacher_id NVARCHAR(50) NOT NULL,
        leave_type_code NVARCHAR(20) NOT NULL,
        [year] NVARCHAR(10) NOT NULL,
        total_days DECIMAL(6,2) NOT NULL,
        CONSTRAINT fk_leave_allocations_school FOREIGN KEY (school_id) REFERENCES schools(school_id),
        CONSTRAINT fk_leave_allocations_teacher FOREIGN KEY (teacher_id) REFERENCES teachers(teacher_id)
    );
END;

IF OBJECT_ID('teacher_leave_applications', 'U') IS NULL
BEGIN
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
        created_at DATETIME2 NOT NULL,
        CONSTRAINT fk_leave_applications_school FOREIGN KEY (school_id) REFERENCES schools(school_id),
        CONSTRAINT fk_leave_applications_teacher FOREIGN KEY (teacher_id) REFERENCES teachers(teacher_id)
    );
END;

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE name = 'ix_teacher_leave_applications_teacher'
      AND object_id = OBJECT_ID('teacher_leave_applications')
)
BEGIN
    CREATE INDEX ix_teacher_leave_applications_teacher
    ON teacher_leave_applications(school_id, teacher_id, from_date);
END;

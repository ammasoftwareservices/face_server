-- Use this instead of TRUNCATE when foreign keys exist.
-- Run it inside the database you want to clear.
-- It keeps the super_admins table so you do not lock yourself out.

IF OBJECT_ID('teacher_leave_applications', 'U') IS NOT NULL DELETE FROM teacher_leave_applications;
IF OBJECT_ID('teacher_leave_allocations', 'U') IS NOT NULL DELETE FROM teacher_leave_allocations;
IF OBJECT_ID('teacher_attendance', 'U') IS NOT NULL DELETE FROM teacher_attendance;
IF OBJECT_ID('student_attendance', 'U') IS NOT NULL DELETE FROM student_attendance;
IF OBJECT_ID('class_teacher_assignments', 'U') IS NOT NULL DELETE FROM class_teacher_assignments;
IF OBJECT_ID('subjects', 'U') IS NOT NULL DELETE FROM subjects;
IF OBJECT_ID('leave_types', 'U') IS NOT NULL DELETE FROM leave_types;
IF OBJECT_ID('school_feature_settings', 'U') IS NOT NULL DELETE FROM school_feature_settings;
IF OBJECT_ID('school_subscriptions', 'U') IS NOT NULL DELETE FROM school_subscriptions;
IF OBJECT_ID('class_master', 'U') IS NOT NULL DELETE FROM class_master;
IF OBJECT_ID('section_master', 'U') IS NOT NULL DELETE FROM section_master;
IF OBJECT_ID('holidays', 'U') IS NOT NULL DELETE FROM holidays;
IF OBJECT_ID('students', 'U') IS NOT NULL DELETE FROM students;
IF OBJECT_ID('teachers', 'U') IS NOT NULL DELETE FROM teachers;
IF OBJECT_ID('admins', 'U') IS NOT NULL DELETE FROM admins;
IF OBJECT_ID('schools', 'U') IS NOT NULL DELETE FROM schools;
IF OBJECT_ID('sync_events', 'U') IS NOT NULL DELETE FROM sync_events;

IF OBJECT_ID('teacher_leave_applications', 'U') IS NOT NULL DBCC CHECKIDENT ('teacher_leave_applications', RESEED, 0);
IF OBJECT_ID('teacher_leave_allocations', 'U') IS NOT NULL DBCC CHECKIDENT ('teacher_leave_allocations', RESEED, 0);
IF OBJECT_ID('teacher_attendance', 'U') IS NOT NULL DBCC CHECKIDENT ('teacher_attendance', RESEED, 0);
IF OBJECT_ID('student_attendance', 'U') IS NOT NULL DBCC CHECKIDENT ('student_attendance', RESEED, 0);
IF OBJECT_ID('class_teacher_assignments', 'U') IS NOT NULL DBCC CHECKIDENT ('class_teacher_assignments', RESEED, 0);
IF OBJECT_ID('subjects', 'U') IS NOT NULL DBCC CHECKIDENT ('subjects', RESEED, 0);
IF OBJECT_ID('leave_types', 'U') IS NOT NULL DBCC CHECKIDENT ('leave_types', RESEED, 0);
IF OBJECT_ID('school_feature_settings', 'U') IS NOT NULL DBCC CHECKIDENT ('school_feature_settings', RESEED, 0);
IF OBJECT_ID('class_master', 'U') IS NOT NULL DBCC CHECKIDENT ('class_master', RESEED, 0);
IF OBJECT_ID('section_master', 'U') IS NOT NULL DBCC CHECKIDENT ('section_master', RESEED, 0);
IF OBJECT_ID('holidays', 'U') IS NOT NULL DBCC CHECKIDENT ('holidays', RESEED, 0);
IF OBJECT_ID('sync_events', 'U') IS NOT NULL DBCC CHECKIDENT ('sync_events', RESEED, 0);

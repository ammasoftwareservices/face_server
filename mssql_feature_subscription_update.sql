IF OBJECT_ID('school_subscriptions', 'U') IS NULL
BEGIN
    CREATE TABLE school_subscriptions (
        school_id NVARCHAR(50) NOT NULL PRIMARY KEY,
        start_date DATE NULL,
        end_date DATE NULL,
        status NVARCHAR(30) NOT NULL DEFAULT 'Active',
        updated_at DATETIME2 NULL,
        CONSTRAINT fk_school_subscriptions_school FOREIGN KEY (school_id) REFERENCES schools(school_id)
    );
END;

IF OBJECT_ID('school_feature_settings', 'U') IS NULL
BEGIN
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
END;

IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE name = 'ix_school_feature_settings_school'
      AND object_id = OBJECT_ID('school_feature_settings')
)
BEGIN
    CREATE INDEX ix_school_feature_settings_school
    ON school_feature_settings(school_id, audience);
END;

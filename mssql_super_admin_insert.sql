IF OBJECT_ID('super_admins', 'U') IS NULL
BEGIN
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
END;

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

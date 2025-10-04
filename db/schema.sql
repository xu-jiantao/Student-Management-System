DROP DATABASE IF EXISTS school_db;
CREATE DATABASE school_db DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE school_db;

-- 基础角色/权限体系
CREATE TABLE roles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    description VARCHAR(255) NULL
) ENGINE=InnoDB;

CREATE TABLE permissions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    code VARCHAR(100) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    category VARCHAR(50) NOT NULL DEFAULT 'menu'
) ENGINE=InnoDB;

CREATE TABLE role_permissions (
    role_id INT NOT NULL,
    permission_id INT NOT NULL,
    PRIMARY KEY (role_id, permission_id),
    CONSTRAINT fk_role_permissions_role FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE,
    CONSTRAINT fk_role_permissions_permission FOREIGN KEY (permission_id) REFERENCES permissions(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(80) NOT NULL UNIQUE,
    email VARCHAR(120) NOT NULL UNIQUE,
    phone VARCHAR(20) NULL,
    password_hash VARCHAR(255) NOT NULL,
    avatar_path VARCHAR(255) NULL,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    first_login TINYINT(1) NOT NULL DEFAULT 1,
    last_login_at DATETIME NULL,
    reset_token VARCHAR(255) NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE user_roles (
    user_id INT NOT NULL,
    role_id INT NOT NULL,
    PRIMARY KEY (user_id, role_id),
    CONSTRAINT fk_user_roles_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_user_roles_role FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- 教学基础数据
CREATE TABLE teachers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NULL,
    employee_number VARCHAR(20) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    gender VARCHAR(10) NULL,
    email VARCHAR(120) NULL,
    phone VARCHAR(20) NULL,
    professional_title VARCHAR(100) NULL,
    hire_date DATE NULL,
    CONSTRAINT fk_teachers_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE TABLE classrooms (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    grade_level VARCHAR(20) NULL,
    description VARCHAR(255) NULL,
    head_teacher_id INT NULL,
    CONSTRAINT fk_classrooms_teacher FOREIGN KEY (head_teacher_id) REFERENCES teachers(id) ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE TABLE courses (
    id INT AUTO_INCREMENT PRIMARY KEY,
    code VARCHAR(20) NOT NULL UNIQUE,
    name VARCHAR(120) NOT NULL,
    credit FLOAT NOT NULL DEFAULT 0,
    description TEXT NULL,
    classroom_id INT NULL,
    teacher_id INT NULL,
    CONSTRAINT fk_courses_classroom FOREIGN KEY (classroom_id) REFERENCES classrooms(id) ON DELETE SET NULL,
    CONSTRAINT fk_courses_teacher FOREIGN KEY (teacher_id) REFERENCES teachers(id) ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE TABLE course_schedules (
    id INT AUTO_INCREMENT PRIMARY KEY,
    course_id INT NOT NULL,
    weekday TINYINT NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    location VARCHAR(100) NULL,
    CONSTRAINT fk_course_schedules_course FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE students (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NULL,
    student_number VARCHAR(20) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    gender VARCHAR(10) NOT NULL,
    date_of_birth DATE NOT NULL,
    class_id INT NULL,
    email VARCHAR(120) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    address VARCHAR(255) NULL,
    guardian_name VARCHAR(100) NULL,
    guardian_phone VARCHAR(20) NULL,
    avatar_path VARCHAR(255) NULL,
    enrollment_date DATE NULL,
    CONSTRAINT fk_students_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    CONSTRAINT fk_students_class FOREIGN KEY (class_id) REFERENCES classrooms(id) ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE TABLE course_students (
    course_id INT NOT NULL,
    student_id INT NOT NULL,
    PRIMARY KEY (course_id, student_id),
    CONSTRAINT fk_course_students_course FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE,
    CONSTRAINT fk_course_students_student FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE grade_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    course_id INT NOT NULL,
    term VARCHAR(20) NOT NULL,
    assessment_type VARCHAR(50) NOT NULL,
    score FLOAT NOT NULL,
    remark VARCHAR(255) NULL,
    recorded_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_grade_records_student FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    CONSTRAINT fk_grade_records_course FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE attendance_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    course_id INT NULL,
    record_date DATE NOT NULL,
    status VARCHAR(20) NOT NULL,
    remarks VARCHAR(255) NULL,
    CONSTRAINT fk_attendance_student FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    CONSTRAINT fk_attendance_course FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE TABLE leave_requests (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    reason VARCHAR(255) NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    approver_id INT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    reviewed_at DATETIME NULL,
    CONSTRAINT fk_leave_requests_student FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    CONSTRAINT fk_leave_requests_approver FOREIGN KEY (approver_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE TABLE announcements (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(150) NOT NULL,
    content TEXT NOT NULL,
    author_id INT NULL,
    target_roles VARCHAR(255) NOT NULL DEFAULT 'all',
    is_pinned TINYINT(1) NOT NULL DEFAULT 0,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_announcements_author FOREIGN KEY (author_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE TABLE todo_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    content VARCHAR(255) NOT NULL,
    due_date DATE NULL,
    is_completed TINYINT(1) NOT NULL DEFAULT 0,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_todo_items_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE system_messages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    title VARCHAR(150) NOT NULL,
    body TEXT NOT NULL,
    is_read TINYINT(1) NOT NULL DEFAULT 0,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_system_messages_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE system_settings (
    `key` VARCHAR(100) PRIMARY KEY,
    `value` TEXT NULL,
    description VARCHAR(255) NULL
) ENGINE=InnoDB;

CREATE TABLE data_backups (
    id INT AUTO_INCREMENT PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(255) NOT NULL,
    created_by INT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_data_backups_user FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE TABLE operation_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NULL,
    action VARCHAR(100) NOT NULL,
    resource VARCHAR(100) NULL,
    description VARCHAR(255) NULL,
    ip_address VARCHAR(45) NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_operation_logs_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE TABLE uploaded_files (
    id INT AUTO_INCREMENT PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    stored_name VARCHAR(255) NOT NULL,
    uploader_id INT NULL,
    file_type VARCHAR(50) NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_uploaded_files_user FOREIGN KEY (uploader_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB;

-- 预置权限
INSERT INTO permissions (code, name, category) VALUES
('dashboard.view', '查看仪表盘', 'menu'),
('students.manage', '学生管理', 'menu'),
('classes.manage', '班级管理', 'menu'),
('teachers.manage', '教师管理', 'menu'),
('courses.manage', '课程管理', 'menu'),
('grades.manage', '成绩管理', 'menu'),
('attendance.manage', '考勤管理', 'menu'),
('announcements.manage', '公告管理', 'menu'),
('profile.view', '个人中心', 'menu'),
('settings.manage', '系统设置', 'menu'),
('students.export', '学生导出', 'action'),
('students.import', '学生导入', 'action'),
('grades.export', '成绩导出', 'action');

INSERT INTO roles (name, description) VALUES
('管理员', '系统管理员'),
('教师', '教师用户'),
('学生', '学生用户');

-- 角色权限映射
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id FROM roles r CROSS JOIN permissions p WHERE r.name = '管理员';

INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r
JOIN permissions p ON p.code IN (
  'dashboard.view', 'students.manage', 'classes.manage', 'courses.manage',
  'grades.manage', 'attendance.manage', 'announcements.manage', 'profile.view',
  'students.import', 'students.export', 'grades.export'
)
WHERE r.name = '教师';

INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r
JOIN permissions p ON p.code IN ('dashboard.view', 'profile.view', 'announcements.manage')
WHERE r.name = '学生';

-- 预置账号
INSERT INTO users (username, email, phone, password_hash, first_login) VALUES
('admin', 'admin@example.com', '13800000000', 'scrypt:32768:8:1$7EHhWGx2L2EJcE6E$c1823f3eeee2e0b5b70eae0dd3d47c9f28b8bed3ffc89191cbe9d39609b48154fac648f8e04cc7850a460c84f7deb3ef08bcd90e56a4cbdf5a65d37d4b0a1721', 1),
('teacher1', 'teacher1@example.com', '13900000001', 'scrypt:32768:8:1$CjoeKpIAEJ7tOH3B$986f2162a4707e2a8ebfca6042d1e67833c6076ffac92c0c88287102afc88b80ed8d4d708398e857def247d1d9777d3c924dbd6bffebcf1560d43178403f08c5', 1),
('student1', 'student1@example.com', '13700000001', 'scrypt:32768:8:1$AEtkXsIZqyYLyUTo$0f528c2c3e384974ffffe6408ce13fa68ef6d9606627c2b0ec6604915dd9c98913050e5ec6a12f5d611994c0a201bf1f70d5f53deb62bbcac66596dba7a67513', 1);

INSERT INTO user_roles (user_id, role_id)
SELECT u.id, r.id FROM users u JOIN roles r ON u.username = 'admin' AND r.name = '管理员';
INSERT INTO user_roles (user_id, role_id)
SELECT u.id, r.id FROM users u JOIN roles r ON u.username = 'teacher1' AND r.name = '教师';
INSERT INTO user_roles (user_id, role_id)
SELECT u.id, r.id FROM users u JOIN roles r ON u.username = 'student1' AND r.name = '学生';

-- 教师与班级
INSERT INTO teachers (user_id, employee_number, name, gender, email, phone, professional_title, hire_date)
SELECT u.id, 'T2023001', '李明', '男', 'teacher1@example.com', '13900000001', '高级教师', '2015-09-01'
FROM users u WHERE u.username = 'teacher1';

INSERT INTO classrooms (name, grade_level, description, head_teacher_id) VALUES
('高一(1)班', '高一', '理科实验班', 1),
('高一(2)班', '高一', '综合发展班', 1);

-- 课程 & 课表
INSERT INTO courses (code, name, credit, description, classroom_id, teacher_id) VALUES
('C101', '语文', 3, '高中语文必修课程', 1, 1),
('C102', '数学', 4, '高中数学基础课程', 1, 1),
('C201', '英语', 3, '英语听说读写综合训练', 2, 1);

INSERT INTO course_schedules (course_id, weekday, start_time, end_time, location) VALUES
(1, 0, '08:00:00', '09:30:00', '教学楼A-301'),
(2, 2, '10:00:00', '11:30:00', '教学楼A-302'),
(3, 4, '14:00:00', '15:30:00', '语言中心-201');

-- 学生数据
INSERT INTO students (user_id, student_number, name, gender, date_of_birth, class_id, email, phone, address, guardian_name, guardian_phone, enrollment_date)
SELECT u.id, 'S2023001', '张三', '男', '2006-03-18', 1, 'student1@example.com', '13700000001', '杭州市西湖区 1 号', '张父', '13788888888', '2021-09-01'
FROM users u WHERE u.username = 'student1';

INSERT INTO students (student_number, name, gender, date_of_birth, class_id, email, phone, address, guardian_name, guardian_phone, enrollment_date) VALUES
('S2023002', '李四', '女', '2006-07-05', 1, 'lisi@example.com', '13700000002', '杭州市滨江区 8 号', '李母', '13799999999', '2021-09-01'),
('S2023003', '王五', '男', '2006-11-12', 2, 'wangwu@example.com', '13700000003', '杭州市余杭区 6 号', '王父', '13611112222', '2021-09-01');

INSERT INTO course_students (course_id, student_id) VALUES
(1, 1), (1, 2), (2, 1), (2, 2), (3, 3);

-- 成绩与考勤
INSERT INTO grade_records (student_id, course_id, term, assessment_type, score, remark) VALUES
(1, 1, '2023-2024上学期', '期中', 88, '作文表现良好'),
(1, 2, '2023-2024上学期', '期中', 92, '逻辑思维优秀'),
(2, 1, '2023-2024上学期', '期中', 81, NULL),
(2, 2, '2023-2024上学期', '期中', 78, '需加强几何部分'),
(3, 3, '2023-2024上学期', '期中', 85, NULL);

INSERT INTO attendance_records (student_id, course_id, record_date, status, remarks) VALUES
(1, 1, '2024-03-01', '出勤', NULL),
(1, 2, '2024-03-01', '出勤', NULL),
(2, 2, '2024-03-01', '缺勤', '感冒请假'),
(3, 3, '2024-03-01', '出勤', NULL);

INSERT INTO leave_requests (student_id, start_date, end_date, reason, status, approver_id, reviewed_at) VALUES
(2, '2024-03-02', '2024-03-03', '生病休息', 'approved', (SELECT id FROM users WHERE username = 'teacher1'), '2024-03-01 09:00:00');

-- 应用内容
INSERT INTO announcements (title, content, author_id, target_roles, is_pinned) VALUES
('校园网络升级通知', '本周末将对校园网络进行维护，请合理安排上网时间。', (SELECT id FROM users WHERE username = 'admin'), 'all', 1),
('月考安排', '高一各班月考安排如下，请班主任组织学生准时参加。', (SELECT id FROM users WHERE username = 'teacher1'), '教师,学生', 0);

INSERT INTO todo_items (user_id, content, due_date, is_completed) VALUES
((SELECT id FROM users WHERE username = 'admin'), '检查学生导入模板', '2024-03-15', 0),
((SELECT id FROM users WHERE username = 'teacher1'), '更新课程教案', '2024-03-10', 0);

INSERT INTO system_messages (user_id, title, body, is_read) VALUES
((SELECT id FROM users WHERE username = 'student1'), '欢迎加入学生信息管理系统', '请及时完善个人资料并关注最新通知。', 0);

INSERT INTO system_settings (`key`, `value`, description) VALUES
('school_name', '未来高中', '学校名称显示'),
('contact_phone', '0571-88888888', '校务联系电话');

INSERT INTO data_backups (filename, file_path, created_by) VALUES
('backup_202403010900.sql', 'backups/backup_202403010900.sql', (SELECT id FROM users WHERE username = 'admin'));

INSERT INTO operation_logs (user_id, action, resource, description, ip_address) VALUES
((SELECT id FROM users WHERE username = 'admin'), 'create', 'announcement', '发布公告 校园网络升级通知', '127.0.0.1');

INSERT INTO uploaded_files (filename, stored_name, uploader_id, file_type) VALUES
('students_template.xlsx', '20240301_students_template.xlsx', (SELECT id FROM users WHERE username = 'admin'), 'excel');

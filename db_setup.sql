DROP TABLE IF EXISTS posts;
DROP TABLE IF EXISTS users;

-- 1. 회원 테이블
CREATE TABLE users (
    id VARCHAR(50) PRIMARY KEY,
    pw VARCHAR(255) NOT NULL,
    name VARCHAR(50) NOT NULL,
    gender VARCHAR(10),
    birthdate DATE,         
    school VARCHAR(100) NOT NULL,
    profile_img VARCHAR(255)
);

-- 2. 게시글 테이블
CREATE TABLE posts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    author VARCHAR(50),
    post_pw VARCHAR(255), 
    filename VARCHAR(255), 
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (author) REFERENCES users(id) ON DELETE CASCADE
);
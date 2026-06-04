-- Codyssey 문제5: mars_weather 테이블 생성
-- MySQL Workbench에서 실행하거나 mars_weather_summary.py가 자동 생성합니다.

CREATE DATABASE IF NOT EXISTS codyssey
    DEFAULT CHARACTER SET utf8mb4
    DEFAULT COLLATE utf8mb4_unicode_ci;

USE codyssey;

DROP TABLE IF EXISTS mars_weather;

CREATE TABLE mars_weather (
    weather_id INT NOT NULL AUTO_INCREMENT,
    mars_date DATETIME NOT NULL,
    temp INT NOT NULL,
    storm INT NOT NULL,
    PRIMARY KEY (weather_id)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4;

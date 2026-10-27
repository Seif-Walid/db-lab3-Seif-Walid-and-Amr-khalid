DROP DATABASE IF EXISTS company;
CREATE DATABASE company;
USE company;

-- 1. Create EMPLOYEauthor_idE table
-- Primary key: ssn
CREATE TABLE EMPLOYEE (
    ssn             INT            NOT NULL,
    fname           VARCHAR(50)    NOT NULL,
    lname           VARCHAR(50)    NOT NULL,
    bdate           DATE,
    address         VARCHAR(100),
    gender          CHAR(1),
    salary          DECIMAL(10, 2),
    Dno             INT,
    PRIMARY KEY (ssn)
);

-- 2. Create DEPARTMENT table
-- Primary key: Dnumber
-- Foreign key: mgr_ssn references EMPLOYEE(ssn)
CREATE TABLE DEPARTMENT (
    Dnumber         INT            NOT NULL,
    Dname           VARCHAR(50)    NOT NULL,
    mgr_ssn         INT,
    mgr_start_date  DATE,
    PRIMARY KEY (Dnumber),
    FOREIGN KEY (mgr_ssn) REFERENCES EMPLOYEE(ssn)
);

-- 3. Add foreign key on EMPLOYEE table pointing to DEPARTMENT(Dnumber)
-- (Added with ALTER TABLE to resolve the circular reference between EMPLOYEE and DEPARTMENT)
ALTER TABLE EMPLOYEE
    ADD FOREIGN KEY (Dno) REFERENCES DEPARTMENT(Dnumber);

-- 4. Create PROJECT table
-- Primary key: Pnumber
-- Foreign key: Dno references DEPARTMENT(Dnumber)
CREATE TABLE PROJECT (
    Pnumber         INT            NOT NULL,
    Pname           VARCHAR(50)    NOT NULL,
    Plocation       VARCHAR(50),
    Dno             INT,
    PRIMARY KEY (Pnumber),
    FOREIGN KEY (Dno) REFERENCES DEPARTMENT(Dnumber)
);

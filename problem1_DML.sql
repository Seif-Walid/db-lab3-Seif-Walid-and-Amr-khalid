
USE company;

-- 1. Insert records into EMPLOYEE (initial insert with Dno as NULL to respect foreign keys)
INSERT INTO EMPLOYEE (ssn, fname, lname, bdate, address, gender, salary, Dno) VALUES
(101, 'Ahmed', 'Ali', '1985-03-15', '12 Alexandria St, Alexandria', 'M', 8500.00, NULL),
(102, 'Sara', 'Hassan', '1990-07-22', '45 Corniche Ave, Alexandria', 'F', 9200.00, NULL),
(103, 'Omar', 'Khaled', '1988-11-05', '8 El-Horreya Rd, Alexandria', 'M', 7800.00, NULL),
(104, 'Mona', 'Ibrahim', '1995-02-18', '20 Stanley St, Alexandria', 'F', 6500.00, NULL);

-- 2. Insert records into DEPARTMENT (referencing manager ssn from EMPLOYEE)
INSERT INTO DEPARTMENT (Dnumber, Dname, mgr_ssn, mgr_start_date) VALUES
(1, 'Research', 101, '2020-01-01'),
(2, 'Administration', 102, '2019-06-15'),
(3, 'Headquarters', 103, '2018-03-01');

-- 3. Update EMPLOYEE records with their department numbers (Dno)
UPDATE EMPLOYEE SET Dno = 1 WHERE ssn = 101;
UPDATE EMPLOYEE SET Dno = 2 WHERE ssn = 102;
UPDATE EMPLOYEE SET Dno = 3 WHERE ssn = 103;
UPDATE EMPLOYEE SET Dno = 1 WHERE ssn = 104;

-- 4. Insert records into PROJECT (referencing Dno from DEPARTMENT)
INSERT INTO PROJECT (Pnumber, Pname, Plocation, Dno) VALUES
(10, 'ProductX', 'Alexandria', 1),
(20, 'ProductY', 'Cairo', 1),
(30, 'Reorganization', 'Alexandria', 2),
(40, 'Newbenefits', 'Alexandria', 3);

# ECE651-Project-Back-end

## Server

SSH: ece651@66.112.218.89:29611 (Password: ece651)

Flask running at http://66.112.218.89:5000.

## API

#### Register

##### Request

URL: /api/v1/user/register

Method: POST

| Key      | Datatype    | Note                 |
| -------- | ----------- | -------------------- |
| name     | VARCHAR(20) |                      |
| username | VARCHAR(20) | not null, unique     |
| password | String      | not null             |
| gender   | BOOLEAN     | 0: female    1: male |

##### Response

HTTP 201:

| Key   | Datatype | Note               |
| ----- | -------- | ------------------ |
| token | String   | expire in one hour |

HTTP 400: missing username or password

HTTP 409: existing username



#### Login

URL: /api/v1/user/login

Method: POST

##### Request

| Key      | Datatype    | Note |
| -------- | ----------- | ---- |
| username | VARCHAR(20) |      |
| password | String      |      |

##### Response

HTTP 200:

| Key   | Datatype | Note               |
| ----- | -------- | ------------------ |
| token | String   | expire in one hour |

HTTP 400: missing username or password

HTTP 401: wrong username or password
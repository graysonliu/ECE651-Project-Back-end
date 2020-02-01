# ECE651-Project-Back-end

## Server

SSH: ece651@66.112.218.89:29611 (Password: ece651)

Flask running at http://66.112.218.89:5000.

## API

Put token in HTTP headers.

### Login

#### /api/v1//login

##### POST

Request Body

| Key      | Datatype    | Note |
| -------- | ----------- | ---- |
| username | VARCHAR(20) |      |
| password | String      |      |

Response Body

| Key   | Datatype | Note               |
| ----- | -------- | ------------------ |
| id    | INT      |                    |
| token | String   | expire in one hour |

### Users

#### /api/v1/users

| HTTP Method | Result                   | Permission |
| ----------- | ------------------------ | ---------- |
| GET         | Get a list of all users. | admin      |
| POST        | Register a new user.     | user       |

##### GET

Response Body

| Key       | Datatype | Note |
| --------- | -------- | ---- |
| user_list | List     |      |

##### POST

Request Body

| Key      | Datatype    | Note                 |
| -------- | ----------- | -------------------- |
| name     | VARCHAR(20) |                      |
| username | VARCHAR(20) | not null, unique     |
| password | String      | not null             |
| gender   | BOOLEAN     | 0: female    1: male |

Response Body

| Key   | Datatype | Note               |
| ----- | -------- | ------------------ |
| id    | INT      |                    |
| token | String   | expire in one hour |

### Error Handling

Using HTTP status code with brief description of the error.
# ECE651-Project-Back-end

## Server

SSH: ece651@66.112.218.89:29611 (Password: ece651)

Flask running at http://66.112.218.89:5000.

## API

Put token in HTTP headers when it is required.

All data interchanges are in JSON format.

### Login

#### /api/v1//login

##### POST

Request Body

| Key      | Datatype    | Note       |
| -------- | ----------- | ---------- |
| username | VARCHAR(20) | compulsory |
| password | String      | compulsory |

Response Body

| Key   | Datatype | Note                |
| ----- | -------- | ------------------- |
| id    | INT      |                     |
| token | String   | expires in one hour |

### Users

#### /api/v1/users

| HTTP Method | Result                              | Note           |
| ----------- | ----------------------------------- | -------------- |
| GET         | Get a list consisting of all users. | admin only     |
| POST        | Register a new user.                | token required |

##### GET

Response Body

| Key       | Datatype | Note |
| --------- | -------- | ---- |
| user_list | List     |      |

##### POST

Request Body

| Key      | Datatype    | Note                           |
| -------- | ----------- | ------------------------------ |
| name     | VARCHAR(20) | optional                       |
| username | VARCHAR(20) | compulsory, unique in database |
| password | String      | compulsory                     |
| gender   | INT         | optional                       |

Response Body

| Key   | Datatype | Note                |
| ----- | -------- | ------------------- |
| id    | INT      |                     |
| token | String   | expires in one hour |

#### /api/v1/users/\<int:user_id\>

| HTTP Method | Result                          | Note           |
| ----------- | ------------------------------- | -------------- |
| GET         | Get information of the user.    | token required |
| PATCH       | Change information of the user. | token required |

##### GET

Send request to see the response body.

##### PATCH

Request Body

| Key          | Datatype    | Note                                          |
| ------------ | ----------- | --------------------------------------------- |
| name         | VARCHAR(20) | optional                                      |
| username     | VARCHAR(20) | optional, unique in database                  |
| gender       | INT         | optional                                      |
| old_password | String      | optional, compulsory when new_password exists |
| new_password | String      | optional, compulsory when old_password exists |

### Error Code

Using HTTP status code with a brief description of the error.
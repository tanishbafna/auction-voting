# Site Map

- Home Page (`/`) [GET, @nologin]
    - Sign Up Form
        - Enter name, username, password, admin passcode, co-admin passcode
        - POST request to `/signUp` (possible AJAX to check if username is unique)
    - Login Form
        - Enter username, password
        - POST request to `/login` (possible AJAX to check if password is correct)

- Sign Up (`/signUp`) [POST, @nologin]
    - Create new user in database if admin passcode is correct and user does not already exist
    - Give user create room permissions (co-admin) if co-admin passcode is correct
    - Redirect to `/`

- Login (`/login`) [POST, @nologin]
    - Authenticate user
    - Redirect to `/rooms`

- Rooms (`/rooms`) [GET, @login]
    - Table of active rooms
    - Create new room
        - Enter number of players
        - Enter starting points
        - Enter deduction points for each added option
        - POST request to `/rooms/create`
    - Join room
        - Enter room ID
        - GET request to `/rooms/<str:roomId>`

- Create Room (`/rooms/create`) [POST, @login, @coAdmin]
    - Create new room in database if user has permissions to create room
    - Give user admin access to room
    - Add player information to room database
    - Redirect to `/rooms/<str:roomId>/options`

- Room (`/rooms/<str:roomId>`) [GET, @login]
    - Allow if player capacity is not full, else redirect to `/rooms`
    - Add player information to room database if player is not already in room
    - Redirect to `/rooms/<str:roomId>/options`

- Add Options (`/rooms/<str:roomId>/options`) [GET, @login, @roomAccess]
    - View Room Info
        - Room ID
        - Number of Players
        - Starting Points
        - Deduction Points
    - Option Form
        - Enter number of options to add
        - Reduce points by deduction points for each added option
        - Enter option names
        - POST request to `/rooms/<str:roomId>/submitOptions`

- Submit Options (`/rooms/<str:roomId>/submitOptions`) [POST, @login, @roomAccess]
    - Add options to room database under user ID
    - Redirect to `/rooms/<str:roomId>/waitingRoom`

- Waiting Room (`/rooms/<str:roomId>/waitingRoom`) [GET, @login, @roomAccess]
    - View Room Info
        - Room ID
        - Number of Players
        - Starting Points
        - Deduction Points
        - Number of unique players who have entered options
    - View Options Button
        - GET request to `/rooms/<str:roomId>/vote` if all players have entered options (possible AJAX)

- Vote (`/rooms/<str:roomId>/vote`) [GET, @login, @roomAccess]
    - Redirect to `/rooms/<str:roomId>/waitingRoom` if all players have not entered options
    - View Room Info
        - Room ID
        - Number of Players
        - Starting Points
        - Deduction Points
    - View User Info
        - Name
        - Current Points
        - Options entered
    - View Options
        - Do not show own options
        - Option names with point value inputs
        - Deduct points from player's total points
        - POST request to `/rooms/<str:roomId>/submitVote` if current points == 0 and own option points not more than 50% of total points (possible AJAX)

- Submit Vote (`/rooms/<str:roomId>/submitVote`) [POST, @login, @roomAccess]
    - Ensure that points allocated sums up to starting points, else redirect to `/rooms/<str:roomId>/vote`
    - Ensure that player has not voted for own options with more than 50% of their total points, else redirect to `/rooms/<str:roomId>/vote`
    - Add point allocations to room database under user ID
    - Redirect to `/rooms/<str:roomId>/waitingResults`

- Waiting Results (`/rooms/<str:roomId>/waitingResults`) [GET, @login, @roomAccess]
    - View Room Info
        - Room ID
        - Number of Players
        - Starting Points
        - Deduction Points
        - Number of unique players who have voted
    - View Results Button
        - GET request to `/rooms/<str:roomId>/results` if all players have voted (possible AJAX)
    
- Results (`/rooms/<str:roomId>/results`) [GET, @login, @roomAccess]
    - Redirect to `/rooms/<str:roomId>/waitingResults` if all players have not voted
    - Store winning option in room database
    - View Room Info
        - Room ID
        - Number of Players
        - Starting Points
        - Deduction Points
    - View User Info
        - Name
        - Current Points
        - Options entered
        - Points allocated
    - View Results
        - Option names with summed up points
        - Highlight winning option
    - End Game Button
        - View only if player is room admin
        - POST request to `/rooms/<str:roomId>/endGame`
    - Return to rooms button
        - Redirect to `/rooms`

- End Game (`/rooms/<str:roomId>/endGame`) [POST, @login, @roomAccess, @roomAdmin]
    - Delete room option from database if player is room admin
    - Redirect to `/rooms`

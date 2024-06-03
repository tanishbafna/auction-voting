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
        - Enter Room Code
        - GET request to `/rooms/<room_code>`

- Create Room (`/rooms/create`) [POST, @login, @coAdmin]
    - Create new room in database if user has permissions to create room
    - Give user admin access to room
    - Add player information to room database
    - Redirect to `/rooms/<room_code>/options`

- Room (`/rooms/<room_code>`) [GET, @login]
    - Allow if player capacity is not full, else redirect to `/rooms`
    - Add player information to room database if player is not already in room
    - Redirect to `/rooms/<room_code>/options`

- Add Options (`/rooms/<room_code>/options`) [GET, @login, @roomAccess]
    - View Room Info
        - Room Code
        - Number of Players
        - Starting Points
        - Deduction Points
    - Option Form
        - Enter number of options to add (max 3)
        - Reduce points by deduction points for each added option
        - Enter option names
        - POST request to `/rooms/<room_code>/submitOptions`

- Submit Options (`/rooms/<room_code>/submitOptions`) [POST, @login, @roomAccess]
    - Add options to room database under user ID
    - Redirect to `/rooms/<room_code>/waitingRoom`

- Waiting Room (`/rooms/<room_code>/waitingRoom`) [GET, @login, @roomAccess]
    - View Room Info
        - Room Code
        - Number of Players
        - Starting Points
        - Deduction Points
        - Number of unique players who have entered options
    - View Options Button
        - GET request to `/rooms/<room_code>/vote` if all players have entered options (possible AJAX)

- Vote (`/rooms/<room_code>/vote`) [GET, @login, @roomAccess]
    - Redirect to `/rooms/<room_code>/waitingRoom` if all players have not entered options
    - View Room Info
        - Room Code
        - Number of Players
        - Starting Points
        - Deduction Points
    - View User Info
        - Name
        - Current Points
        - Options entered
    - View Options
        - Highlight own options
        - Option names with point value inputs
        - Deduct points from player's total points
        - POST request to `/rooms/<room_code>/submitVote` if current points == 0 and own option points not more than 50% of total points (possible AJAX)

- Submit Vote (`/rooms/<room_code>/submitVote`) [POST, @login, @roomAccess]
    - Ensure that points allocated are no greater than current points (post deduction), else redirect to `/rooms/<room_code>/vote`
    - Ensure that player has not voted for own options with more than 50% of their current points, else redirect to `/rooms/<room_code>/vote`
    - Add votes to option database
    - Redirect to `/rooms/<room_code>/waitingResults`

- Waiting Results (`/rooms/<room_code>/waitingResults`) [GET, @login, @roomAccess]
    - View Room Info
        - Room Code
        - Number of Players
        - Starting Points
        - Deduction Points
        - Number of unique players who have voted
    - View Results Button
        - GET request to `/rooms/<room_code>/results` if all players have voted (possible AJAX)
    
- Results (`/rooms/<room_code>/results`) [GET, @login, @roomAccess]
    - Redirect to `/rooms/<room_code>/waitingResults` if all players have not voted
    - Store winning option in room database
    - View Room Info
        - Room Code
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
        - POST request to `/rooms/<room_code>/endGame`
    - Return to rooms button
        - Redirect to `/rooms`

- End Game (`/rooms/<room_code>/endGame`) [POST, @login, @roomAccess, @roomAdmin]
    - Delete room option from database if player is room admin
    - Redirect to `/rooms`

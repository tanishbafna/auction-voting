# Auction Voting

## Step 0: Starting a Room
1. **Create a Room**: One participant creates a room and shares the room code with others (must have admin permissions).
2. **Room Setup**:
   - Define the number of participants allowed in the room (`3 <= n <= 20`).
   - Define the number of points each participant starts with (`x`).
   - Set the cost of additional suggestions (`y`).
   - Decide if the voting is blind (participants never see who suggested which option).
3. **Join the Room**: Other participants join the room using the shared code.

## Step 1: Initial Points and Suggestions
1. **Suggest Initial Option**: Each participant suggests one option for free.
2. **Additional Suggestions**: Additional suggestions cost `y` points each, deducted from the participant's starting points (`x`).
3. **Delete Suggestions**: The room creator can delete any overlapping suggestions before the voting starts. The points spent on deleted suggestions are refunded.
4. **Re-enter Suggestions**: Participants can re-enter suggestions if all their suggestions were deleted.

## Step 2: Distribution of Points
1. **Lists All Options**: Displays all suggested options for all participants.
2. **Anonymity**: Participants do not know who suggested which option.
3. **Distribute Points**:
   - Participants distribute their points across all options.
   - No more than 50% of current points can be allocated to one's own suggestion(s).
   - Points must be distributed in whole numbers and all points must be used.

## Step 3: Determining the Winner
1. **Winning Option**: The option with the highest total points wins.
2. **Handling Ties**:
   - If there's a tie, a runoff vote is conducted.
   - In the runoff, participants receive (10 x number of tied options) points to vote among the tied options only.
   - Here, there are no restrictions on the number of points that can be allocated to one's own suggestion(s).
3. **Blind Voting Results**: If the voting was blind, the identity of the participants who suggested each option remains anonymous even in the results.

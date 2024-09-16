# Why? How? What?

## Use cases

### Standard user/consumer activities
- Book a coffee
- Check account balance
- Check statistics (aka "What is my performance level?" or "Am I consuming too much coffee?")

#### Accounting

- Generate balance overview (list sorted by name/balance)
- List users with negative balance larger than X

#### User management

- Adding new user
- Removing old user
- Deactivate user

#### Account & price management

- Adjust account balance for specific user
- Adjust coffee price (all coffee bookings must lookup current coffee price!)
- Book repair/maintenance cost

##### Account views

- Sorted list according to account balance
- Possibly generation of list of users with account balances of less than - XX €? --> Payup! list
- Possibly automate generation of mails for users with account balances of less than - XX €?
- Global trend aka "Do we need to adjust the price"

#### Statistics

- Distribution of coffees consumption for a day/week/month/quarter/year
- Total coffees booked per day/week/month/quarter/year/overall
- Total amount of kilograms of coffee beans consumed per time period (week/month/quarter/year/overall)
- Bar chart with amount of kg per time period over time (avg. consumption per week for all weeks, avg. per month for all months, etc.)
- Top 3 consumers per week/month/quarter/year/overall
- Repair/Maintenance cost per time period (month/quarter/year/overall)

#### Fun stuff

- Automatic estimation of coffee consumption development
- Announcement of personal and total number of coffees per day ("It's your 3rd coffee today and the 56th in total")
- Random joke for every booked coffee
- Random coffee facts

### Roles

#### Coffee consumer

Our tired standard users

- Identified purely by RFID ID of ZF ID
- Book a coffee
- Check account balance
- Book buying a pack of coffee/balance account

#### Admin

Technical administration with admin priviledges

- Identified by username/pw combo in admin interface or SSH access to machine (Raspi, etc.)

# Driving LogBook

CS50 Final Project 2020/2021

**Video Demo:**  <URL HERE>


## Short Description:
LogBook is a web-application - tool to help user keeping track of job-related rides for the future tax deduction.
After registration and logging in user can add one or multiple vehicles to the system and after that start adding rides using special form. Rides could be seen on a webpage or be exported to CSV. Table of rides can be filtered by vehicle(s) or period needed.

**This LogBook is implemented using:**  
* Flask
* Html
* CSS
* Jinja
* Js
* SQL
* Bootstrap components
* Postgres as a database
* Responsive design 


## Whats inside:

1. **Landing Page** describes basic info about the app

2. **Register Page**
    * Simple registration form
    * Validates input, checks correctness of email and password provided
    * Checks whether email wasn't used yet
    * Redirects straigt to the _Vehicles_-page after registration

3. **Log In Page**
    * Simple Log in form
    * Validates input
    * Redirects to the main working page called _Rides_

4. **Vehicles Page**
    * List of users vehicles 
    * "Add new vehicle" form: 
        * Sets defaults for rides
    * Possibility to delete a vehicle

5. **Rides Page**
    * Shows a list of added rides and total deductible amount
    * "Add ride" form:
        * Allows user to choose one vehicle from previously added vehicles
        * Prefills most of the fields based on chosen vehicle 
            * User can overwrite dafaults
        * Validates fields, checks for correct input
    * User may want to filter the table of rides by:
        a. Period of time when rides were complited
        b. One or multiple users vehicle 
    * User can save filtered or full table of rides as a CSV document at the bottom of the table

6. **Log Out Button** clears the session and redirects to the _Landing Page_
        
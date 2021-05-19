# Driving LogBook

CS50 Final Project 2020/2021

**Video Demo:**  https://youtu.be/8ZyYDxqNGCc


## Short Description:
LogBook is a web-application - tool to help user keeping track of job-related rides for the future tax deduction.
After registration and logging in user can add one or multiple vehicles to the system and after that start adding rides using special form. Rides could be seen on a webpage or be exported to CSV. Table of rides can be filtered by vehicle(s) or period needed.

There are three database tables used for this project: users, vehicles and rides

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

1. **Landing Page** describes basic info about the app.
    I desided to use some Bootstrap components as a base to make this page look more complex. I made some corrections to almost all components by adding more CSS, for example to make the carousel work smoothly. 

2. **Register Page**
    * Simple registration form
    * Validates input, checks correctness of email and password provided
    * Checks whether email wasn't used yet
    * Redirects straigt to the _Vehicles_-page after registration

    The form prompts user to provide an email address, strong password and password confirmation. Form instantly validates provided input and rises an exeption message if email or password field is filled incorrectly, this was implemented using html tags and regex pattern. Flask application also checks the input and rises an alert message in case of an error. App is also quering a database for username to check whether provided username wasn't used yet.
    After submitting the form new row with user information is inserted to the database (users table), new session is opened and user is redirected straight to the Vehicles page, no need to login after registration.

3. **Log In Page**
    * Simple Log in form
    * Validates input
    * Redirects to the main working page called _Rides_

    App validates input, checks if user exists by querying database and opens session if no error occured. User will be redirected to the main working page. 
    

4. **Vehicles Page**
    * List of users vehicles 
    * "Add new vehicle" form: 
        * Sets defaults for rides
    * Possibility to delete a vehicle

    Login is required to visit this page. User may add one or more vehicles to his list by clicking on "Add new vehicle" button and filling opened modal form. This form takes vehicles registration plate number and checks if correct plate number was provided (regex pattern for Finnish registration plate formats was used to check the input). User is prompted to provide mileage allowance for this car and last odometer reading. Those defaults would be used to prefill some fields while adding a new ride and calculate distance and total amount of deduction later. Error message will appear in case of incorrect input. After submitting the form new vehicle row will be added to the database (vehicles table) and new line with its modification time will appear on the "Vehicles" page. User may want to delete added vehicles and it is easy to do by clicking on the bin icon at the end of the line. I desided to create a new modal to ask a user to confirm this action to prevent accidental deleting. 


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

    Login is required to visit this page. List of all added rides and calculated amount of tax deduction will be displayed at this page. There are four buttons on the page: Add ride, Filters, To full list ans Import csv. To add a new ride user need to fill the form: first of all user needs to choose a vehicle from the selector and most of the fields would be prefilled (but each may be overwitten) based on the vehicles defaults. User may provide an odometer reading after the ride was complete or rides distance, those numbers are connected and are calculating automatically, based on each others value. Last odometer reading will be updated after submitting the form. App is parsing and formatting inputs date and time fields to add them to the database and display properly on the page. After submitting the form new line will appear on the "Rides" page and new row will be added to Rides table. in the database. 
    User may want to filter the table, so it's possible by choosing the period needed in a special filter field and/or by checking one or more vehicles to be displayed in the list. "To full list" button will cancel filters and full table of added rides will be displayed. 
    User can easily save his list of rides in CSV format by clicking "Import csv" button. Document is ready to be sent to the bookkeeper for the future taxation.

6. **Log Out Button** clears the session and redirects to the _Landing Page_
        
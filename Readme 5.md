Clinical Records API

About This Project

For this assignment, I created a basic clinical records API using Python and Flask. The purpose of the project is to add, view, update, and delete clinical records. The information is saved using an SQLite database and a JSON Lines file.

Technologies Used

* Python
* Flask
* SQLite
* SQLAlchemy
* Pydantic
* JSON Lines

Additional Fields

I added three fields to the clinical records:

* Diagnosis
* Visit Date
* Provider Name

Installation

The following packages are needed for the application:

pip install flask sqlalchemy pydantic

Starting the Application

python app.py

Open the application at:

http://127.0.0.1:5000

API Endpoints

Method	Endpoint	Description
GET	/clinical/	Shows all records
POST	/clinical/	Adds a new record
GET	/clinical/1	Shows one record
PUT	/clinical/1	Updates a record
DELETE	/clinical/1	Removes a record
GET	/clinical/schema	Shows the data validation schema

Testing the API

The following commands can be used to test the different API operations.

Add a record

curl -X POST http://127.0.0.1:5000/clinical/ -H "Content-Type: application/json" -d "{\"patient_name\":\"Jordan Smith\",\"age\":35,\"diagnosis\":\"Annual checkup\",\"visit_date\":\"2026-11-10\",\"provider_name\":\"Dr. Taylor\"}"

View all records

curl http://127.0.0.1:5000/clinical/

View one record

curl http://127.0.0.1:5000/clinical/1

Update a record

curl -X PUT http://127.0.0.1:5000/clinical/1 -H "Content-Type: application/json" -d "{\"patient_name\":\"Jordan Smith\",\"age\":35,\"diagnosis\":\"Follow-up visit\",\"visit_date\":\"2026-11-10\",\"provider_name\":\"Dr. Taylor\"}"

Delete a record

curl -X DELETE http://127.0.0.1:5000/clinical/1

Test invalid information

This example uses an age of 200 to check that the API rejects information that does not meet the validation rules.

curl -X POST http://127.0.0.1:5000/clinical/ -H "Content-Type: application/json" -d "{\"patient_name\":\"Jordan Smith\",\"age\":200,\"diagnosis\":\"Annual checkup\",\"visit_date\":\"2026-11-10\",\"provider_name\":\"Dr. Taylor\"}"

View the validation schema

curl http://127.0.0.1:5000/clinical/schema

Data Storage

The application uses two files to store the records:

* clinical_data.db stores information in SQLite.
* data/clinical_data.jsonl stores the records in JSON Lines format.

The application is designed to keep both storage locations updated when records are changed.

Reflection

While working on this assignment, I learned how to connect a Flask API to an SQLite database and a JSON Lines file. I also added three fields to the clinical records: diagnosis, visit date, and provider name. One thing I found interesting was learning how the same information could be saved in two different formats. I also learned more about how SQLAlchemy works with databases and how Pydantic checks information before it is saved. This assignment helped me understand how APIs can manage information and how different storage methods can work together. In the future, I would like to learn more about how healthcare systems share information securely.
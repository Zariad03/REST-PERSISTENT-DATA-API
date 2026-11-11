import os
import json

from flask import Flask, jsonify, request, render_template_string
from sqlalchemy import create_engine, Column, Integer, String, Date, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker
from pydantic import BaseModel, Field, ValidationError
from datetime import date

app = Flask(__name__)

# Database setup
engine = create_engine("sqlite:///clinical_data.db")
Base = declarative_base()
Session = sessionmaker(bind=engine)

# JSON file setup
os.makedirs("data", exist_ok=True)
JSON_FILE = "data/clinical_data.jsonl"


# Database model
class ClinicalRecord(Base):
    __tablename__ = "clinical_records"

    id = Column(Integer, primary_key=True)
    patient_name = Column(String(100), nullable=False)
    age = Column(Integer, nullable=False)
    diagnosis = Column(String(200), nullable=False)
    visit_date = Column(Date, nullable=False)
    provider_name = Column(String(120), nullable=False)


# Pydantic validation
class RecordSchema(BaseModel):
    patient_name: str = Field(min_length=2, max_length=100)
    age: int = Field(ge=0, le=120)
    diagnosis: str = Field(min_length=2, max_length=200)
    visit_date: date
    provider_name: str = Field(min_length=2, max_length=120)

    class Config:
        extra = "forbid"


# Add missing columns to an existing database
def migrate_database():
    Base.metadata.create_all(engine)

    columns = [
        column["name"] for column in inspect(engine).get_columns("clinical_records")
    ]

    with engine.begin() as connection:
        if "diagnosis" not in columns:
            connection.execute(
                text(
                    "ALTER TABLE clinical_records ADD COLUMN "
                    "diagnosis VARCHAR(200) NOT NULL DEFAULT 'Not provided'"
                )
            )

        if "visit_date" not in columns:
            connection.execute(
                text(
                    "ALTER TABLE clinical_records ADD COLUMN "
                    "visit_date DATE NOT NULL DEFAULT '2000-01-01'"
                )
            )

        if "provider_name" not in columns:
            connection.execute(
                text(
                    "ALTER TABLE clinical_records ADD COLUMN "
                    "provider_name VARCHAR(120) NOT NULL DEFAULT 'Not provided'"
                )
            )


# Convert records to JSON
def record_to_dict(record):
    return {
        "id": record.id,
        "patient_name": record.patient_name,
        "age": record.age,
        "diagnosis": record.diagnosis,
        "visit_date": record.visit_date.isoformat(),
        "provider_name": record.provider_name,
    }


# Update the JSON Lines file
def update_json():
    session = Session()

    try:
        records = session.query(ClinicalRecord).all()

        with open(JSON_FILE, "w", encoding="utf-8") as file:
            for record in records:
                file.write(json.dumps(record_to_dict(record)) + "\n")
    finally:
        session.close()


# Validate incoming information
def validate_data(data):
    if hasattr(RecordSchema, "model_validate"):
        return RecordSchema.model_validate(data).model_dump()

    return RecordSchema(**data).dict()


# Simple browser page
PAGE = """
<h1>Clinical Records</h1>

<form id="recordForm">
    <input id="patient_name" placeholder="Patient Name" required>
    <input id="age" type="number" placeholder="Age" required>
    <input id="diagnosis" placeholder="Diagnosis" required>
    <input id="visit_date" type="date" required>
    <input id="provider_name" placeholder="Provider Name" required>
    <button type="submit">Add Record</button>
</form>

<p id="message">Loading records...</p>
<table border="1" cellpadding="8">
    <thead>
        <tr>
            <th>ID</th><th>Patient</th><th>Age</th>
            <th>Diagnosis</th><th>Visit Date</th>
            <th>Provider</th><th>Actions</th>
        </tr>
    </thead>
    <tbody id="records"></tbody>
</table>

<script>
async function loadRecords() {
    const message = document.getElementById("message");
    message.textContent = "Loading records...";

    try {
        const response = await fetch("/clinical/");
        if (!response.ok) throw new Error("Could not load records.");

        const records = await response.json();
        const table = document.getElementById("records");
        table.innerHTML = "";

        records.forEach(record => {
            const row = document.createElement("tr");

            [
                record.id, record.patient_name, record.age,
                record.diagnosis, record.visit_date, record.provider_name
            ].forEach(value => {
                const cell = document.createElement("td");
                cell.textContent = value;
                row.appendChild(cell);
            });

            const actions = document.createElement("td");

            const edit = document.createElement("button");
            edit.textContent = "Edit";
            edit.onclick = () => editRecord(record);

            const remove = document.createElement("button");
            remove.textContent = "Delete";
            remove.onclick = () => deleteRecord(record.id);

            actions.append(edit, remove);
            row.appendChild(actions);
            table.appendChild(row);
        });

        message.textContent = records.length + " record(s) found.";
    } catch (error) {
        message.textContent = error.message;
    }
}

document.getElementById("recordForm").onsubmit = async function(event) {
    event.preventDefault();

    const data = {
        patient_name: document.getElementById("patient_name").value,
        age: Number(document.getElementById("age").value),
        diagnosis: document.getElementById("diagnosis").value,
        visit_date: document.getElementById("visit_date").value,
        provider_name: document.getElementById("provider_name").value
    };

    const response = await fetch("/clinical/", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(data)
    });

    const result = await response.json();
    document.getElementById("message").textContent =
        response.ok ? "Record added." : JSON.stringify(result);

    if (response.ok) {
        this.reset();
        loadRecords();
    }
};

async function editRecord(record) {
    const diagnosis = prompt("Enter the new diagnosis:", record.diagnosis);
    if (diagnosis === null) return;

    const response = await fetch("/clinical/" + record.id, {
        method: "PUT",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
            patient_name: record.patient_name,
            age: record.age,
            diagnosis: diagnosis,
            visit_date: record.visit_date,
            provider_name: record.provider_name
        })
    });

    document.getElementById("message").textContent =
        response.ok ? "Record updated." : "Update failed.";

    loadRecords();
}

async function deleteRecord(id) {
    if (!confirm("Delete this record?")) return;

    const response = await fetch("/clinical/" + id, {
        method: "DELETE"
    });

    document.getElementById("message").textContent =
        response.ok ? "Record deleted." : "Delete failed.";

    loadRecords();
}

loadRecords();
</script>
"""


@app.route("/")
def home():
    return render_template_string(PAGE)


# View all records or add a record
@app.route("/clinical/", methods=["GET", "POST"])
def clinical_records():
    session = Session()

    if request.method == "GET":
        try:
            records = session.query(ClinicalRecord).all()
            return jsonify([record_to_dict(r) for r in records])
        finally:
            session.close()

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        session.close()
        return jsonify({"error": "A JSON object is required."}), 400

    try:
        record_data = validate_data(data)
    except ValidationError as error:
        session.close()
        return jsonify({"errors": error.errors()}), 400

    try:
        record = ClinicalRecord(**record_data)
        session.add(record)
        session.commit()

        try:
            with open(JSON_FILE, "a", encoding="utf-8") as file:
                file.write(json.dumps(record_to_dict(record)) + "\n")
        except OSError:
            session.delete(record)
            session.commit()
            return jsonify({"error": "Could not save JSON file."}), 500

        return jsonify(record_to_dict(record)), 201
    finally:
        session.close()


# View, update, or delete one record
@app.route("/clinical/<int:record_id>", methods=["GET", "PUT", "DELETE"])
def single_record(record_id):
    session = Session()

    try:
        record = session.get(ClinicalRecord, record_id)

        if record is None:
            return jsonify({"error": "Record not found."}), 404

        if request.method == "GET":
            return jsonify(record_to_dict(record))

        if request.method == "PUT":
            data = request.get_json(silent=True)

            if not isinstance(data, dict):
                return jsonify({"error": "A JSON object is required."}), 400

            try:
                record_data = validate_data(data)
            except ValidationError as error:
                return jsonify({"errors": error.errors()}), 400

            for key, value in record_data.items():
                setattr(record, key, value)

            session.commit()
            update_json()
            return jsonify(record_to_dict(record))

        session.delete(record)
        session.commit()
        update_json()
        return jsonify({"message": "Record deleted."})

    finally:
        session.close()


# Show the validation schema
@app.route("/clinical/schema")
def show_schema():
    if hasattr(RecordSchema, "model_json_schema"):
        return jsonify(RecordSchema.model_json_schema())

    return jsonify(RecordSchema.schema())


if __name__ == "__main__":
    migrate_database()
    update_json()
    app.run(host="0.0.0.0", port=5000)

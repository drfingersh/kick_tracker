# app.py

from flask import Flask, render_template, request, redirect, url_for, session, send_file, flash
import csv
import os
from io import StringIO, BytesIO
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with your own secret key

# Configuration for file uploads
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'csv'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure the uploads directory exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Define all possible fieldnames
ALL_FIELDNAMES = [
    'Kick Type', 'Kicker', 'Temperature', 'Wind Direction', 'Field Type', 'Field Name',
    'Field Goal_Position', 'Field Goal_Yard Line', 'Field Goal_Op Time', 'Field Goal_Result',
    'Kickoff_Yard Line', 'Kickoff_Position', 'Kickoff_Result Yard Line', 'Kickoff_Landing Location', 'Kickoff_Hang Time',
    'Punt_Kick Yard Line', 'Punt_Kick Location', 'Punt_Landed Yard Line', 'Punt_Landing Location', 'Punt_Op Time', 'Punt_Hang Time'
]

# Routes
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/new_workout', methods=['GET', 'POST'])
def new_workout():
    if request.method == 'POST':
        workout_name = request.form['workout_name']
        temperature = request.form['temperature']
        wind_direction = request.form['wind_direction']  # Angle in degrees
        field_type = request.form['field_type']  # 'High School' or 'College'
        field_name = request.form['field_name']
        kickers_input = request.form['kickers']
        kickers = [k.strip() for k in kickers_input.split(',') if k.strip()]

        # Save workout info to session
        session['temperature'] = temperature
        session['wind_direction'] = wind_direction
        session['field_type'] = field_type
        session['field_name'] = field_name
        session['kickers'] = kickers
        session['workout_name'] = workout_name

        # Clear any existing workout filename from session
        session.pop('existing_workout_filename', None)

        # Create a new workout data list in session
        session['workout_data'] = []

        return redirect(url_for('kick_track'))
    else:
        return render_template('new_workout.html')

@app.route('/existing_workout', methods=['GET', 'POST'])
def existing_workout():
    if request.method == 'POST':
        if 'workout_file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['workout_file']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            # Secure the filename
            filename = secure_filename(file.filename)
            # Read the file content without saving it
            file_contents = file.read().decode('utf-8')
            # Parse the CSV content
            csv_reader = csv.DictReader(StringIO(file_contents))
            workout_data = list(csv_reader)
            # Store data in session
            session['workout_data'] = workout_data
            session['workout_name'] = os.path.splitext(filename)[0]
            # Store the original filename in session
            session['existing_workout_filename'] = filename
            # Extract workout metadata from the data
            if workout_data:
                first_row = workout_data[0]
                session['temperature'] = first_row.get('Temperature', '')
                session['wind_direction'] = first_row.get('Wind Direction', '')
                session['field_type'] = first_row.get('Field Type', '')
                session['field_name'] = first_row.get('Field Name', '')
                session['kickers'] = [first_row.get('Kicker', '')]
            else:
                session['temperature'] = ''
                session['wind_direction'] = ''
                session['field_type'] = ''
                session['field_name'] = ''
                session['kickers'] = []
            return redirect(url_for('kick_track'))
        else:
            flash('Invalid file type. Only CSV files are allowed.')
            return redirect(request.url)
    return render_template('existing_workout.html')

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/kick_track', methods=['GET', 'POST'])
def kick_track():
    if 'workout_name' not in session:
        return redirect(url_for('home'))

    kick_type = request.form.get('kick_type', session.get('current_kick_type', 'Field Goal'))
    session['current_kick_type'] = kick_type

    # Read existing kicks from session
    kicks = session.get('workout_data', [])

    return render_template('kick_track.html', kick_type=kick_type, kicks=kicks)

@app.route('/save_kick', methods=['POST'])
def save_kick():
    if 'workout_name' not in session:
        return redirect(url_for('home'))

    kick_type = request.form['kick_type']
    kicker = request.form['kicker']
    data_row = {
        'Kick Type': kick_type,
        'Kicker': kicker,
        'Temperature': session.get('temperature', ''),
        'Wind Direction': session.get('wind_direction', ''),
        'Field Type': session.get('field_type', ''),
        'Field Name': session.get('field_name', ''),
    }

    # Handle inputs based on kick type
    if kick_type == 'Field Goal':
        position = request.form['position']
        yard_line = request.form['yard_line']
        op_time = request.form.get('time_elapsed', '')
        result = request.form.get('result', '')
        data_row['Field Goal_Position'] = position
        data_row['Field Goal_Yard Line'] = yard_line
        data_row['Field Goal_Op Time'] = op_time
        data_row['Field Goal_Result'] = result
    elif kick_type == 'Kickoff':
        yard_line = request.form['yard_line']
        position = request.form['position']
        result_yard_line = request.form['result_yard_line']
        landing_location = request.form['landing_location']
        hang_time = request.form.get('time_elapsed', '')
        data_row['Kickoff_Yard Line'] = yard_line
        data_row['Kickoff_Position'] = position
        data_row['Kickoff_Result Yard Line'] = result_yard_line
        data_row['Kickoff_Landing Location'] = landing_location
        data_row['Kickoff_Hang Time'] = hang_time
    elif kick_type == 'Punt':
        kick_yard_line = request.form['kick_yard_line']
        kick_location = request.form['kick_location']
        landed_yard_line = request.form['landed_yard_line']
        landed_location = request.form['landed_location']
        op_time = request.form.get('op_time', '')
        hang_time = request.form.get('hang_time', '')
        data_row['Punt_Kick Yard Line'] = kick_yard_line
        data_row['Punt_Kick Location'] = kick_location
        data_row['Punt_Landed Yard Line'] = landed_yard_line
        data_row['Punt_Landing Location'] = landed_location
        data_row['Punt_Op Time'] = op_time
        data_row['Punt_Hang Time'] = hang_time

    # Append to workout data in session
    workout_data = session.get('workout_data', [])
    workout_data.append(data_row)
    session['workout_data'] = workout_data

    return redirect(url_for('kick_track'))

@app.route('/save_workout')
def save_workout():
    if 'workout_name' not in session:
        return redirect(url_for('home'))

    workout_data = session.get('workout_data', [])
    if not workout_data:
        return redirect(url_for('kick_track'))

    # Use the predefined ALL_FIELDNAMES
    fieldnames = ALL_FIELDNAMES

    # Create a CSV in memory using StringIO
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()

    # Ensure each row contains all the fieldnames, filling missing fields with empty strings
    for row in workout_data:
        complete_row = {field: row.get(field, '') for field in fieldnames}
        writer.writerow(complete_row)

    contents = output.getvalue()
    output.close()

    # Encode the string data to bytes
    output_bytes = BytesIO(contents.encode('utf-8'))

    # Determine the filename
    if 'existing_workout_filename' in session:
        filename = session['existing_workout_filename']
    else:
        filename = f"{session['workout_name']}.csv"

    # Clear session data
    session.clear()

    # Send the file using send_file with 'download_name'
    return send_file(
        output_bytes,
        mimetype='text/csv',
        as_attachment=True,
        download_name=filename
    )

@app.route('/edit_kick/<int:kick_number>', methods=['GET', 'POST'])
def edit_kick(kick_number):
    if 'workout_name' not in session:
        return redirect(url_for('home'))

    kicks = session.get('workout_data', [])

    if request.method == 'POST':
        # Update the kick data
        kick = kicks[kick_number]
        kick_type = request.form['kick_type']
        kick['Kick Type'] = kick_type
        kick['Kicker'] = request.form['kicker']
        # Clear existing kick-specific data
        keys_to_clear = [key for key in kick.keys() if key not in ['Kick Type', 'Kicker', 'Temperature', 'Wind Direction', 'Field Type', 'Field Name']]
        for key in keys_to_clear:
            kick[key] = ''
        # Update details based on kick type
        if kick_type == 'Field Goal':
            kick['Field Goal_Position'] = request.form['position']
            kick['Field Goal_Yard Line'] = request.form['yard_line']
            kick['Field Goal_Op Time'] = request.form.get('time_elapsed', '')
            kick['Field Goal_Result'] = request.form.get('result', '')
        elif kick_type == 'Kickoff':
            kick['Kickoff_Yard Line'] = request.form['yard_line']
            kick['Kickoff_Position'] = request.form['position']
            kick['Kickoff_Result Yard Line'] = request.form['result_yard_line']
            kick['Kickoff_Landing Location'] = request.form['landing_location']
            kick['Kickoff_Hang Time'] = request.form.get('time_elapsed', '')
        elif kick_type == 'Punt':
            kick['Punt_Kick Yard Line'] = request.form['kick_yard_line']
            kick['Punt_Kick Location'] = request.form['kick_location']
            kick['Punt_Landed Yard Line'] = request.form['landed_yard_line']
            kick['Punt_Landing Location'] = request.form['landed_location']
            kick['Punt_Op Time'] = request.form.get('op_time', '')
            kick['Punt_Hang Time'] = request.form.get('hang_time', '')
        # Save back to session
        session['workout_data'] = kicks
        return redirect(url_for('kick_track'))
    else:
        if kick_number < 0 or kick_number >= len(kicks):
            return redirect(url_for('kick_track'))
        kick = kicks[kick_number]
        return render_template('edit_kick.html', kick=kick, kick_number=kick_number)

##if __name__ == '__main__':
   # app.run(debug=True)
#

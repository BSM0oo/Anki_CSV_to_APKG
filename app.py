from flask import Flask, request, render_template, send_file, after_this_request
import csv
import genanki
import io
import os
import random
import ast

app = Flask(__name__)

# Limit the maximum allowed payload to 16 megabytes
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        deck_name = request.form.get('deck_name', 'My Anki Deck')
        input_type = request.form.get('input_type', 'csv')
        csv_text = request.form.get('csv_text', '')
        csv_file = request.files.get('csv_file')

        if input_type == 'csv':
            if not csv_text.strip() and (not csv_file or csv_file.filename == ''):
                return render_template('index.html', error="Please provide CSV text or upload a CSV file.", deck_name=deck_name, csv_text=csv_text, input_type=input_type)
            
            if csv_file and csv_file.filename != '':
                try:
                    csv_data = csv_file.read().decode('utf-8')
                except UnicodeDecodeError:
                    return render_template('index.html', error="Error decoding CSV file. Please ensure it is encoded in UTF-8.", deck_name=deck_name, csv_text=csv_text, input_type=input_type)
                except Exception as e:
                    return render_template('index.html', error=f"Error reading CSV file: {e}", deck_name=deck_name, csv_text=csv_text, input_type=input_type)
            else:
                csv_data = csv_text

            # Generate a unique filename for the deck
            deck_filename = f"{deck_name.replace(' ', '_')}_{random.randint(1, 100000)}.apkg"
            deck_filepath = os.path.join('/tmp', deck_filename)

            # Create the deck
            try:
                create_anki_deck_from_csv(csv_data, deck_name, deck_filepath)
            except Exception as e:
                # Attempt to remove the deck file if it was created
                if os.path.exists(deck_filepath):
                    os.remove(deck_filepath)
                return render_template('index.html', error=f"An error occurred: {e}", deck_name=deck_name, csv_text=csv_text, input_type=input_type)

            @after_this_request
            def remove_file(response):
                try:
                    os.remove(deck_filepath)
                except Exception as error:
                    app.logger.error(f"Error removing or closing downloaded file handle: {error}")
                return response

            return send_file(deck_filepath, as_attachment=True, download_name=deck_filename)

        elif input_type == 'tuple':
            if not csv_text.strip():
                return render_template('index.html', error="Please provide Python tuple/list data in the text area.", deck_name=deck_name, csv_text=csv_text, input_type=input_type)
            tuple_data = csv_text.strip()

            # Generate a unique filename for the deck
            deck_filename = f"{deck_name.replace(' ', '_')}_{random.randint(1, 100000)}.apkg"
            deck_filepath = os.path.join('/tmp', deck_filename)

            # Create the deck
            try:
                create_anki_deck_from_tuple_list(tuple_data, deck_name, deck_filepath)
            except Exception as e:
                # Attempt to remove the deck file if it was created
                if os.path.exists(deck_filepath):
                    os.remove(deck_filepath)
                return render_template('index.html', error=f"An error occurred: {e}", deck_name=deck_name, csv_text=csv_text, input_type=input_type)

            @after_this_request
            def remove_file(response):
                try:
                    os.remove(deck_filepath)
                except Exception as error:
                    app.logger.error(f"Error removing or closing downloaded file handle: {error}")
                return response

            return send_file(deck_filepath, as_attachment=True, download_name=deck_filename)
        else:
            return render_template('index.html', error="Invalid input type selected.", deck_name=deck_name, csv_text=csv_text, input_type=input_type)

    else:
        return render_template('index.html')

def create_anki_deck_from_csv(csv_text, deck_name, output_filepath):
    # Generate unique IDs
    deck_id = random.randrange(1 << 30, 1 << 31)
    model_id = random.randrange(1 << 30, 1 << 31)

    # Create a new deck
    deck = genanki.Deck(
        deck_id,
        deck_name
    )

    # Define a basic model (note type)
    model = genanki.Model(
        model_id,
        'Simple Model',
        fields=[
            {'name': 'Front'},
            {'name': 'Back'},
        ],
        templates=[
            {
                'name': 'Card 1',
                'qfmt': '{{Front}}',
                'afmt': '{{FrontSide}}<hr id="answer">{{Back}}',
            },
        ]
    )

    # Read the CSV text and add notes to the deck
    csvfile = io.StringIO(csv_text.strip())
    reader = csv.DictReader(csvfile)

    if 'Front' not in reader.fieldnames or 'Back' not in reader.fieldnames:
        raise ValueError("CSV headers must contain 'Front' and 'Back'.")

    try:
        for row in reader:
            if 'Front' not in row or 'Back' not in row:
                raise ValueError("Each row must have 'Front' and 'Back' fields.")

            front = row['Front']
            back = row['Back']

            note = genanki.Note(
                model=model,
                fields=[front, back]
            )
            deck.add_note(note)
    except csv.Error as e:
        raise ValueError(f"Error parsing CSV data: {e}")

    # Generate the .apkg file
    genanki.Package(deck).write_to_file(output_filepath)

def create_anki_deck_from_tuple_list(tuple_text, deck_name, output_filepath):
    # Generate unique IDs
    deck_id = random.randrange(1 << 30, 1 << 31)
    model_id = random.randrange(1 << 30, 1 << 31)

    # Create a new deck
    deck = genanki.Deck(
        deck_id,
        deck_name
    )

    # Define a basic model (note type)
    model = genanki.Model(
        model_id,
        'Simple Model',
        fields=[
            {'name': 'Front'},
            {'name': 'Back'},
        ],
        templates=[
            {
                'name': 'Card 1',
                'qfmt': '{{Front}}',
                'afmt': '{{FrontSide}}<hr id="answer">{{Back}}',
            },
        ]
    )

    # Safely evaluate the tuple_text
    try:
        data = ast.literal_eval(tuple_text)
    except Exception as e:
        raise ValueError(f"Error parsing tuple/list data: {e}")

    if not isinstance(data, (list, tuple)):
        raise ValueError("Data must be a list or tuple of pairs.")

    for item in data:
        if not isinstance(item, (list, tuple)) or len(item) != 2:
            raise ValueError("Each item must be a pair (front, back).")
        front, back = item
        note = genanki.Note(
            model=model,
            fields=[str(front), str(back)]
        )
        deck.add_note(note)

    # Generate the .apkg file
    genanki.Package(deck).write_to_file(output_filepath)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)

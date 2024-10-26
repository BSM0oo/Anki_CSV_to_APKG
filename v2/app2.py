from flask import Flask, request, render_template, send_file, after_this_request
import csv
import genanki
import io
import os
import random

app = Flask(__name__)

# Limit the maximum allowed payload to 16 megabytes
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        deck_name = request.form.get('deck_name', 'My Anki Deck')
        csv_text = request.form.get('csv_text', '')
        csv_file = request.files.get('csv_file')

        if not csv_text.strip() and (not csv_file or csv_file.filename == ''):
            return render_template('index.html', error="Please provide CSV text or upload a CSV file.", deck_name=deck_name, csv_text=csv_text)

        if csv_file and csv_file.filename != '':
            try:
                csv_data = csv_file.read().decode('utf-8')
            except UnicodeDecodeError:
                return render_template('index.html', error="Error decoding CSV file. Please ensure it is encoded in UTF-8.", deck_name=deck_name, csv_text=csv_text)
            except Exception as e:
                return render_template('index.html', error=f"Error reading CSV file: {e}", deck_name=deck_name, csv_text=csv_text)
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
            return render_template('index.html', error=f"An error occurred: {e}", deck_name=deck_name, csv_text=csv_text)

        @after_this_request
        def remove_file(response):
            try:
                os.remove(deck_filepath)
            except Exception as error:
                app.logger.error(f"Error removing or closing downloaded file handle: {error}")
            return response

        return send_file(deck_filepath, as_attachment=True, download_name=deck_filename)

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

    for row in reader:
        note = genanki.Note(
            model=model,
            fields=[row['Front'], row['Back']]
        )
        deck.add_note(note)

    # Generate the .apkg file
    genanki.Package(deck).write_to_file(output_filepath)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')

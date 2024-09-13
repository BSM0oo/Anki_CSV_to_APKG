# app.py

from flask import Flask, request, render_template, send_file, after_this_request
import csv
import genanki
import io
import os
import random

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        deck_name = request.form.get('deck_name', 'My Anki Deck')
        csv_text = request.form.get('csv_text', '')

        if not csv_text.strip():
            return render_template('index.html', error="CSV text cannot be empty.", deck_name=deck_name, csv_text=csv_text)

        # Generate a unique filename for the deck
        deck_filename = f"{deck_name.replace(' ', '_')}_{random.randint(1, 100000)}.apkg"
        deck_filepath = os.path.join('/tmp', deck_filename)

        # Create the deck
        try:
            create_anki_deck_from_csv(csv_text, deck_name, deck_filepath)
        except Exception as e:
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
    if reader.fieldnames != ['Front', 'Back']:
        raise ValueError("CSV headers must be 'Front' and 'Back'.")

    for row in reader:
        note = genanki.Note(
            model=model,
            fields=[row['Front'], row['Back']]
        )
        deck.add_note(note)

    # Generate the .apkg file
    genanki.Package(deck).write_to_file(output_filepath)

if __name__ == '__main__':
    app.run(debug=True)

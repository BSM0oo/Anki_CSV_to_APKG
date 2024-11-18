from flask import Flask, request, render_template, send_file, after_this_request, flash
import csv
import genanki
import io
import os
import random
import ast
import re
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

def format_text_for_anki(text):
    """Format text for Anki, enhancing with HTML styling."""
    # Define CSS styles for the card
    css_style = """
    <style>
        .card {
            font-family: Arial, sans-serif;
            line-height: 1.5;
            margin: 20px;
        }
        .section-header {
            color: #2563eb;
            font-weight: bold;
            margin-top: 10px;
        }
        .example {
            background-color: #f3f4f6;
            padding: 8px;
            border-left: 4px solid #2563eb;
            margin: 8px 0;
        }
        .definition {
            margin: 8px 0;
        }
        .usefulness {
            color: #059669;
            margin: 8px 0;
        }
    </style>
    """

    # Convert escaped newlines to actual newlines first
    text = text.replace('\\n', '\n')
    
    # Apply styling to specific sections while preserving any existing HTML
    sections = text.split('\n')
    formatted_sections = []
    
    for section in sections:
        section = section.strip()
        if not section:
            continue
            
        # Style specific sections based on their content
        if section.startswith("Also Called:"):
            section = f'<div class="section-header">{section}</div>'
        elif section.startswith("Definition:"):
            section = f'<div class="section-header">Definition:</div><div class="definition">{section[11:]}</div>'
        elif section.startswith("Example:"):
            section = f'<div class="section-header">Example:</div><div class="example">{section[8:]}</div>'
        elif section.startswith("Usefulness:"):
            section = f'<div class="section-header">Usefulness:</div><div class="usefulness">{section[11:]}</div>'
        else:
            section = f'<div>{section}</div>'
        
        formatted_sections.append(section)
    
    # Combine the sections with proper spacing
    formatted_text = '\n'.join(formatted_sections)
    
    # Wrap everything in a card div with the CSS
    return f"{css_style}<div class='card'>{formatted_text}</div>"

def create_deck_infrastructure(deck_name):
    """Create basic deck infrastructure with model and styling."""
    deck_id = random.randrange(1 << 30, 1 << 31)
    model_id = random.randrange(1 << 30, 1 << 31)
    
    deck = genanki.Deck(deck_id, deck_name)
    
    # Enhanced model with better styling
    model = genanki.Model(
        model_id,
        'Enhanced Model',
        fields=[
            {'name': 'Front'},
            {'name': 'Back'},
        ],
        templates=[
            {
                'name': 'Card 1',
                'qfmt': """
                    <div class="front-side">
                        {{Front}}
                    </div>
                """,
                'afmt': """
                    <div class="front-side">
                        {{Front}}
                    </div>
                    <hr id="answer">
                    <div class="back-side">
                        {{Back}}
                    </div>
                """,
            },
        ],
        css="""
        .card {
            font-family: Arial, sans-serif;
            font-size: 16px;
            text-align: left;
            color: #1a1a1a;
            background-color: #ffffff;
            line-height: 1.5;
        }
        .front-side {
            font-size: 1.2em;
            font-weight: bold;
            color: #2563eb;
        }
        hr#answer {
            height: 2px;
            background-color: #e5e7eb;
            margin: 20px 0;
        }
        .back-side {
            margin-top: 20px;
        }
        .section-header {
            color: #2563eb;
            font-weight: bold;
            margin-top: 10px;
        }
        .example {
            background-color: #f3f4f6;
            padding: 8px;
            border-left: 4px solid #2563eb;
            margin: 8px 0;
        }
        .definition {
            margin: 8px 0;
        }
        .usefulness {
            color: #059669;
            margin: 8px 0;
        }
        """
    )
    
    return deck, model

def clean_tuple_text(tuple_text):
    """Clean and standardize tuple/list input text."""
    # Remove any variable assignment if present
    tuple_text = re.sub(r'^.*?=\s*', '', tuple_text.strip())
    
    # Normalize line endings
    tuple_text = tuple_text.replace('\r\n', '\n')
    
    # Remove common indentation from all lines while preserving relative indentation
    lines = tuple_text.split('\n')
    if lines:
        # Find minimum indentation (excluding empty lines)
        min_indent = float('inf')
        for line in lines:
            if line.strip():  # Skip empty lines
                indent = len(line) - len(line.lstrip())
                min_indent = min(min_indent, indent)
        
        if min_indent < float('inf'):
            # Remove the common indentation from all lines
            normalized_lines = []
            for line in lines:
                if line.strip():  # If line is not empty
                    normalized_lines.append(line[min_indent:])
                else:
                    normalized_lines.append(line)
            tuple_text = '\n'.join(normalized_lines)
    
    # If the input is wrapped in extra parentheses, remove them
    if tuple_text.startswith('(') and tuple_text.endswith(')'):
        inner = tuple_text[1:-1].strip()
        if inner.startswith('(') and inner.endswith(')'):
            tuple_text = inner
    
    return tuple_text


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        user_deck_name = request.form.get('deck_name', '').strip()
        # If user didn't enter a name, use datetime
        if not user_deck_name:
            deck_name = datetime.now().strftime("Gen_Deck_%Y-%m-%d_%H-%M-%S")
        else:
            deck_name = user_deck_name
            
        input_type = request.form.get('input_type', 'csv')
        csv_text = request.form.get('csv_text', '')
        csv_file = request.files.get('csv_file')
        
        if input_type == 'csv':
            if not csv_text.strip() and (not csv_file or csv_file.filename == ''):
                flash("Please provide CSV text or upload a CSV file.", "error")
                return render_template('index.html', error="Please provide CSV text or upload a CSV file.", 
                                    deck_name="", csv_text=csv_text, input_type=input_type)
            
            if csv_file and csv_file.filename != '':
                try:
                    csv_data = csv_file.read().decode('utf-8')
                except UnicodeDecodeError:
                    flash("Error decoding CSV file. Please ensure it is encoded in UTF-8.", "error")
                    return render_template('index.html', error="Error decoding CSV file. Please ensure it is encoded in UTF-8.", 
                                        deck_name="", csv_text=csv_text, input_type=input_type)
                except Exception as e:
                    flash(f"Error reading CSV file: {str(e)}", "error")
                    return render_template('index.html', error=f"Error reading CSV file: {e}", 
                                        deck_name="", csv_text=csv_text, input_type=input_type)
            else:
                csv_data = csv_text

            try:
                deck_filename, deck_filepath = create_anki_deck_from_csv(csv_data, deck_name)
            except Exception as e:
                flash(f"Error creating deck: {str(e)}", "error")
                return render_template('index.html', error=f"An error occurred: {e}", 
                                    deck_name="", csv_text=csv_text, input_type=input_type)

        elif input_type == 'tuple':
            if not csv_text.strip():
                flash("Please provide Python tuple/list data in the text area.", "error")
                return render_template('index.html', error="Please provide Python tuple/list data in the text area.", 
                                    deck_name="", csv_text=csv_text, input_type=input_type)
            
            tuple_data = clean_tuple_text(csv_text)
            
            try:
                deck_filename, deck_filepath = create_anki_deck_from_tuple_list(tuple_data, deck_name)
            except Exception as e:
                flash(f"Error creating deck: {str(e)}", "error")
                return render_template('index.html', error=f"An error occurred: {e}", 
                                    deck_name="", csv_text=csv_text, input_type=input_type)
        else:
            flash("Invalid input type selected.", "error")
            return render_template('index.html', error="Invalid input type selected.", 
                                deck_name="", csv_text=csv_text, input_type=input_type)

        @after_this_request
        def remove_file(response):
            try:
                os.remove(deck_filepath)
            except Exception as error:
                app.logger.error(f"Error removing or closing downloaded file handle: {error}")
            return response

        return send_file(deck_filepath, as_attachment=True, download_name=deck_filename)

    # For GET request, return empty deck name
    return render_template('index.html', deck_name="")

def create_anki_deck_from_csv(csv_text, deck_name):
    """Create an Anki deck from CSV data."""
    deck, model = create_deck_infrastructure(deck_name)
    
    csvfile = io.StringIO(csv_text.strip())
    reader = csv.DictReader(csvfile)
    
    if 'Front' not in reader.fieldnames or 'Back' not in reader.fieldnames:
        raise ValueError("CSV headers must contain 'Front' and 'Back'.")
    
    try:
        for row in reader:
            if not all(field in row for field in ['Front', 'Back']):
                raise ValueError("Each row must have 'Front' and 'Back' fields.")
            
            # Format both front and back with proper line breaks
            front_formatted = format_text_for_anki(row['Front'])
            back_formatted = format_text_for_anki(row['Back'])
            
            note = genanki.Note(
                model=model,
                fields=[front_formatted, back_formatted]
            )
            deck.add_note(note)
    except csv.Error as e:
        raise ValueError(f"Error parsing CSV data: {e}")
    
    deck_filename = f"{deck_name.replace(' ', '_')}_{random.randint(1, 100000)}.apkg"
    deck_filepath = os.path.join('/tmp', deck_filename)
    
    genanki.Package(deck).write_to_file(deck_filepath)
    return deck_filename, deck_filepath

def create_anki_deck_from_tuple_list(tuple_text, deck_name):
    """Create an Anki deck from tuple/list data."""
    deck, model = create_deck_infrastructure(deck_name)
    
    try:
        # First try to parse as is
        try:
            data = ast.literal_eval(tuple_text)
        except (SyntaxError, ValueError) as e:
            # If that fails, try wrapping in parentheses
            data = ast.literal_eval(f"({tuple_text})")
    except Exception as e:
        raise ValueError(f"Error parsing tuple/list data. Please check the format. Error: {e}")
    
    # Handle both single tuple/list and nested tuple/list cases
    if isinstance(data, (list, tuple)):
        if len(data) == 2 and all(isinstance(x, str) for x in data):
            # Single pair case
            data = [data]
        elif all(isinstance(x, (list, tuple)) and len(x) == 2 for x in data):
            # List of pairs case
            pass
        else:
            raise ValueError("Data must be either a single pair or a list/tuple of pairs.")
    else:
        raise ValueError("Data must be a list or tuple.")
    
    for item in data:
        if not isinstance(item, (list, tuple)) or len(item) != 2:
            raise ValueError("Each item must be a pair (front, back).")
        
        front, back = item
        # Format both front and back with proper line breaks
        front_formatted = format_text_for_anki(str(front))
        back_formatted = format_text_for_anki(str(back))
        
        note = genanki.Note(
            model=model,
            fields=[front_formatted, back_formatted]
        )
        deck.add_note(note)
    
    deck_filename = f"{deck_name.replace(' ', '_')}_{random.randint(1, 100000)}.apkg"
    deck_filepath = os.path.join('/tmp', deck_filename)
    
    genanki.Package(deck).write_to_file(deck_filepath)
    return deck_filename, deck_filepath

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)
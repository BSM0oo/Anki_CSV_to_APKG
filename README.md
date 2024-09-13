README.md

# Simple Model Deck Generator

This project generates a `.apkg` file for Anki, a popular flashcard application, from a CSV file containing flashcard data.

## Description

The script reads a CSV file with two columns, `Front` and `Back`, and generates an Anki deck with a simple model. Each row in the CSV file corresponds to a flashcard in the deck.

## Installation

1. Clone the repository:

   ```sh
   git clone <repository-url>
   cd <repository-directory>
   ```

2. Install the required dependencies:
   ```sh
   pip install -r requirements.txt
   ```

## Usage

1. Prepare a CSV file with the following headers: `Front`, `Back`.
2. Run the script with the CSV file as input:
   ```sh
   python app.py <path-to-csv-file> <output-filepath>
   ```

## Example

Given a CSV file `flashcards.csv`:

```csv
Front,Back
What is the capital of France?,Paris
What is 2+2?,4
```

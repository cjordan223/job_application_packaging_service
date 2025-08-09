# Job Packaging Tool

A Flask web application that automatically tailors resumes and generates personalized cover letters based on job descriptions using local LLM via Ollama.

## Features

- **Resume Tailoring**: Reorders and emphasizes skills based on job requirements
- **Cover Letter Generation**: Creates unique, personalized cover letters using Ollama
- **PDF Processing**: Extracts text from uploaded PDF templates
- **Keyword Extraction**: Uses TF-IDF to identify relevant keywords from job descriptions
- **Document Generation**: Outputs tailored PDF documents for download

## Prerequisites

1. **Python 3.8+** installed on your system
2. **Ollama** running locally with a compatible model (e.g., `llama3:8b`)

### Installing Ollama

1. Visit [Ollama.ai](https://ollama.ai) and download for your platform
2. Install and start Ollama
3. Pull a compatible model:
   ```bash
   ollama pull llama3:8b
   ```

## Installation

1. **Clone or download** this project to your local machine

2. **Navigate to the project directory**:
   ```bash
   cd job_packager
   ```

3. **Create a virtual environment** (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

4. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. **Start the application**:
   ```bash
   python app.py
   ```

2. **Open your browser** and navigate to:
   ```
   http://127.0.0.1:8000
   ```

3. **Upload Templates**:
   - Upload your resume template (PDF format)
   - Upload your cover letter template (PDF format)
   - Templates are stored locally and reused for future job applications

4. **Process a Job**:
   - Enter the job title
   - Enter the company name
   - Paste the job description
   - Click "Generate Tailored Documents"

5. **Download Results**:
   - Download the tailored resume
   - Download the generated cover letter
   - Or download both as a ZIP file

## Project Structure

```
job_packager/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── templates/
│   └── index.html        # Main web interface
├── uploads/              # Generated automatically
│   ├── pdfs/            # Uploaded PDF templates
│   └── texts/           # Extracted text from PDFs
└── static/              # CSS/JS files (if needed)
```

## Configuration

### Ollama Model

To change the Ollama model, edit the `OLLAMA_MODEL` variable in `app.py`:

```python
OLLAMA_MODEL = 'llama3:8b'  # Change to your preferred model
```

Popular alternatives for Mac M3:
- `mistral:7b-q4_0` - Good balance of speed and quality
- `llama3.1:8b-q4_0` - Higher quality, slower
- `codellama:7b-q4_0` - Optimized for code-related content

### File Storage

Uploaded files are stored in the `uploads/` directory:
- `uploads/pdfs/` - Original PDF templates
- `uploads/texts/` - Extracted text from PDFs
- Generated documents are also stored in `uploads/`

## Troubleshooting

### Ollama Not Running

If you see "Ollama is not running" error:

1. **Check if Ollama is installed**:
   ```bash
   ollama --version
   ```

2. **Start Ollama**:
   ```bash
   ollama serve
   ```

3. **Verify the model is available**:
   ```bash
   ollama list
   ```

4. **Pull the model if needed**:
   ```bash
   ollama pull llama3:8b
   ```

### PDF Extraction Issues

If PDF text extraction fails:

1. **Check PDF format**: Ensure the PDF contains selectable text (not just images)
2. **Try a different PDF**: Some PDFs may have encoding issues
3. **Check file size**: Very large PDFs may cause timeouts

### Performance Issues

For better performance on Mac M3:

1. **Use quantized models**: Models with `-q4_0` suffix are optimized for Apple Silicon
2. **Adjust model size**: Smaller models (3B) are faster than larger ones (7B+)
3. **Close other applications**: Free up memory for Ollama

## Development

### Adding New Features

The application is designed to be extensible. Here are some areas for enhancement:

1. **Better NLP**: Implement synonym matching for keywords
2. **Multi-user support**: Add user authentication and sessions
3. **Multi-page PDFs**: Better handling of complex PDF structures
4. **DOCX support**: Add support for Word documents
5. **Custom prompts**: Allow users to customize Ollama prompts

### Code Structure

- `app.py`: Main application logic
- `extract_pdf_text()`: PDF text extraction
- `extract_keywords()`: Keyword extraction using TF-IDF
- `polish_resume()`: Resume tailoring logic
- `generate_cover_with_ollama()`: Cover letter generation
- `create_pdf()`: PDF generation

## Security Notes

- This is a single-user application for simplicity
- No authentication is implemented
- Files are stored locally
- For production use, consider adding:
  - User authentication
  - File encryption
  - Input validation
  - Rate limiting

## License

This project is provided as-is for educational and personal use.

## Support

For issues and questions:

1. Check the troubleshooting section above
2. Verify Ollama is running and accessible
3. Check the application logs for error messages
4. Ensure all dependencies are installed correctly

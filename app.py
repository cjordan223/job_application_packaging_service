#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Job Packaging Tool - Flask Application
A web application for automatically tailoring resumes and generating cover letters
based on job descriptions using local LLM via Ollama.
"""

import os
import re
import json
import logging
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file, session, redirect, url_for
from werkzeug.utils import secure_filename
import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix
from scipy.sparse.linalg import norm
import PyPDF2
import requests
from fpdf import FPDF
import zipfile
import io

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Change in production

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf'}
USER_ID = 'default_user'  # Single user for simplicity
OLLAMA_URL = 'http://localhost:11434/api/generate'
OLLAMA_MODEL = 'llama3:8b'  # Updated to use available model

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(os.path.join(UPLOAD_FOLDER, 'pdfs'), exist_ok=True)
os.makedirs(os.path.join(UPLOAD_FOLDER, 'texts'), exist_ok=True)


def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def extract_pdf_text(pdf_path):
    """
    Extract text from PDF file using PyPDF2.
    Handles encoding issues and returns cleaned text.
    """
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"

        # Clean encoding issues
        # Replace Unicode replacement character with bullets
        text = text.replace('\ufffd', '•')
        text = text.replace('\x00', '')  # Remove null characters
        text = re.sub(r'\s+', ' ', text)  # Normalize whitespace
        text = text.replace('•', ' • ')  # Ensure bullets are properly spaced

        return text.strip()
    except Exception as e:
        logger.error(f"Error extracting text from PDF {pdf_path}: {e}")
        return ""


def extract_keywords(text, top_k=10):
    """
    Extract top keywords using simple TF-IDF implementation.
    """
    try:
        # Simple preprocessing
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())

        # Remove common stop words
        stop_words = {
            'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
            'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had',
            'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might',
            'can', 'this', 'that', 'these', 'those', 'a', 'an', 'as', 'from', 'not',
            'all', 'any', 'each', 'every', 'no', 'some', 'such', 'than', 'too', 'very'
        }

        words = [word for word in words if word not in stop_words]

        if not words:
            return []

        # Count word frequencies
        word_counts = {}
        for word in words:
            word_counts[word] = word_counts.get(word, 0) + 1

        # Sort by frequency and return top k
        sorted_words = sorted(word_counts.items(),
                              key=lambda x: x[1], reverse=True)
        return [word for word, count in sorted_words[:top_k]]

    except Exception as e:
        logger.error(f"Error extracting keywords: {e}")
        return []


def polish_resume(resume_text, keywords, job_title, company_name):
    """
    Polish resume by reordering skills based on keyword matches.
    """
    try:
        # Define common skill section patterns
        skill_patterns = [
            r'(TECHNICAL SKILLS?|SKILLS?|TECHNOLOGIES?|PROGRAMMING LANGUAGES?|TOOLS?|FRAMEWORKS?)[:\s]*([^•\n]+)',
            r'(LANGUAGES?|PROGRAMMING)[:\s]*([^•\n]+)',
            r'(FRAMEWORKS?|LIBRARIES?|TOOLS?)[:\s]*([^•\n]+)'
        ]

        polished_text = resume_text

        for pattern in skill_patterns:
            matches = re.finditer(pattern, polished_text, re.IGNORECASE)
            for match in matches:
                section_header = match.group(1)
                section_content = match.group(2)

                # Split content by common delimiters
                items = re.split(r'[,;•\n]+', section_content)
                items = [item.strip() for item in items if item.strip()]

                if not items:
                    continue

                # Score items based on keyword matches
                scored_items = []
                for item in items:
                    score = 0
                    item_lower = item.lower()
                    for keyword in keywords:
                        if keyword.lower() in item_lower:
                            score += 1
                    scored_items.append((item, score))

                # Sort by score (highest first)
                scored_items.sort(key=lambda x: x[1], reverse=True)

                # Reconstruct section
                new_content = ', '.join([item for item, score in scored_items])
                new_section = f"{section_header}: {new_content}"

                # Replace in text
                polished_text = polished_text.replace(
                    match.group(0), new_section)

        # Add tailored header
        top_keywords_str = ', '.join(keywords[:5])
        header = f"\n\nTAILORED FOR {job_title.upper()} AT {company_name.upper()}: {top_keywords_str}\n"
        header += "=" * 80 + "\n"

        return header + polished_text

    except Exception as e:
        logger.error(f"Error polishing resume: {e}")
        return resume_text


def generate_cover_with_ollama(resume_text, cover_template, job_title, company_name, job_description):
    """
    Generate cover letter using Ollama API.
    """
    try:
        prompt = f"""Based on the following resume:
{resume_text}

And this example cover letter structure and style:
{cover_template}

Generate a completely unique, personalized cover letter for the position of {job_title} at {company_name}. The job description is:
{job_description}

Highlight relevant experiences, skills, and achievements from the resume that match the job. Keep the tone professional, enthusiastic, and aligned with the example's spirit. Structure it with header, date, greeting (Dear {company_name} Team,), body paragraphs, and closing. Do not fabricate any information."""

        payload = {
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False
        }

        response = requests.post(OLLAMA_URL, json=payload, timeout=60)

        if response.status_code == 200:
            result = response.json()
            return result.get('response', '')
        else:
            logger.error(
                f"Ollama API error: {response.status_code} - {response.text}")
            return f"Error generating cover letter: Ollama API returned {response.status_code}"

    except requests.exceptions.RequestException as e:
        logger.error(f"Error connecting to Ollama: {e}")
        return f"Error: Could not connect to Ollama. Please ensure Ollama is running on {OLLAMA_URL}"
    except Exception as e:
        logger.error(f"Error generating cover letter: {e}")
        return f"Error generating cover letter: {str(e)}"


def create_pdf(text, filename, title):
    """
    Create PDF using FPDF.
    """
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)

        # Add title
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(200, 10, txt=title, ln=True, align='C')
        pdf.ln(10)

        # Add content
        pdf.set_font("Arial", size=12)
        lines = text.split('\n')
        for line in lines:
            if line.strip():
                # Handle bold sections
                if re.match(r'^[A-Z\s]+:$', line.strip()):
                    pdf.set_font("Arial", 'B', 12)
                    pdf.cell(200, 8, txt=line.strip(), ln=True)
                    pdf.set_font("Arial", size=12)
                else:
                    pdf.multi_cell(0, 8, txt=line.strip())
                pdf.ln(2)

        pdf.output(filename)
        return True

    except Exception as e:
        logger.error(f"Error creating PDF {filename}: {e}")
        return False


@app.route('/')
def index():
    """Main page with upload and job processing forms."""
    return render_template('index.html')


@app.route('/upload_templates', methods=['POST'])
def upload_templates():
    """Handle template uploads."""
    try:
        resume_file = request.files.get('resume')
        cover_file = request.files.get('cover_letter')

        uploaded_files = []

        # Handle resume upload
        if resume_file and resume_file.filename:
            if allowed_file(resume_file.filename):
                filename = secure_filename(f"{USER_ID}_resume.pdf")
                filepath = os.path.join(UPLOAD_FOLDER, 'pdfs', filename)
                resume_file.save(filepath)

                # Extract text
                text = extract_pdf_text(filepath)
                text_path = os.path.join(
                    UPLOAD_FOLDER, 'texts', f"{USER_ID}_resume.txt")
                with open(text_path, 'w', encoding='utf-8') as f:
                    f.write(text)

                uploaded_files.append('resume')
                logger.info(f"Resume uploaded and processed: {filename}")
            else:
                return jsonify({'error': 'Invalid file type for resume'}), 400

        # Handle cover letter upload
        if cover_file and cover_file.filename:
            if allowed_file(cover_file.filename):
                filename = secure_filename(f"{USER_ID}_cover_letter.pdf")
                filepath = os.path.join(UPLOAD_FOLDER, 'pdfs', filename)
                cover_file.save(filepath)

                # Extract text
                text = extract_pdf_text(filepath)
                text_path = os.path.join(
                    UPLOAD_FOLDER, 'texts', f"{USER_ID}_cover_letter.txt")
                with open(text_path, 'w', encoding='utf-8') as f:
                    f.write(text)

                uploaded_files.append('cover_letter')
                logger.info(f"Cover letter uploaded and processed: {filename}")
            else:
                return jsonify({'error': 'Invalid file type for cover letter'}), 400

        if uploaded_files:
            return jsonify({'success': f'Successfully uploaded: {", ".join(uploaded_files)}'})
        else:
            return jsonify({'error': 'No valid files uploaded'}), 400

    except Exception as e:
        logger.error(f"Error uploading templates: {e}")
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500


@app.route('/process_job', methods=['POST'])
def process_job():
    """Process job and generate tailored documents."""
    try:
        job_title = request.form.get('job_title', '').strip()
        company_name = request.form.get('company_name', '').strip()
        job_description = request.form.get('job_description', '').strip()

        if not all([job_title, company_name, job_description]):
            return jsonify({'error': 'All fields are required'}), 400

        # Check if templates exist
        resume_text_path = os.path.join(
            UPLOAD_FOLDER, 'texts', f"{USER_ID}_resume.txt")
        cover_text_path = os.path.join(
            UPLOAD_FOLDER, 'texts', f"{USER_ID}_cover_letter.txt")

        if not os.path.exists(resume_text_path):
            return jsonify({'error': 'Resume template not found. Please upload a resume first.'}), 400

        if not os.path.exists(cover_text_path):
            return jsonify({'error': 'Cover letter template not found. Please upload a cover letter first.'}), 400

        # Load templates
        with open(resume_text_path, 'r', encoding='utf-8') as f:
            resume_text = f.read()

        with open(cover_text_path, 'r', encoding='utf-8') as f:
            cover_template = f.read()

        # Extract keywords from job description
        keywords = extract_keywords(job_description, top_k=10)
        logger.info(f"Extracted keywords: {keywords}")

        # Polish resume
        polished_resume = polish_resume(
            resume_text, keywords, job_title, company_name)

        # Generate cover letter
        generated_cover = generate_cover_with_ollama(
            resume_text, cover_template, job_title, company_name, job_description
        )

        # Create PDFs
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        resume_pdf_path = os.path.join(
            UPLOAD_FOLDER, f"tailored_resume_{timestamp}.pdf")
        cover_pdf_path = os.path.join(
            UPLOAD_FOLDER, f"tailored_cover_{timestamp}.pdf")

        resume_success = create_pdf(
            polished_resume, resume_pdf_path, f"Tailored Resume - {job_title}")
        cover_success = create_pdf(
            generated_cover, cover_pdf_path, f"Cover Letter - {job_title}")

        if not resume_success or not cover_success:
            return jsonify({'error': 'Failed to create PDF files'}), 500

        # Create zip file
        zip_path = os.path.join(UPLOAD_FOLDER, f"job_package_{timestamp}.zip")
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            zipf.write(resume_pdf_path, os.path.basename(resume_pdf_path))
            zipf.write(cover_pdf_path, os.path.basename(cover_pdf_path))

        return jsonify({
            'success': 'Documents generated successfully',
            'resume_pdf': resume_pdf_path,
            'cover_pdf': cover_pdf_path,
            'zip_file': zip_path,
            'keywords': keywords
        })

    except Exception as e:
        logger.error(f"Error processing job: {e}")
        return jsonify({'error': f'Processing failed: {str(e)}'}), 500


@app.route('/download/<filename>')
def download_file(filename):
    """Download generated files."""
    try:
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        if os.path.exists(file_path):
            return send_file(file_path, as_attachment=True)
        else:
            return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        logger.error(f"Error downloading file {filename}: {e}")
        return jsonify({'error': 'Download failed'}), 500


@app.route('/check_ollama')
def check_ollama():
    """Check if Ollama is running."""
    try:
        response = requests.get('http://localhost:11434/api/tags', timeout=5)
        if response.status_code == 200:
            return jsonify({'status': 'running', 'models': response.json()})
        else:
            return jsonify({'status': 'error', 'message': 'Ollama not responding'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Ollama not running: {str(e)}'})


if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)

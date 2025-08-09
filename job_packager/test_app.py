#!/usr/bin/env python3
"""
Test script for Job Packaging Tool
This script tests the core functionality without requiring a web interface.
"""

from app import (
    extract_keywords,
    polish_resume,
    extract_pdf_text,
    create_pdf,
    generate_cover_with_ollama
)
import os
import sys
import tempfile
import shutil

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


def test_keyword_extraction():
    """Test keyword extraction functionality."""
    print("Testing keyword extraction...")

    sample_text = """
    We are looking for a Python developer with experience in Flask, Django, and React.
    The ideal candidate should have knowledge of machine learning, data analysis,
    and cloud computing. Experience with AWS, Docker, and Kubernetes is a plus.
    """

    keywords = extract_keywords(sample_text, top_k=5)
    print(f"Extracted keywords: {keywords}")

    expected_keywords = ['python', 'experience',
                         'developer', 'flask', 'django']
    found_expected = any(keyword in keywords for keyword in expected_keywords)

    if found_expected:
        print("✓ Keyword extraction test passed")
    else:
        print("✗ Keyword extraction test failed")

    return found_expected


def test_resume_polishing():
    """Test resume polishing functionality."""
    print("\nTesting resume polishing...")

    sample_resume = """
    TECHNICAL SKILLS:
    Programming Languages: JavaScript, Python, Java, C++
    Frameworks: React, Angular, Django, Flask
    Tools: Git, Docker, AWS, Kubernetes
    """

    keywords = ['python', 'flask', 'react', 'docker']
    polished = polish_resume(sample_resume, keywords,
                             "Software Engineer", "Tech Corp")

    print(f"Polished resume:\n{polished}")

    # Check if the resume was polished (has the tailored header)
    if 'TAILORED FOR SOFTWARE ENGINEER AT TECH CORP' in polished:
        print("✓ Resume polishing test passed")
        return True
    else:
        print("✗ Resume polishing test failed")
        return False


def test_pdf_creation():
    """Test PDF creation functionality."""
    print("\nTesting PDF creation...")

    sample_text = """
    TEST DOCUMENT
    
    This is a sample document for testing PDF creation.
    
    TECHNICAL SKILLS:
    Python, Flask, React, Docker
    
    EXPERIENCE:
    Software Engineer at Tech Company
    """

    # Create a temporary file
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
        temp_pdf_path = tmp_file.name

    try:
        success = create_pdf(sample_text, temp_pdf_path, "Test Document")

        if success and os.path.exists(temp_pdf_path):
            print("✓ PDF creation test passed")
            return True
        else:
            print("✗ PDF creation test failed")
            return False
    finally:
        # Clean up
        if os.path.exists(temp_pdf_path):
            os.unlink(temp_pdf_path)


def test_ollama_connection():
    """Test Ollama connection."""
    print("\nTesting Ollama connection...")

    try:
        import requests
        response = requests.get('http://localhost:11434/api/tags', timeout=5)
        if response.status_code == 200:
            print("✓ Ollama is running and accessible")
            return True
        else:
            print("✗ Ollama is not responding properly")
            return False
    except Exception as e:
        print(f"✗ Ollama connection failed: {e}")
        print("  (This is expected if Ollama is not running)")
        return False


def main():
    """Run all tests."""
    print("Job Packaging Tool - Test Suite")
    print("=" * 40)

    tests = [
        test_keyword_extraction,
        test_resume_polishing,
        test_pdf_creation,
        test_ollama_connection
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"✗ Test {test.__name__} failed with error: {e}")

    print(f"\nTest Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! The application is ready to use.")
    else:
        print("⚠️  Some tests failed. Please check the issues above.")

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

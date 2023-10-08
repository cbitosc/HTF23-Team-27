from flask import Flask, render_template, request, redirect, url_for, flash
import os
from werkzeug.utils import secure_filename
import PyPDF2
from docx import Document
import re
from bs4 import BeautifulSoup
import requests
from aiohttp import ClientSession
import asyncio
app = Flask(__name__)
UPLOAD_FOLDER = 'uploads/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = 'your_secret_key'

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

ALLOWED_EXTENSIONS = {'pdf', 'docx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

OPENAI_API_KEY = "sk-ApCAAfUN1JyI6zo6vNOXT3BlbkFJxpHzWY4vEjzxx********"
os.environ["OPENAI_API_KEY"] = "sk-ApCAAfUN1JyI6zo6vNOXT3BlbkFJxpHzWY4*******"

def chat_gpt4(prompt):
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_API_KEY}"
    }
    data = {
        "model": "gpt-4",
        "messages": [
            {"role": "system", "content": "You are ChatGPT-4, a large language model trained by OpenAI."},
            {"role": "user", "content": prompt},
        ],
        "max_tokens": 4096,
    }
    response = requests.post(url, json=data, headers=headers)
    if response.status_code == 200:
        response_data = response.json()
        message = response_data["choices"][0]["message"]["content"]
        return message
    else:
        raise Exception(
            f"Request failed with status code {response.status_code}: {response.text}"
        )
def chat_gpt3(prompt):
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_API_KEY}"
    }
    data = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {"role": "system", "content": "You are ChatGPT-3, a large language model trained by OpenAI."},
            {"role": "user", "content": prompt},
        ],
        "max_tokens": 2048,
    }
    response = requests.post(url, json=data, headers=headers)
    if response.status_code == 200:
        response_data = response.json()
        message = response_data["choices"][0]["message"]["content"]
        return message
    else:
        raise Exception(
            f"Request failed with status code {response.status_code}: {response.text}"
        )
def extract_text(filepath):
    extension = filepath.split('.')[-1].lower()
    text = ''
    try:
        if extension == 'pdf':
            with open(filepath, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                for page in range(len(reader.pages)):
                    text += reader.pages[page].extract_text()
        elif extension == 'docx':
            doc = Document(filepath)
            for paragraph in doc.paragraphs:
                text += paragraph.text + ' '
    except Exception as e:
        flash('Error extracting text from file: {}'.format(e))

    return text.strip()  # Remove leading and trailing whitespaces
def extract_score(score_string):
    score_regex = re.search(r"(\d{1,3})\/100", score_string)
    if score_regex:
        return int(score_regex.group(1))
    else:
        raise ValueError("Score not found in returned string")
"""def generate_response_llm(prompt):
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_API_KEY}"
    }
    data = {
        "model":  "gpt-3.5-turbo",
        "messages": [
            {"role": "system", "content": "You are ChatGPT-4, a large language model trained by OpenAI."},
            {"role": "user", "content": prompt},
        ],
        "max_tokens": 2048,
    }
    response = requests.post(url, json=data, headers=headers)
    if response.status_code == 200:
        response_data = response.json()
        message = response_data["choices"][0]["message"]["content"]
        #return message
        bulk_response = ""
        for stream_chunks in message:
            try:
                sys.stdout.write(
                    stream_chunks["choices"][0]["delta"]["content"] + '')  # Use sys.stdout.write instead of print
                sys.stdout.flush()  # Flush the buffer to ensure real-time printing)

                chunk_words = stream_chunks["choices"][0]["delta"]["content"]
                chunk_words = repr(chunk_words)
                strip_chunk_words = chunk_words.strip("'")
                yield f"data:{strip_chunk_words}\n\n"
                bulk_response = bulk_response + stream_chunks["choices"][0]["delta"]["content"]
            except:
                continue

        # chat_response = completion["choices"][0]["message"]["content"]
        print("\nBulk Response: ", repr(bulk_response))
        return bulk_response
    else:
        raise Exception(
            f"Request failed with status code {response.status_code}: {response.text}"
        )"""

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        text1 = None
        text2 = None
        # retrieve company and role values from the request
        company = request.form['company']
        role = request.form['role']
        # Check if 'file1' and 'file2' are in request files
        if 'file1' not in request.files or 'file2' not in request.files:
            flash('Both files are required')
            return redirect(request.url)

        file1 = request.files['file1']
        file2 = request.files['file2']

        if file1.filename == '' or file2.filename == '':
            flash('Both files must be selected')
            return redirect(request.url)

        if file1 and allowed_file(file1.filename):
            filename1 = secure_filename(file1.filename)
            file_path1 = os.path.join(app.config['UPLOAD_FOLDER'], filename1)
            file1.save(file_path1)
            text1 = extract_text(file_path1)

        if file2 and allowed_file(file2.filename):
            filename2 = secure_filename(file2.filename)
            file_path2 = os.path.join(app.config['UPLOAD_FOLDER'], filename2)
            file2.save(file_path2)
            text2 = extract_text(file_path2)

        return redirect(url_for('info', text1=text1, text2=text2, company=company, role=role))

    return render_template('upload.html')


@app.route('/info', methods=['GET'])
def info():
    text1 = request.args.get('text1', '')
    text2 = request.args.get('text2', '')
    company = request.args.get('company', '')
    role = request.args.get('role', '')

    content = {
        'resume_data': text1,
        'job_description': text2
    }
    score = rate_resume(content)  # Here we need to refactor `rate_resume` function to accept arguments directly

    content = {
        'job_description': text2
    }
    leetcode_questions = leet_code(
        content)  # Here we need to refactor `leet_code` function to accept arguments directly

    interview_questions = interview_prep(
        content)  # Here we need to refactor `interview_prep` function to accept arguments directly

    content = {
        'company': company,
        'role': role
    }
    user_profiles = get_users(content)  # Here we need to refactor `get_users` function to accept arguments directly

    return render_template('info.html',
    score=score,
    leetcode_questions=leetcode_questions.split('\n'),
    interview_questions=interview_questions.split('\n'),
    user_profiles=user_profiles.split('\n'))
@app.route('/Rate_the_Resume', methods=['POST'])
def rate_resume(content):
    resume_data = content['resume_data']
    job_description = content['job_description']
    total_scores = 0
    # Replace resume data parsing here with your resume parser
    prompt = f"""I want you to act as an ats bot score the resume accordingly 
        based on the jod description mentioned 
        '
       1. Contact Information (10 points)
          Complete information including phone number, email, and address.
    
       2. Resume Format (10 points)
          Clear, concise, easy-to-read format with perfect spelling and grammar. 
    
       3. Work Experience (20 points)
          Relevant experience to the job posting, duration of prior work, and career progression.
    
       4. Education and Qualifications (15 points)
          Relevant education and degrees, certifications, and professional training. 
    
       5. Skills (20 points)
          Hard skills relevant to the job, technical skills, soft skills, and language skills.
    
       6. Achievements, Awards, and Recognition (10 points)
          Achievement in previous roles, awards, and recognitions.
    
       7. Personal Projects, Volunteer Work, Extracurricular Activities (5 points)
          Relevant activities that can demonstrate certain skills and traits required for the job.
    
       8. Resume Customization (5 points)
          Resume tailored specifically for the job position, showing an understanding of the job requirements.
    
       9. References (5 points)
       if provided or willingness to provide upon request.
    
       Total: 100 points
       Availability and quality of references'
    
    based on the above criteria i want you to score this resume(data obtained by our of resume ) .' {resume_data}'
    the job description is {job_description}
    
    I want to display it in a clean way format . only give this input nothing else 
    the format is '??/100' nothing else
"""
    count = 0
    for i in range(10):
        try:
            score_string = chat_gpt4(prompt)
            score = extract_score(score_string)
            total_scores += score
            count=count+1
        except:
            pass

    try:
        average_score = total_scores / count
    except:
        pass
    #print(count)
    return average_score

@app.route('/Leetcode_questions', methods=['POST'])
def leet_code(content):
    job_description = content['job_description']
    prompt=f"""the main thing here is i will give you a job description and you need to do all this process of generation of the questions.
    Envision yourself as a placement trainer for the college, assigned to curate a selection of coding queries gathered from platforms like LeetCode, GeeksforGeeks, and other competitive coding sources spanning the last five years. These questions should align with the recruitment standards of Company specifically for the role . It's essential to include references, and the chosen questions should cover a spectrum of difficulty levels, organized from easy to challenging, with a minimum of three questions for each level and a maximum of 4 questions. in output you just give me references nothing other than that, i dont even want those headings just give me references 
    i dont even want a single text other then those references (those references should be names with the question and as soon as we click on the question it should be redirected to that respective website.
    i want the reference link i dont want normal text explaining the question 
    {job_description}
    also remove those headings and include that website name in the reference link only 
    and i dont want the numbering  of those questions.
    remove the heading just simply give me the link.
    i will specify you a foormat and you need to follow that very strictly 
    1.link
    2.link
    .
    .
    .
    .
    .
    .etc 
    in this way results should be given"""
    response=chat_gpt3(prompt)
    """def get_links(response):
        try:
            links = re.findall("(?P<url>https?://[^\s]+)", response)
            return links
        except:
            leet_code()"""
    def get_links(response):
        try:
            links = re.findall("(?P<url>https?://[^\s]+)", response)
            return "\n".join(links) if links else "No links found"
        except:
            leet_code()
    return get_links(response)
@app.route('/interview_prep', methods=['POST'])
def interview_prep(content):
    job_description = content['job_description']
    prompt=f"""Generate 10 technical interview questions and 10 HR interview questions tailored to a Job description given
     {job_description}. 
        The questions should be more relevant to the skills and important for the interview point of view.Ensure that the technical questions cover a range of difficulty levels suitable for [Fresher], starting from easy and progressing to hard in the format of 
        1. question
        2. question
        .
        .
        .
        so on 
        without mentioning easy, medium, hard"""
    response = chat_gpt3(prompt)
    return response
@app.route('/get_users', methods=['POST'])
def get_users(content):
    def getit(url):
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        return soup.get_text()

    company = content['company']
    role = content["role"]
    site=f"https://www.google.com/search?q=linked+{company}+{role}+profiles&sca_esv=571626697&sxsrf=AM9HkKnjK0cKjuz23emrNlrEsAtNqSgOVw%3A1696720130971&ei=AuUhZdzyOv--4-EP7-yg8A0&ved=0ahUKEwjc-8GFh-WBAxV_3zgGHW82CN4Q4dUDCBA&uact=5&oq=linked+{company}+{role}+profiles&gs_lp=Egxnd3Mtd2l6LXNlcnAiK2xpbmtlZCBqcCBtb3JnYW4gc29mdHdhcmUgZW5naW5lZXIgcHJvZmlsZXMyBxAhGKABGApI-R1Q-AFY7htwAngBkAEAmAGUAaAB_wmqAQQwLjEwuAEDyAEA-AEBwgIKEAAYRxjWBBiwA8ICCBAAGAgYHhgNwgIIEAAYigUYhgPCAggQIRgWGB4YHeIDBBgAIEGIBgGQBgg&sclient=gws-wiz-serp"
    scraped_data = getit(site)
    #return scraped_data
    prompt=f"you will be given a data you have filter out all the names in the data and return them one by one.. the data is {scraped_data} .  *** Only return the names and nothing else ***"
    response = chat_gpt3(prompt)
    return response
@app.route('/chat_bot', methods=['GET'])
def chat_bot_page():
    return render_template('chat_bot.html')

@app.route('/chat', methods=['POST'])
def chat_bot():
    data = request.get_json()  # Get JSON data from the client-side
    user_message = data['user_message']
    prompt=f"you are a consultant chatbot who gives assistance on careers . the question is : '{user_message}'"
    message = chat_gpt3(prompt)  # Call the chat_gpt3 function with the user's message
    return {'message': message}  # return as json
if __name__ == '__main__':
    app.run(debug=True,port=8088)

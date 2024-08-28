# **Phishing Site Maker - Educational Tool**

## **Purpose:**

This project serves as an educational tool to raise awareness about phishing scams. It demonstrates how easily malicious actors can create deceptive replicas of legitimate websites to steal sensitive information.

## **Disclaimer:**

**UNDER NO CIRCUMSTANCES** should this tool be used for malicious purposes. Phishing is a serious crime that can have devastating consequences for victims. Always prioritize ethical use and responsible disclosure.

## **Installation:**

1. **Clone the repository:**

   ```bash
   git clone https://github.com/your-username/phishing-site-maker.git
   ```

2. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

### **Running the Project:**

1. **Navigate to the project directory:**

   ```bash
   cd phishing-site-maker
   ```

2. **Start the Flask development server:**

   ```bash
   python app.py
   ```

3. **Access the project in your browser:**

   The project will be available at `http://127.0.0.1:5000/`.

## **Project Structure:**

```
phishing-site-maker/
├── app.py                  (Main Python script)
├── description.md          (Extra info we wrote)
├── requirements.txt        (List of project dependencies)
├── TODO.md                 (Task list for future development)
└── static/
    └── css/
        └── style.css      (Stylesheet for the project)
└── templates/
    ├── about.html          (About page)
    ├── icon_code.html      (Phishing warning icon)
    └── index.html          (Main page)
```

## **How to Use:**

1. **Visit http://127.0.0.1:5000/ in your browser.**
2. **Enter the URL of a website you want to duplicate.**
3. **Click the "Duplicate" button.**

## **Functionality:**

- The project creates a visually similar replica of the entered website.
- Forms on the cloned site are modified to capture user input without actually submitting it to the original website.
- A clear warning message is displayed at the top of the generated phishing site to inform users that it's for educational purposes only.
- Upon form submission, the project displays a simulated "You have been phished!" page, reminding users to be cautious of their data online.

## **Educational Value:**

This project highlights:

- The relative ease of creating phishing websites.
- The importance of verifying website legitimacy before interacting with forms.

## **Ethical Considerations:**

- Use this tool responsibly for educational and awareness purposes only.
- Never deploy these generated phishing sites on a public server or use them in malicious attempts.
- Consider password-protecting your local development environment to prevent unauthorized access.

## **Disclaimer:**

While the project modifies forms to prevent data transmission, exercise caution when testing with websites that handle sensitive information. We cannot guarantee perfect functionality with all websites.

### **Stay safe online!**

## **Further Development (TODO.md):**

Refer to the TODO.md file for potential future enhancements to the project.

## **Contributing:**

Feel free to fork the repository and submit pull requests with your improvements.




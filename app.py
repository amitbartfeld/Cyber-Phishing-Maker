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


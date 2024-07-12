from flask import Flask, request, render_template, redirect, url_for, jsonify
from bs4 import BeautifulSoup
import os
import requests
import json
from langchain import LLMChain, PromptTemplate
from langchain.llms import GPT4All

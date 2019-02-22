# -*- coding: utf-8 -*-

from flask import Blueprint, render_template

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    return render_template('main/index.html')

@main_bp.route('explore')
def explore():
    return render_template('main/explore.html')
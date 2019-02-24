# -*- coding: utf-8 -*-

from flask import Blueprint, render_template
from betterme.decorators import permission_required

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    return render_template('main/index.html')

@main_bp.route('/explore')
@permission_required('ADMINISTER')
def explore():
    return render_template('main/explore.html')
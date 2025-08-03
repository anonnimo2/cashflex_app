
import os
from flask import Blueprint, request, jsonify
from jobs import distribuir_rendimentos

tasks_bp = Blueprint('tasks', __name__)

@tasks_bp.route('/run/distribuir-safe', methods=['GET'])
def run_distribuir_safe():
    secret = request.args.get('secret')
    if secret != os.getenv('TASK_SECRET'):
        return jsonify({'error': 'Unauthorized'}), 403

    distribuir_rendimentos()
    return jsonify({'status': 'Rendimentos distribuídos com sucesso'})


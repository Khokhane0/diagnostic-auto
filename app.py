from flask import Flask, render_template, jsonify, request
from obd_advanced import AdvancedOBDScanner
import threading
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = 'votre_cle_secrete_ici'

# Instance du scanner avancé
scanner = AdvancedOBDScanner()

# Cache des données
cache_data = {
    'timestamp': 0,
    'data': {},
    'vehicle_info': {}
}

data_lock = threading.Lock()

def update_data_background():
    """Thread de fond qui met à jour les données."""
    global cache_data
    
    while True:
        try:
            if scanner.is_connected():
                # Lecture de toutes les données
                new_data = scanner.read_all_data()
                
                with data_lock:
                    cache_data['data'] = new_data
                    cache_data['timestamp'] = time.time()
                    cache_data['vehicle_info'] = scanner.get_vehicle_info()
                
                logger.debug(f"✅ Données mises à jour")
            else:
                logger.debug("⚠️ Pas de connexion OBD")
                
        except Exception as e:
            logger.error(f"❌ Erreur mise à jour: {e}")
        
        time.sleep(0.5)

@app.route('/')
def dashboard():
    """Page principale."""
    return render_template('dashboard_advanced.html')

@app.route('/api/status')
def api_status():
    """Statut de la connexion."""
    return jsonify({
        'connected': scanner.is_connected(),
        'port': scanner.port,
        'vehicle_info': scanner.get_vehicle_info()
    })

@app.route('/api/data')
def api_data():
    """Toutes les données du véhicule."""
    with data_lock:
        return jsonify({
            'data': cache_data['data'],
            'timestamp': cache_data['timestamp'],
            'age': time.time() - cache_data['timestamp'] if cache_data['timestamp'] > 0 else -1
        })

@app.route('/api/connect', methods=['POST'])
def api_connect():
    """Connexion au véhicule."""
    try:
        data = request.get_json() or {}
        port = data.get('port')
        baudrate = data.get('baudrate', 38400)
        
        if port:
            scanner.port = port
        if baudrate:
            scanner.baudrate = baudrate
        
        success = scanner.connect()
        
        if success:
            with data_lock:
                cache_data['vehicle_info'] = scanner.get_vehicle_info()
        
        return jsonify({
            'success': success,
            'message': 'Connecté !' if success else 'Échec de la connexion',
            'vehicle_info': scanner.get_vehicle_info()
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/disconnect', methods=['POST'])
def api_disconnect():
    """Déconnexion."""
    scanner.disconnect()
    with data_lock:
        cache_data['data'] = {}
        cache_data['timestamp'] = 0
    
    return jsonify({'success': True})

@app.route('/api/read/<pid>')
def api_read_pid(pid):
    """Lit un PID spécifique."""
    if not scanner.is_connected():
        return jsonify({'error': 'Non connecté'}), 400
    
    result = scanner.read_standard_pid(pid)
    return jsonify(result)

@app.route('/api/dtc')
def api_dtc():
    """Récupère tous les codes d'erreur."""
    if not scanner.is_connected():
        return jsonify({'error': 'Non connecté'}), 400
    
    dtc = scanner.read_dtc()
    return jsonify(dtc)

@app.route('/api/clear_dtc', methods=['POST'])
def api_clear_dtc():
    """Efface les codes d'erreur."""
    if not scanner.is_connected():
        return jsonify({'error': 'Non connecté'}), 400
    
    data = request.get_json() or {}
    system = data.get('system', 'all')
    success = scanner.clear_dtc(system)
    
    return jsonify({
        'success': success,
        'message': 'Codes effacés' if success else 'Échec'
    })

@app.route('/api/service', methods=['POST'])
def api_service():
    """Exécute un service spécial."""
    if not scanner.is_connected():
        return jsonify({'error': 'Non connecté'}), 400
    
    data = request.get_json() or {}
    service_type = data.get('service')
    
    if not service_type:
        return jsonify({'error': 'Service non spécifié'}), 400
    
    result = scanner.execute_service(service_type)
    return jsonify(result)

@app.route('/api/systems')
def api_systems():
    """Liste des systèmes supportés."""
    return jsonify({
        'systems': scanner.get_supported_systems()
    })

@app.route('/api/advanced_read', methods=['POST'])
def api_advanced_read():
    """Lecture avancée avec mode et PID personnalisés."""
    if not scanner.is_connected():
        return jsonify({'error': 'Non connecté'}), 400
    
    data = request.get_json() or {}
    mode = data.get('mode')
    pid = data.get('pid')
    name = data.get('name', 'Lecture avancée')
    
    if not mode or not pid:
        return jsonify({'error': 'Mode et PID requis'}), 400
    
    result = scanner.read_advanced_pid(mode, pid, name)
    return jsonify(result)

@app.route('/api/vehicle_info')
def api_vehicle_info():
    """Informations complètes du véhicule."""
    return jsonify(scanner.get_vehicle_info())

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Route non trouvée'}), 404

def main():
    """Point d'entrée."""
    update_thread = threading.Thread(target=update_data_background, daemon=True)
    update_thread.start()
    
    logger.info("🚗 Diagnostic Auto Avancé")
    logger.info("🌐 Serveur: http://127.0.0.1:5000")
    logger.info("📊 Scanner OBD-II complet avec support ABS, Airbag, etc.")
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=False,
        threaded=True,
        use_reloader=False
    )

if __name__ == '__main__':
    main()
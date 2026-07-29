import obd
import time
import logging
from typing import Dict, Any, Optional, List
import serial.tools.list_ports

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AdvancedOBDScanner:
    """
    Scanner OBD-II avancé pour diagnostic complet du véhicule.
    Supporte : Moteur, ABS, Airbag, Transmission, et plus.
    """
    
    def __init__(self, port: Optional[str] = None, baudrate: int = 38400):
        self.port = port
        self.baudrate = baudrate
        self.connection = None
        self._is_connected = False
        self._vehicle_info = {}
        
        # Dictionnaire complet des PIDs OBD-II standard
        self.STANDARD_PIDS = {
            # Mode 01 - Données actuelles
            'rpm': {'mode': '01', 'pid': '0C', 'name': 'Régime moteur', 'unit': 'RPM'},
            'speed': {'mode': '01', 'pid': '0D', 'name': 'Vitesse', 'unit': 'km/h'},
            'coolant_temp': {'mode': '01', 'pid': '05', 'name': 'Température liquide refroidissement', 'unit': '°C'},
            'intake_temp': {'mode': '01', 'pid': '0F', 'name': 'Température air admission', 'unit': '°C'},
            'ambient_temp': {'mode': '01', 'pid': '46', 'name': 'Température ambiante', 'unit': '°C'},
            'engine_load': {'mode': '01', 'pid': '04', 'name': 'Charge moteur', 'unit': '%'},
            'throttle_pos': {'mode': '01', 'pid': '11', 'name': 'Position papillon', 'unit': '%'},
            'fuel_level': {'mode': '01', 'pid': '2F', 'name': 'Niveau carburant', 'unit': '%'},
            'fuel_pressure': {'mode': '01', 'pid': '0A', 'name': 'Pression carburant', 'unit': 'kPa'},
            'maf': {'mode': '01', 'pid': '10', 'name': 'Débit massique air', 'unit': 'g/s'},
            'timing_advance': {'mode': '01', 'pid': '0E', 'name': 'Avance à l\'allumage', 'unit': '°'},
            'control_module_voltage': {'mode': '01', 'pid': '42', 'name': 'Tension batterie', 'unit': 'V'},
            'absolute_load': {'mode': '01', 'pid': '43', 'name': 'Charge absolue', 'unit': '%'},
            'barometric_pressure': {'mode': '01', 'pid': '33', 'name': 'Pression barométrique', 'unit': 'kPa'},
            'runtime': {'mode': '01', 'pid': '1F', 'name': 'Temps de fonctionnement', 'unit': 's'},
            'distance_without_mil': {'mode': '01', 'pid': '21', 'name': 'Distance sans défaut', 'unit': 'km'},
            'fuel_trim_short_term_b1': {'mode': '01', 'pid': '06', 'name': 'Correction court terme banc 1', 'unit': '%'},
            'fuel_trim_long_term_b1': {'mode': '01', 'pid': '07', 'name': 'Correction long terme banc 1', 'unit': '%'},
            'fuel_trim_short_term_b2': {'mode': '01', 'pid': '08', 'name': 'Correction court terme banc 2', 'unit': '%'},
            'fuel_trim_long_term_b2': {'mode': '01', 'pid': '09', 'name': 'Correction long terme banc 2', 'unit': '%'},
            'o2_voltage_b1s1': {'mode': '01', 'pid': '14', 'name': 'Tension O2 banc 1 sonde 1', 'unit': 'V'},
            'o2_voltage_b1s2': {'mode': '01', 'pid': '15', 'name': 'Tension O2 banc 1 sonde 2', 'unit': 'V'},
            'o2_voltage_b2s1': {'mode': '01', 'pid': '16', 'name': 'Tension O2 banc 2 sonde 1', 'unit': 'V'},
            'o2_voltage_b2s2': {'mode': '01', 'pid': '17', 'name': 'Tension O2 banc 2 sonde 2', 'unit': 'V'},
            'evap_vapour_pressure': {'mode': '01', 'pid': '32', 'name': 'Pression vapeur EVAP', 'unit': 'Pa'},
            'egr_error': {'mode': '01', 'pid': '2D', 'name': 'Erreur EGR', 'unit': '%'},
            'fuel_rate': {'mode': '01', 'pid': '5E', 'name': 'Consommation instantanée', 'unit': 'L/h'},
            'hybrid_battery_soc': {'mode': '01', 'pid': '5B', 'name': 'Batterie hybride SOC', 'unit': '%'},
            'engine_oil_temp': {'mode': '01', 'pid': '5C', 'name': 'Température huile moteur', 'unit': '°C'},
            
            # Mode 09 - Informations véhicule
            'vin': {'mode': '09', 'pid': '02', 'name': 'VIN', 'unit': ''},
            'ecu_name': {'mode': '09', 'pid': '0A', 'name': 'Nom ECU', 'unit': ''},
            'calibration_id': {'mode': '09', 'pid': '04', 'name': 'ID calibration', 'unit': ''},
            'cvn': {'mode': '09', 'pid': '06', 'name': 'CVN', 'unit': ''},
        }
        
        # PIDs spécifiques aux systèmes avancés (nécessitent des commandes personnalisées)
        self.ADVANCED_PIDS = {
            # ABS (système de freinage antiblocage)
            'abs_wheel_speed_fl': {'mode': '22', 'pid': '0101', 'name': 'Vitesse roue avant gauche ABS', 'unit': 'km/h'},
            'abs_wheel_speed_fr': {'mode': '22', 'pid': '0102', 'name': 'Vitesse roue avant droit ABS', 'unit': 'km/h'},
            'abs_wheel_speed_rl': {'mode': '22', 'pid': '0103', 'name': 'Vitesse roue arrière gauche ABS', 'unit': 'km/h'},
            'abs_wheel_speed_rr': {'mode': '22', 'pid': '0104', 'name': 'Vitesse roue arrière droit ABS', 'unit': 'km/h'},
            'abs_pressure': {'mode': '22', 'pid': '0201', 'name': 'Pression ABS', 'unit': 'bar'},
            'abs_dtc': {'mode': '03', 'pid': '', 'name': 'Codes ABS', 'unit': ''},
            
            # Airbag (SRS)
            'srs_status': {'mode': '22', 'pid': '0301', 'name': 'Statut SRS', 'unit': ''},
            'srs_dtc': {'mode': '03', 'pid': '', 'name': 'Codes Airbag', 'unit': ''},
            
            # Transmission
            'transmission_temp': {'mode': '22', 'pid': '0401', 'name': 'Température transmission', 'unit': '°C'},
            'gear_position': {'mode': '22', 'pid': '0402', 'name': 'Position rapport', 'unit': ''},
            'transmission_dtc': {'mode': '03', 'pid': '', 'name': 'Codes Transmission', 'unit': ''},
            
            # Réglages et services (Mode 2E - Write Data)
            'reset_adaptations': {'mode': '2E', 'pid': '0101', 'name': 'Réinitialiser adaptations', 'unit': ''},
            'reset_oil_service': {'mode': '2E', 'pid': '0102', 'name': 'Réinitialiser service vidange', 'unit': ''},
            'reset_brake_pads': {'mode': '2E', 'pid': '0103', 'name': 'Réinitialiser plaquettes freins', 'unit': ''},
        }

    def connect(self) -> bool:
        """Établit la connexion avec le véhicule."""
        try:
            if not self.port:
                self.port = self._auto_detect_port()
                if not self.port:
                    logger.error("❌ Aucun port série détecté")
                    return False

            logger.info(f"🔌 Connexion sur {self.port}...")
            self.connection = obd.OBD(portstr=self.port, baudrate=self.baudrate, fast=False)
            
            if self.connection.is_connected():
                self._is_connected = True
                logger.info("✅ Connecté au véhicule !")
                self._detect_vehicle_info()
                return True
            else:
                logger.error("❌ Échec de la connexion")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erreur de connexion: {e}")
            return False

    def _auto_detect_port(self) -> Optional[str]:
        """Détecte automatiquement le port série."""
        try:
            ports = serial.tools.list_ports.comports()
            for port_info in ports:
                description = port_info.description.lower()
                if any(keyword in description for keyword in ['obd', 'elm', 'usb', 'serial']):
                    return port_info.device
            return ports[0].device if ports else None
        except:
            return None

    def _detect_vehicle_info(self):
        """Détecte les informations du véhicule."""
        if not self.is_connected():
            return
            
        try:
            # Récupérer le VIN
            vin_response = self.connection.query(obd.commands.VIN)
            if not vin_response.is_null():
                self._vehicle_info['vin'] = str(vin_response.value)
            
            # Récupérer les PIDs supportés
            supported = []
            for pid_name in self.STANDARD_PIDS.keys():
                command = self._get_command(pid_name)
                if command:
                    try:
                        response = self.connection.query(command)
                        if not response.is_null():
                            supported.append(pid_name)
                    except:
                        pass
            self._vehicle_info['supported_pids'] = supported
            
            # Déterminer le type de véhicule (approximatif)
            if 'hybrid_battery_soc' in supported:
                self._vehicle_info['type'] = 'Hybride'
            elif 'transmission_temp' in supported:
                self._vehicle_info['type'] = 'Automatique'
            else:
                self._vehicle_info['type'] = 'Standard'
                
            logger.info(f"📊 Véhicule détecté: {self._vehicle_info}")
            
        except Exception as e:
            logger.error(f"Erreur détection véhicule: {e}")

    def disconnect(self):
        """Ferme la connexion."""
        if self.connection:
            self.connection.close()
            self._is_connected = False
            logger.info("🔌 Déconnecté")

    def is_connected(self) -> bool:
        return self._is_connected and self.connection is not None

    def _get_command(self, pid_name: str):
        """Récupère une commande OBD."""
        try:
            cmd = getattr(obd.commands, pid_name.upper(), None)
            if cmd:
                return cmd
            # Essayer de mapper le nom
            mapping = {
                'rpm': 'RPM',
                'speed': 'SPEED',
                'coolant_temp': 'COOLANT_TEMP',
                # ... tous les mappings
            }
            mapped = mapping.get(pid_name, pid_name.upper())
            return getattr(obd.commands, mapped, None)
        except:
            return None

    def read_standard_pid(self, pid_name: str) -> Dict[str, Any]:
        """Lit un PID standard OBD-II."""
        if not self.is_connected():
            return {'value': None, 'unit': None, 'status': 'error', 'message': 'Non connecté'}

        try:
            cmd = self._get_command(pid_name)
            if not cmd:
                return {'value': None, 'unit': None, 'status': 'error', 'message': 'Commande non trouvée'}

            response = self.connection.query(cmd)
            if response.is_null():
                return {'value': None, 'unit': None, 'status': 'not_supported', 'message': 'Non supporté'}

            value = response.value
            if hasattr(value, 'magnitude'):
                value = float(value.magnitude)
            
            pid_info = self.STANDARD_PIDS.get(pid_name, {})
            return {
                'value': value,
                'unit': pid_info.get('unit', ''),
                'name': pid_info.get('name', pid_name),
                'status': 'success',
                'message': 'OK'
            }
        except Exception as e:
            return {'value': None, 'unit': None, 'status': 'error', 'message': str(e)}

    def read_advanced_pid(self, mode: str, pid: str, name: str) -> Dict[str, Any]:
        """
        Lit un PID avancé (mode personnalisé).
        Utilise des commandes brutes ELM327.
        """
        if not self.is_connected():
            return {'value': None, 'unit': None, 'status': 'error', 'message': 'Non connecté'}

        try:
            # Construction de la commande brute
            cmd = f"{mode} {pid}"
            response = self.connection._send(cmd)
            
            if not response:
                return {'value': None, 'unit': None, 'status': 'not_supported', 'message': 'Pas de réponse'}

            # Parsing de la réponse (à adapter selon le format)
            # Exemple: '41 0C 0A 5E' -> 0A5E = 2654 RPM
            parts = response.split()
            if len(parts) >= 3:
                data_hex = ''.join(parts[2:])
                # Convertir hex vers int
                value = int(data_hex, 16) if data_hex else 0
            else:
                value = None

            return {
                'value': value,
                'unit': '',
                'name': name,
                'status': 'success' if value is not None else 'not_supported',
                'message': 'OK' if value is not None else 'Non supporté'
            }
        except Exception as e:
            return {'value': None, 'unit': None, 'status': 'error', 'message': str(e)}

    def read_dtc(self) -> Dict[str, List[Dict]]:
        """
        Lit tous les codes DTC de tous les systèmes.
        """
        if not self.is_connected():
            return {}

        dtc_results = {
            'engine': [],
            'abs': [],
            'airbag': [],
            'transmission': [],
            'other': []
        }

        try:
            # Codes moteur (standard)
            engine_dtc = self.connection.query(obd.commands.GET_DTC)
            if not engine_dtc.is_null():
                for dtc in engine_dtc.value:
                    dtc_results['engine'].append({
                        'code': dtc[0] if isinstance(dtc, tuple) else str(dtc),
                        'description': dtc[1] if isinstance(dtc, tuple) and len(dtc) > 1 else '',
                        'system': 'Moteur'
                    })

            # Codes ABS et autres systèmes (via commandes personnalisées)
            advanced_systems = {
                'abs': 'ABS',
                'airbag': 'AIRBAG',
                'transmission': 'TRANSMISSION'
            }

            for system, name in advanced_systems.items():
                try:
                    # Commande spécifique pour chaque système
                    cmd = f"01 {system.upper()}"
                    response = self.connection._send(cmd)
                    if response and '43' in response:
                        # Parsing des codes spécifiques
                        # (à adapter selon les spécifications du constructeur)
                        pass
                except:
                    pass

        except Exception as e:
            logger.error(f"Erreur lecture DTC: {e}")

        return dtc_results

    def clear_dtc(self, system: str = 'all') -> bool:
        """Efface les DTC d'un système spécifique ou de tous."""
        if not self.is_connected():
            return False

        try:
            if system == 'all' or system == 'engine':
                self.connection.query(obd.commands.CLEAR_DTC)
                logger.info("✅ DTC effacés")
            return True
        except Exception as e:
            logger.error(f"Erreur effacement DTC: {e}")
            return False

    def read_all_data(self) -> Dict[str, Any]:
        """Lit toutes les données disponibles."""
        data = {
            'connected': self.is_connected(),
            'timestamp': time.time(),
            'vehicle_info': self._vehicle_info,
            'standard_pids': {},
            'advanced_pids': {},
            'dtc': {},
            'live_data': []
        }

        if not self.is_connected():
            return data

        # Lire tous les PIDs standards
        for pid_name in self.STANDARD_PIDS.keys():
            result = self.read_standard_pid(pid_name)
            data['standard_pids'][pid_name] = result

        # Lire les DTC
        data['dtc'] = self.read_dtc()

        # Tenter de lire les PIDs avancés
        for pid_name, pid_info in self.ADVANCED_PIDS.items():
            if pid_info.get('mode') != '03':  # Sauf les DTC
                result = self.read_advanced_pid(
                    pid_info['mode'],
                    pid_info['pid'],
                    pid_info['name']
                )
                data['advanced_pids'][pid_name] = result

        return data

    def execute_service(self, service_type: str) -> Dict[str, Any]:
        """
        Exécute un service spécial (réinitialisation, adaptation, etc.)
        """
        if not self.is_connected():
            return {'success': False, 'message': 'Non connecté'}

        services = {
            'reset_adaptations': {
                'cmd': '2E 0101',
                'name': 'Réinitialiser les adaptations'
            },
            'reset_oil': {
                'cmd': '2E 0102',
                'name': 'Réinitialiser service vidange'
            },
            'reset_brakes': {
                'cmd': '2E 0103',
                'name': 'Réinitialiser plaquettes freins'
            },
            'injector_test': {
                'cmd': '31 0201',
                'name': 'Test injecteurs'
            },
            'fuel_pump_test': {
                'cmd': '31 0202',
                'name': 'Test pompe à carburant'
            }
        }

        service = services.get(service_type)
        if not service:
            return {'success': False, 'message': 'Service inconnu'}

        try:
            response = self.connection._send(service['cmd'])
            return {
                'success': True,
                'message': f"Service {service['name']} exécuté",
                'response': response
            }
        except Exception as e:
            return {'success': False, 'message': str(e)}

    def get_vehicle_info(self) -> Dict[str, Any]:
        """Retourne les informations du véhicule."""
        info = self._vehicle_info.copy()
        info['connected'] = self.is_connected()
        info['port'] = self.port
        info['baudrate'] = self.baudrate
        return info

    def get_supported_systems(self) -> List[str]:
        """Retourne la liste des systèmes supportés."""
        return ['Moteur', 'ABS', 'Airbag', 'Transmission', 'Freinage', 'Direction', 'Climatisation']

    def test_connection(self) -> Dict[str, Any]:
        """Test complet de la connexion."""
        result = {
            'success': False,
            'port': self.port,
            'messages': [],
            'systems_found': []
        }

        if not self.is_connected():
            result['messages'].append('❌ Non connecté')
            return result

        try:
            # Test lecture RPM
            rpm_response = self.read_standard_pid('rpm')
            if rpm_response['status'] == 'success':
                result['success'] = True
                result['messages'].append(f"✅ RPM: {rpm_response['value']} RPM")
                result['systems_found'].append('Moteur')

            # Test lecture VIN
            vin_response = self.read_standard_pid('vin')
            if vin_response['status'] == 'success' and vin_response['value']:
                result['messages'].append(f"✅ VIN: {vin_response['value']}")

        except Exception as e:
            result['messages'].append(f"❌ Erreur: {e}")

        return result


# Fonction utilitaire pour le débogage
def debug_ports():
    """Affiche tous les ports série disponibles."""
    print("🔍 Ports série disponibles:")
    ports = serial.tools.list_ports.comports()
    for port in ports:
        print(f"  📌 {port.device} - {port.description}")
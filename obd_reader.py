import time
import logging
from typing import Dict, Any, Optional, List
import serial.tools.list_ports

# Import de obd avec gestion d'erreur
try:
    import obd
    OBD_AVAILABLE = True
    print(f" Bibliothèque obd version {obd.__version__} chargée")
except ImportError as e:
    OBD_AVAILABLE = False
    print(f" Erreur: {e}")
    print("Installez avec: pip install obd")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OBDFactory:
    """
    Gère la connexion et la communication avec le véhicule via le câble OBD-II.
    Utilise la bibliothèque 'obd' classique avec accès dynamique.
    """
    
    def __init__(self, port: Optional[str] = None, baudrate: int = 38400):
        """
        Initialise la connexion OBD.
        
        Args:
            port: Port série (ex: 'COM3' sous Windows, '/dev/ttyUSB0' sous Linux)
            baudrate: Vitesse de communication (défaut: 38400 pour ELM327)
        """
        self.port = port
        self.baudrate = baudrate
        self.connection = None
        self._is_connected = False
        
        # Dictionnaire des commandes avec leurs noms (sera résolu dynamiquement)
        self._command_names = {
            'rpm': 'RPM',
            'speed': 'SPEED',
            'coolant_temp': 'COOLANT_TEMP',
            'throttle_pos': 'THROTTLE_POS',
            'engine_load': 'ENGINE_LOAD',
            'fuel_level': 'FUEL_LEVEL',
            'fuel_pressure': 'FUEL_PRESSURE',
            'intake_temp': 'INTAKE_TEMP',
            'maf': 'MAF',
            'timing_advance': 'TIMING_ADVANCE',
            'vin': 'VIN',
            'runtime': 'RUN_TIME',
            'control_module_voltage': 'CONTROL_MODULE_VOLTAGE',
            'absolute_load': 'ABSOLUTE_LOAD',
            'ambient_temp': 'AMBIENT_TEMP',
            'barometric_pressure': 'BAROMETRIC_PRESSURE',
            'distance_without_mil': 'DISTANCE_WITHOUT_MIL',
            'fuel_trim_short_term_b1': 'SHORT_TERM_FUEL_TRIM_B1',
            'fuel_trim_long_term_b1': 'LONG_TERM_FUEL_TRIM_B1',
            'o2_voltage_b1s1': 'O2_B1S1',
            'o2_voltage_b1s2': 'O2_B1S2',
        }
        
        # Cache des commandes résolues
        self._command_cache = {}

    def _get_command(self, pid_name: str):
        """
        Récupère une commande OBD de manière dynamique.
        """
        if not OBD_AVAILABLE:
            return None
            
        # Vérifier si la commande est dans le cache
        if pid_name in self._command_cache:
            return self._command_cache[pid_name]
        
        # Récupérer le nom de la commande
        cmd_name = self._command_names.get(pid_name)
        if not cmd_name:
            logger.warning(f"Commande {pid_name} non trouvée dans le dictionnaire")
            return None
        
        try:
            # Accès dynamique à la commande
            command = getattr(obd.commands, cmd_name, None)
            if command is not None:
                self._command_cache[pid_name] = command
                return command
            else:
                logger.warning(f"Commande {cmd_name} non disponible dans obd.commands")
                return None
        except Exception as e:
            logger.error(f"Erreur lors de l'accès à la commande {cmd_name}: {e}")
            return None

    def connect(self) -> bool:
        """
        Établit la connexion avec le véhicule.
        
        Returns:
            bool: True si la connexion est réussie, False sinon.
        """
        if not OBD_AVAILABLE:
            logger.error(" Bibliothèque obd non disponible")
            return False
            
        try:
            # Si aucun port n'est spécifié, on détecte automatiquement
            if not self.port:
                self.port = self._auto_detect_port()
                if not self.port:
                    logger.error(" Aucun port série OBD-II détecté")
                    return False
                logger.info(f" Port détecté automatiquement: {self.port}")

            logger.info(f" Tentative de connexion sur {self.port} à {self.baudrate} bauds...")
            
            # Création de l'objet OBD
            self.connection = obd.OBD(portstr=self.port, baudrate=self.baudrate)
            
            # Vérification de la connexion
            if self.connection.is_connected():
                self._is_connected = True
                logger.info(" Connecté au véhicule !")
                
                # Test rapide pour vérifier la communication
                rpm_cmd = self._get_command('rpm')
                if rpm_cmd:
                    test_rpm = self.connection.query(rpm_cmd)
                    if not test_rpm.is_null():
                        logger.info(f" RPM: {test_rpm.value}")
                
                return True
            else:
                logger.error(" Échec de la connexion")
                return False
                
        except Exception as e:
            logger.error(f" Erreur de connexion: {e}")
            return False

    def _auto_detect_port(self) -> Optional[str]:
        """
        Détecte automatiquement le port série où est connecté le câble OBD-II.
        
        Returns:
            str: Nom du port détecté, ou None si non trouvé.
        """
        try:
            ports = serial.tools.list_ports.comports()
            
            if not ports:
                logger.warning(" Aucun port série trouvé")
                return None
            
            # Chercher un port qui ressemble à un adaptateur OBD
            for port_info in ports:
                port_name = port_info.device
                description = port_info.description.lower()
                
                # Mots-clés pour les adaptateurs OBD
                keywords = ['obd', 'elm', 'usb', 'serial', 'uart']
                if any(keyword in description for keyword in keywords):
                    logger.info(f" Port OBD potentiel: {port_name}")
                    return port_name
            
            # Si aucun port spécifique, prendre le premier port série
            first_port = ports[0].device
            logger.warning(f" Aucun port OBD spécifique détecté. Utilisation du premier port: {first_port}")
            return first_port
            
        except Exception as e:
            logger.error(f"Erreur lors de la détection automatique du port: {e}")
            return None

    def disconnect(self):
        """Ferme la connexion OBD."""
        if self.connection:
            try:
                self.connection.close()
            except Exception as e:
                logger.warning(f"Erreur lors de la fermeture: {e}")
            finally:
                self._is_connected = False
                self.connection = None
                logger.info("🔌 Déconnecté du véhicule")

    def is_connected(self) -> bool:
        """Vérifie si la connexion est active."""
        return self._is_connected and self.connection is not None

    def get_vin(self) -> Optional[str]:
        """
        Récupère le VIN du véhicule.
        
        Returns:
            str: Le VIN ou None si non disponible.
        """
        if not self.is_connected():
            return None
        
        try:
            vin_cmd = self._get_command('vin')
            if not vin_cmd:
                return None
                
            response = self.connection.query(vin_cmd)
            if response.is_null():
                return None
            return str(response.value)
        except Exception as e:
            logger.error(f"Erreur lors de la lecture du VIN: {e}")
            return None

    def read_pid(self, pid_name: str) -> Dict[str, Any]:
        """
        Lit une valeur PID spécifique.
        
        Args:
            pid_name: Nom de la commande (ex: 'rpm', 'speed')
            
        Returns:
            dict: Contient 'value', 'unit', 'status'
        """
        if not self.is_connected():
            return {
                'value': None,
                'unit': None,
                'status': 'error',
                'message': 'Non connecté'
            }

        try:
            command = self._get_command(pid_name)
            if not command:
                return {
                    'value': None,
                    'unit': None,
                    'status': 'error',
                    'message': f'Commande {pid_name} non supportée'
                }

            # Exécution de la requête
            response = self.connection.query(command)
            
            if response.is_null():
                return {
                    'value': None,
                    'unit': self._get_unit(pid_name),
                    'status': 'not_supported',
                    'message': 'Donnée non disponible'
                }
            
            # Récupération de la valeur (peut être un objet pint.Quantity)
            value = response.value
            unit = str(response.unit) if response.unit else self._get_unit(pid_name)
            
            # Si c'est un objet pint.Quantity, extraire la magnitude
            if hasattr(value, 'magnitude'):
                value = float(value.magnitude)
            elif value is not None:
                try:
                    value = float(value)
                except (ValueError, TypeError):
                    pass
            
            return {
                'value': value,
                'unit': unit,
                'status': 'success',
                'message': 'OK'
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la lecture de {pid_name}: {e}")
            return {
                'value': None,
                'unit': self._get_unit(pid_name),
                'status': 'error',
                'message': str(e)
            }

    def _get_unit(self, pid_name: str) -> str:
        """Retourne l'unité pour un PID donné."""
        units = {
            'rpm': 'RPM',
            'speed': 'km/h',
            'coolant_temp': '°C',
            'throttle_pos': '%',
            'engine_load': '%',
            'fuel_level': '%',
            'fuel_pressure': 'kPa',
            'intake_temp': '°C',
            'maf': 'g/s',
            'timing_advance': '°',
            'vin': '',
            'runtime': 's',
            'distance_without_mil': 'km',
            'control_module_voltage': 'V',
            'absolute_load': '%',
            'ambient_temp': '°C',
            'barometric_pressure': 'kPa',
            'fuel_trim_short_term_b1': '%',
            'fuel_trim_long_term_b1': '%',
            'o2_voltage_b1s1': 'V',
            'o2_voltage_b1s2': 'V',
        }
        return units.get(pid_name, '')

    def read_all_pids(self) -> Dict[str, Any]:
        """
        Lit tous les PIDs disponibles.
        
        Returns:
            dict: Toutes les données du véhicule.
        """
        data = {
            'connected': self.is_connected(),
            'data': {},
            'timestamp': time.time()
        }
        
        if not self.is_connected():
            return data
        
        # Lecture de tous les PIDs
        for pid_name in self._command_names.keys():
            # Ignorer VIN car on le lit séparément
            if pid_name == 'vin':
                continue
            result = self.read_pid(pid_name)
            data['data'][pid_name] = result
        
        # Lecture du VIN séparément
        vin = self.get_vin()
        if vin:
            data['data']['vin'] = {
                'value': vin,
                'unit': '',
                'status': 'success',
                'message': 'OK'
            }
        
        # Lecture des codes DTC
        dtc_result = self.read_dtc()
        if dtc_result:
            data['data']['dtc'] = dtc_result
        
        return data

    def read_dtc(self) -> List[Dict[str, str]]:
        """
        Récupère les codes d'erreur DTC.
        
        Returns:
            list: Liste des codes d'erreur avec leur description.
        """
        if not self.is_connected():
            return []
        
        try:
            # Utilisation de GET_DTC
            dtc_cmd = getattr(obd.commands, 'GET_DTC', None)
            if not dtc_cmd:
                return []
                
            response = self.connection.query(dtc_cmd)
            
            if response.is_null():
                return []
            
            dtc_list = []
            if isinstance(response.value, list):
                for dtc in response.value:
                    if isinstance(dtc, tuple) and len(dtc) >= 2:
                        dtc_list.append({
                            'code': str(dtc[0]),
                            'description': str(dtc[1])
                        })
                    elif isinstance(dtc, str):
                        dtc_list.append({
                            'code': dtc,
                            'description': 'Code d\'erreur'
                        })
                    else:
                        dtc_list.append({
                            'code': str(dtc),
                            'description': 'Code d\'erreur'
                        })
            else:
                # Format unique
                dtc_list.append({
                    'code': str(response.value),
                    'description': 'Code d\'erreur'
                })
            
            return dtc_list
            
        except Exception as e:
            logger.error(f"Erreur lors de la lecture des DTC: {e}")
            return []

    def clear_dtc(self) -> bool:
        """
        Efface tous les codes d'erreur.
        
        Returns:
            bool: True si réussi, False sinon.
        """
        if not self.is_connected():
            return False
        
        try:
            clear_cmd = getattr(obd.commands, 'CLEAR_DTC', None)
            if clear_cmd:
                self.connection.query(clear_cmd)
                logger.info(" Codes DTC effacés")
                return True
            return False
        except Exception as e:
            logger.error(f"Erreur lors de l'effacement des DTC: {e}")
            return False

    def get_supported_pids(self) -> List[str]:
        """
        Retourne la liste des PIDs supportés par le véhicule.
        
        Returns:
            list: Noms des PIDs supportés.
        """
        if not self.is_connected():
            return []
        
        supported = []
        for pid_name in self._command_names.keys():
            try:
                command = self._get_command(pid_name)
                if command:
                    response = self.connection.query(command)
                    if not response.is_null():
                        supported.append(pid_name)
            except Exception:
                # PID non supporté, on continue
                continue
        
        return supported

    def get_vehicle_info(self) -> Dict[str, Any]:
        """
        Récupère les informations générales du véhicule.
        
        Returns:
            dict: Informations du véhicule.
        """
        info = {
            'connected': self.is_connected(),
            'vin': self.get_vin(),
            'supported_pids': self.get_supported_pids(),
            'protocol': None
        }
        
        return info

    def test_connection(self) -> Dict[str, Any]:
        """
        Effectue un test de connexion complet.
        
        Returns:
            dict: Résultat du test avec tous les détails.
        """
        result = {
            'success': False,
            'port': self.port,
            'baudrate': self.baudrate,
            'messages': []
        }
        
        if not self.is_connected():
            result['messages'].append('❌ Non connecté')
            return result
        
        try:
            # Test de lecture d'un PID simple (RPM)
            test_pid = 'rpm'
            response = self.read_pid(test_pid)
            
            if response['status'] == 'success':
                result['success'] = True
                result['messages'].append(f' Test réussi - {test_pid}: {response["value"]} {response["unit"]}')
                result['test_value'] = response['value']
            else:
                result['messages'].append(f' Le PID {test_pid} n\'est pas disponible')
                
            # Test de lecture du VIN
            vin = self.get_vin()
            if vin:
                result['messages'].append(f' VIN récupéré: {vin}')
            else:
                result['messages'].append(' VIN non disponible')
                
        except Exception as e:
            result['messages'].append(f' Erreur lors du test: {e}')
        
        return result


# Fonction utilitaire pour le débogage
def debug_ports():
    """
    Affiche tous les ports série disponibles pour le débogage.
    """
    print(" Ports série disponibles:")
    ports = serial.tools.list_ports.comports()
    if not ports:
        print("  Aucun port série trouvé")
        return
    
    for port in ports:
        print(f"   {port.device}")
        print(f"     Description: {port.description}")
        print(f"     Manufacturer: {port.manufacturer}")
        print(f"     HWID: {port.hwid}")
        print(f" ")
import socket
import requests

class NetworkConfig:
    @staticmethod
    def detect_local_ip() -> str:
        try:
            # Способ 1: Внешний сервис для публичного IP
            public_ip = requests.get('https://api.ipify.org?format=json', timeout=3).json()['ip']
            # Способ 2: Локальный IP для LAN
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            return local_ip if public_ip.startswith(('192.168.', '10.', '172.16.')) else public_ip
        except:
            return "192.168.1.100"  # fallback
    
    @staticmethod
    def get_network_mode():
        """Определяет режим работы сети: direct, relay, offline, hybrid"""
        try:
            # Проверяем доступность локального inference сервера
            import os
            local_ip = os.getenv('LOCAL_INFERENCE_IP', 'auto_detect')
            
            if local_ip == 'auto_detect':
                detected_ip = NetworkConfig.detect_local_ip()
                # Если IP начинается с внутреннего диапазона и не localhost
                if detected_ip.startswith(('192.168.', '10.', '172.')) and detected_ip != '127.0.0.1':
                    return 'direct'  # LAN mode
                else:
                    return 'relay'  # Through VDS
            elif local_ip == 'offline':
                return 'offline'
            else:
                # Проверяем доступность по заданному IP
                return 'hybrid'
        except:
            return 'relay'  # default fallback